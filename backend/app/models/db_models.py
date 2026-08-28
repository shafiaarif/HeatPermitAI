import uuid
from sqlalchemy import Column, String, Float, Integer, Date, Time, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    event_type = Column(String, default="general")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    event_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    attendance = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class HeatAssessment(Base):
    __tablename__ = "heat_assessments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    assessed_start_time = Column(Time, nullable=False)
    assessed_end_time = Column(Time, nullable=False)
    risk_score = Column(Float)
    status = Column(String)
    peak_temperature = Column(Float)
    exceedance_hours = Column(Float)
    persistence_hours = Column(Float)
    heat_index = Column(Float)
    wet_bulb_temp = Column(Float)
    raw_response = Column(JSON)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

class WhatIfComparison(Base):
    __tablename__ = "what_if_comparisons"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    current_assessment_id = Column(UUID(as_uuid=True), ForeignKey("heat_assessments.id"))
    proposed_assessment_id = Column(UUID(as_uuid=True), ForeignKey("heat_assessments.id"))
    exposure_reduction_percent = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SafetyPlan(Base):
    __tablename__ = "safety_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    heat_assessment_id = Column(UUID(as_uuid=True), ForeignKey("heat_assessments.id"))
    plan_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())