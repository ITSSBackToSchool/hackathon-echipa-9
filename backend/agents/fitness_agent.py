from .base_agent import BaseAgent

class FitnessAgent(BaseAgent):
    def get_workout_plan(self, goal: str):
        prompt = f"Create a 7-day workout plan for someone with goal: {goal}"
        return self.ask(prompt)
