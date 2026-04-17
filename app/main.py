from fastapi import FastAPI

from app.api.routes.recommendations import router as recommendations_router


app = FastAPI(
    title="Car Recommendation API",
    version="0.1.0",
    description="Recommendation API Layer for the AI-assisted car recommendation MVP.",
)

app.include_router(recommendations_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
