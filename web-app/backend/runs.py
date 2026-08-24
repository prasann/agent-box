"""In-memory job tracking for long-running local agent actions."""

import json
import threading
import uuid
from collections.abc import Callable, Generator
from datetime import datetime, timezone
from typing import Any


class RunStore:
    """Track local background jobs and expose their event history."""

    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start(
        self,
        agent_id: str,
        action_id: str,
        target: Callable[[Callable[[str, dict[str, Any]], None]], Any],
    ) -> dict[str, Any]:
        run_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        run = {
            "id": run_id,
            "agent_id": agent_id,
            "action_id": action_id,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "result": None,
            "error": None,
            "events": [],
        }
        with self._lock:
            self._runs[run_id] = run
        self._event(run_id, "queued", {"message": "Run queued"})

        thread = threading.Thread(
            target=self._execute,
            args=(run_id, target),
            daemon=True,
            name=f"mission-control-{run_id[:8]}",
        )
        thread.start()
        return self.get(run_id)

    def _execute(
        self,
        run_id: str,
        target: Callable[[Callable[[str, dict[str, Any]], None]], Any],
    ) -> None:
        self._set_status(run_id, "running")
        self._event(run_id, "running", {"message": "Run started"})
        try:
            result = target(lambda event, data: self._event(run_id, event, data))
            with self._lock:
                self._runs[run_id]["result"] = result
            self._set_status(run_id, "completed")
            self._event(run_id, "completed", {"message": "Run completed", "result": result})
        except Exception as exc:
            with self._lock:
                self._runs[run_id]["error"] = str(exc)
            self._set_status(run_id, "failed")
            self._event(run_id, "failed", {"message": str(exc)})

    def _set_status(self, run_id: str, status: str) -> None:
        with self._lock:
            self._runs[run_id]["status"] = status
            self._runs[run_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    def _event(self, run_id: str, event: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._runs[run_id]["events"].append(
                {
                    "event": event,
                    "data": data,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            self._runs[run_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    def get(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise KeyError(run_id)
            return {key: value for key, value in run.items() if key != "events"}

    def stream(self, run_id: str) -> Generator[str, None, None]:
        index = 0
        while True:
            with self._lock:
                run = self._runs.get(run_id)
                if run is None:
                    raise KeyError(run_id)
                events = list(run["events"][index:])
                terminal = run["status"] in {"completed", "failed"}

            for item in events:
                index += 1
                yield f"event: {item['event']}\ndata: {json.dumps(item['data'])}\n\n"

            if terminal and not events:
                return
            if not events:
                yield ": keep-alive\n\n"
            threading.Event().wait(0.5)
