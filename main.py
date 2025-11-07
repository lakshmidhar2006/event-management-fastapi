from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import users, events
from routes import registrations
from routes import chat

app = FastAPI(title="Event Management System API")

# CORS for easy frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Routes
app.include_router(users.router)
app.include_router(events.router)
app.include_router(registrations.router)

# WebSocket Route
app.include_router(chat.router)

@app.get("/")
def home():
    return {"message": "Welcome to the Event Management API"}
