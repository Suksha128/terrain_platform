from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

for d in ["uploads", "results"]:
    Path(d).mkdir(exist_ok=True)

app = FastAPI(
    title="Terrain Intelligence Platform",
    description="DTM-based waterlogging risk and management zone delineation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"service": "Terrain Intelligence Platform", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
