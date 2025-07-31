from fastapi import APIRouter

playground_router = APIRouter(prefix="/playground", tags=["Playground"])


@playground_router.get("/status")
async def playground_status():
    return {"playground": "available"}