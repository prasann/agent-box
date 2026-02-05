"""Text agent CLI commands."""
import click
from ab.core import OllamaClient, get_settings
from .checker import GrammarChecker


@click.group(name="text")
def text_group():
    """Text grammar and typo checker."""
    pass


@text_group.command(name="fix")
@click.option("--no-preview", is_flag=True,
              help="Don't show before/after preview")
def fix(no_preview):
    """Fix typos and grammar in clipboard text."""
    settings = get_settings()
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url
    )
    checker = GrammarChecker(ollama, settings)
    checker.process_clipboard(mode="fix", show_preview=not no_preview)


@text_group.command(name="rewrite")
@click.option("--no-preview", is_flag=True,
              help="Don't show before/after preview")
def rewrite(no_preview):
    """Rewrite text in clipboard for clarity and professionalism."""
    settings = get_settings()
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url
    )
    checker = GrammarChecker(ollama, settings)
    checker.process_clipboard(mode="rewrite", show_preview=not no_preview)
