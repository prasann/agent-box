"""GitHub Copilot SDK integration."""

import asyncio
import subprocess
from typing import Iterator, Optional

from copilot.client import CopilotClient as _CopilotClient


class CopilotError(Exception):
    """Copilot operation error."""
    pass


class CopilotClient:
    """Wrapper for GitHub Copilot SDK client."""
    
    def __init__(self):
        """Initialize Copilot client."""
        self._client: Optional[_CopilotClient] = None
        self._session = None
        self._loop = None
    
    async def _ensure_started(self) -> None:
        """Ensure client is started."""
        if self._client is None:
            try:
                self._client = _CopilotClient()
                await self._client.start()
            except Exception as e:
                raise CopilotError(f"Failed to start Copilot client: {e}")
    
    async def _create_session(self) -> None:
        """Create a new session."""
        if self._session is None:
            await self._ensure_started()
            try:
                self._session = await self._client.create_session({
                    "model": "gpt-4",
                    "streaming": True
                })
            except Exception as e:
                raise CopilotError(f"Failed to create session: {e}")
    
    async def chat_async(self, messages: list[dict[str, str]]) -> str:
        """Send a chat completion request (async).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Response content
            
        Raises:
            CopilotError: If request fails
        """
        await self._create_session()
        
        try:
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
            
            self._session.on(on_event)
            await self._session.send({"prompt": prompt})
            await done.wait()
            
            return "".join(response_parts)
        except Exception as e:
            raise CopilotError(f"Chat completion failed: {e}")
    
    async def chat_stream_async(self, messages: list[dict[str, str]]) -> Iterator[str]:
        """Send a streaming chat completion request (async).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Yields:
            Response chunks
            
        Raises:
            CopilotError: If request fails
        """
        await self._create_session()
        
        try:
            # Build prompt from messages
            prompt = "\n\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages
            ])
            
            chunks = []
            done = asyncio.Event()
            
            def on_event(event):
                if event.type.value == "assistant.message_delta":
                    delta = event.data.delta_content or ""
                    chunks.append(delta)
                elif event.type.value == "session.idle":
                    done.set()
            
            self._session.on(on_event)
            await self._session.send({"prompt": prompt})
            await done.wait()
            
            for chunk in chunks:
                yield chunk
        except Exception as e:
            raise CopilotError(f"Streaming chat completion failed: {e}")
    
    def chat(self, messages: list[dict[str, str]]) -> str:
        """Send a chat completion request (sync wrapper).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Response content
        """
        return asyncio.run(self.chat_async(messages))
    
    def chat_stream(self, messages: list[dict[str, str]]) -> Iterator[str]:
        """Send a streaming chat completion request (sync wrapper).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Yields:
            Response chunks
        """
        async def _run():
            chunks = []
            async for chunk in self.chat_stream_async(messages):
                chunks.append(chunk)
            return chunks
        
        chunks = asyncio.run(_run())
        for chunk in chunks:
            yield chunk
    
    async def stop(self) -> None:
        """Stop the client and cleanup."""
        if self._session:
            await self._session.destroy()
            self._session = None
        if self._client:
            await self._client.stop()
            self._client = None


async def test_copilot_connection_async() -> bool:
    """Test if Copilot connection works (async).
    
    Returns:
        True if connection successful
    """
    try:
        client = CopilotClient()
        response = await client.chat_async([
            {"role": "user", "content": "Say 'OK' if you can hear me."}
        ])
        await client.stop()
        return "ok" in response.lower()
    except Exception:
        return False


def test_copilot_connection() -> bool:
    """Test if Copilot connection works.
    
    Returns:
        True if connection successful
    """
    return asyncio.run(test_copilot_connection_async())
