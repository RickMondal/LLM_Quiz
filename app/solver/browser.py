from __future__ import annotations
import asyncio
from typing import Optional

async def render_page(url: str, user_agent: Optional[str] = None, timeout: float = 45.0) -> str:
    # Import here to avoid hard dependency at module import time
    from playwright.async_api import async_playwright  # type: ignore
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()
        await page.goto(url, timeout=int(timeout * 1000))
        # Wait for network idle / DOM settle
        await page.wait_for_load_state("networkidle")
        html = await page.content()
        await context.close()
        await browser.close()
        return html
