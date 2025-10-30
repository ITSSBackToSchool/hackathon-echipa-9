# backend/app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# ==== Agenți / Adaptoare ====
from agents.coordinator_agent import CoordinatorAgent

# importuri opționale (nu crăpăm dacă lipsesc)
try:
    from adapters.google_calendar_adapter import GoogleCalendarAdapter
except Exception:
    GoogleCalendarAdapter = None

try:
    from agents.food_agent import FoodAgent
except Exception:
    FoodAgent = None

try:
    from agents.fitness_agent import FitnessAgent
except Exception:
    FitnessAgent = None


# ==== Config .env & OpenAI ====
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))
os.environ["OPENAI_API_KEY"] = os.getenv("CHEIE_OPENAI", "")

# ==== Flask app ====
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
CORS(app)

coordinator = CoordinatorAgent()


# ========================= Helpers =========================
_google_adapter_singleton = None
def resolve_google_adapter():
    """1) din coordinator.calendar_agent.adapter; 2) lazy singleton local."""
    global _google_adapter_singleton
    cal_agent = getattr(coordinator, "calendar_agent", None)
    if cal_agent is not None:
        adapter = getattr(cal_agent, "adapter", None)
        if adapter is not None:
            return adapter
    if _google_adapter_singleton is None and GoogleCalendarAdapter is not None:
        _google_adapter_singleton = GoogleCalendarAdapter()
    return _google_adapter_singleton


_food_agent_singleton = None
def resolve_food_agent():
    """1) din coordinator.food_agent; 2) lazy singleton local."""
    global _food_agent_singleton
    fa = getattr(coordinator, "food_agent", None)
    if fa is not None:
        return fa
    if _food_agent_singleton is None and FoodAgent is not None:
        _food_agent_singleton = FoodAgent()
    return _food_agent_singleton


_fitness_agent_singleton = None
def resolve_fitness_agent():
    """1) din coordinator.fitness_agent; 2) lazy singleton local."""
    global _fitness_agent_singleton
    fa = getattr(coordinator, "fitness_agent", None)
    if fa is not None:
        return fa
    if _fitness_agent_singleton is None and FitnessAgent is not None:
        _fitness_agent_singleton = FitnessAgent()
    return _fitness_agent_singleton


def _parse_any_iso(s: str):
    """datetime tz-aware dintr-un ISO (dateTime sau date)."""
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s).replace(tzinfo=datetime.now().astimezone().tzinfo)
    except Exception:
        return None


def build_calendar_context_for_next_days(adapter, days: int = 7, max_per_day: int = 8) -> str:
    """Context compact cu programul din următoarele `days` zile pentru adaptare plan."""
    now = datetime.now().astimezone()
    limit = now + timedelta(days=days)

    events = []
    if hasattr(adapter, "get_now_and_upcoming"):
        data = adapter.get_now_and_upcoming(limit_upcoming=400) or {}
        if data.get("current"):
            events.append(data["current"])
        events.extend(data.get("upcoming", []))
    elif hasattr(adapter, "get_future_events"):
        events = adapter.get_future_events(limit_upcoming=400)
    else:
        return ""

    filtered = []
    for e in events:
        s = _parse_any_iso(e.get("start"))
        if not s or s < now or s > limit:
            continue
        filtered.append(e)

    by_date = {}
    for e in filtered:
        s = _parse_any_iso(e.get("start"))
        en = _parse_any_iso(e.get("end"))
        key = s.date().isoformat() if s else "unknown"
        by_date.setdefault(key, []).append((s, en, e.get("summary", "No Title"), e.get("location", "")))

    lines = [f"User schedule for the next {days} days (from calendar):"]
    for day in sorted(by_date.keys()):
        items = sorted(by_date[day], key=lambda x: (x[0] or datetime.max))[:max_per_day]
        pretty = []
        for s, en, title, loc in items:
            if s and en and s.time() != datetime.min.time():
                slot = f"{s.strftime('%H:%M')}-{en.strftime('%H:%M') if en else '?'} {title}"
            else:
                slot = f"All-day {title}"
            if loc:
                slot += f" @ {loc}"
            pretty.append(slot)
        lines.append(f"- {day}: " + ("; ".join(pretty) if pretty else "no events"))
    lines.append("Adapt around busy slots; use short sessions on packed days and longer sessions when free.")
    return "\n".join(lines)


