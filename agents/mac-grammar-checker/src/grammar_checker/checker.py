"""Grammar checker core logic."""
from .ollama_client import OllamaClient
from .clipboard import get_clipboard, set_clipboard


class GrammarChecker:
    """Simple grammar and typo checker."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def fix_grammar(self, text: str) -> str:
        """Fix only typos and grammar, preserve style."""
        prompt = f"""Fix ONLY typos and grammar errors in this text. Keep the style, tone, and structure exactly the same. Only fix clear mistakes. Return ONLY the corrected text, nothing else.

Text:
{text}

Fixed text:"""
        
        response = self.ollama.generate(prompt=prompt, temperature=0.3)
        return response.strip()
    
    def rewrite(self, text: str) -> str:
        """Full rewrite for clarity and professionalism."""
        prompt = f"""Rewrite this text to be clearer, more professional, and better structured. Fix grammar, improve word choice, and enhance readability. Return ONLY the rewritten text, nothing else.

Text:
{text}

Rewritten text:"""
        
        response = self.ollama.generate(prompt=prompt, temperature=0.7)
        return response.strip()
    
    def process_clipboard(self, mode: str) -> None:
        """Main workflow: clipboard → process → clipboard."""
        # Get clipboard
        text = get_clipboard()
        if not text.strip():
            print("❌ Clipboard is empty")
            return
        
        # Process
        if mode == "fix":
            print("🔍 Fixing grammar and typos...")
            result = self.fix_grammar(text)
        else:  # rewrite
            print("✍️  Rewriting text...")
            result = self.rewrite(text)
        
        # Set clipboard
        set_clipboard(result)
        print("✅ Done! Paste with Cmd+V")
