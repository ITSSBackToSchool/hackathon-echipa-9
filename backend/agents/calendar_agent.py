# agents/calendar_agent.py
"""CalendarAgent wraps calendar functionality and (optionally) uses a
GoogleCalendarAdapter if available. The Google adapter is imported
defensively so the module can be imported even when google packages
aren't installed (useful for local dev/tests).
"""
from .base_agent import BaseAgent

# Try to import the real Google adapter. During development you can swap to a mock by
# editing this line, but the default is the real adapter which will prompt for OAuth
try:
    from adapters.google_calendar_adapter import GoogleCalendarAdapter
except Exception:
    # If import fails (missing google libs), fall back to None so the agent stays importable.
    GoogleCalendarAdapter = None


class CalendarAgent(BaseAgent):
    def __init__(self, name="Calendar"):
        super().__init__(name)
        # Instantiate adapter if available, otherwise leave as None.
        if GoogleCalendarAdapter is not None:
            try:
                self.adapter = GoogleCalendarAdapter()
                self._adapter_init_error = None
            except Exception as e:
                # If adapter initialization fails (missing credentials, libs, etc.), continue without it
                self.adapter = None
                # record the initialization error for diagnostics
                self._adapter_init_error = str(e)
        else:
            self.adapter = None
            self._adapter_init_error = "GoogleCalendarAdapter not available (google packages may be missing)"

    def schedule(self, workout_plan: str, meal_plan: str):
        # If we have an adapter, ask for upcoming events; otherwise proceed with empty events.
        events = []
        if getattr(self, 'adapter', None) is not None:
            try:
                events = self.adapter.get_upcoming_events()
            except Exception:
                events = []

        # Construiește prompt pentru OpenAI
        print("Events from Google Calendar:", events)
        prompt = f"""
        First of all include in your response the upcoming events from the user's calendar{events}.
        You are a smart calendar assistant.
        User's upcoming events: {events}
        Workout plan: {workout_plan}
        Meal plan: {meal_plan}
        Suggest a daily schedule that fits around the existing events.
        """
        return self.ask(prompt)
