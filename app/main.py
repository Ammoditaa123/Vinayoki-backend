from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, get_db
from .load_content import load_content
from . import models
from .routes import users, feed, interactions
from .services.engagement import detect_passive_consumption



app = FastAPI(
    title="Vinayoki API",
    description="Adaptive learning and progress recommendation backend",
    version="1.0.0"
)
Base.metadata.create_all(bind=engine)
load_content()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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