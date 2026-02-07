import os
import asyncio
from typing import Optional
import logging
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Ensure .env is loaded even when this module is imported before main.py
load_dotenv()


class BackboardClient:
    """Client for interacting with Backboard API."""
    
    def __init__(self):
        self.api_key = os.getenv('BACKBOARD_API_KEY')
        self.base_url = os.getenv('BACKBOARD_BASE_URL', 'https://app.backboard.io/api')
        self.model = os.getenv('BACKBOARD_MODEL', 'gpt-4o')
        self.model_provider = os.getenv('BACKBOARD_LLM_PROVIDER', 'openai')
        
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
    
    async def create_thread(self, assistant_id: str) -> str:
        """Create a thread for a given assistant and return thread_id."""
        if not assistant_id:
            raise ValueError("assistant_id is required to create a thread")
        
        session = await self._get_session()
        url = f"{self.base_url}/assistants/{assistant_id}/threads"
        headers = {"X-API-Key": self.api_key}
        
        async with session.post(url, headers=headers, json={}) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Backboard API error {response.status}: {error_text}")
            
            data = await response.json()
            thread_id = data.get("thread_id")
            if not thread_id:
                raise RuntimeError(f"Backboard API response missing thread_id: {data}")
            return thread_id
    
    async def send_message(
        self,
        thread_id: str,
        content: str,
        timeout: float = 60.0,
        memory: str = "Auto",
        send_to_llm: bool = True,
        web_search: str = "off"
    ) -> str:
        """
        Send a message and get response using Backboard API.
        Returns response content.
        """
        session = await self._get_session()

        if not thread_id:
            raise ValueError("thread_id is required")

        url = f"{self.base_url}/threads/{thread_id}/messages"
        headers = {"X-API-Key": self.api_key}
        form = {
            "content": content,
            "llm_provider": self.model_provider,
            "model_name": self.model,
            "memory": memory,
            "send_to_llm": "true" if send_to_llm else "false",
            "stream": "false",
            "web_search": web_search,
        }

        try:
            async with session.post(url, headers=headers, data=form, timeout=timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Backboard API error {response.status}: {error_text}")
                
                data = await response.json()
                return data.get("content", "")
                
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request exceeded timeout of {timeout}s")
        except Exception as e:
            logger.error(f"Backboard API request failed: {e}")
            raise


# Global client instance
backboard = BackboardClient()
