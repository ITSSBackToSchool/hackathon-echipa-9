from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

# Importăm CoordinatorAgent
from agents.coordinator_agent import CoordinatorAgent

# Încarcă variabilele de mediu
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Setare API key OpenAI (dacă o folosești în Coordinator)
os.environ["OPENAI_API_KEY"] = os.getenv("CHEIE_OPENAI", "")

# Creează serverul Flask
app = Flask(__name__)
coordinator = CoordinatorAgent()

# Endpoint principal (POST în loc de GET)
@app.route("/plan", methods=["POST"])
def create_plan():
    # Acceptă JSON; dacă nu e JSON, întoarce 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Expected JSON body"}), 400

    goal = data.get("goal")
    diet_pref = data.get("diet_pref")

    if not goal:
        return jsonify({"error": "Missing field: goal"}), 400
    if not diet_pref:
        return jsonify({"error": "Missing field: diet_pref"}), 400

    try:
        plan = coordinator.plan_day(goal, diet_pref)
        return jsonify(plan), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rulează serverul
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
