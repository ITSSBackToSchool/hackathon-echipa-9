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


from .base_agent import BaseAgent
from ..adapters.google_calendar_adapter import GoogleCalendarAdapter


class CalendarAgent(BaseAgent):
    def __init__(self, name="Calendar"):
        super().__init__(name)
        self.adapter = GoogleCalendarAdapter()

    def schedule(self, workout_plan: str, meal_plan: str):
        # Preia evenimente reale
        events = self.adapter.get_upcoming_events()

        # Construiește prompt pentru OpenAI
        prompt = f"""
        You are a smart calendar assistant.
        User's upcoming events: {events}
        Workout plan: {workout_plan}
        Meal plan: {meal_plan}
        Suggest a daily schedule that fits around the existing events.
        """
        return self.ask(prompt)
