"""
Window Selector Agent —
Given 2-3 candidate time windows (each with a real, fully-assessed risk
score) plus event context, asks the LLM to REASON about the trade-offs
and choose the best one to recommend — not just pick whichever has the
lowest number. A window that's thermally coldest but has poor realistic
attendance (e.g. very early morning for a large public concert) may be a
worse real-world recommendation than a slightly warmer daytime slot.

Falls back to the lowest-risk-score candidate if the LLM call fails or
returns something unparseable — the recommendation is never blocked by
an LLM outage.
"""
import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from pydantic import ValidationError
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-3.5-flash-lite")


class WindowChoice(BaseModel):
    chosen_index: int = Field(..., description="0-based index of the chosen candidate")
    reasoning: str = Field(..., min_length=10)


SELECTOR_PROMPT = """You are choosing the best alternative time window for an outdoor event that currently has unacceptable heat risk.

Event context:
- Type: {event_type}
- Attendance: {attendance} people
- Current schedule: {current_start}-{current_end}, risk score {current_risk}/100 ({current_status})

Candidate windows (all same-day, all already fully risk-assessed):
{candidates_text}

Guidance:
- Don't just pick the coldest option. Consider realistic attendance for each time of day —
  very early morning (before 7 AM) or late night windows often have poor turnout for public events,
  even if they are thermally the safest.
- A slightly warmer daytime or evening slot with a meaningfully lower risk than the CURRENT
  schedule may be a better real-world recommendation than the absolute coldest option.
- If two candidates have similar risk scores, prefer the one with more realistic attendance timing.

Respond with ONLY valid JSON, no other text, matching exactly this shape:
{{
  "chosen_index": <0-based index into the candidates list above>,
  "reasoning": "1-2 sentence explanation of why this window was chosen over the others"
}}"""


def _format_candidates(candidates: list) -> str:
    lines = []
    for i, c in enumerate(candidates):
        lines.append(
            f"[{i}] {c['start_time']}-{c['end_time']} — risk score {c['risk_score']}/100 "
            f"({c['status']}), peak {c['peak_temperature']}°C"
        )
    return "\n".join(lines)


def _rule_based_fallback(candidates: list) -> WindowChoice:
    """Falls back to whichever candidate has the lowest risk_score."""
    best_i = min(range(len(candidates)), key=lambda i: candidates[i]["risk_score"])
    print(f"  [window_selector] Using RULE-BASED FALLBACK — picking index {best_i} (lowest risk_score)")
    return WindowChoice(
        chosen_index=best_i,
        reasoning=f"Selected automatically as the lowest-risk option ({candidates[best_i]['risk_score']}/100).",
    )


def select_best_window(candidates: list, event_type: str, attendance: int,
                        current_start: str, current_end: str,
                        current_risk: float, current_status: str) -> WindowChoice:
    """
    candidates: list of dicts, each with start_time, end_time, risk_score,
                status, peak_temperature (i.e. the output of assess_window()
                for each candidate).
    """
    if len(candidates) == 1:
        return WindowChoice(
            chosen_index=0,
            reasoning="Only one realistic candidate window was available.",
        )

    prompt = SELECTOR_PROMPT.format(
        event_type=event_type,
        attendance=attendance,
        current_start=current_start,
        current_end=current_end,
        current_risk=current_risk,
        current_status=current_status,
        candidates_text=_format_candidates(candidates),
    )

    try:
        print("  [window_selector] Calling Gemini to reason over candidate windows...")
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        print(f"  [window_selector] Raw LLM output: {raw_text[:200]}...")

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        choice = WindowChoice(**parsed)

        if not (0 <= choice.chosen_index < len(candidates)):
            raise ValueError(f"chosen_index {choice.chosen_index} out of range")

        print(f"  [window_selector] LLM chose index {choice.chosen_index}: {choice.reasoning}")
        return choice

    except (json.JSONDecodeError, ValidationError, KeyError, IndexError, ValueError, Exception) as e:
        print(f"  [window_selector] LLM output invalid ({type(e).__name__}: {e}) — falling back to rules")
        return _rule_based_fallback(candidates)