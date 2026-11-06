from pathlib import Path

import pytest

from ab.agents.reads.models import Snapshot
from ab.agents.reads.store import ReadsStore
from ab.agents.reads.capture import CaptureError, capture_pending, extract_passages, public_address, save_capture
from unittest.mock import patch
from ab.agents.reads.search import search
from ab.core.config import Settings
from ab.agents.reads.native import handle_message, read_message
from io import BytesIO
import struct
import time
from ab.agents.reads.assessment import decision_question, llm_assess


def snapshot(revision=1, items=None, **changes):
    return Snapshot.model_validate({
        "source_id": "synthetic", "profile_id": "profile-one", "folder_id": "reads-17",
        "revision": revision, "complete": True,
        "items": items if items is not None else [
            {"item_id": "one", "url": "https://example.org/reading?version=1#section", "title": "Latency numbers"}
        ], **changes,
    })


def test_idempotent_snapshot_preserves_capture(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    with store.connect() as connection:
        connection.execute("UPDATE documents SET capture_status='captured'")
    store.ingest(snapshot())
    assert len(store.documents()) == 1
    assert store.documents()[0]["capture_status"] == "captured"
    assert store.documents()[0]["url"] == "https://example.org/reading?version=1#section"


def test_partial_stale_and_conflicting_snapshots_do_not_remove_items(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot(revision=2))
    for invalid in [snapshot(3, [], complete=False), snapshot(1, []), snapshot(2, [])]:
        with pytest.raises(ValueError):
            store.ingest(invalid)
    assert len(store.documents()) == 1
    store.ingest(snapshot(3, []), dry_run=True)
    assert len(store.documents()) == 1
    store.ingest(snapshot(3, []))
    assert store.documents() == []


def test_duplicate_membership_keeps_document_active(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    first = snapshot()
    second = first.model_copy(update={"profile_id": "profile-two"})
    store.ingest(first)
    store.ingest(second)
    assert store.documents()[0]["membership_count"] == 2
    store.ingest(snapshot(2, []))
    assert store.documents()[0]["membership_count"] == 1


def test_failed_refresh_preserves_last_good_content(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    document = store.documents()[0]
    save_capture(store, document["id"], [{"heading": "Latency", "text": "A memory reference takes nanoseconds."}], document["url"])
    with patch("ab.agents.reads.capture.fetch_public", side_effect=CaptureError("offline")):
        result = capture_pending(store, document["id"])
    assert result["outcomes"][0]["state"] == "failed"
    assert store.passages(document["id"])[0]["text"] == "A memory reference takes nanoseconds."
    assert store.status()["captured"] == 1
    assert store.status()["jobs"][0]["state"] == "failed"


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "::ffff:127.0.0.1"])
def test_fetch_blocks_nonpublic_dns(address):
    with patch("ab.agents.reads.capture.socket.getaddrinfo", return_value=[(2, 1, 6, "", (address, 443))]):
        with pytest.raises(CaptureError, match="blocks"):
            public_address("example.org", 443)


def test_extraction_keeps_source_text():
    paragraphs = " ".join(["A memory reference takes nanoseconds while a network round trip takes milliseconds."] * 12)
    passages = extract_passages(f"<html><body><article><h1>Latency</h1><p>{paragraphs}</p></article></body></html>".encode())
    assert any("A memory reference takes nanoseconds" in part["text"] for part in passages)


def test_lexical_search_quotes_and_membership(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    document = store.documents()[0]
    save_capture(store, document["id"], [{"heading": "API", "text": "Use realtime_session.create to start a session."}], document["url"])
    result = search(store, Settings(_env_file=None), "realtime_session.create")
    assert result["results"][0]["excerpt"] == "Use realtime_session.create to start a session."
    assert search(store, Settings(_env_file=None), "nonexistent") ["results"] == []
    store.ingest(snapshot(2, []))
    assert search(store, Settings(_env_file=None), "realtime_session.create")["results"] == []


def test_privacy_and_unconfigured_provider_never_call_cloud(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    settings = Settings(_env_file=None, azure_openai_endpoint="https://example.org")
    with patch("ab.agents.reads.search.llm_assess") as assess:
        search(store, settings, "Latency", provider="llm", local_only=False)
        document = store.documents()[0]
        store.update_policy(document["id"], "", True)
        search(store, settings, "Latency", provider="llm", local_only=True)
        result = search(store, settings, "Latency", provider="decision", local_only=False)
    assess.assert_not_called()
    assert result["mode"] == "lexical-only"


def test_model_invalid_evidence_degrades_visibly(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    document = store.documents()[0]
    store.update_policy(document["id"], "", True)
    settings = Settings(_env_file=None, azure_openai_endpoint="https://example.org")
    with patch("ab.agents.reads.search.llm_assess", side_effect=ValueError("invalid quote")):
        result = search(store, settings, "Latency", provider="llm", local_only=False)
    assert result["partial"]
    assert result["calls"] == 1
    assert result["mode"] == "lexical-only"


def test_native_bridge_rejects_arbitrary_actions_and_oversized_frames(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    for message in [{"action": "fetch", "url": "http://localhost"}, {"action": "capture", "url": "https://unknown.org", "html": "private"}]:
        with pytest.raises(ValueError):
            handle_message(store, message)
    with pytest.raises(ValueError, match="too large"):
        read_message(BytesIO(struct.pack("<I", 2 * 1024 * 1024)))
    with pytest.raises(ValueError, match="Incomplete"):
        read_message(BytesIO(b"\x01"))


def test_changing_selected_folder_excludes_old_subtree(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    changed = snapshot(2, [{"item_id": "new", "url": "https://example.org/new", "title": "New selection"}], folder_id="different-folder")
    preview = store.ingest(changed, dry_run=True)
    assert preview["removed"] == 1
    assert store.documents()[0]["title"] == "Latency numbers"
    store.ingest(changed)
    assert [item["title"] for item in store.documents()] == ["New selection"]
    assert len(store.sources()) == 1
    with pytest.raises(ValueError, match="Stale"):
        store.ingest(snapshot())


def test_title_match_does_not_fabricate_content_evidence(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    document = store.documents()[0]
    save_capture(store, document["id"], [{"heading": "Unrelated", "text": "A reference about sorting algorithms."}], document["url"])
    result = search(store, Settings(_env_file=None), "Latency")
    assert result["results"][0]["category"] == "metadata-only"
    assert result["results"][0]["excerpt"] is None


def test_llm_rejects_unknown_ids_and_invented_quotes():
    settings = Settings(_env_file=None, azure_openai_endpoint="https://example.org")
    pack = {"document_id": "one", "passages": [{"id": "p1", "text": "Original source text"}]}
    base = {"document_id": "one", "relevance": "direct", "sufficient": "yes", "constraint": "no", "passage_id": "p1", "quote": "Original source text"}
    import json
    for change in [{"document_id": "invented"}, {"passage_id": "invented"}, {"quote": "Invented quotation"}]:
        native = {"choices": [{"message": {"content": json.dumps(base | change)}}]}
        with patch("ab.agents.reads.assessment._post", return_value=native), pytest.raises(ValueError):
            llm_assess(settings, pack, 10)


def test_decision_mapping_validates_all_option_probabilities():
    settings = Settings(_env_file=None, reads_decision_endpoint="https://example.org/infer",
                        reads_decision_request_template='{"input":"$context","question":"$question","options":"$options","model":"$deployment"}',
                        reads_decision_response_path="result.probabilities")
    with patch("ab.agents.reads.assessment._post", return_value={"result": {"probabilities": {"yes": 0.8, "no": 0.2}}}) as post:
        answer, native = decision_question(settings, "Approved text", "Relevant?", ["yes", "no"], 10)
    assert answer == "yes"
    assert post.call_args.args[1]["input"] == "Approved text"
    assert native["distribution"]["yes"] == 0.8
    for distribution in [{"yes": 1}, {"yes": float("nan"), "no": 0.2}, {"yes": 0.8, "no": 0.8}]:
        with patch("ab.agents.reads.assessment._post", return_value={"result": {"probabilities": distribution}}), pytest.raises(ValueError):
            decision_question(settings, "Approved text", "Relevant?", ["yes", "no"], 10)


def test_all_document_assessment_has_explicit_call_budget(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot(items=[{"item_id": str(index), "title": f"Document {index}", "url": f"https://example.org/{index}"} for index in range(4)]))
    for document in store.documents():
        save_capture(store, document["id"], [{"heading": "Evidence", "text": "The relevant original evidence."}], document["url"])
        store.update_policy(document["id"], "", True)
    settings = Settings(_env_file=None, azure_openai_endpoint="https://example.org", reads_max_calls=2)
    def assess(settings, pack, timeout):
        return {"document_id": pack["document_id"], "relevance": "direct", "sufficient": "yes", "constraint": "no", "passage_id": pack["passages"][0]["id"], "quote": "original evidence"}, {}
    with patch("ab.agents.reads.search.llm_assess", side_effect=assess):
        result = search(store, settings, "paraphrase with no lexical matches", provider="llm", local_only=False)
    assert result["calls"] == 2
    assert result["partial"]
    assert result["assessed_packs"] == 2
    assert result["eligible_packs"] == 4
    assert len(result["results"]) == 2


def test_capture_lease_skips_live_job_and_recovers_interruption(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    document = store.documents()[0]
    with store.connect() as connection:
        connection.execute("INSERT INTO jobs VALUES (?, 'running', 1, ?, 0, NULL)", (document["id"], time.time() + 120))
    with patch("ab.agents.reads.capture.fetch_public") as fetch:
        assert capture_pending(store)["outcomes"] == []
        fetch.assert_not_called()
    with store.connect() as connection:
        connection.execute("UPDATE jobs SET lease_until=0")
    with patch("ab.agents.reads.capture.fetch_public", side_effect=CaptureError("offline")):
        assert capture_pending(store)["outcomes"][0]["state"] == "failed"
    assert store.status()["jobs"][0]["attempts"] == 2


def test_redirect_destinations_are_revalidated():
    from ab.agents.reads.capture import fetch_public
    from unittest.mock import Mock
    response = Mock(status=302, headers={"Location": "http://169.254.169.254/latest/meta-data/"})
    with patch("ab.agents.reads.capture.public_address", side_effect=["93.184.216.34", CaptureError("blocked redirect")]) as resolve, patch("ab.agents.reads.capture.urllib3.HTTPSConnectionPool") as pool:
        pool.return_value.urlopen.return_value = response
        with pytest.raises(CaptureError, match="blocked redirect"):
            fetch_public("https://example.org")
    assert resolve.call_count == 2


def test_recapturing_prior_content_selects_latest_success_and_resets_rendered_privacy(tmp_path: Path):
    store = ReadsStore(tmp_path / "reads.db")
    store.ingest(snapshot())
    document = store.documents()[0]
    first = [{"heading": "Version A", "text": "Original evidence."}]
    second = [{"heading": "Version B", "text": "Changed evidence."}]
    save_capture(store, document["id"], first, document["url"])
    save_capture(store, document["id"], second, document["url"])
    store.update_policy(document["id"], "Private notes", True)
    save_capture(store, document["id"], first, document["url"], local_only=True)
    assert store.passages(document["id"])[0]["text"] == "Original evidence."
    assert store.documents()[0]["cloud_allowed"] == 0
    assert store.documents()[0]["note"] == "Private notes"