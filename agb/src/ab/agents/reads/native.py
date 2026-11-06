"""Narrow native-messaging bridge for the authorized Edge extension."""

import json
import re
import struct
import sys
from pathlib import Path

from ab.core.config import get_settings

from .capture import extract_passages, save_capture
from .models import Snapshot
from .store import ReadsStore

HOST_NAME = "com.agentbox.reads"
MAX_MESSAGE = 1024 * 1024


def handle_message(store: ReadsStore, message: dict) -> dict:
    action = message.get("action")
    if action == "snapshot":
        snapshot = Snapshot.model_validate(message["snapshot"])
        if snapshot.source_id != "edge":
            raise ValueError("Native host only accepts Edge snapshots")
        return store.ingest(snapshot)
    if action == "capture":
        url, body = message.get("url"), message.get("html")
        document = next((item for item in store.documents() if item["url"] == url), None)
        if not document or not isinstance(body, str) or len(body.encode()) > 800_000:
            raise ValueError("Rendered capture requires an active saved URL and at most 800 KB of HTML")
        save_capture(store, document["id"], extract_passages(body.encode()), url, local_only=True)
        return {"document": document["id"], "state": "captured"}
    raise ValueError("Unsupported native action")


def read_message(stream):
    header = stream.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise ValueError("Incomplete native message header")
    length = struct.unpack("<I", header)[0]
    if length > MAX_MESSAGE:
        raise ValueError("Native message too large")
    body = stream.read(length)
    if len(body) != length:
        raise ValueError("Incomplete native message")
    message = json.loads(body)
    if not isinstance(message, dict):
        raise ValueError("Native message must be an object")
    return message


def main():
    settings = get_settings()
    origin = sys.argv[1] if len(sys.argv) > 1 else ""
    if not re.fullmatch(r"[a-p]{32}", settings.reads_extension_id) or origin != f"chrome-extension://{settings.reads_extension_id}/":
        return 1
    store = ReadsStore(Path(settings.reads_db))
    while True:
        try:
            message = read_message(sys.stdin.buffer)
            if message is None:
                return 0
            try:
                result = {"ok": True, "result": handle_message(store, message)}
            except (ValueError, KeyError):
                result = {"ok": False, "error": "Snapshot or capture rejected; review the collection and retry"}
        except ValueError:
            return 1
        encoded = json.dumps(result).encode()
        sys.stdout.buffer.write(struct.pack("<I", len(encoded)) + encoded)
        sys.stdout.buffer.flush()


if __name__ == "__main__":
    sys.exit(main())