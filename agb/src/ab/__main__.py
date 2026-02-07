"""Main CLI entry point."""
import click
import sys
from ab.core import setup_logging, get_settings
from ab.agents import text_group, findtab_group


@click.group()
@click.version_option(version="0.1.0", prog_name="agb")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def main(verbose):
    """AB - Personal AI agents for productivity.
    
    Fast, local AI agents powered by Ollama.
    """
    settings = get_settings()
    log_level = "DEBUG" if verbose else settings.log_level
    setup_logging(log_level=log_level, log_file=settings.log_file if not verbose else None)


# Register agent command groups
main.add_command(text_group)
main.add_command(findtab_group)

# Future agents can be added here:
# main.add_command(gmail_group)
# main.add_command(calendar_group)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        click.echo("\n👋 Interrupted", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
