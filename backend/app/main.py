from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.core.exceptions import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "hi"}
