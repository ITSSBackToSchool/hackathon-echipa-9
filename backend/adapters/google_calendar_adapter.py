import os
from datetime import datetime, timedelta
from calendar import monthrange
from typing import List, Dict, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarAdapter:
    def __init__(self):
        self.creds: Optional[Credentials] = None
        self.service = None
        self.authenticate()

    # ---------------- OAuth + Service ----------------
    def authenticate(self):
        # caută credentials.json în mai multe locuri + env
        candidates = []
        env_path = os.getenv("GOOGLE_CREDENTIALS_PATH") or os.getenv("GOOGLE_CREDENTIALS")
        if env_path:
            candidates.append(env_path)

        here = os.path.join(os.path.dirname(__file__), "credentials.json")
        parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "credentials.json"))
        grand = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "credentials.json"))
        candidates.extend([here, parent, grand])

        creds_file = next((p for p in candidates if os.path.exists(p)), None)
        if not creds_file:
            raise FileNotFoundError(f"Could not find Google credentials.json. Tried: {candidates}")

        # token.json (persist consimțământul)
        token_candidates = []
        token_env = os.getenv("GOOGLE_TOKEN_PATH")
        if token_env:
            token_candidates.append(token_env)
        token_candidates.append(os.path.join(os.path.dirname(__file__), "token.json"))
        token_candidates.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "token.json")))
        token_file = next((t for t in token_candidates if os.path.exists(t)), None)

        creds = None
        if token_file:
            try:
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
            try:
                save_to = token_file or os.path.join(os.path.dirname(__file__), "token.json")
                with open(save_to, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            except Exception:
                pass

        self.creds = creds
        self.service = build("calendar", "v3", credentials=self.creds)

    # ---------------- Helpers ----------------
    def _parse_dt(self, ev: dict, key: str) -> Optional[datetime]:
        """
        Returnează datetime tz-aware pentru ev['start'] / ev['end'].
        Suportă 'dateTime' (cu offset/Z) și 'date' (all-day -> miezul nopții în TZ local).
        """
        val = ev.get(key, {})
        if "dateTime" in val:
            # ex: 2025-10-30T09:00:00+02:00 sau ...Z
            return datetime.fromisoformat(val["dateTime"].replace("Z", "+00:00"))
        if "date" in val:
            local_tz = datetime.now().astimezone().tzinfo
            return datetime.fromisoformat(val["date"]).replace(tzinfo=local_tz)
        return None

    def _date_str(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.date().isoformat() if dt else None

    def _simplify(self, ev: dict) -> dict:
        s_dt = self._parse_dt(ev, "start")
        e_dt = self._parse_dt(ev, "end")
        return {
            "summary": ev.get("summary", "No Title"),
            "location": (ev.get("location") or ""),
            "start": ev["start"].get("dateTime", ev["start"].get("date")),
            "end": ev["end"].get("dateTime", ev["end"].get("date")),
            "start_date": self._date_str(s_dt),
            "end_date": self._date_str(e_dt),
        }

    # ---------------- Fetch utils ----------------
    def _list_events(self, time_min_iso: str, time_max_iso: str, cap: int = 500) -> List[dict]:
        """Listează evenimente între timeMin și timeMax, ordonate, cu paging."""
        events, page_token = [], None
        while True:
            resp = self.service.events().list(
                calendarId="primary",
                singleEvents=True,
                orderBy="startTime",
                timeMin=time_min_iso,
                timeMax=time_max_iso,
                maxResults=250,
                pageToken=page_token,
            ).execute()
            items = resp.get("items", [])
            events.extend(items)
            if len(events) >= cap:
                break
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return events

    # ---------------- Cerința ta: split pe luni ----------------
    def get_month_split(self, limit_past: int = 50, limit_future: int = 50) -> Dict[str, List[dict]]:
        """
        Întoarce un dict cu două liste:
          - 'past_current_month': evenimente CU START < now din luna CURENTĂ
          - 'future_next_month' : evenimente CU START în luna URMĂTOARE (>= 1 ale lunii viitoare)
        Format simplificat (fără id/htmlLink), cu start/end + start_date/end_date.
        """
        now = datetime.now().astimezone()

        # limitele pentru luna curentă
        start_of_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # începutul lunii următoare
        next_year = now.year + (1 if now.month == 12 else 0)
        next_month = 1 if now.month == 12 else now.month + 1
        start_of_next = now.replace(year=next_year, month=next_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        # sfârșitul (inclusiv) lunii următoare
        last_day_next = monthrange(next_year, next_month)[1]
        end_of_next = now.replace(
            year=next_year, month=next_month, day=last_day_next,
            hour=23, minute=59, second=59, microsecond=0
        )

        # 1) fetch o singură dată: din începutul lunii curente până la finalul lunii următoare
        all_events = self._list_events(start_of_current.isoformat(), end_of_next.isoformat(), cap=1000)

        past_current_month: List[dict] = []
        future_next_month: List[dict] = []

        for e in all_events:
            s_dt = self._parse_dt(e, "start")
            if not s_dt:
                continue
            # past din luna curentă: start >= start_of_current și start < now
            if start_of_current <= s_dt < now:
                past_current_month.append(self._simplify(e))
            # future din luna viitoare: start >= start_of_next (nu includem viitorul din luna curentă)
            elif s_dt >= start_of_next:
                future_next_month.append(self._simplify(e))

        # sortări
        past_current_month.sort(key=lambda x: x["start"])                 # cronologic crescător
        future_next_month.sort(key=lambda x: x["start"])                  # cronologic crescător

        # aplică limite
        if limit_past is not None and limit_past > 0:
            past_current_month = past_current_month[-limit_past:]         # ultimele N din luna curentă
        if limit_future is not None and limit_future > 0:
            future_next_month = future_next_month[:limit_future]          # primele N din luna viitoare

        return {
            "past_current_month": past_current_month,
            "future_next_month": future_next_month
        }

    # ---------------- Compat: metoda cerută de rutele vechi ----------------
    def get_upcoming_events(self, max_results: int = 20, include_current: bool = True) -> List[dict]:
        """
        Compatibilitate cu rutele existente: returnează o listă combinată
        (eveniment curent dacă există + evenimente viitoare de la ACUM până la sfârșitul lunii următoare).
        """
        data = self.get_now_and_upcoming(limit_upcoming=max_results)
        out: List[dict] = []
        if include_current and data.get("current"):
            cur = data["current"]
            out.append({
                "summary": cur["summary"],
                "location": cur.get("location", ""),
                "start": cur["start"],
                "end": cur["end"],
                "start_date": cur.get("start_date"),
                "end_date": cur.get("end_date"),
            })
        for e in data.get("upcoming", []):
            if len(out) >= max_results:
                break
            out.append({
                "summary": e["summary"],
                "location": e.get("location", ""),
                "start": e["start"],
                "end": e["end"],
                "start_date": e.get("start_date"),
                "end_date": e.get("end_date"),
            })
        return out

    # ---------------- Util: acum + viitoare (folosită mai sus) ----------------
    def get_current_event(self) -> Optional[dict]:
        """Evenimentul care rulează ACUM (dacă există)."""
        now = datetime.now().astimezone()
        resp = self.service.events().list(
            calendarId="primary",
            singleEvents=True,
            orderBy="startTime",
            timeMin=(now - timedelta(days=1)).isoformat(),
            timeMax=(now + timedelta(days=1)).isoformat(),
            maxResults=250,
        ).execute()

        for e in resp.get("items", []):
            s = self._parse_dt(e, "start")
            en = self._parse_dt(e, "end")
            if not s or not en:
                continue
            if s <= now < en:
                return self._simplify(e)
        return None

    def get_future_events(self, limit_upcoming: int = 20) -> List[dict]:
        """Doar evenimente viitoare (de la ACUM până la sfârșitul lunii următoare)."""
        now = datetime.now().astimezone()
        nm_year = now.year + (1 if now.month == 12 else 0)
        nm_month = 1 if now.month == 12 else now.month + 1
        last_day_next = monthrange(nm_year, nm_month)[1]
        end_of_next_month = now.replace(
            year=nm_year, month=nm_month, day=last_day_next,
            hour=23, minute=59, second=59, microsecond=0
        )

        events = self._list_events(now.isoformat(), end_of_next_month.isoformat(), cap=max(250, limit_upcoming))
        simple = [self._simplify(e) for e in events]
        return simple[:limit_upcoming]

    def get_now_and_upcoming(self, limit_upcoming: int = 20) -> Dict[str, Optional[List[dict]]]:
        """Combinație: evenimentul curent + lista viitoarelor (fără dubluri)."""
        current = self.get_current_event()
        upcoming = self.get_future_events(limit_upcoming=limit_upcoming)
        if current:
            upcoming = [e for e in upcoming if not (
                e.get("summary") == current.get("summary")
                and e.get("start") == current.get("start")
                and e.get("end") == current.get("end")
            )]
        return {"current": current, "upcoming": upcoming}
