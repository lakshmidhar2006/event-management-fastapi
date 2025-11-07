from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import db
from models import Registration, Event

router = APIRouter(prefix="/registrations", tags=["Registrations"])

# Atomic "reserve a slot if available" using find_one_and_update.
# Works on standalone Mongo (no replicas/transactions required).
@router.post("/", response_model=dict)
async def register(student_id: str, event_id: str):
    # Check duplicates
    existing = await db.registrations.find_one({
        "studentId": student_id,
        "eventId": event_id,
        "status": "registered"
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already registered")

    # 1) Reserve a seat atomically
    updated_event = await db.events.find_one_and_update(
        {"_id": ObjectId(event_id), "status": "approved", "availableSlots": {"$gt": 0}},
        {"$inc": {"availableSlots": -1}},
        return_document=True  # return the updated doc
    )

    if not updated_event:
        raise HTTPException(status_code=400, detail="Event is full or not approved")

    # 2) Create registration
    reg_doc = {
        "studentId": student_id,
        "eventId": event_id,
        "status": "registered",
        "msgCount": 0
    }
    res = await db.registrations.insert_one(reg_doc)
    return {"message": "Registered", "registrationId": str(res.inserted_id)}


@router.get("/by-event/{event_id}")
async def list_event_regs(event_id: str):
    cur = db.registrations.find({"eventId": event_id})
    regs = await cur.to_list(1000)
    # Normalize ids
    for r in regs:
        r["id"] = str(r.pop("_id"))
    return regs


@router.delete("/{registration_id}", response_model=dict)
async def remove_registration(registration_id: str):
    reg = await db.registrations.find_one({"_id": ObjectId(registration_id)})
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")

    # free up slot
    await db.events.update_one({"_id": ObjectId(reg["eventId"])}, {"$inc": {"availableSlots": 1}})
    await db.registrations.update_one({"_id": ObjectId(registration_id)}, {"$set": {"status": "removed"}})
    return {"message": "Registration removed, slot released"}
