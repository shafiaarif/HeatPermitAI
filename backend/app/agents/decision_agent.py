"""
Decision Agent —  (LangGraph Node 4).
Takes a risk assessment + event context, asks the LLM to recommend
PROCEED / MODIFY / ADD_INTERVENTIONS / POSTPONE, validates the JSON
strictly, and falls back to a deterministic rule if the LLM output
is malformed or unparseable.
Uses Google Gemini (free tier, no payment required) instead of a paid API.
"""
import os
import json
import google.generativeai as genai
from pydantic import ValidationError
from app.agents.decision_schema import DecisionOutput
from dotenv import load_dotenv
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# model = genai.GenerativeModel("gemini-2.5-flash")
model = genai.GenerativeModel("gemini-3.5-flash-lite")

DECISION_PROMPT = """You are a heat-safety decision agent for outdoor events. Given the risk assessment below, recommend ONE of exactly these four actions: PROCEED, MODIFY, ADD_INTERVENTIONS, or POSTPONE.

Risk Assessment:
- Risk Score: {risk_score}/100 ({status})
- Peak Temperature: {peak_temperature}°C
- Exceedance Hours: {exceedance_hours} (hours above 35°C threshold)
- Persistence Hours: {persistence_hours} (longest continuous stretch above 35°C)

Event Context:
- Type: {event_type}
- Attendance: {attendance} people
- Current schedule: {start_time} to {end_time}
- Duration: {duration_hours} hours

Guidance:
- risk_score >= 75 -> lean toward POSTPONE or MODIFY with a significant time change
- risk_score 50-74 -> lean toward MODIFY or ADD_INTERVENTIONS
- risk_score 25-49 -> lean toward ADD_INTERVENTIONS or PROCEED with caution
- risk_score < 25 -> lean toward PROCEED
- If recommending MODIFY, suggest a SPECIFIC alternative time window (e.g. earlier morning or late night) that would plausibly reduce heat exposure for this event's duration.

Respond with ONLY valid JSON, no other text, matching exactly this shape:
{{
  "recommendation": "PROCEED" | "MODIFY" | "ADD_INTERVENTIONS" | "POSTPONE",
  "reasoning": "1-2 sentence explanation",
  "suggested_schedule_change": "e.g. Move start time from 15:00 to 02:00" or null,
  "interventions": ["list of specific actions if ADD_INTERVENTIONS or MODIFY, else empty list"]
}}"""


def _rule_based_fallback(assessment: dict) -> DecisionOutput:
    """
    Deterministic fallback used when the LLM output can't be parsed/validated.
    Mirrors the guidance given to the LLM, so behavior stays sensible even
    if the API call fails entirely.
    """
    score = assessment["risk_score"]
    print(f"  [decision_agent] Using RULE-BASED FALLBACK (score={score})")

    if score >= 75:
        return DecisionOutput(
            recommendation="POSTPONE",
            reasoning=f"Risk score of {score} exceeds the safe threshold for outdoor events; automated fallback recommends postponing or rescheduling.",
            suggested_schedule_change="Move to early morning (e.g. 02:00-08:00) or a cooler day.",
            interventions=[],
        )
    elif score >= 50:
        return DecisionOutput(
            recommendation="MODIFY",
            reasoning=f"Risk score of {score} indicates elevated heat exposure; a schedule change is recommended.",
            suggested_schedule_change="Shift the event 4-6 hours earlier or later to avoid peak heat.",
            interventions=[],
        )
    elif score >= 25:
        return DecisionOutput(
            recommendation="ADD_INTERVENTIONS",
            reasoning=f"Risk score of {score} is moderate; the event can proceed with additional safety measures.",
            suggested_schedule_change=None,
            interventions=["Hydration stations", "Shaded rest areas", "Medical staff on standby"],
        )
    else:
        return DecisionOutput(
            recommendation="PROCEED",
            reasoning=f"Risk score of {score} is low; standard precautions are sufficient.",
            suggested_schedule_change=None,
            interventions=[],
        )


def get_decision(assessment: dict, event: dict) -> DecisionOutput:
    """
    assessment: dict with risk_score, status, peak_temperature, exceedance_hours,
                persistence_hours, duration_hours
    event: dict with event_type, attendance, start_time, end_time
    """
    prompt = DECISION_PROMPT.format(
        risk_score=assessment["risk_score"],
        status=assessment["status"],
        peak_temperature=assessment["peak_temperature"],
        exceedance_hours=assessment["exceedance_hours"],
        persistence_hours=assessment["persistence_hours"],
        event_type=event.get("event_type", "general"),
        attendance=event.get("attendance", 0),
        start_time=event["start_time"],
        end_time=event["end_time"],
        duration_hours=assessment["duration_hours"],
    )

    try:
        print("  [decision_agent] Calling Gemini...")
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        print(f"  [decision_agent] Raw LLM output: {raw_text[:200]}...")

        # Strip markdown code fences if the model wrapped the JSON
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        decision = DecisionOutput(**parsed)
        print(f"  [decision_agent] Validated LLM decision: {decision.recommendation}")
        return decision

    except (json.JSONDecodeError, ValidationError, KeyError, IndexError, Exception) as e:
        print(f"  [decision_agent] LLM output invalid ({type(e).__name__}: {e}) — falling back to rules")
        return _rule_based_fallback(assessment)