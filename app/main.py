from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, get_db
from .load_content import load_content
from .load_learning_cards import load_learning_cards
from . import models
from .routes import users, feed, interactions, cards, card_interactions, stats, learner_state, ml, adaptation
from .services.engagement import detect_passive_consumption


app = FastAPI(
    title="Vinayoki API",
    description="Adaptive learning and progress recommendation backend",
    version="1.0.0"
)
Base.metadata.create_all(bind=engine)
load_content()
load_learning_cards()

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
app.include_router(cards.router)
app.include_router(cards.history_router)
app.include_router(card_interactions.router)
app.include_router(stats.router)
app.include_router(learner_state.router)
app.include_router(ml.router)
app.include_router(adaptation.router)

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

@app.get("/debug-content")
def debug_content(db=Depends(get_db)):
    count = db.query(models.Content).count()

    return {
        "content_count": count,
        "database": str(engine.url),
    }
