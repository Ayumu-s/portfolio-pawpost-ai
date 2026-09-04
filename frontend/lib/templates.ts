import type { Category } from "./categories";

export type TemplateConfig = {
  template_id: string;
  name: string;
  category: Category;
  description: string;
  template_body: string;
  is_default: boolean;
  is_builtin: boolean;
};

export type PersistedTemplate = TemplateConfig & {
  created_at: string;
  updated_at: string;
};

export const BUILTIN_TEMPLATES: TemplateConfig[] = [
  { template_id: "pet_daily", name: "日常投稿", category: "pet", description: "ペットの日常", template_body: "{caption}\n\n{hashtags}", is_default: true, is_builtin: true },
  { template_id: "pet_outing", name: "お出かけ", category: "pet", description: "散歩やお出かけ", template_body: "🐾 {title}\n\n{caption}\n\n{hashtags}", is_default: false, is_builtin: true },
  { template_id: "food_recipe", name: "レシピ紹介", category: "food", description: "料理やレシピ", template_body: "🍳 {title}\n\n{caption}\n\n{hashtags}", is_default: true, is_builtin: true },
  { template_id: "food_daily", name: "今日のごはん", category: "food", description: "料理記録", template_body: "今日のごはん：{title}\n\n{caption}\n\n{hashtags}", is_default: false, is_builtin: true },
  { template_id: "restaurant_store_info", name: "店舗情報付き", category: "restaurant", description: "店舗情報を固定表示", template_body: "🍽 {title}\n\n{caption}\n\n────────────\n🏠 {shop_name}\n📍 {address}\n📞 {phone}\n🕐 {business_hours}\n🔗 {url}\n\n{hashtags}", is_default: true, is_builtin: true },
  { template_id: "restaurant_new_menu", name: "新メニュー紹介", category: "restaurant", description: "新商品・新メニュー", template_body: "✨ NEW MENU ✨\n\n{title}\n\n{caption}\n\n価格：{price}\n\n────────────\n🏠 {shop_name}\n📍 {address}\n📞 {phone}\n\n{hashtags}", is_default: false, is_builtin: true },
  { template_id: "restaurant_campaign", name: "キャンペーン", category: "restaurant", description: "期間限定やキャンペーン", template_body: "📣 {title}\n\n{caption}\n\n{campaign}\n\n{hashtags}", is_default: false, is_builtin: true },
  { template_id: "pr_announcement", name: "お知らせ", category: "pr", description: "企業からのお知らせ", template_body: "【{title}】\n\n{caption}\n\n詳しくはこちら\n{url}\n\n{hashtags}", is_default: true, is_builtin: true },
  { template_id: "pr_event", name: "イベント告知", category: "pr", description: "イベントや開催案内", template_body: "📢 {title}\n\n{caption}\n\n開催日：{event_date}\n{url}\n\n{hashtags}", is_default: false, is_builtin: true },
  { template_id: "pr_product", name: "商品・サービス紹介", category: "pr", description: "商品やサービス", template_body: "✨ {title}\n\n{caption}\n\n{cta}\n{url}\n\n{hashtags}", is_default: false, is_builtin: true },
  { template_id: "travel_spot", name: "スポット紹介", category: "travel", description: "旅先やスポット", template_body: "📍 {location}\n\n{caption}\n\n{hashtags}", is_default: true, is_builtin: true },
  { template_id: "travel_diary", name: "旅行記", category: "travel", description: "旅の記録", template_body: "{title}\n\n{caption}\n\n{hashtags}", is_default: false, is_builtin: true },
  { template_id: "custom_free", name: "カスタムテンプレート", category: "custom", description: "自由設定用", template_body: "{title}\n\n{caption}\n\n{hashtags}", is_default: true, is_builtin: true },
];

export const templateOptionsFor = (category: Category) => BUILTIN_TEMPLATES.filter((template) => template.category === category);
