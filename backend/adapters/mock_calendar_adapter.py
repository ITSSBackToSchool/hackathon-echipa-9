"""Mock calendar adapter that returns test data instantly."""

class MockCalendarAdapter:
    def __init__(self):
        pass  # No auth or API setup needed
        
    def get_upcoming_events(self, max_results=10):
        """Return test events instantly."""
        return [
            {
                'summary': 'Test Event Today',
                'start': '2025-10-30T10:00:00+02:00',
                'end': '2025-10-30T11:00:00+02:00'
            },
            {
                'summary': 'Test Event Tomorrow',
                'start': '2025-10-31T14:00:00+02:00',
                'end': '2025-10-31T15:00:00+02:00'
            },
            {
                'summary': 'Test Event Next Week',
                'start': '2025-11-05T09:00:00+02:00',
                'end': '2025-11-05T10:00:00+02:00'
            }
        ]