from typing import Optional
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Float, BigInteger, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timezone
import uuid

class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    Extends fastapi-users base user with role and metadata.
    """
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="viewer")  # viewer, operator, admin

class AuditEvent(Base):
    """
    Records every critical user action for accountability.
    """
    __tablename__ = "audit_events"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("user.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))  # e.g., "SOLVE", "EXPORT", "LOGIN"
    payload_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True) # Hash of scenario or params
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Contextual data
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Flight(Base):
    """
    The core tactical data model representing an individual flight and its optimized state.
    """
    __tablename__ = "flights"

    # Core IDs
    flight_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    
    # Routing & Geography
    origin: Mapped[str] = mapped_column(String(10))
    destination: Mapped[str] = mapped_column(String(10))
    origin_lat: Mapped[float] = mapped_column(Float)
    origin_lon: Mapped[float] = mapped_column(Float)
    dest_lat: Mapped[float] = mapped_column(Float)
    dest_lon: Mapped[float] = mapped_column(Float)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    velocity: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    track: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dist_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Schedule
    departure_time: Mapped[datetime] = mapped_column(DateTime)
    arrival_time: Mapped[datetime] = mapped_column(DateTime)
    block_time: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    departure_hour: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    arrival_hour: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Passenger & Commercial
    business_pax: Mapped[int] = mapped_column(BigInteger, default=0)
    leisure_pax: Mapped[int] = mapped_column(BigInteger, default=0)
    passenger_count: Mapped[int] = mapped_column(BigInteger, default=0)
    pax_connection_count: Mapped[int] = mapped_column(BigInteger, default=0)
    load_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_tl: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    fuel_cost_tl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    co2_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    op_cost_tl: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    delay_cost_per_min: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    market_qsi_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_gap_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    yield_quality_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Aircraft Asset
    aircraft_id: Mapped[str] = mapped_column(String(20))
    ac_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ac_cat: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ac_range_km: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ac_remaining_fh: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ac_capacity: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    assigned_aircraft: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    engine_health: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    maintenance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Crew
    crew_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    crew_cert: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    crew_base_fatigue: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Operational Status
    is_night_flight: Mapped[bool] = mapped_column(Boolean, default=False)
    contrail_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weather_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tech_failure_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    causal_factor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    saf_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gate_id: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    pax_mobility_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ntn_link_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_canceled: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_delay: Mapped[int] = mapped_column(BigInteger, default=0)
    slot_pressure_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI & Logic Metadata
    decision_logic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
