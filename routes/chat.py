from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from bson import ObjectId
from database import db
from models import Message

router = APIRouter(tags=["Chat"])

# In-memory connection registry per event
EVENT_ROOMS: dict[str, set[WebSocket]] = {}


async def add_ws(event_id: str, ws: WebSocket):
    await ws.accept()
    EVENT_ROOMS.setdefault(event_id, set()).add(ws)


def remove_ws(event_id: str, ws: WebSocket):
    if event_id in EVENT_ROOMS and ws in EVENT_ROOMS[event_id]:
        EVENT_ROOMS[event_id].remove(ws)
        if not EVENT_ROOMS[event_id]:
            EVENT_ROOMS.pop(event_id, None)


async def broadcast(event_id: str, payload: dict):
    for ws in list(EVENT_ROOMS.get(event_id, set())):
        try:
            await ws.send_json(payload)
        except RuntimeError:
            # dead connection
            remove_ws(event_id, ws)


@router.websocket("/ws/events/{event_id}")
async def event_chat(ws: WebSocket, event_id: str, sender_id: str, role: str):
    # Ensure event exists
    evt = await db.events.find_one({"_id": ObjectId(event_id)})
    if not evt or evt.get("status") != "approved":
        await ws.close(code=4404)
        return

    await add_ws(event_id, ws)
    try:
        await broadcast(event_id, {"system": True, "message": f"{sender_id} joined"})
        while True:
            data = await ws.receive_json()
            content: str = data.get("content", "").strip()
            if not content:
                continue

            # Student message limit: at most 2 per event
            if role == "student":
                count = await db.messages.count_documents({"eventId": event_id, "senderId": sender_id, "messageType": "student"})
                if count >= 2:
                    await ws.send_json({"error": "Message limit reached for students (2)."})
                    continue

            msg_type = "announcement" if role == "organizer" else "student"
            msg_doc = {
                "senderId": sender_id,
                "eventId": event_id,
                "content": content,
                "messageType": msg_type
            }
            await db.messages.insert_one(msg_doc)

            await broadcast(event_id, {"senderId": sender_id, "type": msg_type, "content": content})
    except WebSocketDisconnect:
        remove_ws(event_id, ws)
        await broadcast(event_id, {"system": True, "message": f"{sender_id} left"})
