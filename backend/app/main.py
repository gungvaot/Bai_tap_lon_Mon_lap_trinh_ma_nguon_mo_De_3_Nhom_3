import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, clubs, events
from .seed import seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    seed()
    yield


app = FastAPI(
    title="Quản lý CLB và sự kiện sinh viên",
    version="1.0",
    root_path=os.getenv("ROOT_PATH", ""),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
for r in (auth.router, clubs.router, events.router):
    app.include_router(r)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}