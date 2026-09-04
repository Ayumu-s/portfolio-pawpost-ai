import json

from fastapi.testclient import TestClient

from app.api import posts
from app.main import app
from app.schemas import GeneratedPost, ProvidersUsed
from app.services.template_renderer import (
    TemplateValidationError,
    extract_template_hashtags,
    render_template,
    resolve_template,
)


def test_template_hashtags_are_extracted_and_ai_tags_are_appended() -> None:
    body = "{caption}\n\n#カフェ #東京カフェ"

    assert extract_template_hashtags(body) == ["#カフェ", "#東京カフェ"]
    rendered = render_template(
        body,
        {"caption": "今日のおすすめです。", "hashtags": "#東京グルメ #カフェ巡り #ランチ"},
    )

    assert rendered.endswith("#カフェ #東京カフェ #東京グルメ #カフェ巡り #ランチ")


def test_template_hashtags_do_not_duplicate_when_hashtags_placeholder_is_present() -> None:
    rendered = render_template(
        "{caption}\n\n#カフェ #東京カフェ\n\n{hashtags}",
        {
            "caption": "今日のおすすめです。",
            "hashtags": "#カフェ #東京カフェ #東京グルメ",
        },
    )

    assert rendered.count("#カフェ") == 1
    assert rendered.count("#東京カフェ") == 1
    assert rendered.endswith("#東京グルメ")


def test_template_renderer_removes_empty_fixed_information_rows() -> None:
    rendered = render_template(
        "🍽 {title}\n\n{caption}\n\n────────────\n🏠 {shop_name}\n📍 {address}\n📞 {phone}\n🕐 {business_hours}\n\n{hashtags}",
        {
            "title": "新メニュー",
            "caption": "おすすめです。",
            "shop_name": "ABC Kitchen",
            "address": "東京都",
            "phone": "",
            "business_hours": "11:00〜21:00",
            "hashtags": "#ランチ",
        },
    )
    assert "ABC Kitchen" in rendered
    assert "東京都" in rendered
    assert "📞" not in rendered
    assert "────────────" not in rendered


def test_template_renderer_rejects_unknown_variable() -> None:
    try:
        render_template("{caption}\n{unknown_variable}", {"caption": "本文"})
    except TemplateValidationError as error:
        assert "{unknown_variable}" in str(error)
    else:
        raise AssertionError("unknown template variable was accepted")


def test_template_category_mismatch_is_rejected() -> None:
    try:
        resolve_template("pet", "restaurant_new_menu")
    except TemplateValidationError as error:
        assert "カテゴリ" in str(error)
    else:
        raise AssertionError("category mismatch was accepted")


def test_category_api_accepts_restaurant_profile_and_keeps_fixed_values(monkeypatch) -> None:
    expected = GeneratedPost(
        title="夏限定パスタ",
        caption="香り豊かな一皿をご紹介します。",
        hashtags=["#東京グルメ"],
        image_description="パスタ",
        style="recommend",
        category="restaurant",
        account_name="ABC Kitchen",
        template_id="restaurant_store_info",
        rendered_post="🍽 夏限定パスタ\n\n香り豊かな一皿をご紹介します。\n\n🏠 ABC Kitchen\n📍 東京都渋谷区\n📞 03-1234-5678",
        providers=ProvidersUsed(image="mock", text="mock"),
    )

    class FakeGenerator:
        async def generate(self, **kwargs):
            assert kwargs["category"] == "restaurant"
            assert kwargs["account_profile"].profile_data["phone"] == "03-1234-5678"
            assert kwargs["template_id"] == "restaurant_store_info"
            return expected

    monkeypatch.setattr(posts, "post_generator", FakeGenerator())
    response = TestClient(app).post(
        "/api/posts/generate",
        files={"image": ("dish.jpg", b"fake-jpeg", "image/jpeg")},
        data={
            "category": "restaurant",
            "account_name": "ABC Kitchen",
            "profile_data": json.dumps({
                "shop_name": "ABC Kitchen",
                "address": "東京都渋谷区",
                "phone": "03-1234-5678",
                "business_hours": "11:00〜21:00",
            }, ensure_ascii=False),
            "template_id": "restaurant_store_info",
            "dog_name": "",
        },
    )
    assert response.status_code == 200
    assert response.json()["category"] == "restaurant"
    assert response.json()["account_name"] == "ABC Kitchen"


def test_category_validation_requires_only_the_minimum_profile_fields() -> None:
    client = TestClient(app)
    for category, profile in [
        ("food", {"account_name": "おうちごはん"}),
        ("restaurant", {"shop_name": "ABC Kitchen"}),
        ("pr", {"company_name": "株式会社ABC"}),
        ("travel", {"account_name": "週末旅"}),
        ("custom", {"account_name": "記録", "theme": "日々"}),
    ]:
        # Validation runs before provider/media work, so no image is needed.
        response = client.post(
            "/api/posts/generate",
            data={
                "category": category,
                "account_name": profile.get("account_name", ""),
                "profile_data": json.dumps(profile, ensure_ascii=False),
            },
        )
        assert response.status_code == 400

    missing = client.post(
        "/api/posts/generate",
        data={"category": "restaurant", "profile_data": json.dumps({})},
    )
    assert missing.status_code == 422
    assert "必須プロフィール" in missing.json()["detail"]
