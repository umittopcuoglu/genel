from decimal import Decimal
from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, JSON, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.front_office import Room, RoomType, Reservation
    from app.models.finance import Folio
    from app.models.user import User


class Venue(BaseModel):
    """Event venues/salons (conference, banquet halls)."""
    __tablename__ = "venues"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity_min: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity_max: Mapped[int] = mapped_column(Integer, nullable=False)
    setup_types: Mapped[dict] = mapped_column(JSON, nullable=True)  # ["classroom", "theater", "banquet"]
    status: Mapped[str] = mapped_column(String(15), default="active", nullable=False)

    events: Mapped[list["Event"]] = relationship("Event", back_populates="venue")


class Group(BaseModel):
    """Group/MICE reservations (corporate, tour groups)."""
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    agency_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    contract_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="inquiry", nullable=False)
    block_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    block_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    pax_count: Mapped[int] = mapped_column(Integer, nullable=False)
    group_folio_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("folios.id"), nullable=True)
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # lazy="selectin": GroupResponse ilişkileri Pydantic serileştirmede lazy-load (MissingGreenlet) yapmasın
    room_blocks: Mapped[list["RoomBlock"]] = relationship("RoomBlock", back_populates="group", lazy="selectin")
    events: Mapped[list["Event"]] = relationship("Event", back_populates="group", lazy="selectin")
    rooming_list: Mapped[list["GroupRoomingList"]] = relationship("GroupRoomingList", back_populates="group", lazy="selectin")


class RoomBlock(BaseModel):
    """Room inventory blocks for groups."""
    __tablename__ = "room_blocks"

    group_id: Mapped[str] = mapped_column(Uuid, ForeignKey("groups.id"), nullable=False)
    room_type_id: Mapped[str] = mapped_column(Uuid, ForeignKey("room_types.id"), nullable=False)
    qty_required: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_confirmed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pickup_date: Mapped[date] = mapped_column(Date, nullable=False)
    release_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="pending", nullable=False)

    group: Mapped["Group"] = relationship("Group", back_populates="room_blocks")


class Event(BaseModel):
    """MICE events/meetings within a group stay."""
    __tablename__ = "events"

    group_id: Mapped[str] = mapped_column(Uuid, ForeignKey("groups.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)  # conference, meeting, wedding, gala
    venue_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("venues.id"), nullable=True)
    capacity_required: Mapped[int] = mapped_column(Integer, nullable=False)
    setup_type: Mapped[str] = mapped_column(String(30), nullable=False)  # classroom, theater, banquet
    start_datetime: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    catering_required: Mapped[bool] = mapped_column(default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    group: Mapped["Group"] = relationship("Group", back_populates="events")
    venue: Mapped["Venue"] = relationship("Venue", back_populates="events")
    resources: Mapped[list["EventResource"]] = relationship("EventResource", back_populates="event")


class EventResource(BaseModel):
    """Resources required for events (equipment, catering, staff)."""
    __tablename__ = "event_resources"

    event_id: Mapped[str] = mapped_column(Uuid, ForeignKey("events.id"), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(30), nullable=False)  # equipment, catering, staff
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    qty_required: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="requested", nullable=False)

    event: Mapped["Event"] = relationship("Event", back_populates="resources")


class GroupRoomingList(BaseModel):
    """Individual guest rooming list for group (pre-assignment)."""
    __tablename__ = "group_rooming_list"

    group_id: Mapped[str] = mapped_column(Uuid, ForeignKey("groups.id"), nullable=False)
    guest_name: Mapped[str] = mapped_column(String(100), nullable=False)
    guest_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    room_type_requested: Mapped[str] = mapped_column(String(30), nullable=False)
    checkin_date: Mapped[date] = mapped_column(Date, nullable=False)
    checkout_date: Mapped[date] = mapped_column(Date, nullable=False)
    reservation_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("reservations.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="pending", nullable=False)

    group: Mapped["Group"] = relationship("Group", back_populates="rooming_list")
