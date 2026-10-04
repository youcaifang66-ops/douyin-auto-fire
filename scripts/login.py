from __future__ import annotations

import asyncio
import base64
import gzip
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playwright.async_api import async_playwright

from app.browser import open_private_messages


DOUYIN_URL = "https://www.douyin.com/"

async def login() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(locale="zh-CN")
        page = await context.new_page()
        await page.goto(DOUYIN_URL, wait_until="domcontentloaded")
        await _open_login(page)
        print("请在浏览器中扫码登录。登录完成并看到抖音首页后，回到终端按 Enter。")
        await asyncio.to_thread(input)
        await page.goto(DOUYIN_URL, wait_until="domcontentloaded")
        await _verify_home_login(page)
        # A homepage session can exist while IM still requires authentication.
        # Never replace the saved credentials until private messages work.
        await open_private_messages(page)
        await context.storage_state(path="storage-state.json.tmp")
        await browser.close()
        Path("storage-state.json.tmp").replace("storage-state.json")
        export_dir = Path("storage_state")
        export_dir.mkdir(exist_ok=True)
        compressed = base64.b64encode(gzip.compress(Path("storage-state.json").read_bytes()))
        (export_dir / "actions.gz.b64").write_bytes(compressed)
        print("已验证私信页面，登录状态已保存到 storage-state.json")
        print("GitHub Actions：将文件完整内容保存为仓库 Secret DOUYIN_STORAGE_STATE。不要提交文件到仓库。")
        print("完整 JSON 超过 Secret 限制时，将 storage_state/actions.gz.b64 保存为 DOUYIN_STORAGE_STATE_GZIP。")


async def _open_login(page) -> None:
    login = page.get_by_text("登录", exact=True)
    if await login.count():
        try:
            await login.first.click(timeout=10_000)
        except Exception:
            pass

    qr_login = page.get_by_text("扫码登录", exact=True)
    if await qr_login.count():
        try:
            await qr_login.first.click(timeout=5_000)
        except Exception:
            pass


async def _verify_home_login(page) -> None:
    login = page.get_by_text("登录", exact=True)
    if await login.count() and await login.first.is_visible():
        raise RuntimeError("未检测到登录成功，请重新运行并完成扫码确认")


if __name__ == "__main__":
    asyncio.run(login())
