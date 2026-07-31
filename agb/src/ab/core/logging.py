"""Shared logging configuration."""
import logging
from pathlib import Path
from rich.logging import RichHandler


def setup_logging(log_level: str = "INFO", log_file: Path = None):
    """Configure logging for all agents."""
    
    handlers = [RichHandler(rich_tracebacks=True, show_time=False)]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=handlers
    )
    
    # Azure SDK auth chatter is noisy at INFO and not useful for CLI output
    for noisy_logger in ("azure", "msal"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
