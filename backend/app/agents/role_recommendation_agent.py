"""
Role Recommendation Agent — , upgraded to LLM-generated.
Given the risk assessment + event context (type, attendance, duration),
asks the LLM to generate role-specific guidance for 5 personas: attendees,
medical team, event staff, performers, event manager. This makes the
guidance genuinely event-specific (a 200-person yoga festival gets
different practical advice than a 10,000-person concert) instead of a
fixed template keyed only on risk status.

Falls back to the original deterministic templates if the LLM call fails
or returns something unparseable — reliability over creativity when the
LLM is unavailable, same pattern as the Decision Agent.
"""
import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-3.5-flash-lite")


class RoleGuidance(BaseModel):
    attendees: str = Field(..., min_length=10)
    medical_team: str = Field(..., min_length=10)
    event_staff: str = Field(..., min_length=10)
    performers: str = Field(..., min_length=10)
    event_manager: str = Field(..., min_length=10)


ROLE_PROMPT = """You are a heat-safety advisor generating role-specific guidance for an outdoor event.

Risk Assessment:
- Risk Score: {risk_score}/100 ({status})
- Peak Temperature: {peak_temperature}°C
- Exceedance Hours: {exceedance_hours} (hours above 35°C threshold)

Event Context:
- Type: {event_type}
- Attendance: {attendance} people
- Schedule: {start_time} to {end_time} ({duration_hours} hours)

Generate ONE short, practical, 1-2 sentence instruction for each of these five roles, tailored to
THIS specific event — its size, type, and duration, not just the risk tier in the abstract.
A 200-person morning yoga session needs different practical guidance than a 10,000-person evening concert,
even at the same risk score. Be concrete (e.g. specific rotation intervals, staffing implications tied to
the actual attendance number, hydration station counts proportional to crowd size) rather than generic.

Respond with ONLY valid JSON, no other text, matching exactly this shape:
{{
  "attendees": "...",
  "medical_team": "...",
  "event_staff": "...",
  "performers": "...",
  "event_manager": "..."
}}"""


ROLE_TEMPLATES = {
    "HIGH RISK": {
        "attendees": "Extreme heat expected. Stay hydrated, seek shade or cooling areas frequently, and limit continuous outdoor exposure. Watch for signs of heat exhaustion in yourself and others.",
        "medical_team": "Deploy at full staffing with dedicated heat-illness response capability. Pre-position cooling equipment (ice, misting fans) at multiple stations. Expect elevated incident volume.",
        "event_staff": "Rotate outdoor personnel every 30 minutes. Mandatory hydration breaks. Any staff member showing heat-stress symptoms should be relieved immediately.",
        "performers": "Schedule frequent, extended cooling breaks between sets. Avoid prolonged direct-sun performance segments where possible.",
        "event_manager": "Strongly consider rescheduling or the suggested schedule change. If proceeding, activate the full emergency heat response plan and brief all staff before doors open.",
    },
    "MODERATE RISK": {
        "attendees": "Warm conditions expected. Stay hydrated and use shaded or cooled areas during peak hours.",
        "medical_team": "Increase heat-related readiness above baseline. Have cooling supplies accessible.",
        "event_staff": "Rotate outdoor personnel every 45-60 minutes. Encourage regular water breaks.",
        "performers": "Standard cooling breaks recommended between sets during peak-heat hours.",
        "event_manager": "Proceed with standard heat-safety protocols active. Monitor conditions and be ready to escalate interventions if heat rises.",
    },
    "LOW-MODERATE RISK": {
        "attendees": "Mild heat expected. Stay hydrated as a general precaution.",
        "medical_team": "Standard staffing sufficient; keep basic hydration/cooling supplies on hand.",
        "event_staff": "Normal rotation schedule; water available on request.",
        "performers": "No special heat accommodations required beyond standard breaks.",
        "event_manager": "Proceed as planned. Standard safety protocols are sufficient.",
    },
    "LOW RISK": {
        "attendees": "Comfortable conditions expected. No special heat precautions needed.",
        "medical_team": "Standard event staffing sufficient.",
        "event_staff": "Normal operations.",
        "performers": "No heat-related accommodations needed.",
        "event_manager": "Proceed as planned. No additional heat-safety measures required.",
    },
}


def _rule_based_fallback(status: str) -> dict:
    """Deterministic fallback used when the LLM output can't be parsed/validated."""
    print(f"  [role_agent] Using RULE-BASED FALLBACK (status={status})")
    return ROLE_TEMPLATES.get(status, ROLE_TEMPLATES["MODERATE RISK"])


def get_role_recommendations(assessment: dict, event: dict) -> dict:
    """
    assessment: dict with risk_score, status, peak_temperature, exceedance_hours,
                duration_hours
    event: dict with event_type, attendance, start_time, end_time
    """
    prompt = ROLE_PROMPT.format(
        risk_score=assessment["risk_score"],
        status=assessment["status"],
        peak_temperature=assessment["peak_temperature"],
        exceedance_hours=assessment["exceedance_hours"],
        event_type=event.get("event_type", "general"),
        attendance=event.get("attendance", 0),
        start_time=event.get("start_time", "?"),
        end_time=event.get("end_time", "?"),
        duration_hours=assessment.get("duration_hours", "?"),
    )

    try:
        print("  [role_agent] Calling Gemini for event-specific role guidance...")
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        print(f"  [role_agent] Raw LLM output: {raw_text[:200]}...")

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        guidance = RoleGuidance(**parsed)
        print("  [role_agent] Validated LLM role guidance")
        return guidance.model_dump()

    except (json.JSONDecodeError, ValidationError, KeyError, IndexError, Exception) as e:
        print(f"  [role_agent] LLM output invalid ({type(e).__name__}: {e}) — falling back to templates")
        return _rule_based_fallback(assessment["status"])