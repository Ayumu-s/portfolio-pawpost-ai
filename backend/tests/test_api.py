from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api import posts
from app.main import app
from app.schemas import GeneratedPost, ProvidersUsed

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "PawPost AI"}


def test_config_does_not_expose_secrets() -> None:
    response = client.get("/api/config")
    assert response.status_code == 200
    assert set(response.json()) == {"image_provider", "text_provider"}
    serialized = response.text.casefold()
    assert "api_key" not in serialized
    assert "secret" not in serialized


def test_local_loopback_origins_are_allowed() -> None:
    for origin in (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ):
        response = client.options(
            "/api/config",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_generate_validates_image_type() -> None:
    response = client.post(
        "/api/posts/generate",
        files={"image": ("dog.gif", b"GIF89a", "image/gif")},
        data={"dog_name": "ココ"},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "JPEG / PNG / WebP / HEIC / HEIF の画像を選択してください。"


def test_generate_requires_an_image() -> None:
    response = client.post("/api/posts/generate", data={"dog_name": "ココ"})
    assert response.status_code == 400
    assert response.json()["detail"] == "まず愛犬の写真を選択してください。"


def test_generate_returns_provider_result(monkeypatch) -> None:
    expected = GeneratedPost(
        caption="きょうは海を見にきたよ🐶🌊",
        hashtags=["#海デビュー", "#犬のいる暮らし"],
        image_description="砂浜に小型犬が立っている。",
        style="cute",
        caption_length="short",
        caption_char_count=len("きょうは海を見にきたよ🐶🌊"),
        hashtag_count=3,
        providers=ProvidersUsed(image="mock", text="mock"),
    )
    generate = AsyncMock(return_value=expected)
    monkeypatch.setattr(posts.post_generator, "generate", generate)

    response = client.post(
        "/api/posts/generate",
        files={"image": ("dog.jpg", b"fake-jpeg", "image/jpeg")},
        data={
            "dog_name": "ココ",
            "voice": "dog",
            "style": "cute",
            "image_provider": "mock",
            "text_provider": "mock",
            "required_hashtags": "#海デビュー",
            "caption_length": "short",
            "hashtag_count": "3",
        },
    )
    assert response.status_code == 200
    assert response.json() == expected.model_dump()
    assert generate.await_args.kwargs["required_hashtags"] == ["#海デビュー"]
    assert generate.await_args.kwargs["caption_length"] == "short"
    assert generate.await_args.kwargs["hashtag_count"] == 3


def test_generate_rejects_required_hashtags_over_limit(monkeypatch) -> None:
    monkeypatch.setattr(posts.post_generator, "generate", AsyncMock())
    response = client.post(
        "/api/posts/generate",
        files={"image": ("dog.jpg", b"fake-jpeg", "image/jpeg")},
        data={
            "dog_name": "ココ",
            "required_hashtags": "#a #b #c #d #e #f",
            "hashtag_count": "5",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "ハッシュタグは最大5個まで指定できます。"


def test_generate_rejects_required_hashtags_over_selected_count(monkeypatch) -> None:
    monkeypatch.setattr(posts.post_generator, "generate", AsyncMock())
    response = client.post(
        "/api/posts/generate",
        files={"image": ("dog.jpg", b"fake-jpeg", "image/jpeg")},
        data={
            "dog_name": "ココ",
            "required_hashtags": "#a #b #c #d",
            "hashtag_count": "3",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"].startswith("必須ハッシュタグが設定数を超えています")


def test_generate_rejects_template_hashtags_over_selected_count(monkeypatch) -> None:
    monkeypatch.setattr(posts.post_generator, "generate", AsyncMock())
    response = client.post(
        "/api/posts/generate",
        data={
            "dog_name": "ココ",
            "template_id": "custom",
            "custom_template": "{caption}\n\n#a #b #c #d",
            "hashtag_count": "3",
        },
    )
    assert response.status_code == 422
    assert "テンプレート内の固定ハッシュタグ" in response.json()["detail"]


def test_generate_rejects_invalid_caption_length(monkeypatch) -> None:
    monkeypatch.setattr(posts.post_generator, "generate", AsyncMock())
    response = client.post(
        "/api/posts/generate",
        files={"image": ("dog.jpg", b"fake-jpeg", "image/jpeg")},
        data={"dog_name": "ココ", "caption_length": "huge"},
    )
    assert response.status_code == 422


def test_generate_rejects_invalid_hashtag_count(monkeypatch) -> None:
    monkeypatch.setattr(posts.post_generator, "generate", AsyncMock())
    response = client.post(
        "/api/posts/generate",
        files={"image": ("dog.jpg", b"fake-jpeg", "image/jpeg")},
        data={"dog_name": "ココ", "hashtag_count": "2"},
    )
    assert response.status_code == 422


def test_generate_normalizes_heic_before_provider(monkeypatch) -> None:
    expected = GeneratedPost(
        caption="HEICも読めたよ🐾",
        hashtags=["#犬のいる暮らし"],
        image_description="小型犬が写っている。",
        style="auto",
        providers=ProvidersUsed(image="mock", text="mock"),
    )
    generate = AsyncMock(return_value=expected)
    monkeypatch.setattr(posts.post_generator, "generate", generate)
    monkeypatch.setattr(
        posts,
        "normalize_image_bytes",
        lambda **kwargs: (b"converted-jpeg", "image/jpeg"),
    )

    response = client.post(
        "/api/posts/generate",
        files={"image": ("iphone.heic", b"fake-heic", "image/heic")},
        data={"dog_name": "ココ"},
    )
    assert response.status_code == 200
    assert generate.await_args.kwargs["image_bytes"] == b"converted-jpeg"
    assert generate.await_args.kwargs["mime_type"] == "image/jpeg"
