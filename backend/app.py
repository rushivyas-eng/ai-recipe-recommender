from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI(
    title="AI Recipe Recommendation API",
    description="Experimental, open-source recipe recommender",
    version="1.0.0"
)

app.include_router(router)
