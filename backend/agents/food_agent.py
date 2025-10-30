# agents/food_agent.py
from .base_agent import BaseAgent

class FoodAgent(BaseAgent):
    def get_meal_plan(self, diet_pref: str):
        """
        Generează un plan alimentar pe 7 zile pe baza preferințelor alimentare.
        diet_pref: string (ex: "vegan", "high protein", "low carb")
        """
        prompt = f"""
        You are a nutrition expert. Create a 7-day meal plan for someone who follows a {diet_pref} diet.
        Include breakfast, lunch, dinner, and optional snacks for each day.
        Make it varied and balanced.
        """
        return self.ask(prompt)
