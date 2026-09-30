"""LangChain adapter; the optional provider is loaded only on first invocation."""

from typing import Any


class OllamaChatService:
    def __init__(
        self,
        model: str,
        *,
        base_url: str = "http://localhost:11434",
        timeout: float = 120,
        client: Any = None,
    ):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self._client = client

    def complete(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must not be blank")
        if self._client is None:
            from langchain_ollama import ChatOllama

            self._client = ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=0.2,
                client_kwargs={"timeout": self.timeout},
            )
        content = self._client.invoke(prompt).content
        if not isinstance(content, str) or not content.strip():
            raise ValueError("LLM returned an empty or unsupported response")
        return content
