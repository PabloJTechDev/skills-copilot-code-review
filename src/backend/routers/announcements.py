"""Announcements endpoints for the High School Management System API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"],
)


def _require_signed_in_user(teacher_username: Optional[str]) -> Dict[str, Any]:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _parse_date_yyyy_mm_dd(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")


def _utc_day_end(date_str: str) -> datetime:
    base = _parse_date_yyyy_mm_dd(date_str)
    return base.replace(hour=23, minute=59, second=59, microsecond=999000)


def _serialize_announcement(doc: Dict[str, Any]) -> Dict[str, Any]:
    start_date = doc.get("start_date")
    expiration_date = doc.get("expiration_date")

    def to_date_str(dt: Optional[datetime]) -> Optional[str]:
        if not dt:
            return None
        if isinstance(dt, datetime):
            return dt.date().isoformat()
        return None

    return {
        "id": str(doc.get("_id")),
        "message": doc.get("message", ""),
        "start_date": to_date_str(start_date),
        "expiration_date": to_date_str(expiration_date),
        "created_at": to_date_str(doc.get("created_at")),
        "updated_at": to_date_str(doc.get("updated_at")),
    }


class AnnouncementUpsert(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    expiration_date: str = Field(description="YYYY-MM-DD")
    start_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get active announcements for all users.

    An announcement is active when:
    - start_date is missing/None OR start_date <= now
    - expiration_date >= now

    Dates are compared in UTC.
    """
    now = datetime.utcnow()

    query = {
        "$and": [
            {
                "$or": [
                    {"start_date": {"$exists": False}},
                    {"start_date": None},
                    {"start_date": {"$lte": now}},
                ]
            },
            {"expiration_date": {"$gte": now}},
        ]
    }

    docs = list(announcements_collection.find(query).sort("expiration_date", 1))
    return [_serialize_announcement(d) for d in docs]


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def list_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List all announcements (requires authentication)."""
    _require_signed_in_user(teacher_username)

    docs = list(announcements_collection.find({}).sort("expiration_date", 1))
    return [_serialize_announcement(d) for d in docs]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementUpsert,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create a new announcement (requires authentication)."""
    _require_signed_in_user(teacher_username)

    start_dt: Optional[datetime] = None
    if payload.start_date:
        start_dt = _parse_date_yyyy_mm_dd(payload.start_date)

    expiration_dt = _utc_day_end(payload.expiration_date)
    if start_dt and expiration_dt < start_dt:
        raise HTTPException(status_code=400, detail="expiration_date must be on/after start_date")

    now = datetime.utcnow()
    doc = {
        "message": payload.message.strip(),
        "start_date": start_dt,
        "expiration_date": expiration_dt,
        "created_at": now,
        "updated_at": now,
    }

    result = announcements_collection.insert_one(doc)
    created = announcements_collection.find_one({"_id": result.inserted_id})
    return _serialize_announcement(created or {"_id": result.inserted_id, **doc})


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpsert,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Update an announcement (requires authentication)."""
    _require_signed_in_user(teacher_username)

    try:
        oid = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    start_dt: Optional[datetime] = None
    if payload.start_date:
        start_dt = _parse_date_yyyy_mm_dd(payload.start_date)

    expiration_dt = _utc_day_end(payload.expiration_date)
    if start_dt and expiration_dt < start_dt:
        raise HTTPException(status_code=400, detail="expiration_date must be on/after start_date")

    update = {
        "$set": {
            "message": payload.message.strip(),
            "start_date": start_dt,
            "expiration_date": expiration_dt,
            "updated_at": datetime.utcnow(),
        }
    }

    result = announcements_collection.update_one({"_id": oid}, update)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": oid})
    return _serialize_announcement(updated or {"_id": oid})


@router.delete("/{announcement_id}", response_model=Dict[str, Any])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Delete an announcement (requires authentication)."""
    _require_signed_in_user(teacher_username)

    try:
        oid = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement id")

    result = announcements_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
