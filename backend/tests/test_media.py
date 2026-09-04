import asyncio

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.api import posts
from app.main import app
from app.schemas import GeneratedPost, ProvidersUsed
from app.services.media_analyzer import MediaAnalyzer
from app.services.video_utils import extract_video_frames


class FakeVisionManager:
    def __init__(self) -> None:
        self.calls = []

    async def analyze_image(self, provider_name, image_bytes, mime_type, media_type="single_image"):
        self.calls.append((provider_name, image_bytes, mime_type, media_type))
        return f"説明{len(self.calls)}"


def test_multi_image_analysis_preserves_order_and_media_type() -> None:
    manager = FakeVisionManager()
    analysis = asyncio.run(
        MediaAnalyzer(manager).analyze_images(
            [(b"one", "image/jpeg"), (b"two", "image/png")],
            provider_name="mock",
            media_type="multi_image",
        )
    )
    assert analysis.media_count == 2
    assert analysis.video_frame_count == 0
    assert "画像1の説明" in analysis.description
    assert "説明2" in analysis.description
    assert [call[3] for call in manager.calls] == ["multi_image", "multi_image"]


def test_video_analysis_uses_video_media_type(monkeypatch) -> None:
    manager = FakeVisionManager()
    monkeypatch.setattr("app.services.media_analyzer.extract_video_frames", lambda *args, **kwargs: [b"frame1", b"frame2"])
    analysis = asyncio.run(
        MediaAnalyzer(manager).analyze_video(
            b"video", filename="walk.mp4", provider_name="mock"
        )
    )
    assert analysis.media_count == 1
    assert analysis.video_frame_count == 2
    assert [call[3] for call in manager.calls] == ["video", "video"]


def test_video_frames_are_sampled_and_bounded(tmp_path) -> None:
    video_path = tmp_path / "sample.mp4"
    writer = cv2.VideoWriter(
        str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 5.0, (64, 64)
    )
    for index in range(20):
        writer.write(np.full((64, 64, 3), index * 8, dtype=np.uint8))
    writer.release()
    frames = extract_video_frames(video_path.read_bytes(), filename=video_path.name)
    assert 1 <= len(frames) <= 12
    assert all(frame.startswith(b"\xff\xd8") for frame in frames)


def test_api_accepts_up_to_ten_carousel_images(monkeypatch) -> None:
    expected = GeneratedPost(
        caption="写真を順番に振り返ろう🐾",
        hashtags=["#犬のいる暮らし"],
        image_description="カルーセル",
        style="auto",
        media_type="multi_image",
        media_count=2,
        providers=ProvidersUsed(image="mock", text="mock"),
    )
    generate_media = _async_mock(expected)
    monkeypatch.setattr(posts.post_generator, "generate_media", generate_media)
    response = TestClient(app).post(
        "/api/posts/generate",
        files=[
            ("images", ("one.jpg", b"one", "image/jpeg")),
            ("images", ("two.png", b"two", "image/png")),
        ],
        data={"dog_name": "ココ", "media_type": "multi_image"},
    )
    assert response.status_code == 200
    assert response.json()["media_count"] == 2
    assert generate_media.await_args.kwargs["media_type"] == "multi_image"
    assert len(generate_media.await_args.kwargs["images"]) == 2


def test_api_rejects_more_than_ten_carousel_images(monkeypatch) -> None:
    monkeypatch.setattr(posts.post_generator, "generate_media", _async_mock(None))
    files = [("images", (f"{index}.jpg", b"x", "image/jpeg")) for index in range(11)]
    response = TestClient(app).post(
        "/api/posts/generate",
        files=files,
        data={"dog_name": "ココ", "media_type": "multi_image"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "複数画像は最大10枚までです。"


def test_api_rejects_unsupported_video() -> None:
    response = TestClient(app).post(
        "/api/posts/generate",
        files={"video": ("walk.avi", b"video", "video/avi")},
        data={"dog_name": "ココ", "media_type": "video"},
    )
    assert response.status_code == 415
    assert "mp4" in response.json()["detail"]


class _AsyncMock:
    def __init__(self, value):
        self.value = value
        self.await_args = None

    async def __call__(self, **kwargs):
        self.await_args = type("AwaitArgs", (), {"kwargs": kwargs})()
        return self.value


def _async_mock(value):
    return _AsyncMock(value)
