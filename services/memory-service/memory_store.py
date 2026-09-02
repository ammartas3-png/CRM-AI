import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str
    entityType: str
    observations: list[str] = Field(default_factory=list)


class Relation(BaseModel):
    from_entity: str = Field(alias="from")
    to_entity: str = Field(alias="to")
    relationType: str

    model_config = {"populate_by_name": True}


class MemoryStore:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.lock = threading.Lock()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("", encoding="utf-8")

    def _read_all(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if not self.storage_path.exists():
            return records
        for line in self.storage_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
        return records

    def _write_all(self, records: list[dict[str, Any]]) -> None:
        content = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
        if content:
            content += "\n"
        self.storage_path.write_text(content, encoding="utf-8")

    def read_graph(self) -> dict[str, Any]:
        entities_map: dict[str, Entity] = {}
        relations: list[dict[str, str]] = []

        for record in self._read_all():
            record_type = record.get("type")
            if record_type == "entity":
                entity = Entity(**record["data"])
                entities_map[entity.name] = entity
            elif record_type == "relation":
                relation = Relation(**record["data"])
                relations.append(
                    {
                        "from": relation.from_entity,
                        "to": relation.to_entity,
                        "relationType": relation.relationType,
                    }
                )

        return {
            "entities": [entity.model_dump() for entity in entities_map.values()],
            "relations": relations,
        }

    def upsert_entity(self, entity: Entity) -> None:
        with self.lock:
            records = self._read_all()
            updated = False
            for record in records:
                if record.get("type") == "entity" and record["data"]["name"] == entity.name:
                    existing = Entity(**record["data"])
                    merged_observations = list(
                        dict.fromkeys(existing.observations + entity.observations)
                    )
                    record["data"]["observations"] = merged_observations
                    record["data"]["entityType"] = entity.entityType
                    updated = True
                    break
            if not updated:
                records.append({"type": "entity", "data": entity.model_dump()})
            self._write_all(records)

    def add_relation(self, relation: Relation) -> None:
        with self.lock:
            records = self._read_all()
            payload = {
                "type": "relation",
                "data": {
                    "from": relation.from_entity,
                    "to": relation.to_entity,
                    "relationType": relation.relationType,
                },
            }
            if payload not in records:
                records.append(payload)
            self._write_all(records)

    def search_entities(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        query_lower = query.lower()
        graph = self.read_graph()
        matches: list[dict[str, Any]] = []
        for entity in graph["entities"]:
            haystack = " ".join(
                [entity.get("name", ""), entity.get("entityType", "")]
                + entity.get("observations", [])
            ).lower()
            if query_lower in haystack:
                matches.append(entity)
            if len(matches) >= limit:
                break
        return matches


def get_default_store() -> MemoryStore:
    storage_path = Path(
        os.getenv("MEMORY_STORAGE_PATH", "/app/data/memory.jsonl")
    )
    return MemoryStore(storage_path=storage_path)


def store_validation_event(
    store: MemoryStore,
    *,
    user_id: str,
    chat_id: str,
    file_name: str,
    valid: bool,
    issues: list[str],
    converted_to: str,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid.uuid4())
    user_entity = f"telegram_user_{user_id or chat_id or 'unknown'}"
    file_entity = f"file_{event_id}"

    store.upsert_entity(
        Entity(
            name=user_entity,
            entityType="TelegramUser",
            observations=[f"Last validation at {timestamp}"],
        )
    )
    store.upsert_entity(
        Entity(
            name=file_entity,
            entityType="ValidatedFile",
            observations=[
                f"Original file: {file_name}",
                f"Converted format: {converted_to}",
                f"Valid: {valid}",
                f"Issues: {', '.join(issues) if issues else 'none'}",
                f"Validated at: {timestamp}",
            ],
        )
    )
    store.add_relation(
        Relation(
            **{
                "from": user_entity,
                "to": file_entity,
                "relationType": "uploaded",
            }
        )
    )

    return {
        "event_id": event_id,
        "user_entity": user_entity,
        "file_entity": file_entity,
        "timestamp": timestamp,
    }
