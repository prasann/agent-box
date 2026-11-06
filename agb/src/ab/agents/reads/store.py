"""Transactional collection storage; exact URLs are document identities."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import Snapshot


class ReadsStore:
    def __init__(self, path: Path):
        self.path = path.expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
                    profile_id TEXT NOT NULL, folder_id TEXT NOT NULL,
                    revision INTEGER NOT NULL, digest TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, url TEXT UNIQUE NOT NULL,
                    note TEXT NOT NULL DEFAULT '', cloud_allowed INTEGER NOT NULL DEFAULT 0,
                    capture_status TEXT NOT NULL DEFAULT 'metadata-only',
                    last_error TEXT, captured_at TEXT, resolved_url TEXT
                );
                CREATE TABLE IF NOT EXISTS memberships (
                    source TEXT NOT NULL REFERENCES sources(id), item_id TEXT NOT NULL,
                    document TEXT NOT NULL REFERENCES documents(id), title TEXT NOT NULL,
                    folder_path TEXT NOT NULL, saved_at TEXT, active INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY(source, item_id)
                );
                CREATE TABLE IF NOT EXISTS versions (
                    id TEXT PRIMARY KEY, document TEXT NOT NULL REFERENCES documents(id),
                    content_hash TEXT NOT NULL, extractor TEXT NOT NULL, captured_at TEXT NOT NULL,
                    resolved_url TEXT NOT NULL, UNIQUE(document, content_hash)
                );
                CREATE TABLE IF NOT EXISTS passages (
                    id TEXT PRIMARY KEY, version TEXT NOT NULL REFERENCES versions(id),
                    heading TEXT NOT NULL, text TEXT NOT NULL, position INTEGER NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS reading_fts USING fts5(
                    document UNINDEXED, passage UNINDEXED, title, url, note, heading, text,
                    tokenize='unicode61'
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    document TEXT PRIMARY KEY REFERENCES documents(id),
                    state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    lease_until REAL, next_retry REAL NOT NULL DEFAULT 0, last_error TEXT
                );
            """)
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def ingest(self, snapshot: Snapshot, dry_run: bool = False) -> dict:
        if not snapshot.complete:
            raise ValueError("Only complete snapshots can be accepted; no memberships changed")
        source = hashlib.sha256(json.dumps([
            snapshot.source_id, snapshot.profile_id, snapshot.folder_id
        ]).encode()).hexdigest()
        digest = hashlib.sha256(json.dumps(
            sorted((item.model_dump(mode="json") for item in snapshot.items), key=lambda item: item["item_id"]),
            sort_keys=True,
        ).encode()).hexdigest()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute("SELECT * FROM sources WHERE id = ?", (source,)).fetchone()
            latest = connection.execute("SELECT MAX(revision) FROM sources WHERE source_id=? AND profile_id=?",
                                        (snapshot.source_id, snapshot.profile_id)).fetchone()[0]
            if latest is not None and snapshot.revision < latest:
                raise ValueError("Stale snapshot revision for this profile")
            if previous and snapshot.revision < previous["revision"]:
                raise ValueError("Stale snapshot revision")
            if previous and snapshot.revision == previous["revision"] and digest != previous["digest"]:
                raise ValueError("Revision already accepted with different content")
            old_ids = {row[0] for row in connection.execute(
                "SELECT m.item_id FROM memberships m JOIN sources s ON s.id=m.source WHERE s.source_id=? AND s.profile_id=? AND m.active=1",
                (snapshot.source_id, snapshot.profile_id)
            )}
            new_ids = {item.item_id for item in snapshot.items}
            result = {"source": source, "count": len(new_ids), "added": len(new_ids - old_ids),
                      "removed": len(old_ids - new_ids), "dry_run": dry_run}
            if dry_run:
                return result
            connection.execute(
                "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision, digest=excluded.digest",
                (source, snapshot.source_id, snapshot.profile_id, snapshot.folder_id, snapshot.revision, digest),
            )
            connection.execute("""UPDATE memberships SET active = 0 WHERE source IN (
                SELECT id FROM sources WHERE source_id=? AND profile_id=?
            )""", (snapshot.source_id, snapshot.profile_id))
            for item in snapshot.items:
                document = hashlib.sha256(item.url.encode()).hexdigest()
                connection.execute("INSERT OR IGNORE INTO documents(id, url) VALUES (?, ?)", (document, item.url))
                connection.execute("""
                    INSERT INTO memberships VALUES (?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(source, item_id) DO UPDATE SET document=excluded.document,
                    title=excluded.title, folder_path=excluded.folder_path,
                    saved_at=excluded.saved_at, active=1
                """, (source, item.item_id, document, item.title, item.folder_path,
                      item.saved_at.isoformat() if item.saved_at else None))
            self._reindex(connection)
            return result

    def sources(self) -> list[dict]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute("""SELECT s.* FROM sources s
                WHERE revision=(SELECT MAX(revision) FROM sources WHERE source_id=s.source_id AND profile_id=s.profile_id)
                ORDER BY id""")]

    def documents(self) -> list[dict]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute("""
                SELECT d.*, (SELECT m.title FROM memberships m WHERE m.document=d.id AND m.active=1
                ORDER BY m.source, m.item_id LIMIT 1) AS title,
                (SELECT COUNT(*) FROM memberships m WHERE m.document=d.id AND m.active=1) AS membership_count
                FROM documents d WHERE EXISTS (
                    SELECT 1 FROM memberships m WHERE m.document=d.id AND m.active=1
                ) ORDER BY title, d.id
            """)]

    def _reindex(self, connection):
        connection.execute("DELETE FROM reading_fts")
        connection.execute("""
            INSERT INTO reading_fts(document, passage, title, url, note, heading, text)
            SELECT d.id, COALESCE(p.id, ''), m.title, d.url, d.note,
                   COALESCE(p.heading, ''), COALESCE(p.text, '')
            FROM documents d JOIN memberships m ON m.document=d.id AND m.active=1
            LEFT JOIN versions v ON v.id=(SELECT id FROM versions WHERE document=d.id
                ORDER BY captured_at DESC, rowid DESC LIMIT 1)
            LEFT JOIN passages p ON p.version=v.id
        """)

    def update_policy(self, document: str, note: str, cloud_allowed: bool):
        with self.connect() as connection:
            if not connection.execute("SELECT 1 FROM documents WHERE id=?", (document,)).fetchone():
                raise ValueError("Unknown document")
            connection.execute("UPDATE documents SET note=?, cloud_allowed=? WHERE id=?",
                               (note, int(cloud_allowed), document))
            self._reindex(connection)

    def passages(self, document: str) -> list[dict]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute("""
                SELECT p.* FROM passages p WHERE version=(SELECT id FROM versions
                WHERE document=? ORDER BY captured_at DESC, rowid DESC LIMIT 1)
                ORDER BY position
            """, (document,))]

    def status(self) -> dict:
        documents = self.documents()
        with self.connect() as connection:
            jobs = [dict(row) for row in connection.execute("SELECT * FROM jobs ORDER BY document")]
        return {"total": len(documents), "captured": sum(bool(self.passages(item["id"])) for item in documents),
                "sources": self.sources(), "documents": documents, "jobs": jobs}