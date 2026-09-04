export type Category = "pet" | "food" | "restaurant" | "pr" | "travel" | "custom";

export type CategoryField = {
  key: string;
  label: string;
  placeholder: string;
  kind?: "text" | "textarea";
  required?: boolean;
};

export type CategoryConfig = {
  label: string;
  description: string;
  fields: CategoryField[];
  styles: Array<{ value: string; label: string }>;
};

const commonStyles = [
  { value: "auto", label: "AIおまかせ" },
  { value: "friendly", label: "親しみやすい" },
  { value: "casual", label: "カジュアル" },
  { value: "simple", label: "シンプル" },
  { value: "polite", label: "丁寧" },
];

export const CATEGORY_CONFIG: Record<Category, CategoryConfig> = {
  pet: {
    label: "ペット",
    description: "愛犬・愛猫の日常やお出かけ",
    fields: [
      { key: "name", label: "名前", placeholder: "例：ココ", required: true },
      { key: "species", label: "種類", placeholder: "例：犬" },
      { key: "breed", label: "犬種・猫種", placeholder: "例：トイプードル" },
      { key: "sex", label: "性別", placeholder: "例：女の子" },
      { key: "personality", label: "性格", placeholder: "例：元気で食いしん坊", kind: "textarea" },
    ],
    styles: [
      { value: "auto", label: "おまかせ" },
      { value: "cute", label: "かわいい" },
      { value: "funny", label: "面白い" },
      { value: "diary", label: "日記風" },
      { value: "simple", label: "シンプル" },
      { value: "owner", label: "飼い主目線" },
      { value: "dog", label: "本人目線" },
    ],
  },
  food: {
    label: "料理・レシピ",
    description: "料理記録やレシピ紹介",
    fields: [
      { key: "account_name", label: "アカウント名", placeholder: "例：簡単おうちごはん", required: true },
      { key: "cuisine", label: "料理ジャンル", placeholder: "例：時短料理" },
      { key: "theme", label: "投稿テーマ", placeholder: "例：忙しい人向けの夕食" },
      { key: "audience", label: "想定読者", placeholder: "例：忙しい会社員" },
      { key: "dish_name", label: "料理名", placeholder: "例：トマトパスタ" },
      { key: "ingredients", label: "主な材料", placeholder: "入力した内容だけ反映します" },
      { key: "cooking_time", label: "調理時間", placeholder: "例：15分" },
      { key: "cooking_point", label: "調理ポイント", placeholder: "例：フライパンひとつ", kind: "textarea" },
    ],
    styles: commonStyles,
  },
  restaurant: {
    label: "飲食店",
    description: "店舗公式のメニュー・お知らせ",
    fields: [
      { key: "shop_name", label: "店名", placeholder: "例：ABC Kitchen", required: true },
      { key: "industry", label: "業種", placeholder: "例：イタリアン" },
      { key: "address", label: "住所", placeholder: "登録した値だけ表示します" },
      { key: "phone", label: "電話番号", placeholder: "登録した値だけ表示します" },
      { key: "business_hours", label: "営業時間", placeholder: "例：11:00〜21:00" },
      { key: "regular_holiday", label: "定休日", placeholder: "例：火曜日" },
      { key: "access", label: "アクセス", placeholder: "例：駅から徒歩5分" },
      { key: "url", label: "Webサイト", placeholder: "https://..." },
      { key: "reservation_url", label: "予約URL", placeholder: "https://..." },
      { key: "product_name", label: "料理・商品名", placeholder: "例：夏限定冷製パスタ" },
      { key: "price", label: "価格", placeholder: "例：1,200円" },
      { key: "campaign", label: "キャンペーン内容", placeholder: "例：8月限定", kind: "textarea" },
    ],
    styles: [
      { value: "auto", label: "おまかせ" },
      { value: "recommend", label: "おすすめ紹介" },
      { value: "premium", label: "高級感" },
      { value: "friendly", label: "親しみやすい" },
      { value: "simple", label: "シンプル" },
    ],
  },
  pr: {
    label: "企業・広報",
    description: "企業・ブランドの公式発信",
    fields: [
      { key: "account_name", label: "アカウント名", placeholder: "例：株式会社ABC" },
      { key: "company_name", label: "企業名", placeholder: "例：株式会社ABC" },
      { key: "brand_name", label: "ブランド名", placeholder: "例：ABCブランド" },
      { key: "industry", label: "業種", placeholder: "例：食品メーカー" },
      { key: "service_overview", label: "サービス概要", placeholder: "サービスの説明", kind: "textarea" },
      { key: "target", label: "ターゲット", placeholder: "例：子育て世代" },
      { key: "url", label: "公式サイト", placeholder: "https://..." },
      { key: "event_name", label: "イベント名", placeholder: "例：新商品発表会" },
      { key: "product_name", label: "商品名", placeholder: "例：新商品ABC" },
      { key: "service_name", label: "サービス名", placeholder: "例：ABC Cloud" },
      { key: "event_date", label: "開催日", placeholder: "例：2026年9月1日" },
      { key: "cta", label: "CTA", placeholder: "例：詳しくは公式サイトへ", kind: "textarea" },
    ],
    styles: [
      { value: "auto", label: "おまかせ" },
      { value: "official", label: "公式" },
      { value: "casual", label: "カジュアル広報" },
      { value: "recruit", label: "採用広報" },
      { value: "expert", label: "専門的" },
      { value: "simple", label: "シンプル" },
    ],
  },
  travel: {
    label: "旅行・お出かけ",
    description: "旅先やお出かけの記録",
    fields: [
      { key: "account_name", label: "アカウント名", placeholder: "例：週末おでかけ日記", required: true },
      { key: "theme", label: "アカウントテーマ", placeholder: "例：犬と行ける旅" },
      { key: "travel_style", label: "旅行スタイル", placeholder: "例：週末の日帰り旅" },
      { key: "area", label: "主なエリア", placeholder: "例：関東" },
      { key: "audience", label: "想定読者", placeholder: "例：家族旅行を探す人" },
      { key: "location", label: "場所", placeholder: "入力した場所だけ使用します" },
      { key: "facility_name", label: "施設名", placeholder: "入力した施設名だけ使用します" },
      { key: "visit_date", label: "訪問日", placeholder: "例：2026年8月10日" },
      { key: "impression", label: "感想", placeholder: "印象に残ったこと", kind: "textarea" },
      { key: "recommendation", label: "おすすめポイント", placeholder: "おすすめポイント", kind: "textarea" },
      { key: "transport", label: "交通情報", placeholder: "入力した情報だけ使用します" },
    ],
    styles: commonStyles,
  },
  custom: {
    label: "自由設定",
    description: "テーマを自由に決めて使う汎用カテゴリ",
    fields: [
      { key: "account_name", label: "アカウント名", placeholder: "例：わたしの記録", required: true },
      { key: "theme", label: "アカウントのテーマ", placeholder: "例：日々の小さな発見", required: true },
      { key: "purpose", label: "投稿の目的", placeholder: "例：活動を知ってもらう" },
      { key: "audience", label: "想定読者", placeholder: "例：同じ趣味の人" },
      { key: "tone", label: "文章トーン", placeholder: "例：丁寧で親しみやすく" },
      { key: "supplement", label: "補足情報", placeholder: "AIに伝えたい補足", kind: "textarea" },
    ],
    styles: commonStyles,
  },
};

export const CATEGORY_OPTIONS = (Object.keys(CATEGORY_CONFIG) as Category[]).map((value) => ({
  value,
  label: CATEGORY_CONFIG[value].label,
}));
