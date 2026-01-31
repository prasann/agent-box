"""Simple conversation REPL for PR review."""

import asyncio
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown

from .analyzer import PRAnalyzer
from .state import ReviewState
from .gh_utils import post_pr_comment, post_pr_review, GhError
from .prompts import build_refinement_prompt, COMMENT_GENERATION_PROMPT


console = Console()


class ReviewREPL:
    """Interactive review conversation loop."""
    
    def __init__(self, pr_number: int):
        """Initialize REPL.
        
        Args:
            pr_number: Pull request number
        """
        self.pr_number = pr_number
        self.analyzer = PRAnalyzer(pr_number)
        self.state = ReviewState(pr_number)
        
        # Setup prompt session
        history_file = Path.home() / ".pr-agent-history"
        self.prompt_session = PromptSession(history=FileHistory(str(history_file)))
    
    async def start(self) -> None:
        """Start the REPL."""
        console.print("[bold blue]🤖 PR Review Agent[/bold blue]")
        console.print()
        
        # Check if we have existing analysis
        conversation = self.state.get_conversation()
        
        if not conversation or len(conversation) < 2:
            # Perform initial analysis
            console.print("[dim]Analyzing PR... This may take a moment.[/dim]")
            console.print()
            
            try:
                analysis = await self.analyzer.analyze()
                
                # Display analysis
                console.print(Markdown(analysis))
                console.print()
            except Exception as e:
                console.print(f"[red]❌ Analysis failed: {e}[/red]")
                console.print()
                console.print("[dim]You can still ask questions about the PR.[/dim]")
                console.print()
        else:
            # Resume existing session
            console.print("[green]✓ Resuming existing session[/green]")
            console.print(f"[dim]Conversation has {len(conversation)} messages[/dim]")
            console.print()
        
        # Show help
        console.print("[dim]Commands:[/dim]")
        console.print("[dim]  Type your questions naturally[/dim]")
        console.print("[dim]  /post    - Post review to GitHub[/dim]")
        console.print("[dim]  /comment - Post as a comment only[/dim]")
        console.print("[dim]  /exit    - Exit session[/dim]")
        console.print()
        
        # Main loop
        await self._run_loop()
    
    async def _run_loop(self) -> None:
        """Run the conversation loop."""
        while True:
            try:
                # Get user input
                user_input = await asyncio.to_thread(
                    self.prompt_session.prompt,
                    f"pr-{self.pr_number}> "
                )
                
                user_input = user_input.strip()
                if not user_input:
                    continue
                
                # Handle exit
                if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                    console.print()
                    console.print("[green]✓ Session saved[/green]")
                    break
                
                # Handle post commands
                if user_input.lower() == "/post":
                    await self._handle_post("review")
                    continue
                
                if user_input.lower() == "/comment":
                    await self._handle_post("comment")
                    continue
                
                # Handle regular question
                await self._handle_question(user_input)
                
            except KeyboardInterrupt:
                console.print()
                continue
            except EOFError:
                break
        
        # Cleanup
        await self.analyzer.cleanup()
    
    async def _handle_question(self, question: str) -> None:
        """Handle user question.
        
        Args:
            question: User's question
        """
        # Add user message
        self.state.add_message("user", question)
        
        # Get response
        console.print()
        console.print("[dim]Thinking...[/dim]")
        
        try:
            response = await self.analyzer._chat(self.state.get_conversation())
            self.state.add_message("assistant", response)
            
            # Display response
            console.print()
            console.print(Markdown(response))
            console.print()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print()
    
    async def _handle_post(self, action: str) -> None:
        """Handle post command.
        
        Args:
            action: 'review' or 'comment'
        """
        console.print()
        console.print("[dim]Generating review summary...[/dim]")
        
        # Ask LLM to generate formatted review
        self.state.add_message("user", COMMENT_GENERATION_PROMPT)
        
        try:
            review_text = await self.analyzer._chat(self.state.get_conversation())
            self.state.add_message("assistant", review_text)
            
            # Display what will be posted
            console.print()
            console.print("[bold]Review to be posted:[/bold]")
            console.print()
            console.print(Markdown(review_text))
            console.print()
            
            # Confirm
            confirm = await asyncio.to_thread(
                input,
                f"Post this as a {'review' if action == 'review' else 'comment'}? (y/N): "
            )
            
            if confirm.lower() != 'y':
                console.print("[yellow]Cancelled[/yellow]")
                return
            
            # Post to GitHub
            console.print()
            console.print("[dim]Posting to GitHub...[/dim]")
            
            try:
                if action == "review":
                    post_pr_review(self.pr_number, review_text)
                    console.print("[green]✓ Review posted successfully![/green]")
                else:
                    post_pr_comment(self.pr_number, review_text)
                    console.print("[green]✓ Comment posted successfully![/green]")
            except GhError as e:
                console.print(f"[red]❌ Failed to post: {e}[/red]")
            
            console.print()
            
        except Exception as e:
            console.print(f"[red]Error generating review: {e}[/red]")
            console.print()
