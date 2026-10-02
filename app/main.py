from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .load_content import load_content
from .database import engine, Base, get_db
from . import models
from .routes import users
from .routes import feed
from .routes import interactions
from .services.engagement import detect_passive_consumption

Base.metadata.create_all(bind=engine)
load_content()

app = FastAPI(
    title="Vinayoki API",
    description="Adaptive learning and progress recommendation backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(feed.router)
app.include_router(interactions.router)

@app.get("/")
def root():
    return {
        "message": "Vinayoki API is running",
        "status": "healthy"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.get("/engagement/{user_id}")
def get_engagement_state(
    user_id: int,
    db = Depends(get_db)
):
    return detect_passive_consumption(
        db,
        user_id
    )