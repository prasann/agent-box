"""Command parser and handlers for the chat interface."""

import re
from enum import Enum
from typing import Optional
from dataclasses import dataclass

from pr_agent.models.feedback import FeedbackSeverity


class CommandType(str, Enum):
    """Types of commands available in the chat."""
    FEEDBACK_ADD = "feedback"
    FEEDBACK_LIST = "list"
    FEEDBACK_DELETE = "delete"
    GENERATE = "generate"
    PREVIEW = "preview"
    POST = "post"
    STATUS = "status"
    CONTEXT = "context"
    HELP = "help"
    EXIT = "exit"


@dataclass
class Command:
    """Parsed command with arguments."""
    type: CommandType
    args: list[str]
    raw: str
    
    def get_arg(self, index: int, default: Optional[str] = None) -> Optional[str]:
        """Get argument at index with optional default.
        
        Args:
            index: Argument index (0-based)
            default: Default value if not present
            
        Returns:
            Argument value or default
        """
        if index < len(self.args):
            return self.args[index]
        return default


@dataclass
class FeedbackArgs:
    """Parsed arguments for feedback command."""
    file: str
    comment: str
    lines: Optional[str] = None
    severity: FeedbackSeverity = FeedbackSeverity.SUGGESTION


class CommandParser:
    """Parser for chat commands."""
    
    # Regex for parsing feedback command
    # Format: /feedback <file>:<lines> <severity> <comment>
    # Lines and severity are optional
    FEEDBACK_PATTERN = re.compile(
        r'^/feedback\s+'
        r'(?P<file>[^\s:]+)'
        r'(?::(?P<lines>\d+(?:-\d+)?))?\s+'
        r'(?:(?P<severity>critical|important|suggestion|question)\s+)?'
        r'(?P<comment>.+)$',
        re.IGNORECASE
    )
    
    def parse(self, text: str) -> Optional[Command]:
        """Parse a command string.
        
        Args:
            text: Input text
            
        Returns:
            Parsed command, or None if not a command
        """
        text = text.strip()
        
        # Check if it's a command (starts with /)
        if not text.startswith('/'):
            return None
        
        # Split into command and args
        parts = text.split(None, 1)
        if not parts:
            return None
        
        cmd_str = parts[0][1:].lower()  # Remove leading /
        args_str = parts[1] if len(parts) > 1 else ""
        
        # Map command strings to types
        command_map = {
            'feedback': CommandType.FEEDBACK_ADD,
            'list': CommandType.FEEDBACK_LIST,
            'delete': CommandType.FEEDBACK_DELETE,
            'del': CommandType.FEEDBACK_DELETE,
            'generate': CommandType.GENERATE,
            'preview': CommandType.PREVIEW,
            'post': CommandType.POST,
            'status': CommandType.STATUS,
            'context': CommandType.CONTEXT,
            'help': CommandType.HELP,
            'exit': CommandType.EXIT,
            'quit': CommandType.EXIT,
        }
        
        cmd_type = command_map.get(cmd_str)
        if not cmd_type:
            return None
        
        # Parse arguments
        args = args_str.split() if args_str else []
        
        return Command(type=cmd_type, args=args, raw=text)
    
    def parse_feedback(self, text: str) -> Optional[FeedbackArgs]:
        """Parse a feedback command into structured arguments.
        
        Args:
            text: Feedback command string
            
        Returns:
            Parsed feedback arguments, or None if invalid
        """
        match = self.FEEDBACK_PATTERN.match(text)
        if not match:
            return None
        
        file = match.group('file')
        lines = match.group('lines')
        severity_str = match.group('severity')
        comment = match.group('comment')
        
        # Parse severity
        severity = FeedbackSeverity.SUGGESTION
        if severity_str:
            try:
                severity = FeedbackSeverity(severity_str.lower())
            except ValueError:
                pass  # Use default
        
        return FeedbackArgs(
            file=file,
            lines=lines,
            comment=comment,
            severity=severity
        )


class CommandValidator:
    """Validate command arguments."""
    
    @staticmethod
    def validate_feedback_add(args: list[str]) -> tuple[bool, Optional[str]]:
        """Validate feedback add command arguments.
        
        Args:
            args: Command arguments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(args) < 2:
            return False, "Usage: /feedback <file>:<lines> [severity] <comment>"
        
        # Check if first arg looks like file path
        file_arg = args[0]
        if not file_arg:
            return False, "File path is required"
        
        return True, None
    
    @staticmethod
    def validate_delete(args: list[str]) -> tuple[bool, Optional[str]]:
        """Validate delete command arguments.
        
        Args:
            args: Command arguments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(args) != 1:
            return False, "Usage: /delete <feedback_id>"
        
        try:
            int(args[0])
            return True, None
        except ValueError:
            return False, "Feedback ID must be a number"
    
    @staticmethod
    def validate_post(args: list[str]) -> tuple[bool, Optional[str]]:
        """Validate post command arguments.
        
        Args:
            args: Command arguments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(args) > 1:
            return False, "Usage: /post [approve|request-changes|comment]"
        
        if len(args) == 1:
            action = args[0].lower()
            if action not in ['approve', 'request-changes', 'comment']:
                return False, "Action must be: approve, request-changes, or comment"
        
        return True, None


def get_help_text() -> str:
    """Get help text for all commands.
    
    Returns:
        Formatted help text
    """
    return """
Available Commands:

💬 Chat & Questions
  Just type your question naturally - no command needed!
  
📝 Feedback Management
  /feedback <file>:<lines> [severity] <comment>
      Add feedback for a specific file and line range
      Severity: critical, important, suggestion (default), question
      Example: /feedback auth.ts:45-60 critical Need null check here
  
  /list
      List all feedback items
  
  /delete <id>
      Delete a feedback item by ID
      Example: /delete 3

📋 Review Actions
  /generate
      Generate a review summary from collected feedback
  
  /preview
      Preview the review before posting to GitHub
  
  /post [action]
      Post the review to GitHub
      Actions: approve, request-changes, comment (default)
      Example: /post request-changes

ℹ️ Information
  /status
      Show current session status and statistics
  
  /context
      Show loaded PR context details
  
  /help
      Show this help message

🚪 Exit
  /exit or /quit
      Exit the chat session (saves automatically)
"""


def get_command_examples() -> dict[CommandType, list[str]]:
    """Get example commands for each type.
    
    Returns:
        Dictionary mapping command types to example strings
    """
    return {
        CommandType.FEEDBACK_ADD: [
            "/feedback auth.ts:45 Need null check here",
            "/feedback main.py:120-135 critical This could cause a memory leak",
            "/feedback utils.js:88 question Why is this async?",
        ],
        CommandType.FEEDBACK_LIST: [
            "/list",
        ],
        CommandType.FEEDBACK_DELETE: [
            "/delete 3",
        ],
        CommandType.GENERATE: [
            "/generate",
        ],
        CommandType.PREVIEW: [
            "/preview",
        ],
        CommandType.POST: [
            "/post",
            "/post request-changes",
            "/post approve",
        ],
        CommandType.STATUS: [
            "/status",
        ],
        CommandType.CONTEXT: [
            "/context",
        ],
        CommandType.HELP: [
            "/help",
        ],
        CommandType.EXIT: [
            "/exit",
            "/quit",
        ],
    }
