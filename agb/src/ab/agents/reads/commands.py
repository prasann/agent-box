"""Reads CLI; all collection logic is shared with Control Center."""

import json
import re
import shlex
import sys
from pathlib import Path

import click

from ab.core.config import get_settings

from .capture import capture_pending
from .models import Snapshot
from .native import HOST_NAME
from .search import search
from .store import ReadsStore


def store() -> ReadsStore:
    return ReadsStore(Path(get_settings().reads_db))


def emit(value):
    click.echo(json.dumps(value, indent=2, ensure_ascii=True))


@click.group("reads")
def reads_group():
    """Search saved readings with original-text evidence."""


@reads_group.command("sources")
def sources():
    """List accepted source/profile/folder identities."""
    emit(store().sources())


@reads_group.command("sync")
@click.argument("snapshot_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True)
def sync(snapshot_file: Path, dry_run: bool):
    """Accept an adapter JSON snapshot (also useful for synthetic fixtures)."""
    try:
        if snapshot_file.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("Snapshot exceeds 4 MB")
        emit(store().ingest(Snapshot.model_validate_json(snapshot_file.read_text()), dry_run))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@reads_group.command("status")
def status():
    """Show collection, capture coverage, jobs, and last errors."""
    emit(store().status())


@reads_group.command("capture")
@click.option("--pending", is_flag=True, help="Capture pending public pages (default).")
@click.option("--document", default=None, help="Retry/refresh one document ID.")
@click.option("--limit", default=10, type=click.IntRange(1, 50))
def capture(pending: bool, document: str | None, limit: int):
    """Fetch public pages without browser credentials."""
    result = capture_pending(store(), document, limit)
    emit(result)
    if any(item["state"] != "captured" for item in result["outcomes"]):
        raise click.ClickException("Some captures failed; last good content was retained")


@reads_group.command("search")
@click.argument("query")
@click.option("--provider", type=click.Choice(["lexical", "llm", "decision"]), default="lexical")
@click.option("--local-only/--allow-cloud", default=True)
@click.option("--constraints", default="")
@click.option("--limit", default=5, type=click.IntRange(1, 20))
def search_command(query: str, provider: str, local_only: bool, constraints: str, limit: int):
    """Recall a saved reading. Cloud mode still requires per-item approval."""
    result = search(store(), get_settings(), query, provider, local_only, constraints, limit)
    result.pop("diagnostics", None)
    emit(result)


@reads_group.command("policy")
@click.argument("document")
@click.option("--note", default="")
@click.option("--allow-cloud/--local-only", default=False)
def policy(document: str, note: str, allow_cloud: bool):
    """Set a reading's note and explicit cloud-processing permission."""
    store().update_policy(document, note, allow_cloud)
    emit({"document": document, "cloud_allowed": allow_cloud})


@reads_group.command("evaluate")
@click.argument("evaluation_file", type=click.Path(exists=True, path_type=Path, dir_okay=False))
@click.option("--provider", type=click.Choice(["lexical", "llm", "decision"]), default="lexical")
@click.option("--local-only/--allow-cloud", default=True)
def evaluate(evaluation_file: Path, provider: str, local_only: bool):
    """Run local JSON cases with query, expected_ids, and optional constraints."""
    cases = json.loads(evaluation_file.read_text())
    results = []
    collection = store()
    for case in cases:
        result = search(collection, get_settings(), case["query"], provider, local_only,
                        case.get("constraints", ""), limit=3)
        expected = set(case["expected_ids"])
        found = {item["id"] for item in result["results"]}
        result["retrieval_passed"] = bool(expected & found) if expected else not found
        result["assessor_completed"] = not result["partial"] and (
            provider == "lexical" or (result["mode"] == provider and result["calls"] > 0
                                       and result["assessed_packs"] == result["eligible_packs"])
        )
        result["passed"] = result["retrieval_passed"] and result["assessor_completed"]
        results.append(result)
    emit({"passed": sum(result["passed"] for result in results), "total": len(results), "cases": results})


@reads_group.command("install-edge-host")
@click.argument("extension_id")
def install_edge_host(extension_id: str):
    """Register this Python installation as Edge's native host (macOS)."""
    if sys.platform != "darwin" or not re.fullmatch(r"[a-p]{32}", extension_id):
        raise click.ClickException("Requires macOS and the 32-character ID from edge://extensions")
    root = Path.home() / ".agb" / "reads" / "native-host"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    launcher = root / "host.sh"
    launcher.write_text("#!/bin/sh\n" + f"export AB_READS_EXTENSION_ID={extension_id}\n" +
                        f"export AB_READS_DB={shlex.quote(get_settings().reads_db)}\n" +
                        f"exec {shlex.quote(sys.executable)} -m ab.agents.reads.native \"$@\"\n")
    launcher.chmod(0o700)
    manifests = Path.home() / "Library/Application Support/Microsoft Edge/NativeMessagingHosts"
    manifests.mkdir(parents=True, exist_ok=True)
    manifest = manifests / f"{HOST_NAME}.json"
    manifest.write_text(json.dumps({"name": HOST_NAME, "description": "Agent Box Reads collection sync",
                                    "path": str(launcher), "type": "stdio",
                                    "allowed_origins": [f"chrome-extension://{extension_id}/"]}, indent=2))
    emit({"manifest": str(manifest), "launcher": str(launcher)})