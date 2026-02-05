"""macOS clipboard operations."""
import subprocess


def get_clipboard() -> str:
    """Get text from macOS clipboard."""
    result = subprocess.run(['pbpaste'], capture_output=True, text=True)
    return result.stdout


def set_clipboard(text: str) -> None:
    """Set text to macOS clipboard."""
    subprocess.run(['pbcopy'], input=text.encode('utf-8'))
