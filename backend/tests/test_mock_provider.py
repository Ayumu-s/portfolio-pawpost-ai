import asyncio

from app.config import Settings
from app.schemas import AccountProfile, DogProfile
from app.services.ai.manager import AIManager


def test_mock_provider_generates_without_external_ai() -> None:
    manager = AIManager(Settings(image_ai_provider="mock", text_ai_provider="mock"))

    description = asyncio.run(
        manager.analyze_image("mock", "mock-image".encode(), "image/jpeg")
    )
    result = asyncio.run(
        manager.generate_post(
            "mock",
            description,
            DogProfile(name="ココ"),
            "海辺の散歩",
            ["#犬のいる暮らし"],
            "auto",
            "standard",
            5,
        )
    )

    assert "外部AIには接続せず" in description
    assert "Mockモード" in result.caption
    assert result.hashtags[0] == "#犬のいる暮らし"


def test_mock_provider_generates_restaurant_demo_copy() -> None:
    manager = AIManager(Settings(image_ai_provider="mock", text_ai_provider="mock"))
    profile = AccountProfile(
        category="restaurant",
        profile_data={
            "shop_name": "小皿食堂 ひより",
            "product_name": "季節のランチプレート",
            "price": "1,480円",
            "campaign": "旬の野菜を楽しむランチフェア",
        },
    )

    result = asyncio.run(
        manager.generate_post(
            "mock",
            "mock description",
            DogProfile(name="サンプル"),
            "彩り野菜と香草チキンのランチ",
            ["#季節のランチ"],
            "recommend",
            "standard",
            5,
            category="restaurant",
            account_profile=profile,
        )
    )

    assert "小皿食堂 ひより" in result.title
    assert "季節のランチプレート" in result.caption
    assert "1,480円" in result.caption
    assert "公開用Mock" in result.caption
