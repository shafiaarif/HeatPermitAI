"""
Strict schema for the Decision Agent's LLM output.
Used to validate the LLM's JSON before trusting it — if parsing/validation
fails, decision_agent.py falls back to a rule-based decision instead.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class DecisionOutput(BaseModel):
    recommendation: Literal["PROCEED", "MODIFY", "ADD_INTERVENTIONS", "POSTPONE"]
    reasoning: str = Field(..., min_length=10, description="1-2 sentence explanation")
    suggested_schedule_change: Optional[str] = Field(
        None, description="e.g. 'Move start time from 15:00 to 02:00', or null if not applicable"
    )
    interventions: list[str] = Field(default_factory=list, description="Specific actions if ADD_INTERVENTIONS or MODIFY")