# app/llm_client.py
import os
import requests

class LLMClient:
    def chat(self, system: str, user: str, max_tokens: int = 350, temperature: float = 0.2) -> str:
        raise NotImplementedError

class OpenRouterClient(LLMClient):
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.model = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
        self.base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")

        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is missing")

    def chat(self, system: str, user: str, max_tokens: int = 350, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optional but recommended by many OpenRouter clients:
            # "HTTP-Referer": "http://localhost",
            # "X-Title": "fantasy-soccer-ai",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

def get_llm_client() -> LLMClient:
    provider = os.environ.get("LLM_PROVIDER", "openrouter").lower()
    if provider == "openrouter":
        return OpenRouterClient()
    raise RuntimeError(f"Unsupported LLM_PROVIDER={provider}")
