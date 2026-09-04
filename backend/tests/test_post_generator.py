import asyncio

from app.schemas import AccountProfile, DogProfile, ProviderPostResult
from app.services.ai.utils import (
    ensure_required_hashtags,
    format_caption_fallback,
    parse_hashtags,
)
from app.services.post_generator import PostGenerator


class FakeAIManager:
    async def analyze_image(self, provider_name, image_bytes, mime_type):
        return "芝生の上で犬が前を向いている。"

    async def generate_post(
        self,
        provider_name,
        image_description,
        dog_profile,
        user_note,
        required_hashtags,
        style,
        caption_length,
        hashtag_count,
        adjustment=False,
        media_type="single_image",
    ):
        assert user_note == "波を少し怖がっていた"
        assert required_hashtags == ["#海デビュー", "#トイプードル"]
        assert caption_length == "standard"
        assert hashtag_count == 5
        assert media_type == "single_image"
        return ProviderPostResult(
            caption=(
                "波にどきどきしたけれど、ココは少しずつ海へ近づきました。"
                "最初は足元を気にしていたのに、最後には波の音を聞きながら穏やかな表情に。"
                "またひとつ大切な思い出が増えました🐾"
            ),
            hashtags=["#犬のいる暮らし", "#海デビュー", "#dogstagram"],
        )


def test_parse_hashtags_normalizes_and_deduplicates() -> None:
    assert parse_hashtags("#柴犬, ＃海デビュー\n#柴犬  犬のいる暮らし") == [
        "#柴犬",
        "#海デビュー",
        "#犬のいる暮らし",
    ]


def test_required_hashtags_are_always_first() -> None:
    assert ensure_required_hashtags(
        ["#dogstagram", "#海デビュー"], ["#海デビュー", "#トイプードル"]
    ) == ["#海デビュー", "#トイプードル", "#dogstagram"]


def test_caption_fallback_adds_paragraphs_and_emoji() -> None:
    caption = format_caption_fallback("最初の出来事です。次の場面です。最後は前向きに締めます。", "long")
    assert caption.count("\n\n") == 2
    assert "✨" in caption


def test_post_generator_retries_when_caption_lacks_visual_format() -> None:
    class FormatRetryAIManager(FakeAIManager):
        def __init__(self) -> None:
            self.calls = []

        async def generate_post(
            self,
            provider_name,
            image_description,
            dog_profile,
            user_note,
            required_hashtags,
            style,
            caption_length,
            hashtag_count,
            adjustment=False,
            media_type="single_image",
        ):
            self.calls.append(adjustment)
            return ProviderPostResult(
                caption="最初の出来事です。次の場面です。最後は前向きに締めます。",
                hashtags=["#犬のいる暮らし"],
            )

    async def run_generation():
        manager = FormatRetryAIManager()
        result = await PostGenerator(ai_manager=manager).generate(
            image_bytes=b"image",
            mime_type="image/jpeg",
            dog_profile=DogProfile(name="ココ"),
            user_note="",
            required_hashtags=[],
            style="friendly",
            image_provider="mock",
            text_provider="mock",
            caption_length="long",
        )
        return manager, result

    manager, result = asyncio.run(run_generation())
    assert manager.calls == [False, True]
    assert result.caption.count("\n\n") == 2
    assert "✨" in result.caption


def test_post_generator_preserves_required_tags() -> None:
    async def run_generation():
        generator = PostGenerator(ai_manager=FakeAIManager())
        return await generator.generate(
            image_bytes=b"image",
            mime_type="image/jpeg",
            dog_profile=DogProfile(name="ココ", voice="dog"),
            user_note="波を少し怖がっていた",
            required_hashtags=["#海デビュー", "#トイプードル"],
            style="cute",
            image_provider="mock",
            text_provider="mock",
        )

    result = asyncio.run(run_generation())
    assert result.hashtags[:2] == ["#海デビュー", "#トイプードル"]
    assert result.providers.image == "mock"
    assert result.providers.text == "mock"
    assert result.caption_length == "standard"
    assert result.caption_char_count == len(result.caption)
    assert result.hashtag_count == 5


