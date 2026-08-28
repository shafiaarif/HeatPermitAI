"""
Pydantic request/response schemas — validates incoming data before it
touches the database or FortyGuard, so bad input fails fast with a
clear error instead of crashing deeper in the pipeline.
"""
from pydantic import BaseModel, Field
from datetime import date, time
from uuid import UUID


class EventCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    event_type: str = Field(default="general", max_length=50)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    event_date: date
    start_time: time
    end_time: time
    attendance: int = Field(default=0, ge=0)


class EventResponse(BaseModel):
    id: UUID          # <- str se UUID mein badla
    name: str
    event_type: str
    latitude: float
    longitude: float
    event_date: date
    start_time: time
    end_time: time
    attendance: int

    class Config:
        from_attributes = True