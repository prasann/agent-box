"""CLI entry points."""
import sys
from .checker import GrammarChecker
from .ollama_client import OllamaClient


def fix_main():
    """Entry point for 'fix' command."""
    try:
        ollama = OllamaClient()
        checker = GrammarChecker(ollama)
        checker.process_clipboard(mode="fix")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def rewrite_main():
    """Entry point for 'rewrite' command."""
    try:
        ollama = OllamaClient()
        checker = GrammarChecker(ollama)
        checker.process_clipboard(mode="rewrite")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    fix_main()
