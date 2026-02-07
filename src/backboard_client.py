import os
import asyncio
from typing import Optional, List, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


class BackboardClient:
    """Client for interacting with Backboard Responses API."""
    
    def __init__(self):
        self.api_key = os.getenv('BACKBOARD_API_KEY')
        self.base_url = os.getenv('BACKBOARD_BASE_URL', 'https://api.backboard.io')
        self.model = os.getenv('BACKBOARD_MODEL', 'gpt-4o-mini')
        
        if not self.api_key:
            raise ValueError("BACKBOARD_API_KEY not set")
        
        try:
            import aiohttp
            self.aiohttp = aiohttp
            self.session: Optional[aiohttp.ClientSession] = None
        except ImportError:
            raise ImportError("aiohttp package required. Install with: pip install aiohttp")
    
    async def _get_session(self) -> 'aiohttp.ClientSession':
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = self.aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the client session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def create_conversation(self, system_prompt: str, initial_messages: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """
        Create a conversation context.
        Returns a message history list.
        """
        messages = []
        
        # Add system message
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add initial messages
        if initial_messages:
            messages.extend(initial_messages)
        
        return messages
    
    async def send_message(
        self,
        messages: List[Dict[str, str]],
        user_message: str,
        timeout: float = 60.0,
        max_tokens: int = 500
    ) -> tuple[str, List[Dict[str, str]]]:
        """
        Send a message and get response using Backboard Responses API.
        Returns (response_text, updated_messages).
        """
        session = await self._get_session()
        
        # Add user message to conversation
        updated_messages = messages + [{"role": "user", "content": user_message}]
        
        # Prepare request
        url = f"{self.base_url}/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": updated_messages,
            "max_tokens": max_tokens
        }
        
        try:
            async with session.post(url, headers=headers, json=payload, timeout=timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Backboard API error {response.status}: {error_text}")
                
                data = await response.json()
                
                # Extract assistant response
                assistant_message = data['choices'][0]['message']['content']
                
                # Add assistant response to conversation
                updated_messages.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message, updated_messages
                
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request exceeded timeout of {timeout}s")
        except Exception as e:
            logger.error(f"Backboard API request failed: {e}")
            raise


# Global client instance
backboard = BackboardClient()
