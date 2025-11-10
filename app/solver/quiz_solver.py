from __future__ import annotations
import asyncio
import json
import math
import os
import time
from typing import Any, Dict, Optional

import httpx
import pandas as pd
from .browser import render_page
from .parser import extract_submit_url, detect_question_type, extract_table_urls


class QuizSolver:
    def __init__(self, email: str, secret: str, user_agent: Optional[str] = None, timeout: float = 45.0):
        self.email = email
        self.secret = secret
        self.user_agent = user_agent
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        await self.client.aclose()

    async def solve_quiz_chain(self, start_url: str, deadline_ts: float):
        url = start_url
        while time.time() < deadline_ts and url:
            result = await self.solve_single(url, deadline_ts)
            if result.get("stop"):
                break
            url = result.get("next_url")

    async def solve_single(self, url: str, deadline_ts: float) -> Dict[str, Any]:
        # render page
        html = await render_page(url, user_agent=self.user_agent, timeout=min(self.timeout, max(5, deadline_ts - time.time())))
        submit_url = extract_submit_url(html)
        if not submit_url:
            # fallback: try same domain /submit
            try:
                base = url.split("/quiz")[0]
                submit_url = base + "/submit"
            except Exception:
                pass
        answer: Any = None
        qtype = detect_question_type(html)
        if qtype == "sum_value_column":
            # find data file
            links = extract_table_urls(html)
            data = None
            for link in links:
                if link.lower().endswith(".csv"):
                    r = await self.client.get(link)
                    r.raise_for_status()
                    data = pd.read_csv(pd.compat.StringIO(r.text))
                    break
                elif link.lower().endswith(".json"):
                    r = await self.client.get(link)
                    r.raise_for_status()
                    js = r.json()
                    data = pd.json_normalize(js)
                    break
                elif link.lower().endswith(".pdf"):
                    # lightweight: try to read tables via tabula if available; else skip
                    try:
                        import pdfplumber  # type: ignore
                        r = await self.client.get(link)
                        r.raise_for_status()
                        import io
                        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
                            # heuristic: page 2 (index 1)
                            if len(pdf.pages) >= 2:
                                table = pdf.pages[1].extract_table()
                                if table:
                                    # first row header
                                    headers = table[0]
                                    rows = table[1:]
                                    data = pd.DataFrame(rows, columns=headers)
                    except Exception:
                        pass
            if data is not None and "value" in [c.lower() for c in data.columns]:
                # find the exact column name case-insensitive
                colname = next(c for c in data.columns if c.lower() == "value")
                # coerce numeric
                s = pd.to_numeric(data[colname], errors="coerce").fillna(0)
                answer = int(s.sum()) if float(s.sum()).is_integer() else float(s.sum())

        if answer is None:
            # last resort: try to find digits hint in HTML
            import re
            m = re.search(r"answer is\s*([0-9]+)", html, flags=re.IGNORECASE)
            if m:
                answer = int(m.group(1))

        if submit_url and answer is not None:
            payload = {"email": self.email, "secret": self.secret, "url": url, "answer": answer}
            try:
                resp = await self.client.post(submit_url, json=payload)
                # Do not raise on non-200; handle body
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                if isinstance(data, dict):
                    correct = data.get("correct")
                    next_url = data.get("url")
                    if correct is True and not next_url:
                        return {"stop": True}
                    if next_url:
                        return {"stop": False, "next_url": next_url}
                    if correct is False and time.time() + 10 < deadline_ts:
                        # try once more if we got a next_url
                        if next_url:
                            return {"stop": False, "next_url": next_url}
                # If we can't parse, stop
                return {"stop": True}
            except Exception:
                return {"stop": True}
        # If we can't compute or submit, stop
        return {"stop": True}
