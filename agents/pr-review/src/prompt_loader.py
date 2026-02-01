"""Prompt loading and rendering using Prompty format."""

from pathlib import Path
from typing import Any


# Try to import prompty, provide helpful error if not installed
try:
    import prompty
except ImportError:
    raise ImportError(
        "prompty is not installed. Install it with: uv add prompty"
    )


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptLoader:
    """Loads and renders Prompty templates."""
    
    def __init__(self, prompts_dir: Path = PROMPTS_DIR):
        """Initialize prompt loader.
        
        Args:
            prompts_dir: Directory containing .prompty files
        """
        self.prompts_dir = prompts_dir
        self._cache: dict[str, Any] = {}
    
    def load(self, name: str) -> Any:
        """Load a prompt template.
        
        Args:
            name: Prompt name (without .prompty extension)
            
        Returns:
            Loaded Prompty template
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        if name in self._cache:
            return self._cache[name]
        
        prompt_path = self.prompts_dir / f"{name}.prompty"
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt '{name}' not found at {prompt_path}"
            )
        
        # Load using prompty's load function
        prompt = prompty.load(str(prompt_path))
        self._cache[name] = prompt
        return prompt
    
    def render(self, name: str, **kwargs: Any) -> str:
        """Load and render a prompt with variables.
        
        Args:
            name: Prompt name
            **kwargs: Variables to substitute in template
            
        Returns:
            Rendered prompt text
        """
        # Read the file and extract content manually
        # Prompty's execute() would call the LLM, we just want the template
        prompt_path = self.prompts_dir / f"{name}.prompty"
        with open(prompt_path, 'r') as f:
            content = f.read()
        
        # Extract content after --- markers (frontmatter)
        parts = content.split('---')
        if len(parts) >= 3:
            # Everything after the second --- is the template
            template = '---'.join(parts[2:]).strip()
        else:
            template = content
        
        # Simple variable substitution using {{var}} format
        for key, value in kwargs.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return template


# Global instance
_loader = PromptLoader()


def load_prompt(name: str) -> Any:
    """Load a prompt template.
    
    Args:
        name: Prompt name (without .prompty extension)
        
    Returns:
        Loaded Prompty template
    """
    return _loader.load(name)


def render_prompt(name: str, **kwargs: Any) -> str:
    """Load and render a prompt with variables.
    
    Args:
        name: Prompt name
        **kwargs: Variables to substitute in template
        
    Returns:
        Rendered prompt text
    """
    return _loader.render(name, **kwargs)
