#!/usr/bin/env python3
"""Quick smoke tests for shared conversion and memory store."""

import os
import sys
import tempfile
from pathlib import Path

services_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(services_root))
sys.path.insert(0, str(services_root / "memory-service"))

from shared.file_convert import normalize_upload_to_csv
from memory_store import MemoryStore, store_validation_event


def test_csv_passthrough() -> None:
    csv_bytes = b"col1,col2\na,b\n"
    name, text, out = normalize_upload_to_csv("test.csv", csv_bytes, "text/csv")
    assert name == "test.csv"
    assert "col1,col2" in text
    assert out == csv_bytes


def test_xlsx_to_csv() -> None:
    import io
    import openpyxl

    buffer = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["name", "email"])
    ws.append(["Ali", "ali@example.com"])
    wb.save(buffer)

    name, text, out = normalize_upload_to_csv("users.xlsx", buffer.getvalue())
    assert name == "users.csv"
    assert "name,email" in text
    assert "Ali,ali@example.com" in text
    assert out.decode("utf-8") == text


def test_memory_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(storage_path=Path(tmp) / "memory.jsonl")
        event = store_validation_event(
            store,
            user_id="123",
            chat_id="456",
            file_name="users.xlsx",
            valid=False,
            issues=["duplicate rows"],
            converted_to="csv",
        )
        assert "event_id" in event
        graph = store.read_graph()
        assert len(graph["entities"]) >= 2
        assert len(graph["relations"]) >= 1


if __name__ == "__main__":
    test_csv_passthrough()
    test_xlsx_to_csv()
    test_memory_store()
    print("all-tests-ok")
