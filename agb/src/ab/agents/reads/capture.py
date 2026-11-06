"""Bounded public-only fetching, extraction, and durable capture jobs."""

import hashlib
import ipaddress
import socket
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

import urllib3

from .store import ReadsStore


class CaptureError(ValueError):
    def __init__(self, message: str, state: str = "failed"):
        super().__init__(message)
        self.state = state


def public_address(host: str, port: int) -> str:
    try:
        addresses = list(dict.fromkeys(result[4][0] for result in socket.getaddrinfo(
            host, port, type=socket.SOCK_STREAM
        )))
    except OSError as exc:
        raise CaptureError("DNS lookup failed") from exc
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise CaptureError("Public capture blocks private, loopback, and metadata destinations")
    return addresses[0]


def fetch_public(url: str) -> tuple[bytes, str]:
    deadline = time.monotonic() + 40
    for redirect in range(6):
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise CaptureError("Only public HTTP(S) URLs without credentials can be captured")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if port not in {80, 443}:
            raise CaptureError("Public capture only supports ports 80 and 443")
        address = public_address(parsed.hostname, port)
        pool_type = urllib3.HTTPSConnectionPool if parsed.scheme == "https" else urllib3.HTTPConnectionPool
        tls = {"server_hostname": parsed.hostname, "assert_hostname": parsed.hostname} if parsed.scheme == "https" else {}
        pool = pool_type(address, port, timeout=urllib3.Timeout(connect=5, read=5), **tls)
        response = None
        try:
            response = pool.urlopen("GET", (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else ""),
                                    headers={"Host": parsed.hostname, "User-Agent": "AgentBoxReads/0.1", "Accept-Encoding": "identity"},
                                    redirect=False, retries=False, preload_content=False)
            if response.status in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                if not location or redirect == 5:
                    raise CaptureError("Redirect limit or missing redirect destination")
                url = urljoin(url, location)
                if time.monotonic() > deadline:
                    raise CaptureError("Capture time limit exceeded")
                continue
            if response.status in {401, 403}:
                raise CaptureError("Page requires authorization; no browser cookies were sent", "login-required")
            if response.status >= 400:
                raise CaptureError(f"Page returned HTTP {response.status}", "unavailable")
            content_type = response.headers.get("Content-Type", "").split(";")[0].lower()
            if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
                raise CaptureError(f"Unsupported content type: {content_type or 'unknown'}", "unsupported")
            if response.headers.get("Content-Encoding", "identity").lower() not in {"identity", ""}:
                raise CaptureError("Compressed responses are not supported by public capture", "unsupported")
            chunks = []
            size = 0
            for chunk in response.stream(64 * 1024, decode_content=False):
                size += len(chunk)
                if size > 4 * 1024 * 1024 or time.monotonic() > deadline:
                    raise CaptureError("Capture exceeded size or time limit; partial text was not saved")
                chunks.append(chunk)
            body = b"".join(chunks)
            if content_type == "text/plain":
                import html
                body = ("<html><body><article><pre>" + html.escape(body.decode("utf-8", errors="replace")) + "</pre></article></body></html>").encode()
            return body, url
        except (urllib3.exceptions.HTTPError, OSError) as exc:
            raise CaptureError("Public request failed") from exc
        finally:
            if response is not None:
                response.close()
            pool.close()
    raise CaptureError("Redirect limit exceeded")


def extract_passages(body: bytes) -> list[dict]:
    import trafilatura

    extracted = trafilatura.extract(body, output_format="xml", include_tables=True,
                                    include_comments=False, include_formatting=True)
    if not extracted:
        raise CaptureError("No readable text extracted; rendered-page capture may be required", "unavailable")
    root = ElementTree.fromstring(extracted)
    main = root.find("main")
    if main is None:
        raise CaptureError("No article body extracted", "unavailable")
    heading = ""
    passages = []
    for node in main:
        text = " ".join(" ".join(node.itertext()).split())
        if node.tag == "head":
            heading = text
        if not text:
            continue
        for offset in range(0, len(text), 2200):
            passages.append({"heading": heading, "text": text[offset:offset + 2400]})
    if not passages:
        raise CaptureError("No readable passages extracted", "unavailable")
    return passages


def save_capture(store: ReadsStore, document: str, passages: list[dict], resolved_url: str,
                 local_only: bool = False):
    from importlib.metadata import version as package_version

    captured_at = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(str([(part["heading"], part["text"]) for part in passages]).encode()).hexdigest()
    version = hashlib.sha256(f"{document}:{digest}".encode()).hexdigest()
    with store.connect() as connection:
        connection.execute("""INSERT INTO versions VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET captured_at=excluded.captured_at,
            resolved_url=excluded.resolved_url, extractor=excluded.extractor""",
                           (version, document, digest, f"trafilatura/{package_version('trafilatura')}", captured_at, resolved_url))
        for position, part in enumerate(passages):
            connection.execute("INSERT OR IGNORE INTO passages VALUES (?, ?, ?, ?, ?)",
                               (f"{version}:{position}", version, part["heading"], part["text"], position))
        connection.execute("UPDATE documents SET capture_status='captured', last_error=NULL, captured_at=?, resolved_url=? WHERE id=?",
                           (captured_at, resolved_url, document))
        if local_only:
            connection.execute("UPDATE documents SET cloud_allowed=0 WHERE id=?", (document,))
        connection.execute("UPDATE jobs SET state='succeeded', lease_until=NULL, last_error=NULL WHERE document=?", (document,))
        store._reindex(connection)


def capture_pending(store: ReadsStore, document_id: str | None = None, limit: int = 10) -> dict:
    documents = store.documents()
    if document_id and not any(item["id"] == document_id for item in documents):
        raise ValueError("Unknown active document")
    selected = [item for item in documents if item["id"] == document_id or (
        not document_id and item["capture_status"] != "captured"
    )][:limit]
    outcomes = []
    for item in selected:
        now = time.time()
        with store.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            job = connection.execute("SELECT * FROM jobs WHERE document=?", (item["id"],)).fetchone()
            if job and ((job["state"] == "running" and (job["lease_until"] or 0) > now) or (
                not document_id and job["next_retry"] > now
            )):
                continue
            attempts = (job["attempts"] if job else 0) + 1
            connection.execute("""INSERT INTO jobs VALUES (?, 'running', ?, ?, 0, NULL)
                ON CONFLICT(document) DO UPDATE SET state='running', attempts=excluded.attempts,
                lease_until=excluded.lease_until""", (item["id"], attempts, now + 180))
            connection.execute("UPDATE documents SET capture_status='queued' WHERE id=?", (item["id"],))
        try:
            body, resolved = fetch_public(item["url"])
            passages = extract_passages(body)
            save_capture(store, item["id"], passages, resolved)
            outcomes.append({"document": item["id"], "state": "captured"})
        except Exception as exc:
            state = exc.state if isinstance(exc, CaptureError) else "failed"
            error = str(exc) if isinstance(exc, CaptureError) else "Extraction failed; retry capture"
            with store.connect() as connection:
                connection.execute("UPDATE documents SET capture_status=?, last_error=? WHERE id=?", (state, error, item["id"]))
                connection.execute("UPDATE jobs SET state='failed', lease_until=NULL, next_retry=?, last_error=? WHERE document=?",
                                   (now + min(3600, 30 * 2 ** min(attempts, 6)), error, item["id"]))
            outcomes.append({"document": item["id"], "state": state, "error": error})
    return {"outcomes": outcomes}