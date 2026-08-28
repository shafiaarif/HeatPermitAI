# backend/test_heat_intelligence_access.py
import os, requests
from dotenv import load_dotenv
load_dotenv()

response = requests.post(
    'https://api.fortyguard.com/v1/heat_intelligence',
    headers={'api-key': os.getenv("FORTYGUARD_API_KEY")},
    json={
        'latitude': 36.1699,
        'longitude': -115.1398,
        'temperature': 41.5,
        'date': '2024-07-20',
        'analysis': ['environmental']
    }
)
print("Status code:", response.status_code)
print("Response:", response.json())