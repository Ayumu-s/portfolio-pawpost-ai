"""Deterministic provider used by the public portfolio demo."""

from __future__ import annotations

from ...category_settings import Category
from ...config import Settings
from ...content_settings import CaptionLength
from ...schemas import AccountProfile, DogProfile, MediaType, ProviderPostResult, PostStyle
from .base import AIProvider
from .utils import parse_hashtags


class MockProvider(AIProvider):
    """Return fictional, source-independent results without network access."""

    def __init__(self, settings: Settings | None = None) -> None:
        del settings

    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        media_type: MediaType = "single_image",
    ) -> str:
        del image_bytes, mime_type
        media_label = {
            "single_image": "1枚の画像",
            "multi_image": "複数画像",
            "video": "動画の代表フレーム",
        }[media_type]
        return (
            f"公開用Mock入力として{media_label}を受け取りました。"
            "外部AIには接続せず、実画像の内容は解析していません。"
        )

    async def generate_post(
        self,
        image_description: str,
        dog_profile: DogProfile,
        user_note: str,
        required_hashtags: list[str],
        style: PostStyle,
        caption_length: CaptionLength,
        hashtag_count: int,
        adjustment: bool = False,
        media_type: MediaType = "single_image",
        category: Category = "pet",
        account_profile: AccountProfile | None = None,
    ) -> ProviderPostResult:
        del image_description, style, hashtag_count, adjustment, media_type
        subject = _subject(dog_profile, account_profile)
        note = " ".join(user_note.split())[:80]
        if category == "restaurant" and account_profile is not None:
            title = _restaurant_title(account_profile)
            caption = _restaurant_caption(caption_length, account_profile, note)
        else:
            title = f"{subject}の公開デモ"
            caption = _caption(caption_length, subject, note)
        hashtags = parse_hashtags(
            [*required_hashtags, "#PawPostAI", "#デモモード", "#投稿案"]
        )
        return ProviderPostResult(
            title=title,
            caption=caption,
            hashtags=hashtags,
        )


def _subject(dog_profile: DogProfile, account_profile: AccountProfile | None) -> str:
    if account_profile is not None:
        profile_data = account_profile.profile_data
        return (
            account_profile.account_name.strip()
            or profile_data.get("name", "").strip()
            or profile_data.get("shop_name", "").strip()
            or profile_data.get("brand_name", "").strip()
            or profile_data.get("company_name", "").strip()
            or "公開用アカウント"
        )
    return dog_profile.name.strip() or "サンプル"


def _caption(caption_length: CaptionLength, subject: str, note: str) -> str:
    if caption_length == "one_liner":
        return f"{subject}の投稿案をMockで作成しました。内容を確認できます🐾"

    short = (
        f"{subject}の投稿案を、外部AIなしのMockモードで作成しました。"
        "内容は投稿前に自由に編集できます🐾"
    )
    if caption_length == "short":
        return short

    note_line = f"入力メモ「{note}」を反映する想定です。" if note else "入力内容を反映する想定です。"
    standard = (
        f"{subject}の一枚を使った、PawPost AI公開デモの投稿案です。\n\n"
        "画像の内容を外部AIへ送らず、Mockモードで生成しています。"
        f"{note_line}生成後の文章は、公開前に内容を確認して自由に編集できます🐾"
    )
    if caption_length == "standard":
        return standard

    detailed = (
        standard
        + "\n\n"
        "このデモでは、素材の入力から文章生成、編集、Instagram風プレビューまでの流れを確認できます。"
    )
    if caption_length == "detailed":
        return detailed

    return (
        detailed
        + "\n\n"
        "公開前に文章や事実関係を確認し、必要に応じて手動で整えてから利用します。"
    )


def _restaurant_title(account_profile: AccountProfile) -> str:
    product_name = account_profile.profile_data.get("product_name", "").strip()
    shop_name = _subject(DogProfile(name="サンプル"), account_profile)
    return f"{product_name or '季節のおすすめ'} | {shop_name}"


def _restaurant_caption(
    caption_length: CaptionLength,
    account_profile: AccountProfile,
    note: str,
) -> str:
    data = account_profile.profile_data
    shop_name = (
        account_profile.account_name.strip()
        or data.get("shop_name", "").strip()
        or "このお店"
    )
    product_name = data.get("product_name", "").strip() or "季節のおすすめ"
    price = data.get("price", "").strip()
    campaign = data.get("campaign", "").strip()

    if caption_length == "one_liner":
        return f"{product_name}を、{shop_name}の今日のおすすめとしてご紹介します🍽️"
    if caption_length == "short":
        return f"{shop_name}の今日のおすすめは{product_name}。旬の味わいをゆっくり楽しめる一皿です🍽️"

    standard = (
        f"{shop_name}から、{product_name}のご紹介です。\n\n"
        f"{campaign or '季節の食材を使った、ゆっくり味わいたい一皿です。'}"
        + (f" 価格は{price}です。" if price else "")
        + (f"\n\nメモ「{note}」をもとにした公開用Mockの投稿案です。" if note else "\n\n公開用Mockで作成した投稿案です。")
        + "内容は投稿前に自由に編集できます🍽️"
    )
    if caption_length == "standard":
        return standard
    if caption_length == "detailed":
        return standard + "\n\n店舗情報や営業時間を確認してから公開する想定です。"
    return standard + "\n\n写真と事実関係を確認し、必要に応じて手動で整えてから利用します。"
