import ollama

from config.settings import settings


class OllamaClient:

    def generate(self, prompt: str) -> str:

        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]
