# agents/base_agent.py
import os

# Import openai lazily / defensively so the package is optional at import-time
try:
    import openai
except Exception:
    openai = None


class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def ask(self, prompt: str):
        """
        Use OpenAI to answer the prompt. If the `openai` package is not installed
        a RuntimeError is raised with a helpful message so imports won't fail.
        """
        if openai is None:
            raise RuntimeError(
                "openai package is not installed. Install it (pip install openai) to use BaseAgent.ask()"
            )

        # ensure API key is set at call time
        openai.api_key = os.getenv("OPENAI_API_KEY")

        response = openai.ChatCompletion.create(
            model="gpt-5-nano",
            messages=[{"role": "system", "content": f"You are {self.name} agent."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
