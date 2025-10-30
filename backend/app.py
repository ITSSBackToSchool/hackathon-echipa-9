from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

# Importăm CoordinatorAgent
from agents.coordinator_agent import CoordinatorAgent

# Încarcă variabilele de mediu
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Setare API key OpenAI
os.environ["OPENAI_API_KEY"] = os.getenv("CHEIE_OPENAI")

# Creează serverul Flask
app = Flask(__name__)
coordinator = CoordinatorAgent()

# Endpoint principal
@app.route("/plan", methods=["GET"])
def get_plan():
    goal = request.args.get("goal", "muscle gain")
    diet_pref = request.args.get("diet_pref", "high protein")
    try:
        plan = coordinator.plan_day(goal, diet_pref)
        return jsonify(plan)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rulează serverul
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
