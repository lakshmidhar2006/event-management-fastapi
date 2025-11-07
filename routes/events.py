from fastapi import APIRouter, HTTPException
from typing import List
from bson import ObjectId
from database import db
from models import Event

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=dict)
async def create_event(event: Event):
    # organizerId must exist
    org = await db.users.find_one({"_id": ObjectId(event.organizerId), "role": "organizer", "verified": True})
    if not org:
        raise HTTPException(status_code=400, detail="Organizer must be verified")

    doc = event.model_dump(exclude={"id"}, by_alias=True)
    res = await db.events.insert_one(doc)
    return {"id": str(res.inserted_id), "message": "Event created (pending approval)"}


@router.get("/", response_model=list[Event])
async def list_events(only_approved: bool = True):
    q = {"status": "approved"} if only_approved else {}
    cur = db.events.find(q).sort("date", 1)
    return [Event.from_mongo(d) for d in await cur.to_list(1000)]


@router.patch("/{event_id}/approve", response_model=dict)
async def approve_event(event_id: str):
    res = await db.events.update_one({"_id": ObjectId(event_id)}, {"$set": {"status": "approved"}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event approved"}
