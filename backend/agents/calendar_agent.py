# agents/calendar_agent.py
from .base_agent import BaseAgent

class CalendarAgent(BaseAgent):
    def schedule(self, workout_plan: str, meal_plan: str):
        """
        Creează un calendar zilnic combinând planul de antrenament și planul alimentar.
        returnează un text structurat sau JSON.
        """
        prompt = f"""
        You are a smart calendar assistant. 
        Organize the following workout and meal plan into a daily schedule for 7 days.
        Include time slots for meals and workouts, assuming the user wakes up at 7 AM and sleeps at 11 PM.

        Workout Plan:
        {workout_plan}

        Meal Plan:
        {meal_plan}

        Return the schedule in a clear, structured format.
        """
        return self.ask(prompt)
