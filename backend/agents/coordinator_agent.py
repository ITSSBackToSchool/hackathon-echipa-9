# agents/coordinator_agent.py
from .fitness_agent import FitnessAgent
from .food_agent import FoodAgent
from calendar_agent import CalendarAgent  # presupunem că ai deja un calendar_agent

class CoordinatorAgent:
    def __init__(self):
        self.fitness_agent = FitnessAgent("Fitness")
        self.food_agent = FoodAgent("Food")
        self.calendar_agent = CalendarAgent("Calendar")

    def plan_day(self, goal: str, diet_pref: str):
        workout = self.fitness_agent.get_workout_plan(goal)
        meal = self.food_agent.get_meal_plan(diet_pref)
        schedule = self.calendar_agent.schedule(workout, meal)  # presupunem că ai o funcție care organizează ziua
        return {
            "workout": workout,
            "meal": meal,
            "schedule": schedule
        }
