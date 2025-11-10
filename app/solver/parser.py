from __future__ import annotations
import re
from typing import Optional

SUBMIT_PAYLOAD_RE = re.compile(r"Post your answer to (https?://\S+) with this JSON payload:", re.IGNORECASE)
QUESTION_RE = re.compile(r"Q(\d+)\.\s*(.*?)\n", re.DOTALL)
VALUE_SUM_HINT = re.compile(r"sum of the \"value\" column", re.IGNORECASE)


def extract_submit_url(html: str) -> Optional[str]:
    m = SUBMIT_PAYLOAD_RE.search(html)
    if m:
        return m.group(1).rstrip('.')
    return None


def detect_question_type(html: str) -> str:
    if VALUE_SUM_HINT.search(html):
        return "sum_value_column"
    return "generic"


def extract_table_urls(html: str) -> list[str]:
    # naive extraction of hrefs to .pdf or .csv etc.
    return re.findall(r'href="(https?://[^"\s]+\.(?:csv|pdf|json))"', html, re.IGNORECASE)
