import os
import asyncio
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BackboardClient:
    """Client for interacting with Backboard API (OpenAI-compatible)."""
    
    def __init__(self):
        self.api_key = os.getenv('BACKBOARD_API_KEY')
        self.base_url = os.getenv('BACKBOARD_BASE_URL', 'https://api.openai.com/v1')
        self.optimist_assistant_id = os.getenv('OPTIMIST_ASSISTANT_ID')
        self.pessimist_assistant_id = os.getenv('PESSIMIST_ASSISTANT_ID')
        
        if not self.api_key:
            raise ValueError("BACKBOARD_API_KEY not set")
        if not self.optimist_assistant_id:
            raise ValueError("OPTIMIST_ASSISTANT_ID not set")
        if not self.pessimist_assistant_id:
            raise ValueError("PESSIMIST_ASSISTANT_ID not set")
        
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
    
    async def create_thread(self) -> str:
        """Create a new thread and return thread_id."""
        thread = await self.client.beta.threads.create()
        return thread.id
    
    async def add_message(self, thread_id: str, content: str, role: str = "user") -> None:
        """Add a message to a thread."""
        await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content
        )
    
    async def run_assistant(
        self, 
        thread_id: str, 
        assistant_id: str, 
        timeout: float = 60.0
    ) -> str:
        """
        Run an assistant on a thread and wait for completion.
        Returns the assistant's response text.
        Raises TimeoutError if timeout is exceeded.
        """
        run = await self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        response = await self.wait_for_run(thread_id, run.id, timeout=timeout)
        return response
    
    async def wait_for_run(
        self, 
        thread_id: str, 
        run_id: str, 
        timeout: float = 60.0,
        poll_interval: float = 1.0
    ) -> str:
        """
        Wait for a run to complete and return the assistant's message.
        Raises TimeoutError if timeout is exceeded.
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                try:
                    await self.client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run_id
                    )
                except Exception as e:
                    logger.error(f"Failed to cancel run {run_id}: {e}")
                raise TimeoutError(f"Run {run_id} exceeded timeout of {timeout}s")
            
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                
                if messages.data:
                    content = messages.data[0].content[0].text.value
                    return content
                else:
                    raise RuntimeError(f"Run {run_id} completed but no messages found")
            
            elif run.status in ["failed", "cancelled", "expired"]:
                error_msg = f"Run {run_id} ended with status: {run.status}"
                if hasattr(run, 'last_error') and run.last_error:
                    error_msg += f" - {run.last_error}"
                raise RuntimeError(error_msg)
            
            await asyncio.sleep(poll_interval)