# ========================= API: Planner =========================
@app.route("/plan", methods=["POST"])
def create_plan():
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


# ========================= API: Calendar =========================
@app.route("/events", methods=["GET"])
def get_events():
    try:
        max_results = request.args.get("max_results", default=10, type=int)
        adapter = resolve_google_adapter()
        if adapter is None:
            return jsonify({"events": [], "adapter_present": False, "adapter_error": "calendar adapter not available"}), 200

        if hasattr(adapter, "get_upcoming_events"):
            events = adapter.get_upcoming_events(max_results=max_results)
            return jsonify({"events": events, "adapter_present": True, "adapter_error": None}), 200

        if hasattr(adapter, "get_now_and_upcoming"):
            data = adapter.get_now_and_upcoming(limit_upcoming=max_results)
            out = []
            if data.get("current"):
                cur = data["current"]
                out.append({
                    "summary": cur.get("summary", "No Title"),
                    "location": cur.get("location", ""),
                    "start": cur.get("start"),
                    "end": cur.get("end"),
                    "start_date": cur.get("start_date"),
                    "end_date": cur.get("end_date"),
                })
            for e in data.get("upcoming", []):
                if len(out) >= max_results:
                    break
                out.append({
                    "summary": e.get("summary", "No Title"),
                    "location": e.get("location", ""),
                    "start": e.get("start"),
                    "end": e.get("end"),
                    "start_date": e.get("start_date"),
                    "end_date": e.get("end_date"),
                })
            return jsonify({"events": out, "adapter_present": True, "adapter_error": None}), 200

        return jsonify({"events": [], "adapter_present": True, "adapter_error": "adapter has no supported methods"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/calendar/month-split", methods=["GET"])
def api_calendar_month_split():
    try:
        adapter = resolve_google_adapter()
        if adapter is None:
            return jsonify({"error": "calendar adapter not available"}), 400
        if not hasattr(adapter, "get_month_split"):
            return jsonify({"error": "adapter missing get_month_split"}), 400
        limit_past = int(request.args.get("limit_past", "50"))
        limit_future = int(request.args.get("limit_future", "50"))
        data = adapter.get_month_split(limit_past=limit_past, limit_future=limit_future)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/calendar/now-and-next", methods=["GET"])
def api_calendar_now_and_next():
    try:
        adapter = resolve_google_adapter()
        if adapter is None:
            return jsonify({"error": "calendar adapter not available"}), 400
        if not hasattr(adapter, "get_now_and_upcoming"):
            return jsonify({"error": "adapter missing get_now_and_upcoming"}), 400
        limit = int(request.args.get("limit", "10"))
        data = adapter.get_now_and_upcoming(limit_upcoming=limit)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========================= API: Food (calendar-aware) =========================
@app.route("/api/food/generate", methods=["POST"])
def api_food_generate():
    data = request.get_json(silent=True) or {}
    diet_pref   = (data.get("diet_pref") or "").strip()
    user_prompt = (data.get("prompt") or "").strip()

    agent = resolve_food_agent()
    if agent is None:
        return jsonify({"error": "FoodAgent indisponibil"}), 500

    calendar_ctx = ""
    adapter = resolve_google_adapter()
    if adapter is not None:
        try:
            calendar_ctx = build_calendar_context_for_next_days(adapter, days=7, max_per_day=8)
        except Exception:
            calendar_ctx = ""

    try:
        if user_prompt:
            ctx = []
            if diet_pref: ctx.append(f"Dietary preference: {diet_pref}.")
            if calendar_ctx: ctx.append(calendar_ctx)
            final_prompt = (("\n\n".join(ctx) + "\n\n") if ctx else "") + \
                "Task: " + user_prompt + "\n\n" + \
                "Adapt to the schedule above; quick/portable meals on packed days; batch-cooking on lighter days."
            content = agent.ask(final_prompt)
        else:
            pref = diet_pref if diet_pref else "balanced"
            final_prompt = (f"Dietary preference: {pref}.\n" if pref else "") + \
                (calendar_ctx + "\n\n" if calendar_ctx else "") + \
                "You are a nutrition expert. Create a 7-day meal plan adapted to the user's calendar above. " \
                "Include breakfast, lunch, dinner, snacks; quick meals on busy days; batch-cooking on free days."
            content = agent.ask(final_prompt)

        return jsonify({"diet_pref": diet_pref or None, "used_calendar": bool(calendar_ctx), "content": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========================= API: Fitness (calendar-aware) =========================
@app.route("/api/fitness/generate", methods=["POST"])
def api_fitness_generate():
    """
    Body JSON (toate opționale):
    {
      "goal": "muscle gain | fat loss | endurance | general fitness | ...",
      "experience": "beginner | intermediate | advanced",
      "equipment": "gym | dumbbells | bodyweight | bands | mixed",
      "injuries": "ex: knee pain; avoid overhead press...",
      "prompt": "text liber"
    }
    - Citește automat programul din calendar pe 7 zile.
    - Dacă `prompt` e prezent -> îl folosește împreună cu contextul.
    - Altfel -> generează un plan pe 7 zile (workout split) adaptat programului.
    """
    data = request.get_json(silent=True) or {}
    goal        = (data.get("goal") or "").strip()
    experience  = (data.get("experience") or "").strip()
    equipment   = (data.get("equipment") or "").strip()
    injuries    = (data.get("injuries") or "").strip()
    user_prompt = (data.get("prompt") or "").strip()

    agent = resolve_fitness_agent()
    if agent is None:
        return jsonify({"error": "FitnessAgent indisponibil"}), 500

    # context din calendar
    calendar_ctx = ""
    adapter = resolve_google_adapter()
    if adapter is not None:
        try:
            calendar_ctx = build_calendar_context_for_next_days(adapter, days=7, max_per_day=8)
        except Exception:
            calendar_ctx = ""

    # compunem contextul fix
    ctx_parts = []
    if goal:       ctx_parts.append(f"Fitness goal: {goal}.")
    if experience: ctx_parts.append(f"Experience level: {experience}.")
    if equipment:  ctx_parts.append(f"Available equipment: {equipment}.")
    if injuries:   ctx_parts.append(f"Injury/limitations: {injuries}.")
    if calendar_ctx: ctx_parts.append(calendar_ctx)
    ctx_block = "\n".join(ctx_parts).strip()

    try:
        if user_prompt:
            final_prompt = (ctx_block + "\n\n" if ctx_block else "") + \
                f"Task: {user_prompt}\n\n" \
                "Please adapt to the user's calendar: schedule short, efficient sessions on busy days " \
                "(e.g., 20–30 min EMOM/AMRAP or circuit), longer sessions on lighter days; " \
                "include warm-up, cool-down, and weekly progression guidance."
            content = agent.ask(final_prompt)
        else:
            # prompt implicit 7 zile
            base_goal = goal if goal else "general fitness"
            final_prompt = \
                (f"Fitness goal: {base_goal}.\n" if base_goal else "") + \
                (f"Experience level: {experience}.\n" if experience else "") + \
                (f"Available equipment: {equipment}.\n" if equipment else "") + \
                (f"Injury/limitations: {injuries}.\n" if injuries else "") + \
                (calendar_ctx + "\n\n" if calendar_ctx else "") + \
                "You are a strength & conditioning coach. Build a 7-day workout plan ADAPTED to the calendar above. " \
                "Specify for each day: session type, main exercises (sets x reps or time), intensity/RPE, and duration. " \
                "On packed days propose short 20–30 min routines; on free days include longer sessions. " \
                "Include warm-up and cool-down guidance, plus weekly progression tips."
            content = agent.ask(final_prompt)

        return jsonify({
            "goal": goal or None,
            "experience": experience or None,
            "equipment": equipment or None,
            "injuries": injuries or None,
            "used_calendar": bool(calendar_ctx),
            "content": content
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========================= Front-end (templates) =========================
@app.route("/")
def index_page():
    return render_template("index.html")

@app.route("/index")
def index_redirect():
    return redirect(url_for("index_page"))

@app.route("/calendar")
def calendar_page():
    return render_template("calendar.html")

@app.route("/food")
def food_page():
    return render_template("food.html")

@app.route("/fitness")
def fitness_page():
    return render_template("fitness.html")


# ========================= Run =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
