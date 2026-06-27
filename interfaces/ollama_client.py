from typing import Optional

import ollama

from config.settings import settings


class OllamaClient:
    def __init__(self, temperature: float = 0.0, seed: Optional[int] = None):
        self.temperature = temperature
        self.seed = seed

    def generate(self, prompt: str, json_format: bool = False) -> str:
        options = {
            "temperature": self.temperature,
            "top_p": 1,
        }
        if self.seed is not None:
            options["seed"] = self.seed

        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            options=options,
            format="json" if json_format else "",
            messages=[{"role": "user", "content": prompt}],
        )

        return response["message"]["content"]
