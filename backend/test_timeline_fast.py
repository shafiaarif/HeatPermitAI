# backend/test_timeline_fast.py
from app.services.timeline_service import get_event_hourly_timeline

result = get_event_hourly_timeline(
    latitude=36.1699, longitude=-115.1398,
    date_str="2024-07-20", start_time="15:00", end_time="21:00",
    baseline_temperature=41.5,
)
for entry in result:
    print(entry)