import ollama

from config.settings import settings


class OllamaClient:

    def generate(self, prompt: str) -> str:

        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            options={
                "temperature": 0,
                "top_p": 1,
                "seed": 42,
            },
            messages=[{"role": "user", "content": prompt}],
        )

        return response["message"]["content"]
