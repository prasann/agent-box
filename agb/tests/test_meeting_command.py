from pathlib import Path

from ab.__main__ import main
from click.testing import CliRunner


def test_meeting_command_group_is_registered():
    result = CliRunner().invoke(main, ["meeting", "--help"])

    assert result.exit_code == 0
    assert "start" in result.output
    assert "open" in result.output
    assert "status" in result.output


def test_base_package_is_pip_resolvable_without_sibling_dependency():
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text()
    required = pyproject.split("dependencies = [", 1)[1].split("]", 1)[0]

    assert "meeting-assistant" not in required
    assert (
        'meeting = [\n    "meeting-assistant[audio,stt]>=0.1.0",\n]'
        in pyproject
    )
