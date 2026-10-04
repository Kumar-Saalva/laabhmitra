"""SQLite storage (SQLModel): profiles, the last result snapshot, notifications, pack status.

Only booleans like pan_available are stored. There is no column for any ID number.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, select

DB_PATH = os.getenv("LAABHMITRA_DB", str(Path(__file__).resolve().parents[1] / "laabhmitra.db"))
if DB_PATH == ":memory:":
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

PACK_STATUSES = ["not_started", "docs_ready", "applied", "sanctioned", "received"]


class ProfileRow(SQLModel, table=True):
    id: str = Field(primary_key=True)
    data: str                                  # profile as JSON
    consent_timestamp: str
    updated_at: str
    snapshot: str = "{}"                       # last statuses, for the watch diff


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: str = Field(index=True)
    scheme_id: str
    kind: str                                  # improved | now_active | verify_badge
    old: str
    new: str
    created_at: str


class PackStatus(SQLModel, table=True):
    profile_id: str = Field(primary_key=True)
    scheme_id: str = Field(primary_key=True)
    status: str = "not_started"
    amount_received_inr: Optional[int] = None
    updated_at: str = ""


def init_db():
    SQLModel.metadata.create_all(engine)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_profile(profile_id: str) -> Optional[dict]:
    with Session(engine) as s:
        row = s.get(ProfileRow, profile_id)
        return json.loads(row.data) if row else None


def get_snapshot(profile_id: str) -> dict:
    with Session(engine) as s:
        row = s.get(ProfileRow, profile_id)
        return json.loads(row.snapshot) if row else {}


def save_profile(profile: dict, snapshot: dict, notes: list, profile_id: Optional[str] = None) -> str:
    """Create or update a profile, store its new snapshot and any notifications."""
    profile_id = profile_id or uuid.uuid4().hex[:12]
    stamp = now()
    with Session(engine) as s:
        row = s.get(ProfileRow, profile_id)
        if row is None:
            row = ProfileRow(id=profile_id, data="{}", consent_timestamp=stamp, updated_at=stamp)
        row.data = json.dumps(profile, ensure_ascii=False)
        row.snapshot = json.dumps(snapshot)
        row.updated_at = stamp
        s.add(row)
        for n in notes:
            s.add(Notification(profile_id=profile_id, created_at=stamp, **n))
        s.commit()
    return profile_id


def list_notifications(profile_id: str) -> list:
    with Session(engine) as s:
        rows = s.exec(select(Notification).where(Notification.profile_id == profile_id)
                      .order_by(Notification.id.desc())).all()
        return [r.model_dump() for r in rows]


def get_pack_status(profile_id: str, scheme_id: str) -> dict:
    with Session(engine) as s:
        row = s.get(PackStatus, (profile_id, scheme_id))
        return row.model_dump() if row else {"profile_id": profile_id, "scheme_id": scheme_id,
                                             "status": "not_started", "amount_received_inr": None}


def list_pack_statuses(profile_id: str) -> list:
    with Session(engine) as s:
        rows = s.exec(select(PackStatus).where(PackStatus.profile_id == profile_id)).all()
        return [r.model_dump() for r in rows]


def set_pack_status(profile_id: str, scheme_id: str, status: str, amount: Optional[int]) -> dict:
    with Session(engine) as s:
        row = s.get(PackStatus, (profile_id, scheme_id)) or PackStatus(profile_id=profile_id, scheme_id=scheme_id)
        row.status, row.amount_received_inr, row.updated_at = status, amount, now()
        s.add(row)
        s.commit()
        s.refresh(row)
        return row.model_dump()
