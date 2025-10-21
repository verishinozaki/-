from __future__ import annotations

import io
from typing import Any, Dict, List

import pandas as pd


TEST_CASE_COLUMNS = [
    "Test ID",
    "Title",
    "Objective",
    "Preconditions / Test Data",
    "Steps",
    "Expected Results",
    "Priority",
    "Notes",
    "Status",
    "Assignee",
]


def build_excel_workbook(source_url: str, test_cases: List[Dict[str, Any]]) -> io.BytesIO:
    """Create an in-memory Excel workbook from LLM generated test cases."""
    if not test_cases:
        raise ValueError("test_cases must not be empty")

    formatted_cases = []
    for case in test_cases:
        formatted_cases.append(
            {
                "Test ID": case.get("test_id", ""),
                "Title": case.get("title", ""),
                "Objective": case.get("objective", ""),
                "Preconditions / Test Data": "\n".join(case.get("preconditions", [])),
                "Steps": "\n".join(_enumerate_items(case.get("steps", []))),
                "Expected Results": "\n".join(_enumerate_items(case.get("expected_results", []))),
                "Priority": case.get("priority", ""),
                "Notes": case.get("notes", ""),
                "Status": "",
                "Assignee": "",
            }
        )

    data_frame = pd.DataFrame(formatted_cases, columns=TEST_CASE_COLUMNS)

    summary_frame = pd.DataFrame(
        {
            "項目": ["テスト対象URL", "テストケース数"],
            "内容": [source_url, len(formatted_cases)],
        }
    )

    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="xlsxwriter") as writer:
        summary_frame.to_excel(writer, sheet_name="Summary", index=False)
        data_frame.to_excel(writer, sheet_name="TestCases", index=False)

        workbook = writer.book
        summary_sheet = writer.sheets["Summary"]
        cases_sheet = writer.sheets["TestCases"]

        summary_sheet.set_column(0, 0, 20)
        summary_sheet.set_column(1, 1, 80)

        wrap_format = workbook.add_format({"text_wrap": True, "valign": "top"})
        for idx, column in enumerate(TEST_CASE_COLUMNS):
            width = 18 if column not in {"Steps", "Expected Results", "Notes"} else 40
            cases_sheet.set_column(idx, idx, width, wrap_format)

        header_format = workbook.add_format(
            {"bold": True, "bg_color": "#DDEBF7", "border": 1, "text_wrap": True}
        )
        for col_num, value in enumerate(TEST_CASE_COLUMNS):
            cases_sheet.write(0, col_num, value, header_format)

    stream.seek(0)
    return stream


def _enumerate_items(values: List[str]) -> List[str]:
    return [f"{idx + 1}. {value}" for idx, value in enumerate(values) if value]
