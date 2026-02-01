"""PR analysis using GitHub Copilot SDK."""

import asyncio
from copilot import CopilotClient

from .gh_utils import get_pr_info, get_pr_diff, GhError
from .state import ReviewState
from .prompt_loader import render_prompt
from .repo_utils import checkout_pr, restore_branch, RepoError


class AnalyzerError(Exception):
    """Analyzer error."""
    pass


class PRAnalyzer:
    """Analyzes PRs using LLM."""
    
    def __init__(self, pr_number: int):
        """Initialize analyzer.
        
        Args:
            pr_number: Pull request number
        """
        self.pr_number = pr_number
        self.state = ReviewState(pr_number)
        self.client: CopilotClient | None = None
        self.session = None
        self.repo_path: str | None = None
        self.original_branch: str | None = None
    
    async def _ensure_client(self) -> None:
        """Ensure Copilot client is initialized with workspace access."""
        if self.client is None:
            try:
                self.client = CopilotClient()
                await self.client.start()
                self.session = await self.client.create_session({
                    "model": "gpt-4",
                    "streaming": True,
                    "working_directory": self.repo_path  # Enable full codebase access
                })
            except Exception as e:
                raise AnalyzerError(f"Failed to initialize Copilot: {e}")
    
    async def analyze(self) -> str:
        """Perform initial PR analysis with full codebase access.
        
        Returns:
            Analysis result as string
            
        Raises:
            AnalyzerError: If analysis fails
        """
        # Fetch PR data
        try:
            pr_info = get_pr_info(self.pr_number)
            diff = get_pr_diff(self.pr_number)
        except GhError as e:
            raise AnalyzerError(f"Failed to fetch PR data: {e}")
        
        # Checkout PR branch to access codebase
        try:
            self.repo_path, self.original_branch = checkout_pr(self.pr_number)
        except RepoError as e:
            raise AnalyzerError(str(e))
        
        # Build prompt with codebase context using Prompty
        from .prompts import format_pr_info, format_file_list
        analysis_prompt = render_prompt(
            "pr_review_with_context",
            pr_info=format_pr_info(pr_info),
            file_list=format_file_list(pr_info),
            diff=diff,
            repo_path=self.repo_path
        )
        
        # Initialize Copilot
        await self._ensure_client()
        
        # Add system message (don't persist - too large)
        system_prompt = render_prompt("system")
        self.state.add_message("system", system_prompt, persist=False)
        
        # Add analysis request (don't persist - contains huge diff)
        self.state.add_message("user", analysis_prompt, persist=False)
        
        # Get response
        try:
            response = await self._chat(self.state.get_conversation())
            # Don't persist the initial analysis response either - it's huge
            self.state.add_message("assistant", response, persist=False)
            return response
        except Exception as e:
            raise AnalyzerError(f"Analysis failed: {e}")
    
    async def _chat(self, messages: list[dict[str, str]]) -> str:
        """Send chat request to Copilot.
        
        Args:
            messages: Conversation messages
            
        Returns:
            Response content
        """
        await self._ensure_client()
        
        # Build prompt from messages
        prompt = "\n\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        # Collect response
        response_parts = []
        done = asyncio.Event()
        
        def on_event(event):
            if event.type.value == "assistant.message":
                response_parts.append(event.data.content)
            elif event.type.value == "session.idle":
                done.set()
        
        self.session.on(on_event)
        await self.session.send({"prompt": prompt})
        await done.wait()
        
        return "".join(response_parts)
    
    async def cleanup(self) -> None:
        """Cleanup resources and restore branch."""
        if self.session:
            await self.session.destroy()
            self.session = None
        if self.client:
            await self.client.stop()
            self.client = None
        
        # Restore original branch
        if self.original_branch:
            try:
                restore_branch(self.original_branch)
            except RepoError as e:
                # Log warning but don't fail - user can manually fix
                print(f"Warning: Failed to restore branch '{self.original_branch}': {e}")
