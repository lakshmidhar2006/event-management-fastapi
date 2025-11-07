from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field

# Helpers for Mongo ObjectId <-> str
from bson import ObjectId

def oid(x: str | ObjectId | None) -> Optional[str]:
    if x is None:
        return None
    return str(x)

class MongoModel(BaseModel):
    id: Optional[str] = Field(default=None, serialization_alias="_id")

    # Convert _id from Mongo to id (string)
    @classmethod
    def from_mongo(cls, d: dict):
        if not d:
            return None
        d = {**d}
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
        return cls.model_validate(d)


# ---------- User ----------
Role = Literal["student", "organizer", "admin"]

class StudentProfile(BaseModel):
    college: Optional[str] = None
    avatarUrl: Optional[str] = None
    mobile: Optional[str] = None

class OrganizerProfile(BaseModel):
    organization: Optional[str] = None
    preferences: list[str] = []

class User(MongoModel):
    name: str
    email: EmailStr
    password: str
    role: Role
    verified: bool = False
    studentProfile: Optional[StudentProfile] = None
    orgProfile: Optional[OrganizerProfile] = None


# ---------- Event ----------
Status = Literal["pending", "approved", "rejected"]

class Event(MongoModel):
    name: str
    description: str
    date: datetime
    location: str
    totalSlots: int
    availableSlots: int
    status: Status = "pending"
    isPaid: bool = False
    price: Optional[float] = None
    organizerId: str


# ---------- Registration ----------
RegStatus = Literal["registered", "removed", "waitlisted"]

class Registration(MongoModel):
    studentId: str
    eventId: str
    status: RegStatus = "registered"
    msgCount: int = 0
    createdAt: datetime = Field(default_factory=datetime.utcnow)


# ---------- Message ----------
MessageType = Literal["announcement", "student"]

class Message(MongoModel):
    senderId: str
    eventId: str
    content: str
    messageType: MessageType = "student"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
