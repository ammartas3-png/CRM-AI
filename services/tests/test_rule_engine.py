#!/usr/bin/env python3
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rule-engine"))

import openpyxl
from engine import run_zero_token_validation


def make_xlsx() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Ad", "Telefon", "Mail"])
    ws.append(["Ali Veli", "0532 111 22 33", "Ali@Email.COM"])
    ws.append(["", "0532 111 22 33", "bad-email"])  # duplicate phone + invalid email
    ws.append(["Ayse", "003212345678", "ayse@test.com"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def main() -> None:
    result = run_zero_token_validation("sample.xlsx", make_xlsx())
    assert "phone" in result.corrected_csv
    assert result.stats["token_cost"] == 0
    assert result.fixed_rows >= 1
    print("rule-engine-ok")
    print(result.message)
    print("ai_needed", result.stats["ai_needed_count"])


if __name__ == "__main__":
    main()
