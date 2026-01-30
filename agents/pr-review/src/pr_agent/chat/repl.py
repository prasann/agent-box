"""Interactive chat REPL for PR review."""

import asyncio
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown

from ..agent_client import CustomCopilotClient, CopilotError
from ..state import Session
from ..context.context_builder import PRContext
from .commands import CommandParser, CommandType, CommandValidator
from .handlers import CommandHandler

console = Console()


class ChatREPL:
    """Interactive chat REPL for PR review."""
    
    def __init__(self, session: Session, repo_root: Path):
        """Initialize chat REPL.
        
        Args:
            session: PR review session
            repo_root: Repository root directory
        """
        self.session = session
        self.repo_root = repo_root
        self.pr_data = session.pr_data
        self.copilot: Optional[CustomCopilotClient] = None
        self.pr_context: Optional[PRContext] = None
        
        # Setup command handling
        self.command_parser = CommandParser()
        self.command_handler = CommandHandler(session, console)
        
        # Setup prompt session
        history_file = Path.home() / ".pr-agent-history"
        self.prompt_session = PromptSession(history=FileHistory(str(history_file)))
        
    async def start(self) -> None:
        """Start the chat REPL."""
        # Initialize Copilot client
        console.print("[dim]Initializing AI assistant...[/dim]")
        try:
            self.copilot = CustomCopilotClient()
            await self.copilot._ensure_started()
        except CopilotError as e:
            error_msg = str(e)
            console.print(f"[red]❌ Failed to initialize Copilot: {e}[/red]")
            
            if "protocol version mismatch" in error_msg.lower():
                console.print()
                console.print("[yellow]⚠️  SDK/CLI Version Mismatch[/yellow]")
                console.print("[dim]The GitHub Copilot SDK and CLI are out of sync.[/dim]")
                console.print()
                console.print("[bold]Quick Fix Options:[/bold]")
                console.print("1. Wait for GitHub to release an updated gh-copilot extension")
                console.print("2. Use the Copilot Chat in VS Code or GitHub.com for now")
                console.print()
                console.print("[dim]This is a known issue with the Copilot SDK being newer than the CLI.[/dim]")
                console.print("[dim]We'll update the agent once the CLI is updated.[/dim]")
            else:
                console.print("[yellow]Note: Make sure the Copilot CLI is installed:[/yellow]")
                console.print("[yellow]  gh extension install github/gh-copilot[/yellow]")
            return
        
        # Build initial context
        await self._build_context()
        
        # Welcome message
        console.print()
        console.print("[bold green]✓ Ready to review![/bold green]")
        console.print()
        console.print("[dim]Type your questions about the PR or commands:[/dim]")
        console.print("[dim]  /help    - Show available commands[/dim]")
        console.print("[dim]  /exit    - Exit the session[/dim]")
        console.print()
        
        # Main loop
        await self._run_loop()
    
    async def _build_context(self) -> None:
        """Build initial context for the AI."""
        metadata = self.pr_data.metadata
        system_message = {
            "role": "system",
            "content": (
                "You are an expert code reviewer helping to review a pull request. "
                "You have access to the PR metadata and diff. "
                "Provide helpful, constructive feedback. "
                "Be specific and point to actual code when possible."
            )
        }
        
        context_message = {
            "role": "system",
            "content": (
                f"PR #{metadata.number}: {metadata.title}\n"
                f"By: @{metadata.author.login}\n"
                f"Files changed: {metadata.changed_files}\n"
                f"Additions: +{metadata.additions}, Deletions: -{metadata.deletions}\n\n"
                f"Changed files:\n" + 
                "\n".join([f"- {f.path}" for f in metadata.files[:20]])
            )
        }
        
        self.session.add_message(system_message["role"], system_message["content"])
        self.session.add_message(context_message["role"], context_message["content"])
    
    async def _run_loop(self) -> None:
        """Run the main REPL loop."""
        while True:
            try:
                # Get user input
                user_input = await asyncio.to_thread(
                    self.prompt_session.prompt,
                    f"pr-{self.session.pr_number}> "
                )
                
                user_input = user_input.strip()
                if not user_input:
                    continue
                
                # Check for exit
                if user_input.lower() in ["exit", "quit", "/exit", "/quit"]:
                    console.print("\n[dim]Saving session...[/dim]")
                    self.session.save()
                    console.print("[green]✓ Session saved[/green]")
                    break
                
                # Handle commands
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue
                
                # Handle regular question
                await self._handle_question(user_input)
                
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
        
        # Cleanup
        if self.copilot:
            await self.copilot.stop()
    
    async def _handle_command(self, command: str) -> None:
        """Handle slash commands.
        
        Args:
            command: Command string starting with /
        """
        # Parse command
        parsed = self.command_parser.parse(command)
        
        if not parsed:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            console.print("[dim]Type /help for available commands[/dim]")
            return
        
        # Route to appropriate handler
        if parsed.type == CommandType.HELP:
            self.command_handler.handle_help()
        
        elif parsed.type == CommandType.STATUS:
            self.command_handler.handle_status()
        
        elif parsed.type == CommandType.CONTEXT:
            self.command_handler.handle_context(self.pr_context)
        
        elif parsed.type == CommandType.FEEDBACK_ADD:
            # Parse feedback arguments
            feedback_args = self.command_parser.parse_feedback(command)
            if feedback_args:
                self.command_handler.handle_feedback_add(feedback_args)
            else:
                console.print("[red]Invalid feedback format[/red]")
                console.print("[dim]Usage: /feedback <file>:<lines> [severity] <comment>[/dim]")
        
        elif parsed.type == CommandType.FEEDBACK_LIST:
            self.command_handler.handle_feedback_list()
        
        elif parsed.type == CommandType.FEEDBACK_DELETE:
            # Validate and execute
            is_valid, error = CommandValidator.validate_delete(parsed.args)
            if is_valid:
                item_id = int(parsed.args[0])
                self.command_handler.handle_feedback_delete(item_id)
            else:
                console.print(f"[red]{error}[/red]")
        
        elif parsed.type == CommandType.PREVIEW:
            self.command_handler.handle_preview()
        
        elif parsed.type == CommandType.EDIT:
            self.command_handler.handle_edit()
        
        elif parsed.type == CommandType.GENERATE:
            review_text = self.command_handler.handle_generate()
            if review_text:
                console.print("\n")
                console.print(Markdown(review_text))
        
        elif parsed.type == CommandType.POST:
            # Validate and execute
            is_valid, error = CommandValidator.validate_post(parsed.args)
            if is_valid:
                action = parsed.get_arg(0, "comment")
                self.command_handler.handle_post(action)
            else:
                console.print(f"[red]{error}[/red]")
        
        else:
            console.print(f"[yellow]Command not yet implemented: {parsed.type.value}[/yellow]")
    
    async def _handle_question(self, question: str) -> None:
        """Handle user question.
        
        Args:
            question: User's question
        """
        # Add user message to conversation
        self.session.add_message("user", question)
        
        # Get response from Copilot
        console.print()
        console.print("[dim]Thinking...[/dim]")
        
        try:
            response = await self.copilot.chat_async(self.session.conversation)
            
            # Add assistant response to conversation
            self.session.add_message("assistant", response)
            
            # Display response
            console.print()
            console.print(Markdown(response))
            console.print()
            
            # Save conversation
            self.session.save()
            
        except CopilotError as e:
            console.print(f"\n[red]Error: {e}[/red]\n")
