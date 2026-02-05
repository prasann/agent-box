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
