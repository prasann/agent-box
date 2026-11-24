import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "vscode-prompts/.github/hooks/scripts/notify-copilot.sh"
)


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent-box-notify-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.capture = self.root / "notification"
        self.env = {
            **os.environ,
            "HOME": str(self.root),
            "PATH": f"{self.root}:{os.environ['PATH']}",
            "NOTIFY_CAPTURE": str(self.capture),
        }
        for name, body in {
            "osascript": "exit 0\n",
            "terminal-notifier": (
                'printf "%s\\n" "$@" > "$NOTIFY_CAPTURE"\n'
                'exit "${NOTIFY_EXIT:-0}"\n'
            ),
        }.items():
            command = self.root / name
            command.write_text("#!/bin/sh\n" + body)
            command.chmod(0o755)

    def run_hook(self, payload):
        return subprocess.run(
            ["bash", str(SCRIPT)],
            input=payload,
            text=True,
            capture_output=True,
            env=self.env,
            timeout=5,
        )

    def test_native_completion_with_escaped_project_name(self):
        result = self.run_hook(json.dumps({
            "cwd": '/tmp/project "quoted"',
            "stopReason": "end_turn",
            "sessionId": "test",
            "timestamp": 0,
            "transcriptPath": "/tmp/transcript",
            "stop_hook_active": False,
        }))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})
        args = self.capture.read_text().splitlines()
        self.assertEqual(args[args.index("-subtitle") + 1], 'project "quoted"')
        self.assertEqual(args[args.index("-group") + 1], 'project "quoted"-Stop')
        self.assertEqual(
            args[args.index("-activate") + 1], "com.microsoft.VSCodeInsiders"
        )
        log = (self.root / ".agent-box/logs/notifications.log").read_text()
        self.assertIn('agentStop [project "quoted"]', log)

    def test_invalid_input_does_not_notify(self):
        for payload in ("not json", "{}", '{"cwd":42}', '{"cwd":""}'):
            with self.subTest(payload=payload):
                result = self.run_hook(payload)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr)
                self.assertFalse(self.capture.exists())

    def test_notification_failure_is_not_logged_as_success(self):
        self.env["NOTIFY_EXIT"] = "1"
        result = self.run_hook('{"cwd":"/tmp/project"}')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / ".agent-box/logs/notifications.log").exists())


if __name__ == "__main__":
    unittest.main()
