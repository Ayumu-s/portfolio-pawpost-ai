"""Shared category, profile, style, and built-in template configuration."""

from __future__ import annotations

from typing import Literal

Category = Literal["pet", "food", "restaurant", "pr", "travel", "custom"]

CATEGORY_LABELS: dict[Category, str] = {
    "pet": "ペット",
    "food": "料理・レシピ",
    "restaurant": "飲食店",
    "pr": "企業・広報",
    "travel": "旅行・お出かけ",
    "custom": "自由設定",
}

CATEGORY_REQUIRED_FIELDS: dict[Category, tuple[str, ...]] = {
    "pet": ("name",),
    "food": ("account_name",),
    "restaurant": ("shop_name",),
    "pr": (),
    "travel": ("account_name",),
    "custom": ("account_name", "theme"),
}

CATEGORY_STYLES: dict[Category, tuple[tuple[str, str], ...]] = {
    "pet": (("auto", "AIおまかせ"), ("cute", "かわいい"), ("funny", "面白い"), ("diary", "日記風"), ("simple", "シンプル"), ("owner", "飼い主目線"), ("dog", "ペット本人目線")),
    "food": (("auto", "AIおまかせ"), ("friendly", "親しみやすい"), ("casual", "カジュアル"), ("simple", "シンプル"), ("polite", "丁寧"), ("diary", "日記風")),
    "restaurant": (("auto", "AIおまかせ"), ("recommend", "おすすめ紹介"), ("premium", "高級感"), ("friendly", "親しみやすい"), ("simple", "シンプル")),
    "pr": (("auto", "AIおまかせ"), ("official", "公式"), ("casual", "カジュアル広報"), ("recruit", "採用広報"), ("expert", "専門的"), ("simple", "シンプル")),
    "travel": (("auto", "AIおまかせ"), ("diary", "旅行記"), ("friendly", "親しみやすい"), ("simple", "シンプル"), ("polite", "丁寧")),
    "custom": (("auto", "AIおまかせ"), ("friendly", "親しみやすい"), ("casual", "カジュアル"), ("simple", "シンプル"), ("polite", "丁寧")),
}

BUILTIN_TEMPLATES: tuple[dict[str, object], ...] = (
    {"template_id": "pet_daily", "name": "日常投稿", "category": "pet", "description": "ペットの日常", "template_body": "{caption}\n\n{hashtags}", "is_default": True, "is_builtin": True},
    {"template_id": "pet_outing", "name": "お出かけ", "category": "pet", "description": "散歩やお出かけ", "template_body": "🐾 {title}\n\n{caption}\n\n{hashtags}", "is_default": False, "is_builtin": True},
    {"template_id": "food_recipe", "name": "レシピ紹介", "category": "food", "description": "料理やレシピ", "template_body": "🍳 {title}\n\n{caption}\n\n{hashtags}", "is_default": True, "is_builtin": True},
    {"template_id": "food_daily", "name": "今日のごはん", "category": "food", "description": "料理記録", "template_body": "今日のごはん：{title}\n\n{caption}\n\n{hashtags}", "is_default": False, "is_builtin": True},
    {"template_id": "restaurant_store_info", "name": "店舗情報付き", "category": "restaurant", "description": "店舗情報を固定表示", "template_body": "🍽 {title}\n\n{caption}\n\n────────────\n🏠 {shop_name}\n📍 {address}\n📞 {phone}\n🕐 {business_hours}\n🔗 {url}\n\n{hashtags}", "is_default": True, "is_builtin": True},
    {"template_id": "restaurant_new_menu", "name": "新メニュー紹介", "category": "restaurant", "description": "新商品・新メニュー", "template_body": "✨ NEW MENU ✨\n\n{title}\n\n{caption}\n\n価格：{price}\n\n────────────\n🏠 {shop_name}\n📍 {address}\n📞 {phone}\n\n{hashtags}", "is_default": False, "is_builtin": True},
    {"template_id": "restaurant_campaign", "name": "キャンペーン", "category": "restaurant", "description": "期間限定やキャンペーン", "template_body": "📣 {title}\n\n{caption}\n\n{campaign}\n\n{hashtags}", "is_default": False, "is_builtin": True},
    {"template_id": "pr_announcement", "name": "お知らせ", "category": "pr", "description": "企業からのお知らせ", "template_body": "【{title}】\n\n{caption}\n\n詳しくはこちら\n{url}\n\n{hashtags}", "is_default": True, "is_builtin": True},
    {"template_id": "pr_event", "name": "イベント告知", "category": "pr", "description": "イベントや開催案内", "template_body": "📢 {title}\n\n{caption}\n\n開催日：{event_date}\n{url}\n\n{hashtags}", "is_default": False, "is_builtin": True},
    {"template_id": "pr_product", "name": "商品・サービス紹介", "category": "pr", "description": "商品やサービス", "template_body": "✨ {title}\n\n{caption}\n\n{cta}\n{url}\n\n{hashtags}", "is_default": False, "is_builtin": True},
    {"template_id": "travel_spot", "name": "スポット紹介", "category": "travel", "description": "旅先やスポット", "template_body": "📍 {location}\n\n{caption}\n\n{hashtags}", "is_default": True, "is_builtin": True},
    {"template_id": "travel_diary", "name": "旅行記", "category": "travel", "description": "旅の記録", "template_body": "{title}\n\n{caption}\n\n{hashtags}", "is_default": False, "is_builtin": True},
    {"template_id": "custom_free", "name": "カスタムテンプレート", "category": "custom", "description": "自由設定用", "template_body": "{title}\n\n{caption}\n\n{hashtags}", "is_default": True, "is_builtin": True},
)

ALLOWED_TEMPLATE_VARIABLES: set[str] = {
    "title", "caption", "hashtags", "account_name", "url",
    "pet_name", "species", "breed",
    "dish_name", "ingredients", "cooking_time",
    "shop_name", "address", "phone", "business_hours", "regular_holiday", "access", "reservation_url", "product_name", "price", "campaign",
    "company_name", "brand_name", "event_name", "service_name", "event_date", "cta",
    "location", "facility_name", "visit_date",
}


def builtin_templates_for(category: Category) -> list[dict[str, object]]:
    return [template for template in BUILTIN_TEMPLATES if template["category"] == category]


def default_template_for(category: Category) -> dict[str, object]:
    return next(template for template in builtin_templates_for(category) if template["is_default"])
