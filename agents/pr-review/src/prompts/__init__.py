"""Prompts module for PR review agent.

This module provides utilities for loading and rendering .prompty files.
"""

from pathlib import Path

# Directory containing prompt files
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"

__all__ = ["PROMPTS_DIR"]
