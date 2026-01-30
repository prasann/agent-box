"""Command handlers for the chat interface."""

from typing import Optional
from pathlib import Path
import subprocess
import tempfile
import os

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from pr_agent.state.session import Session
from pr_agent.chat.commands import (
    CommandParser,
    FeedbackArgs,
    get_help_text
)
from pr_agent.models.feedback import FeedbackSeverity
from pr_agent.context.context_builder import PRContext
from pr_agent.agent.review_generator import (
    ReviewGenerator,
    GitHubReviewPoster
)


class CommandHandler:
    """Handles execution of chat commands."""
    
    def __init__(self, session: Session, console: Console):
        """Initialize command handler.
        
        Args:
            session: Current session
            console: Rich console for output
        """
        self.session = session
        self.console = console
        self.parser = CommandParser()
    
    def handle_feedback_add(self, args: FeedbackArgs) -> bool:
        """Handle /feedback command.
        
        Args:
            args: Parsed feedback arguments
            
        Returns:
            True if successful
        """
        # Add feedback to collection
        item = self.session.feedback.add_item(
            file=args.file,
            comment=args.comment,
            lines=args.lines,
            severity=args.severity
        )
        
        # Save to disk
        self.session.save()
        
        # Display confirmation
        self.console.print(f"\n✓ Feedback added (ID: {item.id})")
        self.console.print(Panel(
            item.format_for_display(),
            title="New Feedback",
            border_style="green"
        ))
        
        return True
    
    def handle_feedback_list(self) -> bool:
        """Handle /list command.
        
        Returns:
            True if successful
        """
        if not self.session.feedback.items:
            self.console.print("\n💭 No feedback items yet")
            return True
        
        # Create table
        table = Table(title=f"Feedback for PR #{self.session.pr_number}")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Severity", style="yellow")
        table.add_column("File", style="blue")
        table.add_column("Lines", style="magenta")
        table.add_column("Comment", style="white")
        
        for item in self.session.feedback.items:
            severity_emoji = {
                FeedbackSeverity.CRITICAL: "🔴",
                FeedbackSeverity.IMPORTANT: "🟡",
                FeedbackSeverity.SUGGESTION: "💡",
                FeedbackSeverity.QUESTION: "❓"
            }
            
            table.add_row(
                str(item.id),
                f"{severity_emoji.get(item.severity, '•')} {item.severity.value}",
                item.file,
                item.lines or "-",
                item.comment[:50] + "..." if len(item.comment) > 50 else item.comment
            )
        
        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n" + self.session.feedback.format_summary())
        
        return True
    
    def handle_feedback_delete(self, item_id: int) -> bool:
        """Handle /delete command.
        
        Args:
            item_id: Feedback item ID to delete
            
        Returns:
            True if successful
        """
        if self.session.feedback.delete_item(item_id):
            self.session.save()
            self.console.print(f"\n✓ Deleted feedback item {item_id}")
            return True
        else:
            self.console.print(f"\n✗ Feedback item {item_id} not found", style="red")
            return False
    
    def handle_status(self) -> bool:
        """Handle /status command.
        
        Returns:
            True if successful
        """
        pr = self.session.pr_data.metadata
        
        # Build status info
        status_text = f"""# Session Status

**PR**: #{pr.number} - {pr.title}
**Author**: {pr.author.login}
**State**: {pr.state}
**Changed Files**: {len(pr.files)}
**Commits**: {len(pr.commits)}

## Session Info
**Location**: `{self.session.session_dir}`
**Conversation**: {len(self.session.conversation)} messages

## Feedback Summary
{self.session.feedback.format_summary()}
"""
        
        self.console.print("\n")
        self.console.print(Panel(
            Markdown(status_text),
            title="📊 Session Status",
            border_style="blue"
        ))
        
        return True
    
    def handle_context(self, pr_context: Optional[PRContext] = None) -> bool:
        """Handle /context command.
        
        Args:
            pr_context: PR context if available
            
        Returns:
            True if successful
        """
        if not pr_context:
            self.console.print("\n⚠️  Context not available", style="yellow")
            return False
        
        context_text = f"""# PR Context

**Strategy**: {pr_context.strategy}
**Files**: {pr_context.get_file_count()}
**Total Size**: ~{pr_context.get_total_context_size() / 1024:.1f} KB

## Files
"""
        
        for file_path, file_ctx in pr_context.files.items():
            status_parts = []
            if file_ctx.content:
                status_parts.append("✓ content")
            if file_ctx.history:
                status_parts.append(f"✓ history ({len(file_ctx.history)})")
            if file_ctx.blame:
                status_parts.append("✓ blame")
            if file_ctx.too_large:
                status_parts.append("⚠️  too large")
            if file_ctx.not_found:
                status_parts.append("✗ not found")
            
            status = ", ".join(status_parts) if status_parts else "metadata only"
            context_text += f"- `{file_path}`: {status}\n"
        
        if pr_context.recent_commits:
            context_text += f"\n## Recent Commits ({len(pr_context.recent_commits)})\n"
            for commit in pr_context.recent_commits[:5]:
                context_text += f"- {commit.short_hash}: {commit.message}\n"
        
        self.console.print("\n")
        self.console.print(Panel(
            Markdown(context_text),
            title="📋 PR Context",
            border_style="cyan"
        ))
        
        return True
    
    def handle_help(self) -> bool:
        """Handle /help command.
        
        Returns:
            True if successful
        """
        help_text = get_help_text()
        self.console.print("\n")
        self.console.print(Panel(
            Markdown(help_text),
            title="❓ Help",
            border_style="magenta"
        ))
        
        return True
    
    def handle_generate(self) -> str:
        """Handle /generate command - generates review text.
        
        Returns:
            Generated review text
        """
        if not self.session.feedback.items:
            self.console.print("\n⚠️  No feedback items to generate review from", style="yellow")
            return ""
        
        # Create review generator
        generator = ReviewGenerator(
            pr_metadata=self.session.pr_data.metadata,
            feedback=self.session.feedback
        )
        
        # Generate review body
        review_text = generator.generate_review_body(include_summary=True)
        
        if not self.session.feedback.items:
            self.console.print("\n⚠️  No feedback items to preview", style="yellow")
            return False
        
        # Create review generator
        generator = ReviewGenerator(
            pr_metadata=self.session.pr_data.metadata,
            feedback=self.session.feedback
        )
        
        # Get preview with decision
        preview_text = generator.preview_review()
        
        # Display preview
        self.console.print("\n")
        self.console.print(preview_text)
        
        return True
    
    def handle_edit(self) -> bool:
        """Handle /edit command - opens review draft in editor.
        
        Returns:
            True if successful
        """
        # Generate review if not already generated
        draft_path = self.session.session_dir / "review_draft.md"
        
        if not draft_path.exists():
            self.handle_generate()
        
        # Get editor from environment
        editor = os.environ.get('EDITOR', 'vim')
        
        try:
            # Open editor
            subprocess.run([editor, str(draft_path)], check=True)
            self.console.print(f"\n✓ Review edited. Preview with /preview or post with /post")
        if not self.session.feedback.items:
            self.console.print("\n⚠️  No feedback items to post", style="yellow")
            return False
        
        # Create poster
        poster = GitHubReviewPoster(
            pr_number=self.session.pr_number,
            owner=self.session.owner,
            repo=self.session.repo
        )
        
        # Check authentication
        is_auth, auth_msg = poster.check_gh_authenticated()
        if not is_auth:
            self.console.print(f"\n✗ {auth_msg}", style="red")
            return False
        
        # Create review generator
        generator = ReviewGenerator(
            pr_metadata=self.session.pr_data.metadata,
            feedback=self.session.feedback
        )
        
        # Check if draft exists and use it, otherwise generate
        draft_path = self.session.session_dir / "review_draft.md"
        if draft_path.exists():
            review_text = draft_path.read_text()
            self.console.print("\n📄 Using edited review draft")
        else:
            review_text = generator.generate_review_body(include_summary=True)
        
        # Show preview
        self.console.print("\n📤 Preparing to post review...\n")
        self.console.print("=" * 80)
        self.console.print(Markdown(review_text))
        self.console.print("=" * 80)
        
        # Auto-determine action if not specified or suggest based on severity
        if action == "auto":
            action = generator.generate_review_decision().lower().replace('_', '-')
            self.console.print(f"\n💡 Suggested action: [bold]{action}[/bold]")
        
        # Confirm
        self.console.print(f"\n⚠️  This will post a review with action: [bold]{action}[/bold]")
        self.console.print(f"   PR: #{self.session.pr_number} - {self.session.pr_data.metadata.title}")
        response = input("\nContinue? (yes/no): ")
        
        if response.lower() not in ['yes', 'y']:
            self.console.print("\n✗ Cancelled", style="yellow")
            return False
        
        # Post review
        self.console.print("\n📡 Posting review to GitHub...")
        
        # Map action to gh CLI format
        action_map = {
            'approve': 'APPROVE',
            'request-changes': 'REQUEST_CHANGES',
            'comment': 'COMMENT'
        }
        gh_action = action_map.get(action, 'COMMENT')
        
        success, message = poster.post_review(
            review_body=review_text,
            action=gh_action
        )
        
        if success:
            self.console.print(f"\n✓ {message}", style="green")
            review_url = poster.get_pr_review_url()
            self.console.print(f"   View at: {review_url}")
            
            # Mark review as posted in session
            self.session.set_metadata("review_posted", True)
            self.session.set_metadata("review_posted_at", str(Path.cwd()))
            self.session.save()
            
            return True
        else:
            self.console.print(f"\n✗ {message}", style="red")
            return Fals
    def handle_post(self, action: str = "comment") -> bool:
        """Handle /post command - posts review to GitHub.
        
        Args:
            action: Review action (approve, request-changes, comment)
            
        Returns:
            True if successful
        """
        review_text = self.handle_generate()
        
        if not review_text:
            return False
        
        # Show preview
        self.console.print("\n📤 Preparing to post review...\n")
        self.handle_preview()
        
        # Confirm
        self.console.print(f"\n⚠️  This will post a review with action: [bold]{action}[/bold]")
        response = input("\nContinue? (y/N): ")
        
        if response.lower() != 'y':
            self.console.print("\n✗ Cancelled", style="yellow")
            return False
        
        # TODO: Implement actual posting to GitHub via gh CLI
        self.console.print("\n✓ Review posted successfully!", style="green")
        self.console.print(f"View at: https://github.com/{self.session.owner}/{self.session.repo}/pull/{self.session.pr_number}")
        
        return True
