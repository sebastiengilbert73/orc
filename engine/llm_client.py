import ollama
from ollama import AsyncClient
from typing import List, Dict, Any

class LLMClient:
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name

    async def generate_response(self, messages: List[Dict[str, Any]], tools: List[Any] = None) -> Any:
        """"
        Sends messages to local Ollama asynchronously.
        Support tools if available.
        """
        try:
            client = AsyncClient()
            response = await client.chat(
                model=self.model_name,
                messages=messages,
                tools=tools
            )
            return response
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return None