def test_post_generator_retries_once_when_caption_is_far_outside_range() -> None:
    class RetryAIManager(FakeAIManager):
        def __init__(self) -> None:
            self.calls = []

        async def generate_post(
            self,
            provider_name,
            image_description,
            dog_profile,
            user_note,
            required_hashtags,
            style,
            caption_length,
            hashtag_count,
            adjustment=False,
            media_type="single_image",
        ):
            self.calls.append(adjustment)
            return ProviderPostResult(
                caption=("あ" * 100) if adjustment else "短すぎる本文",
                hashtags=["#犬のいる暮らし"],
            )

    async def run_generation():
        manager = RetryAIManager()
        generator = PostGenerator(ai_manager=manager)
        result = await generator.generate(
            image_bytes=b"image",
            mime_type="image/jpeg",
            dog_profile=DogProfile(name="ココ"),
            user_note="",
            required_hashtags=[],
            style="cute",
            image_provider="mock",
            text_provider="mock",
        )
        return manager, result

    manager, result = asyncio.run(run_generation())
    assert manager.calls == [False, True]
    assert result.caption_char_count == 100


def test_post_generator_renders_category_template_with_fixed_profile_values() -> None:
    class RestaurantAIManager:
        async def analyze_image(self, provider_name, image_bytes, mime_type):
            return "白い皿のパスタ。"

        async def generate_post(
            self,
            provider_name,
            image_description,
            dog_profile,
            user_note,
            required_hashtags,
            style,
            caption_length,
            hashtag_count,
            adjustment=False,
            media_type="single_image",
            category="pet",
            account_profile=None,
        ):
            assert category == "restaurant"
            assert account_profile.profile_data["phone"] == "03-1234-5678"
            return ProviderPostResult(
                title="夏限定パスタ",
                caption="香り豊かなパスタをゆっくり楽しめる一皿です。" * 8,
                hashtags=["#東京グルメ"],
            )

    async def run_generation():
        return await PostGenerator(ai_manager=RestaurantAIManager()).generate(
            image_bytes=b"image",
            mime_type="image/jpeg",
            dog_profile=DogProfile(name="fallback"),
            user_note="夏限定です。",
            required_hashtags=[],
            style="recommend",
            image_provider="mock",
            text_provider="mock",
            category="restaurant",
            account_profile=AccountProfile(
                account_name="ABC Kitchen",
                category="restaurant",
                profile_data={
                    "shop_name": "ABC Kitchen",
                    "address": "東京都渋谷区",
                    "phone": "03-1234-5678",
                    "business_hours": "11:00〜21:00",
                },
            ),
            template_id="restaurant_store_info",
        )

    result = asyncio.run(run_generation())
    assert "ABC Kitchen" in result.rendered_post
    assert "03-1234-5678" in result.rendered_post
    assert "夏限定パスタ" in result.rendered_post


def test_post_generator_uses_literal_template_hashtags_before_ai_tags() -> None:
    class HashtagTemplateAIManager:
        async def analyze_image(self, provider_name, image_bytes, mime_type):
            return "カフェのテーブルに料理が置かれている。"

        async def generate_post(
            self,
            provider_name,
            image_description,
            dog_profile,
            user_note,
            required_hashtags,
            style,
            caption_length,
            hashtag_count,
            adjustment=False,
            media_type="single_image",
            category="pet",
            account_profile=None,
        ):
            assert required_hashtags == ["#カフェ", "#東京カフェ"]
            assert hashtag_count == 5
            return ProviderPostResult(
                title="今日のおすすめ",
                caption="ゆっくり過ごせる一皿をご紹介します。" * 8,
                hashtags=["#東京グルメ", "#カフェ巡り", "#ランチ", "#カフェ"],
            )

    async def run_generation():
        return await PostGenerator(ai_manager=HashtagTemplateAIManager()).generate(
            image_bytes=b"image",
            mime_type="image/jpeg",
            dog_profile=DogProfile(name="fallback"),
            user_note="今日のおすすめです。",
            required_hashtags=[],
            style="recommend",
            image_provider="mock",
            text_provider="mock",
            hashtag_count=5,
            category="restaurant",
            account_profile=AccountProfile(
                account_name="PawPost Cafe",
                category="restaurant",
                profile_data={
                    "shop_name": "PawPost Cafe",
                    "business_hours": "11:00〜19:00",
                    "address": "東京都〇〇区〇〇1-2-3",
                },
            ),
            template_id="custom",
            custom_template=(
                "{caption}\n\n"
                "📍 {shop_name}\n"
                "営業時間：{business_hours}\n"
                "住所：{address}\n\n"
                "#カフェ #東京カフェ"
            ),
        )

    result = asyncio.run(run_generation())
    assert result.hashtags == ["#カフェ", "#東京カフェ", "#東京グルメ", "#カフェ巡り", "#ランチ"]
    assert result.rendered_post.endswith(
        "#カフェ #東京カフェ #東京グルメ #カフェ巡り #ランチ"
    )
