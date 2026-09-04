import csv
import io
import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CSVValidationInput(BaseModel):
    csv_text: str = Field(..., description="CSV content as plain text")


class CSVValidationTool(BaseTool):
    name: str = "csv_validator"
    description: str = (
        "Validate CSV structure: row count, column count, empty rows, duplicate rows, "
        "and missing header cells. Returns JSON summary."
    )
    args_schema: type[BaseModel] = CSVValidationInput

    def _run(self, csv_text: str) -> str:
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        if not rows:
            return json.dumps({"valid": False, "error": "CSV is empty."})

        header = rows[0]
        data_rows = rows[1:]
        non_empty_rows = [row for row in data_rows if any(str(cell).strip() for cell in row)]
        row_lengths = {len(row) for row in rows}
        duplicate_rows = len(non_empty_rows) - len({tuple(row) for row in non_empty_rows})
        empty_header_cells = sum(1 for cell in header if not str(cell).strip())

        issues: list[str] = []
        if len(header) == 0:
            issues.append("Header row is missing.")
        if empty_header_cells:
            issues.append(f"{empty_header_cells} empty header cell(s) found.")
        if len(row_lengths) > 1:
            issues.append(f"Inconsistent column counts detected: {sorted(row_lengths)}.")
        if duplicate_rows > 0:
            issues.append(f"{duplicate_rows} duplicate data row(s) found.")
        if len(non_empty_rows) == 0:
            issues.append("No data rows found after header.")

        summary = {
            "valid": len(issues) == 0,
            "columns": len(header),
            "header": header,
            "total_rows": len(data_rows),
            "non_empty_rows": len(non_empty_rows),
            "duplicate_rows": duplicate_rows,
            "issues": issues,
        }
        return json.dumps(summary, ensure_ascii=False)


def run_rule_based_validation(csv_text: str) -> dict[str, Any]:
    tool = CSVValidationTool()
    return json.loads(tool._run(csv_text))
