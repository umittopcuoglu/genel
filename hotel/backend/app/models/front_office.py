"""
Front Office modelleri: Oda tipleri, odalar, misafirler, rezervasyonlar,
stay (konaklama) ve trace (departman notları).
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Integer, Numeric as SA_Decimal, Boolean, Date, DateTime,
    Text, ForeignKey, Enum as SA_Enum, UniqueConstraint, Index,
    Uuid, SmallInteger
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import BaseModel


#  Enum'lar

class RoomStatus(str, enum.Enum):
    CLEAN = "clean"
    DIRTY = "dirty"
    INSPECTED = "inspected"
    OCCUPIED = "occupied"
    OUT_OF_ORDER = "out_of_order"
    RESERVED = "reserved"


class ReservationStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ReservationSource(str, enum.Enum):
    DIRECT = "direct"
    WALK_IN = "walk_in"
    OTA = "ota"
    CHANNEL = "channel"
    CORPORATE = "corporate"


class TracePriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TraceStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


#  Modeller

class RoomType(BaseModel):
    __tablename__ = "room_types"
    code = mapped_column(String(20), unique=True, nullable=False, index=True)
    name = mapped_column(String(100), nullable=False)
    description = mapped_column(Text, nullable=True)
    max_guests = mapped_column(SmallInteger, nullable=False, default=2)
    default_rate = mapped_column(SA_Decimal(10, 2), nullable=False, default=0)
    amenities = mapped_column(Text, nullable=True)
    is_active = mapped_column(Boolean, default=True)
    rooms = relationship("Room", back_populates="room_type", cascade="all, delete-orphan")


class Room(BaseModel):
    __tablename__ = "rooms"
    room_number = mapped_column(String(10), nullable=False, index=True)
    floor = mapped_column(SmallInteger, nullable=False, default=1)
    room_type_id = mapped_column(Uuid, ForeignKey("room_types.id"), nullable=False, index=True)
    status = mapped_column(SA_Enum(RoomStatus, name="room_status_enum"), nullable=False, default=RoomStatus.CLEAN, index=True)
    is_smoking = mapped_column(Boolean, default=False)
    notes = mapped_column(Text, nullable=True)
    is_active = mapped_column(Boolean, default=True)
    room_type = relationship("RoomType", back_populates="rooms")
    stays = relationship("Stay", back_populates="room")
    __table_args__ = (UniqueConstraint("room_number", name="uq_room_number"), Index("ix_rooms_floor_status", "floor", "status"))


class Guest(BaseModel):
    __tablename__ = "guests"
    first_name = mapped_column(String(100), nullable=False)
    last_name = mapped_column(String(100), nullable=False)
    email = mapped_column(String(255), nullable=True, index=True)
    phone = mapped_column(String(30), nullable=True)
    nationality = mapped_column(String(3), nullable=True)
    id_document_type = mapped_column(String(30), nullable=True)
    id_document_number = mapped_column(String(50), nullable=True)
    birth_date = mapped_column(Date, nullable=True)
    address = mapped_column(Text, nullable=True)
    city = mapped_column(String(100), nullable=True)
    country = mapped_column(String(3), nullable=True)
    postal_code = mapped_column(String(20), nullable=True)
    company = mapped_column(String(200), nullable=True)
    tax_id = mapped_column(String(50), nullable=True)
    notes = mapped_column(Text, nullable=True)
    is_blacklisted = mapped_column(Boolean, default=False)
    is_vip = mapped_column(Boolean, default=False)
    total_stays = mapped_column(Integer, default=0)
    total_spent = mapped_column(SA_Decimal(12, 2), default=0)
    reservations = relationship("Reservation", back_populates="guest", cascade="all, delete-orphan")
    stays = relationship("Stay", back_populates="guest")
    __table_args__ = (Index("ix_guests_name", "first_name", "last_name"), Index("ix_guests_phone", "phone"))


class Reservation(BaseModel):
    __tablename__ = "reservations"
    reservation_number = mapped_column(String(20), unique=True, nullable=False, index=True)
    guest_id = mapped_column(Uuid, ForeignKey("guests.id"), nullable=False, index=True)
    status = mapped_column(SA_Enum(ReservationStatus, name="reservation_status_enum"), nullable=False, default=ReservationStatus.CONFIRMED, index=True)
    source = mapped_column(SA_Enum(ReservationSource, name="reservation_source_enum"), nullable=False, default=ReservationSource.DIRECT)
    check_in = mapped_column(Date, nullable=False, index=True)
    check_out = mapped_column(Date, nullable=False)
    adults = mapped_column(SmallInteger, nullable=False, default=1)
    children = mapped_column(SmallInteger, nullable=False, default=0)
    room_type_id = mapped_column(Uuid, ForeignKey("room_types.id"), nullable=True)
    assigned_room_id = mapped_column(Uuid, ForeignKey("rooms.id"), nullable=True)
    requested_room_number = mapped_column(String(10), nullable=True)
    special_requests = mapped_column(Text, nullable=True)
    payment_method = mapped_column(String(50), nullable=True)
    rate_plan_id = mapped_column(Uuid, ForeignKey("rate_plans.id"), nullable=True)
    total_amount = mapped_column(SA_Decimal(12, 2), default=0)
    balance = mapped_column(SA_Decimal(12, 2), default=0)
    deposit_amount = mapped_column(SA_Decimal(10, 2), default=0)
    deposit_paid = mapped_column(Boolean, default=False)
    channel_ref = mapped_column(String(100), nullable=True)
    cancellation_reason = mapped_column(Text, nullable=True)
    cancelled_at = mapped_column(DateTime(timezone=True), nullable=True)
    checked_in_at = mapped_column(DateTime(timezone=True), nullable=True)
    checked_out_at = mapped_column(DateTime(timezone=True), nullable=True)
    no_show_marked_at = mapped_column(DateTime(timezone=True), nullable=True)
    guest = relationship("Guest", back_populates="reservations")
    room_type = relationship("RoomType")
    assigned_room = relationship("Room")
    stays = relationship("Stay", back_populates="reservation", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_reservations_dates", "check_in", "check_out"), Index("ix_reservations_status_date", "status", "check_in"))


class Stay(BaseModel):
    __tablename__ = "stays"
    reservation_id = mapped_column(Uuid, ForeignKey("reservations.id"), nullable=False, index=True)
    room_id = mapped_column(Uuid, ForeignKey("rooms.id"), nullable=False, index=True)
    guest_id = mapped_column(Uuid, ForeignKey("guests.id"), nullable=False, index=True)
    actual_check_in = mapped_column(DateTime(timezone=True), nullable=True)
    actual_check_out = mapped_column(DateTime(timezone=True), nullable=True)
    pax_count = mapped_column(SmallInteger, nullable=False, default=1)
    folio_balance = mapped_column(SA_Decimal(12, 2), default=0)
    is_checked_in = mapped_column(Boolean, default=False)
    is_checked_out = mapped_column(Boolean, default=False)
    is_house_use = mapped_column(Boolean, default=False)
    notes = mapped_column(Text, nullable=True)
    reservation = relationship("Reservation", back_populates="stays")
    room = relationship("Room", back_populates="stays")
    guest = relationship("Guest", back_populates="stays")
    __table_args__ = (Index("ix_stays_active", "is_checked_in", "is_checked_out"),)


class Trace(BaseModel):
    __tablename__ = "traces"
    reservation_id = mapped_column(Uuid, ForeignKey("reservations.id"), nullable=True, index=True)
    stay_id = mapped_column(Uuid, ForeignKey("stays.id"), nullable=True, index=True)
    guest_id = mapped_column(Uuid, ForeignKey("guests.id"), nullable=True, index=True)
    room_id = mapped_column(Uuid, ForeignKey("rooms.id"), nullable=True, index=True)
    department = mapped_column(String(50), nullable=False, index=True)
    subject = mapped_column(String(200), nullable=False)
    description = mapped_column(Text, nullable=True)
    priority = mapped_column(SA_Enum(TracePriority, name="trace_priority_enum"), nullable=False, default=TracePriority.NORMAL)
    status = mapped_column(SA_Enum(TraceStatus, name="trace_status_enum"), nullable=False, default=TraceStatus.OPEN, index=True)
    assigned_to = mapped_column(String(100), nullable=True)
    due_date = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes = mapped_column(Text, nullable=True)
    __table_args__ = (Index("ix_traces_department_status", "department", "status"), Index("ix_traces_due_date", "due_date"))
