"""Tests for the remaining agent command registrations."""
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from ab.__main__ import main
from ab.core.config import Settings


class AgentCommandTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.settings = Settings(_env_file=None)

    def test_remaining_commands_load(self):
        with patch("ab.__main__.get_settings", return_value=self.settings), patch(
            "ab.__main__.setup_logging"
        ):
            for command in ("text", "shell"):
                with self.subTest(command=command):
                    result = self.runner.invoke(main, [command, "--help"])
                    self.assertEqual(result.exit_code, 0, result.output)

    def test_retired_command_is_not_registered(self):
        self.assertNotIn("findtab", main.commands)
        result = self.runner.invoke(main, ["findtab", "--help"])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("No such command", result.output)

    def test_retired_settings_are_removed(self):
        self.assertFalse(
            any(name.startswith("findtab_") for name in Settings.model_fields)
        )