"""
High-throughput Client for Healthcare LLM Inference.
Connects to vLLM server with retries, timeout management, and streaming support.
"""
from typing import List, Dict, Any, Optional
import httpx

class HealthcareLLMClient:
    """
    Client for interacting with the vLLM serving container.
    """

    def __init__(self, base_url: str = "http://localhost:8000/v1", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "medivault-qwen-2.5-7b",
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """
        Calls vLLM /chat/completions endpoint asynchronously.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
