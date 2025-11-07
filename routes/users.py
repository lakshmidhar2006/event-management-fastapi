from fastapi import APIRouter, HTTPException
from pydantic import EmailStr
from typing import List
from bson import ObjectId
from database import db
from models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=dict)
async def create_user(user: User):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    doc = user.model_dump(exclude={"id"}, by_alias=True)
    res = await db.users.insert_one(doc)
    return {"id": str(res.inserted_id), "message": "User created"}


@router.get("/", response_model=list[User])
async def list_users():
    cur = db.users.find()
    return [User.from_mongo(d) for d in await cur.to_list(length=500)]


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return User.from_mongo(doc)
