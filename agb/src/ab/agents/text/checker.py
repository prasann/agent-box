"""Grammar checker core logic."""
from ab.core import Settings
from ab.core.azure_openai_client import AzureOpenAIClient
from .clipboard import get_clipboard, set_clipboard
from rich.console import Console
from rich.panel import Panel

console = Console()


class GrammarChecker:
    """Simple grammar and typo checker."""
    
    def __init__(self, llm_client: AzureOpenAIClient, settings: Settings):
        self.llm = llm_client
        self.settings = settings
    
    def fix_grammar(self, text: str) -> str:
        """Fix only typos and grammar, preserve style."""
        prompt = f"""Fix ONLY typos and grammar errors in this text. Keep the style, tone, and structure exactly the same. Only fix clear mistakes. Return ONLY the corrected text, nothing else.

Text:
{text}

Fixed text:"""
        
        response = self.llm.generate(prompt=prompt, temperature=0.3)
        return response.strip()
    
    def rewrite(self, text: str) -> str:
        """Full rewrite for clarity and professionalism."""
        prompt = f"""Rewrite this text to be clearer, more professional, and better structured. Fix grammar, improve word choice, and enhance readability. Return ONLY the rewritten text, nothing else.

Text:
{text}

Rewritten text:"""
        
        response = self.llm.generate(prompt=prompt, temperature=0.7)
        return response.strip()
    
    def process_clipboard(self, mode: str, show_preview: bool = True) -> None:
        """Main workflow: clipboard → process → clipboard."""
        # Get clipboard
        text = get_clipboard()
        if not text.strip():
            console.print("❌ Clipboard is empty", style="bold red")
            return
        
        # Show original if preview enabled
        if show_preview and self.settings.text_show_preview:
            console.print(Panel(text, title="[bold cyan]Original", border_style="cyan"))
        
        # Process
        if mode == "fix":
            console.print("🔍 Fixing grammar and typos...", style="yellow")
            result = self.fix_grammar(text)
        else:  # rewrite
            console.print("✍️  Rewriting text...", style="yellow")
            result = self.rewrite(text)
        
        # Show result if preview enabled
        if show_preview and self.settings.text_show_preview:
            console.print(Panel(result, title="[bold green]Result", border_style="green"))
        
        # Set clipboard
        set_clipboard(result)
        console.print("✅ Done! Paste with Cmd+V", style="bold green")
