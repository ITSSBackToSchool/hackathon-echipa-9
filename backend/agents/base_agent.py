# agents/base_agent.py
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def ask(self, prompt: str):
        response = openai.ChatCompletion.create(
            model="gpt-5-nano",
            messages=[{"role": "system", "content": f"You are {self.name} agent."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]
