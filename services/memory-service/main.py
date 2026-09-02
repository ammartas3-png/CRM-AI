import os
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from memory_store import Entity, MemoryStore, get_default_store, store_validation_event

app = FastAPI(title="MCP-Compatible Memory Service", version="1.0.0")
store: MemoryStore = get_default_store()


class ValidationMemoryRequest(BaseModel):
    user_id: str = Field(default="unknown")
    chat_id: str = Field(default="unknown")
    file_name: str
    valid: bool
    issues: list[str] = Field(default_factory=list)
    converted_to: str = Field(default="csv")
    message: Optional[str] = None


class EntityUpsertRequest(BaseModel):
    name: str
    entityType: str
    observations: list[str] = Field(default_factory=list)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "service": "memory-service", "storage": os.getenv("MEMORY_STORAGE_PATH")}


@app.get("/memory/graph")
async def read_graph() -> JSONResponse:
    return JSONResponse(status_code=200, content={"ok": True, "graph": store.read_graph()})


@app.get("/memory/search")
async def search_memory(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    results = store.search_entities(query=query, limit=limit)
    return JSONResponse(status_code=200, content={"ok": True, "results": results})


@app.get("/memory/user/{user_id}/history")
async def user_history(user_id: str, limit: int = Query(default=20, ge=1, le=100)) -> JSONResponse:
    query = f"telegram_user_{user_id}"
    results = store.search_entities(query=query, limit=limit)
    graph = store.read_graph()
    related_files = [
        relation
        for relation in graph["relations"]
        if relation["from"] == f"telegram_user_{user_id}"
    ]
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "user_id": user_id,
            "entities": results,
            "relations": related_files[:limit],
        },
    )


@app.post("/memory/entities")
async def upsert_entity(payload: EntityUpsertRequest) -> JSONResponse:
    store.upsert_entity(
        Entity(
            name=payload.name,
            entityType=payload.entityType,
            observations=payload.observations,
        )
    )
    return JSONResponse(status_code=200, content={"ok": True})


@app.post("/memory/validation")
async def save_validation(payload: ValidationMemoryRequest) -> JSONResponse:
    event = store_validation_event(
        store,
        user_id=payload.user_id,
        chat_id=payload.chat_id,
        file_name=payload.file_name,
        valid=payload.valid,
        issues=payload.issues,
        converted_to=payload.converted_to,
    )
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "saved": True,
            "event": event,
            "message_preview": (payload.message or "")[:300],
        },
    )
