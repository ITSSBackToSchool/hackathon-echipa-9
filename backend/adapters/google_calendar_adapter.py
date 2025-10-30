import os
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class GoogleCalendarAdapter:
    def __init__(self):
        self.creds = None
        self.service = None
        # Cache for events
        self._events_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # cache TTL in seconds (5 minutes)
        self.authenticate()

    def authenticate(self):
        # Folosește flow-ul de desktop
        # Locate credentials.json. Allow an env var override, and fall back to
        # common locations (adapters/credentials.json, backend/credentials.json).
        possible = []
        env_path = os.getenv('GOOGLE_CREDENTIALS_PATH') or os.getenv('GOOGLE_CREDENTIALS')
        if env_path:
            possible.append(env_path)

        cur = os.path.join(os.path.dirname(__file__), 'credentials.json')
        possible.append(cur)

        parent = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'credentials.json'))
        possible.append(parent)

        grand = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json'))
        possible.append(grand)

        creds_file = None
        for p in possible:
            if os.path.exists(p):
                creds_file = p
                break

        if creds_file is None:
            # give a clear error listing which paths were tried
            raise FileNotFoundError(f"Could not find Google credentials.json. Tried: {possible}")

        flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
        self.creds = flow.run_local_server(port=0)
        self.service = build('calendar', 'v3', credentials=self.creds)

    def get_upcoming_events(self, max_results=10):
        # Check if we have a valid cache
        now = time.time()
        if (self._events_cache is not None and 
            self._cache_timestamp is not None and 
            now - self._cache_timestamp < self._cache_ttl):
            print("[Calendar] Using cached events")
            return self._events_cache

        # Cache miss or expired - fetch from API
        print("[Calendar] Fetching fresh events from API")
        # Build a time window: start = first day of current month at 00:00 (local timezone)
        # end = last day of next month at 23:59:59 (local timezone)
        from datetime import datetime, timedelta
        import calendar

        now_local = datetime.now().astimezone()  # tz-aware local time
        start_of_month = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # compute year/month for next month
        nm_year = now_local.year + (1 if now_local.month == 12 else 0)
        nm_month = 1 if now_local.month == 12 else now_local.month + 1
        # last day of next month
        last_day_next = calendar.monthrange(nm_year, nm_month)[1]
        end_of_next_month = now_local.replace(year=nm_year, month=nm_month, day=last_day_next,
                                              hour=23, minute=59, second=59, microsecond=0)

        # Convert to RFC3339 strings (include timezone offset)
        time_min = start_of_month.isoformat()
        time_max = end_of_next_month.isoformat()

        # Debug prints (server console)
        print(f"[Calendar] Query window: timeMin={time_min}, timeMax={time_max}")

        events_result = self.service.events().list(
            calendarId='primary',
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime',
            timeMin=time_min,
            timeMax=time_max,
        ).execute()
        events = events_result.get('items', [])
        
        # Simplify and cache the events
        simplified_events = [
            {
                'summary': e.get('summary', 'No Title'),
                'start': e['start'].get('dateTime', e['start'].get('date')),
                'end': e['end'].get('dateTime', e['end'].get('date'))
            } for e in events
        ]
        
        # Update cache
        self._events_cache = simplified_events
        self._cache_timestamp = now
        
        return simplified_events
