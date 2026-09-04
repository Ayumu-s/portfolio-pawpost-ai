"""Headless smoke test for the local PawPost UI and API."""

import base64
import os
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


RESULTS = Path(__file__).resolve().parents[1] / "test-results"
RESULTS.mkdir(exist_ok=True)

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

BACKEND_URL = os.getenv("PAWPOST_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
FRONTEND_URL = os.getenv("PAWPOST_FRONTEND_URL", "http://127.0.0.1:3000").rstrip("/")
DEFAULT_FRONTEND_BACKEND_ORIGINS = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
)


def run() -> None:
    console_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # The frontend's public API base is compiled at dev-server startup.
        # Rewrite only the default local API origin when testing on another port.
        if BACKEND_URL not in DEFAULT_FRONTEND_BACKEND_ORIGINS:
            def rewrite_backend_request(route):
                request_url = route.request.url
                for origin in DEFAULT_FRONTEND_BACKEND_ORIGINS:
                    if request_url.startswith(origin):
                        request_url = BACKEND_URL + request_url[len(origin):]
                        break
                if request_url == route.request.url:
                    route.continue_()
                else:
                    route.continue_(url=request_url)

            page.route("**/*", rewrite_backend_request)

        health = page.request.get(f"{BACKEND_URL}/api/health")
        assert health.ok and health.json() == {"status": "ok", "app": "PawPost AI"}
        assert page.request.get(f"{BACKEND_URL}/docs").ok

        page.goto(FRONTEND_URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_load_state("networkidle", timeout=60_000)
        assert page.title().startswith("PawPost AI")
        assert page.get_by_role("heading", level=1).filter(has_text="料理の一枚から").is_visible()
        assert page.get_by_text("サンプルでそのまま試す", exact=True).is_visible()
        sample_buttons = page.locator("button.demo-sample")
        assert sample_buttons.count() == 3
        assert page.locator("button.demo-sample.active").count() == 1
        assert page.locator('.drop-zone.selected img[alt="選択した投稿写真"]').is_visible()

        # The public restaurant demo can be switched without selecting a local file.
        sample_buttons.nth(1).click()
        expect(sample_buttons.nth(1)).to_have_class(re.compile(r".*\bactive\b"), timeout=10_000)
        assert page.get_by_label("店名 必須").input_value()

        generate_button = page.locator("button.generate-button")
        page.locator(".ai-settings summary").click()
        expect(generate_button).to_contain_text("Mock / デモ × Mock / デモ")
        generate_button.click()
        page.get_by_role("heading", name="投稿文を整える").wait_for(timeout=20_000)
        assert page.locator(".result-editor").is_visible()

        caption = page.get_by_label("投稿文")
        caption.fill("季節のランチを、できたての香りごとどうぞ🍝")
        assert "季節のランチを、できたての香りごとどうぞ🍝" in page.locator(".insta-copy").inner_text()
        assert "文字" in page.locator(".caption-meta").inner_text()
        page.screenshot(path=str(RESULTS / "pawpost-desktop.png"), full_page=True)

        # Keep the basic media-mode flow covered as well as the no-upload demo path.
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(FRONTEND_URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_load_state("networkidle", timeout=60_000)
        overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        assert overflow <= 1, f"mobile horizontal overflow: {overflow}px"
        assert page.locator("button.demo-sample").count() == 3
        assert page.locator('.drop-zone.selected img[alt="選択した投稿写真"]').is_visible()
        assert page.locator("button.generate-button").is_visible()

        photo_input = page.locator("#dog-photo-input")
        assert "image/jpeg" in (photo_input.get_attribute("accept") or "")
        assert photo_input.get_attribute("hidden") is None
        assert page.locator('label[for="dog-photo-input"]').is_visible()
        page.get_by_role("button", name="写真複数").click()
        page.locator("#dog-photo-input").set_input_files([
            {"name": "one.png", "mimeType": "image/png", "buffer": PNG_1X1},
            {"name": "two.png", "mimeType": "image/png", "buffer": PNG_1X1},
        ])
        assert page.locator(".multi-image-thumb").count() == 2
        next_photo = page.get_by_role("button", name="次の写真")
        next_photo.click()
        assert page.locator(".media-count-badge").inner_text() == "2 / 2"
        page.get_by_role("button", name="前の写真").click()
        assert page.locator(".media-count-badge").inner_text() == "1 / 2"
        page.get_by_role("button", name="動画").click()
        assert page.locator('label[for="dog-video-input"]').is_visible()
        page.locator("#dog-video-input").set_input_files(
            {"name": "walk.mp4", "mimeType": "video/mp4", "buffer": b"fake-video"}
        )
        assert page.locator(".insta-video").is_visible()
        page.screenshot(path=str(RESULTS / "pawpost-mobile.png"), full_page=True)
        browser.close()

    if console_errors:
        raise AssertionError(f"Browser console errors: {console_errors}")
    print("E2E_OK: health, Swagger, restaurant demo generation, live edit, and mobile layout")


if __name__ == "__main__":
    run()
