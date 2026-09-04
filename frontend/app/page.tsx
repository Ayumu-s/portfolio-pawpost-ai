"use client";

import { ChangeEvent, DragEvent, FormEvent, TouchEvent, useEffect, useMemo, useRef, useState } from "react";
import { CATEGORY_CONFIG, CATEGORY_OPTIONS, Category } from "../lib/categories";
import { PersistedTemplate, TemplateConfig, templateOptionsFor } from "../lib/templates";

type Provider = "mock";
type MediaType = "single_image" | "multi_image" | "video";
type Style = "auto" | "cute" | "funny" | "diary" | "simple" | "owner" | "dog" | "friendly" | "casual" | "polite" | "recommend" | "premium" | "official" | "recruit" | "expert";
type Voice = "owner" | "dog";
type CaptionLength = "one_liner" | "short" | "standard" | "detailed" | "long";

type GeneratedPost = {
  caption: string;
  hashtags: string[];
  image_description: string;
  title?: string;
  rendered_post?: string;
  template_id?: string;
  category?: Category;
  account_name?: string;
  style: Style;
  caption_length?: CaptionLength;
  caption_char_count?: number;
  hashtag_count?: number;
  media_type?: MediaType;
  media_count?: number;
  video_frame_count?: number;
  providers: { image: Provider; text: Provider };
};

function getApiBase() {
  if (process.env.NEXT_PUBLIC_API_BASE_URL) return process.env.NEXT_PUBLIC_API_BASE_URL;
  if (typeof window === "undefined") return "http://localhost:8000";
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_BASE = getApiBase();
const MAX_IMAGE_SIZE = 15 * 1024 * 1024;
const MAX_MEDIA_IMAGES = 10;
const MAX_VIDEO_SIZE = 100 * 1024 * 1024;
const VIDEO_ACCEPT = "video/mp4,video/quicktime,video/webm,video/x-m4v,.mp4,.mov,.webm,.m4v";
const VIDEO_EXTENSIONS = [".mp4", ".mov", ".webm", ".m4v"];
const ACCEPTED_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/heic",
  "image/heif",
  "image/heic-sequence",
  "image/heif-sequence",
]);
const ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"];
const HEIC_TYPES = new Set([
  "image/heic",
  "image/heif",
  "image/heic-sequence",
  "image/heif-sequence",
]);

function fileExtension(file: File) {
  const name = file.name.toLowerCase();
  const lastDot = name.lastIndexOf(".");
  return lastDot >= 0 ? name.slice(lastDot) : "";
}

function isHeicFile(file: File) {
  return HEIC_TYPES.has(file.type.toLowerCase()) || [".heic", ".heif"].includes(fileExtension(file));
}

function isSupportedImageFile(file: File) {
  return ACCEPTED_TYPES.has(file.type.toLowerCase()) || ACCEPTED_EXTENSIONS.includes(fileExtension(file));
}

function isSupportedVideoFile(file: File) {
  return (
    (file.type.toLowerCase().startsWith("video/") && VIDEO_EXTENSIONS.includes(fileExtension(file)))
    || VIDEO_EXTENSIONS.includes(fileExtension(file))
  );
}

async function convertHeicToJpeg(file: File): Promise<File> {
  const { default: heic2any } = await import("heic2any");
  const converted = await heic2any({ blob: file, toType: "image/jpeg", quality: 0.9 });
  const jpegBlob = Array.isArray(converted) ? converted[0] : converted;
  const baseName = file.name.replace(/\.(heic|heif)$/i, "") || "photo";
  return new File([jpegBlob], `${baseName}.jpg`, { type: "image/jpeg", lastModified: Date.now() });
}

const providerLabels: Record<Provider, string> = {
  mock: "Mock / デモ",
};
const providerOptions: Provider[] = ["mock"];

const captionLengthOptions: Array<{
  value: CaptionLength;
  label: string;
  range: string;
  description: string;
}> = [
  { value: "one_liner", label: "一言", range: "30〜60文字", description: "写真を主役にした短い投稿" },
  { value: "short", label: "短め", range: "60〜100文字", description: "日常の一コマを簡潔に" },
  { value: "standard", label: "標準", range: "100〜160文字", description: "おすすめ。出来事と気持ちを自然に" },
  { value: "detailed", label: "しっかり", range: "160〜250文字", description: "出来事を少し詳しく残す" },
  { value: "long", label: "長め", range: "250〜400文字", description: "旅行・誕生日・思い出など" },
];

const hashtagCountOptions = [3, 4, 5] as const;

type RestaurantDemoSample = {
  id: string;
  label: string;
  meta: string;
  src: string;
  fileName: string;
  productName: string;
  price: string;
  campaign: string;
  note: string;
  hashtags: string;
};

const RESTAURANT_DEMO_PROFILE: Record<string, string> = {
  shop_name: "小皿食堂 ひより",
  industry: "季節の料理とカフェ",
  address: "東京都〇〇区 ひより通り1-2-3",
  phone: "03-0000-0000",
  business_hours: "11:00〜20:00",
  regular_holiday: "火曜日",
  access: "駅から徒歩5分",
  product_name: "自家製トマトバジルパスタ",
  price: "1,280円",
  campaign: "自家製ソースで仕上げる季節のおすすめ",
};

const RESTAURANT_DEMO_SAMPLES: RestaurantDemoSample[] = [
  {
    id: "pasta",
    label: "トマトバジルパスタ",
    meta: "季節のおすすめ",
    src: "/demo/restaurant/restaurant-pasta.png",
    fileName: "restaurant-pasta.png",
    productName: "自家製トマトバジルパスタ",
    price: "1,280円",
    campaign: "自家製ソースで仕上げる季節のおすすめ",
    note: "自家製トマトソースとバジルが香る、ランチのおすすめです。",
    hashtags: "#自家製パスタ #東京ランチ",
  },
  {
    id: "lunch",
    label: "季節のランチプレート",
    meta: "ランチメニュー",
    src: "/demo/restaurant/restaurant-lunch.png",
    fileName: "restaurant-lunch.png",
    productName: "香草チキンの季節ランチ",
    price: "1,480円",
    campaign: "旬の野菜を楽しむ季節のランチフェア",
    note: "彩り野菜と香草チキンを一皿で楽しめる、今日のランチです。",
    hashtags: "#季節のランチ #東京グルメ",
  },
  {
    id: "parfait",
    label: "抹茶と果実のパフェ",
    meta: "カフェメニュー",
    src: "/demo/restaurant/restaurant-matcha-parfait.png",
    fileName: "restaurant-matcha-parfait.png",
    productName: "抹茶と果実の季節パフェ",
    price: "980円",
    campaign: "午後のひと休みに楽しむ季節のデザート",
    note: "抹茶の香りと旬の果実を重ねた、午後におすすめのパフェです。",
    hashtags: "#季節のパフェ #カフェ巡り",
  },
];

function normalizeHashtagPreview(value: string) {
  const unique: string[] = [];
  const seen = new Set<string>();
  value
    .split(/[\s,、，]+/)
    .filter(Boolean)
    .forEach((tag) => {
      const normalized = tag.startsWith("#") || tag.startsWith("＃") ? tag : `#${tag}`;
      const key = normalized.slice(1).toLocaleLowerCase();
      if (!key || seen.has(key)) return;
      seen.add(key);
      unique.push(normalized.replace(/^＃/, "#"));
    });
  return unique;
}

function extractTemplateHashtagsPreview(templateBody: string) {
  return normalizeHashtagPreview((templateBody.match(/#[^\s#{}]+/g) || []).join(" "));
}

type IconName =
  | "heart" | "comment" | "send" | "bookmark" | "photo"
  | "sliders" | "smile" | "note" | "minus" | "home" | "diamond"
  | "users" | "book" | "megaphone" | "pin" | "edit" | "utensils"
  | "store" | "badge";

const CATEGORY_ICONS: Record<Exclude<Category, "pet">, IconName> = {
  food: "utensils",
  restaurant: "store",
  pr: "megaphone",
  travel: "pin",
  custom: "edit",
};

const STYLE_ICONS: Record<string, IconName> = {
  auto: "sliders",
  friendly: "heart",
  cute: "heart",
  funny: "smile",
  casual: "smile",
  diary: "note",
  polite: "note",
  simple: "minus",
  owner: "home",
  recommend: "badge",
  premium: "diamond",
  official: "diamond",
  recruit: "users",
  expert: "book",
};

const TEMPLATE_CACHE_KEY = "pawpost-custom-templates-v2";
const LEGACY_TEMPLATE_KEY = "pawpost-custom-template";

function readTemplateCache(): PersistedTemplate[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(TEMPLATE_CACHE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeTemplateCache(templates: PersistedTemplate[]) {
  try {
    localStorage.setItem(TEMPLATE_CACHE_KEY, JSON.stringify(templates));
  } catch {
    // Backend remains the source of truth when browser storage is unavailable.
  }
}

function renderTemplateClient(
  templateBody: string,
  values: Record<string, string>,
  fixedHashtags: string[] = [],
  aiHashtags: string[] = [],
) {
  const templateFixedHashtags = fixedHashtags.length
    ? fixedHashtags
    : extractTemplateHashtagsPreview(templateBody);
  const providedHashtags = normalizeHashtagPreview(values.hashtags || "");
  const fixedKeys = new Set(templateFixedHashtags.map((tag) => tag.slice(1).toLocaleLowerCase()));
  const dynamicHashtags = aiHashtags.length
    ? aiHashtags
    : providedHashtags.filter((tag) => !fixedKeys.has(tag.slice(1).toLocaleLowerCase()));
  const renderValues = templateFixedHashtags.length
    ? { ...values, hashtags: dynamicHashtags.join(" ") }
    : values;
  const renderedLines = templateBody.split(/\r?\n/).flatMap((line) => {
    const variables = [...line.matchAll(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g)].map((match) => match[1]);
    if (variables.length && variables.every((key) => !renderValues[key]?.trim())) return [];
    const rendered = line.replace(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g, (_, key: string) => renderValues[key] || "");
    if (rendered.trim() === "────────────") return [];
    return [rendered];
  });
  const output: string[] = [];
  renderedLines.forEach((line) => {
    if (!line.trim() && (!output.length || !output[output.length - 1].trim())) return;
    output.push(line.trimEnd());
  });
  while (output.length && !output[output.length - 1].trim()) output.pop();

  if (templateFixedHashtags.length && dynamicHashtags.length && !templateBody.includes("{hashtags}")) {
    let targetIndex = -1;
    output.forEach((line, index) => {
      const lineTags = normalizeHashtagPreview(line);
      if (lineTags.some((tag) => fixedKeys.has(tag.slice(1).toLocaleLowerCase()))) targetIndex = index;
    });
    const dynamicText = dynamicHashtags.join(" ");
    if (targetIndex >= 0) output[targetIndex] = `${output[targetIndex].trimEnd()} ${dynamicText}`;
    else output.push(dynamicText);
  }
  return output.join("\n");
}

const ALLOWED_TEMPLATE_VARIABLES = new Set([
  "title", "caption", "hashtags", "account_name", "url", "pet_name", "species", "breed",
  "dish_name", "ingredients", "cooking_time", "shop_name", "address", "phone", "business_hours",
  "regular_holiday", "access", "reservation_url", "product_name", "price", "campaign", "company_name",
  "brand_name", "event_name", "service_name", "event_date", "cta", "location", "facility_name", "visit_date",
]);

function invalidTemplateVariables(body: string) {
  return [...new Set([...body.matchAll(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g)].map((match) => match[1]))]
    .filter((variable) => !ALLOWED_TEMPLATE_VARIABLES.has(variable));
}

function PawMark({ small = false }: { small?: boolean }) {
  return (
    <svg className={small ? "paw-mark small" : "paw-mark"} viewBox="0 0 56 56" aria-hidden="true">
      <ellipse cx="28" cy="36" rx="14" ry="12" />
      <ellipse cx="13" cy="25" rx="6" ry="8" transform="rotate(-24 13 25)" />
      <ellipse cx="23" cy="14" rx="6" ry="8" transform="rotate(-8 23 14)" />
      <ellipse cx="35" cy="14" rx="6" ry="8" transform="rotate(8 35 14)" />
      <ellipse cx="44" cy="25" rx="6" ry="8" transform="rotate(24 44 25)" />
    </svg>
  );
}

function Icon({ name }: { name: IconName }) {
  const paths = {
    heart: <path d="M12 21s-8-4.7-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 6.3-8 11-8 11Z" />,
    comment: <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 10 10 0 0 1-3.9-.8L3 21l1.8-4.4A8.7 8.7 0 1 1 21 11.5Z" />,
    send: <path d="m22 2-7.2 20-4.1-8.7L2 9.2 22 2Zm-11.3 11.3L15.5 9" />,
    bookmark: <path d="M6 3h12v18l-6-4-6 4V3Z" />,
    photo: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="2" /><path d="m21 15-5-5L5 20" /></>,
    sparkle: <><path d="M12 2c.5 5.3 2.7 7.5 8 8-5.3.5-7.5 2.7-8 8-.5-5.3-2.7-7.5-8-8 5.3-.5 7.5-2.7 8-8Z" /><path d="M19 17c.2 2 1 2.8 3 3-2 .2-2.8 1-3 3-.2-2-1-2.8-3-3 2-.2 2.8-1 3-3Z" /></>,
    sliders: <><path d="M4 6h16" /><path d="M4 12h16" /><path d="M4 18h16" /><circle cx="9" cy="6" r="2" fill="currentColor" stroke="none" /><circle cx="15" cy="12" r="2" fill="currentColor" stroke="none" /><circle cx="11" cy="18" r="2" fill="currentColor" stroke="none" /></>,
    smile: <><circle cx="12" cy="12" r="9" /><path d="M8 14s1.3 2 4 2 4-2 4-2" /><path d="M9 9h.01M15 9h.01" /></>,
    note: <><path d="M6 3h9l3 3v15H6z" /><path d="M9 12h6M9 16h6" /></>,
    minus: <path d="M5 12h14" />,
    home: <path d="m4 11 8-7 8 7v9H4v-9Z" />,
    diamond: <path d="m12 3 8 9-8 9-8-9 8-9Z" />,
    users: <><circle cx="9" cy="9" r="3" /><path d="M3 20a6 6 0 0 1 12 0" /><path d="M16 6.5a3 3 0 0 1 0 5.8M17 15a5 5 0 0 1 4 5" /></>,
    book: <><path d="M5 4h10a4 4 0 0 1 4 4v12H9a4 4 0 0 0-4 0V4Z" /><path d="M9 20V8a4 4 0 0 1 4-4" /></>,
    megaphone: <><path d="m4 11 15-5v12L4 13v-2Z" /><path d="M8 14.5 9.5 20" /></>,
    pin: <><path d="M12 21s6-5.2 6-10a6 6 0 1 0-12 0c0 4.8 6 10 6 10Z" /><circle cx="12" cy="11" r="2" /></>,
    edit: <><path d="m4 16.5-.8 4.3 4.3-.8L19 8.5l-3-3L4 16.5Z" /><path d="m14.5 6.5 3 3" /></>,
    utensils: <><path d="M7 3v7M4.5 3v4.5a2.5 2.5 0 0 0 5 0V3M7 10v11" /><path d="M16 3v18M16 3c2.2 1.7 3 4 3 7h-3" /></>,
    store: <><path d="M4 10h16l-1-5H5l-1 5Z" /><path d="M5 10v10h14V10M9 20v-6h6v6" /><path d="M3 10a2 2 0 0 0 4 0 2 2 0 0 0 4 0 2 2 0 0 0 4 0 2 2 0 0 0 4 0" /></>,
    badge: <><path d="m12 3 2 1 2.2-.2 1.4 1.8 2 .9-.1 2.3 1 2-1 2 .1 2.3-2 .9-1.4 1.8-2.2-.2-2 1-2-1-2.2.2L6.4 18l-2-.9.1-2.3-1-2 1-2-.1-2.3 2-.9L7.8 4 10 4.2l2-1Z" /><path d="m9 12 2 2 4-4" /></>,
  };
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

function CategoryIcon({ category }: { category: Category }) {
  return category === "pet" ? <PawMark small /> : <Icon name={CATEGORY_ICONS[category]} />;
}

function StyleIcon({ value }: { value: string }) {
  return value === "dog" ? <PawMark small /> : <Icon name={STYLE_ICONS[value] || "note"} />;
}

function InstagramPreview({
  dogName,
  accountName,
  category,
  imageUrl,
  imageUrls,
  mediaType,
  videoUrl,
  caption,
  renderedPost,
  hashtags,
  generated,
}: {
  dogName: string;
  accountName: string;
  category: Category;
  imageUrl: string;
  imageUrls: string[];
  mediaType: MediaType;
  videoUrl: string;
  caption: string;
  renderedPost: string;
  hashtags: string[];
  generated: boolean;
}) {
  const account = accountName.trim() || (dogName.trim() ? dogName.trim() + "のまいにち" : "投稿アカウント");
  const displayPost = renderedPost.trim() || [caption, hashtags.join(" ")].filter(Boolean).join("\n\n");
  const [activeIndex, setActiveIndex] = useState(0);
  const [touchStartX, setTouchStartX] = useState<number | null>(null);
  const isCarousel = mediaType === "multi_image" && imageUrls.length > 1;
  const activeImageUrl = imageUrls[activeIndex] || imageUrl;

  useEffect(() => {
    setActiveIndex(0);
  }, [mediaType, imageUrls, videoUrl]);

  const moveCarousel = (direction: number) => {
    if (!isCarousel) return;
    setActiveIndex((current) => (current + direction + imageUrls.length) % imageUrls.length);
  };

  const handleTouchStart = (event: TouchEvent<HTMLDivElement>) => {
    setTouchStartX(event.changedTouches[0]?.clientX ?? null);
  };

  const handleTouchEnd = (event: TouchEvent<HTMLDivElement>) => {
    if (touchStartX === null) return;
    const endX = event.changedTouches[0]?.clientX ?? touchStartX;
    const distance = endX - touchStartX;
    if (Math.abs(distance) > 36) moveCarousel(distance < 0 ? 1 : -1);
    setTouchStartX(null);
  };

  return (
    <section className="preview-wrap" aria-label="Instagram投稿プレビュー">
      <div className="preview-heading">
        <div>
          <span className="eyebrow">リアルタイム表示</span>
          <h2>投稿の仕上がり</h2>
        </div>
        <span className={`preview-status ${generated ? "done" : ""}`}>
          <i /> {generated ? "生成済み" : "入力にあわせて更新"}
        </span>
      </div>

      <article className="insta-card">
        <header className="insta-header">
          <div className="avatar">
            <span className="category-avatar-icon"><CategoryIcon category={category} /></span>
          </div>
          <div><strong>{account}</strong><span>投稿案のプレビュー</span></div>
          <button className="dots" type="button" aria-label="その他">•••</button>
        </header>

        <div
          className={`insta-image ${imageUrl || imageUrls.length || videoUrl ? "has-photo" : ""} ${isCarousel ? "is-carousel" : ""}`}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {mediaType === "video" && videoUrl ? (
            <video className="insta-video" src={videoUrl} controls muted playsInline aria-label={`${dogName || "投稿"}の動画プレビュー`} />
          ) : activeImageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <>
            <img src={activeImageUrl} alt={`${dogName || "投稿"}の写真 ${activeIndex + 1} プレビュー`} />
              {isCarousel && (
                <>
                  <span className="media-count-badge" aria-live="polite">{activeIndex + 1} / {imageUrls.length}</span>
                  <button className="carousel-control previous" type="button" onClick={() => moveCarousel(-1)} aria-label="前の写真">‹</button>
                  <button className="carousel-control next" type="button" onClick={() => moveCarousel(1)} aria-label="次の写真">›</button>
                  <div className="carousel-dots" role="tablist" aria-label="プレビュー写真の選択">
                    {imageUrls.map((url, index) => (
                      <button
                        key={`${url}-dot`}
                        type="button"
                        className={activeIndex === index ? "active" : ""}
                        role="tab"
                        aria-selected={activeIndex === index}
                        aria-label={`${index + 1}枚目を表示`}
                        onClick={() => setActiveIndex(index)}
                      />
                    ))}
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="photo-placeholder">
              <div className="placeholder-sun" />
              <div className="placeholder-hill hill-back" />
              <div className="placeholder-hill hill-front" />
              <PawMark />
              <strong>ここに、とっておきの一枚。</strong>
              <span>写真を選ぶとプレビューできます</span>
            </div>
          )}
        </div>

        <div className="insta-actions">
          <div><Icon name="heart" /><Icon name="comment" /><Icon name="send" /></div>
          <Icon name="bookmark" />
        </div>
        <div className="insta-copy">
          <strong className="likes">すき！ 24件</strong>
          <p className={`preview-rendered ${displayPost ? "" : "muted-copy"}`}>
            {displayPost || "AIが写真を見て、ここにぴったりの言葉をつくります。"}
          </p>
          <time>たった今</time>
        </div>
      </article>
      <p className="preview-note"><span aria-hidden="true" /> Instagramへの実投稿は行いません</p>
    </section>
  );
}

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const fileProcessingRef = useRef(false);
  const [mediaType, setMediaType] = useState<MediaType>("single_image");
  const [category, setCategory] = useState<Category>("restaurant");
  const [profileData, setProfileData] = useState<Record<string, string>>({ ...RESTAURANT_DEMO_PROFILE });
  const [accountName, setAccountName] = useState("");
  const [templateId, setTemplateId] = useState("auto");
  const [customTemplateName, setCustomTemplateName] = useState("");
  const [customTemplate, setCustomTemplate] = useState("");
  const [savedTemplates, setSavedTemplates] = useState<PersistedTemplate[]>([]);
  const [isTemplatesLoading, setIsTemplatesLoading] = useState(true);
  const [templateSaveMessage, setTemplateSaveMessage] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState("");
  const [images, setImages] = useState<File[]>([]);
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [video, setVideo] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [dogName, setDogName] = useState("");
  const [breed, setBreed] = useState("");
  const [sex, setSex] = useState("");
  const [personality, setPersonality] = useState("");
  const [voice, setVoice] = useState<Voice>("owner");
  const [userNote, setUserNote] = useState("自家製トマトソースとバジルが香る、ランチのおすすめです。");
  const [requiredHashtags, setRequiredHashtags] = useState("#自家製パスタ #東京ランチ");
  const [style, setStyle] = useState<Style>("recommend");
  const [captionLength, setCaptionLength] = useState<CaptionLength>("standard");
  const [hashtagCount, setHashtagCount] = useState<number>(5);
  const [imageProvider, setImageProvider] = useState<Provider>("mock");
  const [textProvider, setTextProvider] = useState<Provider>("mock");
  const [result, setResult] = useState<GeneratedPost | null>(null);
  const [editedCaption, setEditedCaption] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [demoSampleId, setDemoSampleId] = useState("");
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  const categoryConfig = CATEGORY_CONFIG[category];
  const categoryTemplates: TemplateConfig[] = [
    ...templateOptionsFor(category),
    ...savedTemplates.filter((template) => template.category === category),
  ];
  const selectedTemplate = categoryTemplates.find((template) => template.template_id === templateId)
    || categoryTemplates.find((template) => template.is_default)
    || categoryTemplates[0];
  const selectedSavedTemplate = savedTemplates.find((template) => template.template_id === templateId);
  const isTemplateEditorOpen = templateId === "custom" || Boolean(selectedSavedTemplate);

  useEffect(() => {
    const cachedTemplates = readTemplateCache();
    if (cachedTemplates.length) setSavedTemplates(cachedTemplates);
    try {
      const saved = JSON.parse(localStorage.getItem(LEGACY_TEMPLATE_KEY) || "{}");
      if (saved && typeof saved === "object") {
        setCustomTemplateName(typeof saved.name === "string" ? saved.name : "");
        setCustomTemplate(typeof saved.body === "string" ? saved.body : "");
      }
    } catch {
      // Ignore malformed local-only settings.
    }

    let active = true;
    fetch(`${API_BASE}/api/templates`)
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then((templates: PersistedTemplate[]) => {
        if (!active || !Array.isArray(templates)) return;
        setSavedTemplates(templates);
        writeTemplateCache(templates);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setIsTemplatesLoading(false);
      });
    return () => { active = false; };
  }, []);

  const updateProfileField = (key: string, value: string) => {
    setProfileData((current) => ({ ...current, [key]: value }));
    if (category === "pet") {
      if (key === "name") setDogName(value);
      if (key === "breed") setBreed(value);
      if (key === "sex") setSex(value);
      if (key === "personality") setPersonality(value);
    }
    if (key === "account_name") setAccountName(value);
  };

  const changeCategory = (next: Category) => {
    setCategory(next);
    // Profile fields are category-scoped; clear the previous category's facts
    // so they cannot leak into the next prompt. Shared post settings remain.
    setProfileData({});
    setAccountName("");
    if (next !== "pet") {
      setDogName("");
      setBreed("");
      setSex("");
      setPersonality("");
      setVoice("owner");
    }
    setTemplateId("auto");
    const nextStyles = CATEGORY_CONFIG[next].styles;
    if (!nextStyles.some((item) => item.value === style)) setStyle("auto");
    setError("");
    clearGeneratedResult();
  };

  const changeTemplate = (nextId: string) => {
    setTemplateId(nextId);
    setTemplateSaveMessage("");
    const saved = savedTemplates.find((template) => template.template_id === nextId);
    if (saved) {
      setCustomTemplateName(saved.name);
      setCustomTemplate(saved.template_body);
    }
  };

  const saveCustomTemplate = async () => {
    const invalidVariables = invalidTemplateVariables(customTemplate);
    if (invalidVariables.length) {
      setTemplateSaveMessage(`使用できない変数: ${invalidVariables.map((variable) => `{${variable}}`).join(", ")}`);
      return;
    }
    if (!customTemplate.trim()) {
      setTemplateSaveMessage("テンプレート本文を入力してください。");
      return;
    }
    const existing = selectedSavedTemplate && selectedSavedTemplate.category === category
      ? selectedSavedTemplate
      : null;
    const endpoint = existing
      ? `${API_BASE}/api/templates/${encodeURIComponent(existing.template_id)}`
      : `${API_BASE}/api/templates`;
    try {
      const response = await fetch(endpoint, {
        method: existing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template_id: existing?.template_id,
          category,
          name: customTemplateName.trim() || "名前なしテンプレート",
          template_body: customTemplate,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "テンプレートを保存できませんでした。");
      const saved = payload as PersistedTemplate;
      const nextTemplates = [...savedTemplates.filter((template) => template.template_id !== saved.template_id), saved];
      setSavedTemplates(nextTemplates);
      writeTemplateCache(nextTemplates);
      setTemplateId(saved.template_id);
      setCustomTemplateName(saved.name);
      setCustomTemplate(saved.template_body);
      setTemplateSaveMessage("サーバーに保存しました");
    } catch (requestError) {
      try {
        localStorage.setItem(LEGACY_TEMPLATE_KEY, JSON.stringify({ name: customTemplateName, body: customTemplate }));
      } catch {
        // Keep the visible error when both persistent paths are unavailable.
      }
      setTemplateSaveMessage(requestError instanceof Error ? `${requestError.message} 端末内の旧保存領域には退避しました。` : "保存できませんでした。");
    }
  };

  const deleteSavedTemplate = async () => {
    if (!selectedSavedTemplate) return;
    if (!window.confirm(`「${selectedSavedTemplate.name}」を削除しますか？`)) return;
    try {
      const response = await fetch(`${API_BASE}/api/templates/${encodeURIComponent(selectedSavedTemplate.template_id)}`, { method: "DELETE" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "テンプレートを削除できませんでした。");
      const nextTemplates = savedTemplates.filter((template) => template.template_id !== selectedSavedTemplate.template_id);
      setSavedTemplates(nextTemplates);
      writeTemplateCache(nextTemplates);
      setTemplateId("auto");
      setCustomTemplateName("");
      setCustomTemplate("");
      setTemplateSaveMessage("削除しました");
    } catch (requestError) {
      setTemplateSaveMessage(requestError instanceof Error ? requestError.message : "削除できませんでした。");
    }
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/config`)
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then((config: { image_provider: Provider; text_provider: Provider }) => {
        setImageProvider(config.image_provider);
        setTextProvider(config.text_provider);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!image) { setImageUrl(""); return; }
    const url = URL.createObjectURL(image);
    setImageUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [image]);

  useEffect(() => {
    const urls = images.map((file) => URL.createObjectURL(file));
    setImageUrls(urls);
    return () => urls.forEach((url) => URL.revokeObjectURL(url));
  }, [images]);

  useEffect(() => {
    if (!video) { setVideoUrl(""); return; }
    const url = URL.createObjectURL(video);
    setVideoUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [video]);

  const requiredTagsPreview = useMemo(
    () => normalizeHashtagPreview(requiredHashtags),
    [requiredHashtags]
  );

  const selectedCaptionLength = captionLengthOptions.find(
    (option) => option.value === captionLength
  ) || captionLengthOptions[2];

  const previewProfileData: Record<string, string> = category === "pet"
    ? { ...profileData, name: dogName, pet_name: dogName, species: profileData.species || "dog", breed, sex, personality, voice }
    : { ...profileData, account_name: accountName || profileData.account_name || "" };
  const previewTemplateBody = templateId === "custom"
    ? customTemplate
    : selectedTemplate?.template_body || "{caption}\n\n{hashtags}";
  const templateHashtagsPreview = extractTemplateHashtagsPreview(previewTemplateBody);
  const effectiveRequiredTagsPreview = normalizeHashtagPreview(
    [...templateHashtagsPreview, ...requiredTagsPreview].join(" ")
  );
  const previewCaption = result ? editedCaption : userNote;
  const previewHashtags = result?.hashtags
    || normalizeHashtagPreview([...templateHashtagsPreview, ...requiredTagsPreview].join(" "));
  const previewAiHashtags = templateHashtagsPreview.length
    ? previewHashtags.filter(
        (tag) => !templateHashtagsPreview.some(
          (fixedTag) => fixedTag.slice(1).toLocaleLowerCase() === tag.slice(1).toLocaleLowerCase()
        )
      )
    : previewHashtags;
  const previewAccountName = accountName
    || previewProfileData.account_name
    || previewProfileData.shop_name
    || previewProfileData.company_name
    || previewProfileData.brand_name
    || (category === "pet" && dogName ? `${dogName}のまいにち` : "");
  const previewValues = {
    ...previewProfileData,
    account_name: previewAccountName,
    title: result?.title || previewCaption.split("。", 1)[0].slice(0, 40),
    caption: previewCaption,
    hashtags: previewAiHashtags.join(" "),
  };
  const renderedPreview = previewCaption || previewHashtags.length
    ? renderTemplateClient(previewTemplateBody, previewValues, templateHashtagsPreview, previewAiHashtags)
    : "";

  const chooseImage = async (file?: File, demoId = "") => {
    if (!file || fileProcessingRef.current || isLoading) return;
    setError("");

    if (!isSupportedImageFile(file)) {
      setError("JPEG / PNG / WebP / HEIC / HEIF の画像を選択してください。");
      return;
    }

    if (file.size > MAX_IMAGE_SIZE) {
      setError("画像サイズは15MB以下にしてください。");
      return;
    }

    fileProcessingRef.current = true;
    const heic = isHeicFile(file);
    setDemoSampleId(demoId);
    // Show the selected file immediately. If an iPhone browser takes a
    // moment to convert HEIC, the user still gets instant visual feedback.
    setImage(file);
    setResult(null);
    setEditedCaption("");
    setIsConverting(heic);
    try {
      const normalizedFile = heic ? await convertHeicToJpeg(file) : file;
      if (normalizedFile.size > MAX_IMAGE_SIZE) {
        setError("画像サイズは15MB以下にしてください。");
        return;
      }
      setImage(normalizedFile);
      setResult(null);
      setEditedCaption("");
    } catch {
      setError("HEIC / HEIF画像をJPEGに変換できませんでした。");
    } finally {
      fileProcessingRef.current = false;
      setIsConverting(false);
    }
  };

  const clearGeneratedResult = () => {
    setResult(null);
    setEditedCaption("");
  };

  const selectRestaurantSample = async (sample: RestaurantDemoSample) => {
    if (fileProcessingRef.current || isLoading || isDemoLoading) return;
    setError("");
    setIsDemoLoading(true);
    try {
      const response = await fetch(sample.src);
      if (!response.ok) throw new Error("sample image request failed");
      const blob = await response.blob();
      const file = new File([blob], sample.fileName, {
        type: blob.type || "image/png",
        lastModified: Date.now(),
      });
      await chooseImage(file, sample.id);
      setProfileData((current) => ({
        ...RESTAURANT_DEMO_PROFILE,
        ...current,
        product_name: sample.productName,
        price: sample.price,
        campaign: sample.campaign,
      }));
      setUserNote(sample.note);
      setRequiredHashtags(sample.hashtags);
      setStyle("recommend");
    } catch {
      setDemoSampleId("");
      setError("サンプル画像を読み込めませんでした。");
    } finally {
      setIsDemoLoading(false);
    }
  };

  useEffect(() => {
    if (category !== "restaurant" || mediaType !== "single_image" || image || isDemoLoading) return;
    void selectRestaurantSample(RESTAURANT_DEMO_SAMPLES[0]);
    // The effect intentionally runs when the public demo context is selected.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, mediaType]);

  const chooseImages = async (files: File[]) => {
    if (fileProcessingRef.current || isLoading) return;
    setError("");
    if (!files.length) return;
    if (files.length > MAX_MEDIA_IMAGES) {
      setError("複数画像は最大10枚まで選択できます。");
      return;
    }
    const invalid = files.find((file) => !isSupportedImageFile(file));
    if (invalid) {
      setError("JPEG / PNG / WebP / HEIC / HEIF の画像を選択してください。");
      return;
    }
    const oversized = files.find((file) => file.size > MAX_IMAGE_SIZE);
    if (oversized) {
      setError("画像サイズは1枚15MB以下にしてください。");
      return;
    }

    fileProcessingRef.current = true;
    setDemoSampleId("");
    setImages(files);
    setImage(null);
    setVideo(null);
    clearGeneratedResult();
    const hasHeic = files.some(isHeicFile);
    setIsConverting(hasHeic);
    try {
      const normalized = await Promise.all(
        files.map((file) => isHeicFile(file) ? convertHeicToJpeg(file) : file)
      );
      if (normalized.some((file) => file.size > MAX_IMAGE_SIZE)) {
        setError("画像サイズは1枚15MB以下にしてください。");
        return;
      }
      setImages(normalized);
    } catch {
      setError("HEIC / HEIF画像をJPEGに変換できませんでした。");
    } finally {
      fileProcessingRef.current = false;
      setIsConverting(false);
    }
  };

  const chooseVideo = (file?: File) => {
    if (!file || isLoading) return;
    setError("");
    if (!isSupportedVideoFile(file)) {
      setError("mp4 / mov / webm / m4v の動画を選択してください。");
      return;
    }
    if (file.size > MAX_VIDEO_SIZE) {
      setError("動画サイズは100MB以下にしてください。");
      return;
    }
    setVideo(file);
    setImage(null);
    setImages([]);
    setDemoSampleId("");
    clearGeneratedResult();
  };

  const changeMediaType = (next: MediaType) => {
    setMediaType(next);
    setError("");
    setImage(null);
    setImages([]);
    setVideo(null);
    setDemoSampleId("");
    clearGeneratedResult();
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (videoInputRef.current) videoInputRef.current.value = "";
  };

  const removeImage = (index: number) => {
    setImages((current) => current.filter((_, currentIndex) => currentIndex !== index));
    clearGeneratedResult();
  };

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (mediaType === "multi_image") void chooseImages(files);
    else void chooseImage(files[0]);

    /*
     * 同じ写真を続けて選択した場合でも
     * onChange が発火するようにリセットする。
     */
    event.target.value = "";
  };

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const files = Array.from(event.dataTransfer.files || []);
    if (mediaType === "multi_image") void chooseImages(files);
    else void chooseImage(files[0]);
  };

  const generate = async (event?: FormEvent) => {
    event?.preventDefault();
    setError("");

    if (mediaType === "single_image" && !image) {
      setError("まず投稿する写真を選択してください。");
      return;
    }
    if (mediaType === "multi_image" && !images.length) {
      setError("複数画像を1枚以上選択してください。");
      return;
    }
    if (mediaType === "video" && !video) {
      setError("まず投稿する動画を選択してください。");
      return;
    }

    const effectiveProfileData: Record<string, string> = category === "pet"
      ? {
          ...profileData,
          name: dogName.trim(),
          species: profileData.species || "dog",
          breed: breed.trim(),
          sex: sex.trim(),
          personality: personality.trim(),
          voice,
        }
      : { ...profileData, account_name: accountName.trim() || profileData.account_name || "" };

    const requiredCategoryFields = categoryConfig.fields.filter((field) => field.required);
    const missingCategoryField = requiredCategoryFields.find((field) => !effectiveProfileData[field.key]?.trim());
    if (missingCategoryField || (category === "pr" && !effectiveProfileData.company_name?.trim() && !effectiveProfileData.brand_name?.trim())) {
      setError(category === "pr" ? "企業名またはブランド名を入力してください。" : `${missingCategoryField?.label || "プロフィール"}を入力してください。`);
      return;
    }

    if (effectiveRequiredTagsPreview.length > 5) {
      setError(templateHashtagsPreview.length
        ? "テンプレート内の固定ハッシュタグと必須ハッシュタグは最大5個まで指定できます。"
        : "ハッシュタグは最大5個まで指定できます。");
      return;
    }

    if (effectiveRequiredTagsPreview.length > hashtagCount) {
      setError(templateHashtagsPreview.length
        ? "テンプレート内の固定ハッシュタグと必須ハッシュタグが設定数を超えています。ハッシュタグ数を増やしてください。"
        : "必須ハッシュタグが設定数を超えています。ハッシュタグ数を増やすか、必須タグを減らしてください。");
      return;
    }

    const templateBody = templateId === "custom" ? customTemplate : selectedTemplate?.template_body || "{caption}\n\n{hashtags}";
    const invalidVariables = invalidTemplateVariables(templateBody);
    if (invalidVariables.length) {
      setError(`使用できないテンプレート変数があります: ${invalidVariables.map((variable) => `{${variable}}`).join(", ")}`);
      return;
    }
    if (templateId === "custom" && !customTemplate.trim()) {
      setError("カスタムテンプレート本文を入力してください。");
      return;
    }
    try {
      localStorage.setItem("pawpost-custom-template", JSON.stringify({ name: customTemplateName, body: customTemplate }));
    } catch {
      // The generation request itself remains usable if localStorage is unavailable.
    }

    const data = new FormData();
    data.append("media_type", mediaType);
    if (mediaType === "single_image" && image) data.append("image", image);
    if (mediaType === "multi_image") images.forEach((file) => data.append("images", file));
    if (mediaType === "video" && video) data.append("video", video);
    data.append("dog_name", dogName.trim());
    data.append("breed", breed.trim());
    data.append("sex", sex.trim());
    data.append("personality", personality.trim());
    data.append("voice", voice);
    data.append("user_note", userNote.trim());
    data.append("required_hashtags", requiredHashtags.trim());
    data.append("style", style);
    data.append("image_provider", imageProvider);
    data.append("text_provider", textProvider);
    data.append("caption_length", captionLength);
    data.append("hashtag_count", String(hashtagCount));
    data.append("category", category);
    data.append("account_name", category === "pet" ? (accountName.trim() || `${dogName.trim()}のまいにち`) : (accountName.trim() || effectiveProfileData.account_name || effectiveProfileData.shop_name || effectiveProfileData.company_name || effectiveProfileData.brand_name || ""));
    data.append("profile_data", JSON.stringify(effectiveProfileData));
    data.append("template_id", templateId);
    data.append("custom_template", customTemplate);
    data.append("custom_template_name", customTemplateName);

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/posts/generate`, {
        method: "POST",
        body: data,
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          payload.detail ||
            "投稿文を生成できませんでした。しばらくしてから再度お試しください。"
        );
      }

      const post = payload as GeneratedPost;
      setResult(post);
      setEditedCaption(post.caption);

      if (window.innerWidth < 960) {
        document
          .getElementById("post-preview")
          ?.scrollIntoView({ behavior: "smooth" });
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "投稿文を生成できませんでした。"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="PawPost AI ホーム">
          <span className="brand-mark"><PawMark small /></span>
          <span><b>PawPost</b><em>AI</em></span>
        </a>
        <span className="mvp-badge">下書きのみ / Mockモード</span>
      </header>

      <div className="paper-rule" />

      <section className="intro" id="top">
        <div className="intro-copy">
          <div className="studio-kicker"><span className="studio-kicker-dot" /> {category === "restaurant" ? "飲食店デモ · 投稿案作成" : "投稿案作成"}</div>
          <span className="eyebrow">AI投稿案作成</span>
          <h1>{category === "restaurant" ? <>料理の一枚から、<br /><i>お店の魅力を伝える。</i></> : <>写真と少しのヒントから、<br /><i>AIが投稿文をつくる。</i></>}</h1>
          <div className="intro-signals" aria-label="投稿作成の特徴">
            <span><b>01</b> 写真・動画</span>
            <span><b>02</b> AIで生成</span>
            <span><b>03</b> その場で編集</span>
          </div>
        </div>
        <div className="intro-side">
          {category === "restaurant" ? (
            <p>架空の料理サンプルを最初から用意。<br />店舗情報を整えて、投稿案の流れをその場で確認できます。</p>
          ) : (
            <p>カテゴリやスタイルを選んで、投稿案を生成。<br />できあがった文章は、その場で自由に編集できます。</p>
          )}
        </div>
      </section>

      <div className="workspace">
        <form className="editor" onSubmit={generate}>
          <div className="workflow-strip" aria-label="投稿作成の流れ">
            <div className="workflow-title"><span className="status-pulse" /> 投稿フロー</div>
            <div className="workflow-steps">
              <span className="workflow-step active"><b>01</b>素材</span>
              <span className="workflow-line" />
              <span className="workflow-step"><b>02</b>生成</span>
              <span className="workflow-line" />
              <span className="workflow-step"><b>03</b>編集</span>
            </div>
            <span className="workflow-note">下書きまで。実投稿はしません。</span>
          </div>
          <section className="editor-section category-section">
            <div className="section-title">
              <span>00</span>
              <div>
                <h2>投稿カテゴリ</h2>
                <p>{categoryConfig.description}</p>
              </div>
            </div>
            <div className="category-grid" role="list" aria-label="投稿カテゴリ">
              {CATEGORY_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={category === option.value ? "active" : ""}
                  aria-pressed={category === option.value}
                  aria-label={option.label}
                  onClick={() => changeCategory(option.value)}
                >
                  <span className="category-icon"><CategoryIcon category={option.value} /></span>{option.label}
                </button>
              ))}
            </div>
          </section>

          <section className="editor-section photo-section">
            <div className="section-title">
              <span>01</span>
              <div>
                <h2>{mediaType === "video" ? "とっておきの動画" : mediaType === "multi_image" ? "とっておきの写真" : "とっておきの一枚"}</h2>
                <p>{mediaType === "video" ? "MP4・MOV・WebM / 100MBまで" : mediaType === "multi_image" ? "JPEG・PNG・WebP・HEIC・HEIF / 最大10枚" : "JPEG・PNG・WebP・HEIC・HEIF / 15MBまで"}</p>
              </div>
            </div>

            <div className="media-mode-grid" aria-label="投稿メディアの種類">
              {([
                ["single_image", "写真1枚"],
                ["multi_image", "写真複数"],
                ["video", "動画"],
              ] as Array<[MediaType, string]>).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={mediaType === value ? "active" : ""}
                  aria-pressed={mediaType === value}
                  onClick={() => changeMediaType(value)}
                >
                  {label}
                </button>
              ))}
            </div>

            {category === "restaurant" && mediaType === "single_image" && (
              <div className="demo-samples" aria-label="飲食店デモのサンプル">
                <div className="demo-samples-heading">
                  <div>
                    <span className="demo-samples-kicker">公開デモ / RESTAURANT</span>
                    <strong>サンプルでそのまま試す</strong>
                  </div>
                  <small>画像を選ばなくても、料理写真と店舗情報をセットできます</small>
                </div>
                <div className="demo-sample-grid">
                  {RESTAURANT_DEMO_SAMPLES.map((sample) => (
                    <button
                      type="button"
                      key={sample.id}
                      className={`demo-sample ${demoSampleId === sample.id ? "active" : ""}`}
                      onClick={() => void selectRestaurantSample(sample)}
                      disabled={isDemoLoading || isLoading}
                    >
                      <span className="demo-sample-image">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={sample.src} alt={`${sample.label}のサンプル`} />
                        {demoSampleId === sample.id && <span className="demo-sample-check">✓</span>}
                      </span>
                      <span className="demo-sample-copy">
                        <strong>{sample.label}</strong>
                        <small>{sample.meta}</small>
                      </span>
                    </button>
                  ))}
                </div>
                <p className="demo-sample-note">画像・店名・価格はすべて架空のポートフォリオ用データです。</p>
              </div>
            )}

            <input
              id="dog-photo-input"
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.jpg,.jpeg,.png,.webp,.heic,.heif"
              multiple={mediaType === "multi_image"}
              disabled={isConverting || isLoading}
              onChange={onFileChange}
              style={{
                position: "absolute",
                width: "1px",
                height: "1px",
                padding: 0,
                margin: "-1px",
                overflow: "hidden",
                clip: "rect(0, 0, 0, 0)",
                whiteSpace: "nowrap",
                border: 0,
              }}
            />

            <input
              id="dog-video-input"
              ref={videoInputRef}
              type="file"
              accept={VIDEO_ACCEPT}
              disabled={isLoading}
              onChange={(event) => {
                chooseVideo(event.target.files?.[0]);
                event.target.value = "";
              }}
              style={{
                position: "absolute",
                width: "1px",
                height: "1px",
                padding: 0,
                margin: "-1px",
                overflow: "hidden",
                clip: "rect(0, 0, 0, 0)",
                whiteSpace: "nowrap",
                border: 0,
              }}
            />

            {mediaType === "video" ? (
              <label htmlFor="dog-video-input" className={`drop-zone ${video ? "selected" : ""}`}>
                {videoUrl ? (
                  <>
                    <video className="video-upload-preview" src={videoUrl} controls muted playsInline />
                    <div className="replace-photo">動画を変更</div>
                  </>
                ) : (
                  <>
                    <span className="upload-icon"><Icon name="photo" /></span>
                    <strong>動画を選ぶ</strong>
                    <p>タップして動画を選択</p>
                    <span className="upload-hint">mp4 / mov / webm / m4v・100MBまで</span>
                  </>
                )}
              </label>
            ) : (
              <>
                <label
                  htmlFor="dog-photo-input"
                  className={`drop-zone ${isDragging ? "dragging" : ""} ${(image || images.length) ? "selected" : ""}`}
                  aria-busy={isConverting}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={onDrop}
                >
              {mediaType === "single_image" && imageUrl ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={imageUrl} alt="選択した投稿写真" />
                  <div className="replace-photo">{isConverting ? "写真を変換しています…" : "写真を変更"}</div>
                </>
              ) : mediaType === "multi_image" && imageUrls.length ? (
                <>
                  <div className="multi-image-preview">
                    {imageUrls.map((url, index) => (
                      <div className="multi-image-thumb" key={`${url}-${index}`}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={url} alt={`選択した写真 ${index + 1}`} />
                        <button type="button" onClick={(event) => { event.preventDefault(); event.stopPropagation(); removeImage(index); }} aria-label={`写真${index + 1}を削除`}>×</button>
                      </div>
                    ))}
                  </div>
                  <div className="replace-photo">{isConverting ? "写真を変換しています…" : `${images.length} / ${MAX_MEDIA_IMAGES}枚・写真を追加`}</div>
                </>
              ) : (
                <>
                  <span className="upload-icon">
                    <Icon name="photo" />
                  </span>
                  <strong>{isConverting ? "写真を変換しています…" : mediaType === "multi_image" ? "写真を選ぶ" : "写真を選ぶ"}</strong>
                  <p>{isConverting ? "少しだけお待ちください" : "タップ、またはここにドロップ"}</p>
                  <span className="upload-hint">
                    {mediaType === "multi_image" ? "最大10枚・スマホの写真ライブラリからも選べます" : "スマホの写真ライブラリからも選べます"}
                  </span>
                </>
              )}
                </label>
              </>
            )}
          </section>

          <section className="editor-section">
            <div className="section-title">
              <span>02</span>
              <div>
                <h2>{category === "pet" ? "この子のこと" : "アカウント・プロフィール"}</h2>
                <p>{category === "pet" ? "いつもの魅力を教えてください" : "カテゴリに合う情報を入力してください"}</p>
              </div>
            </div>

            {category === "pet" ? (
              <div className="field-grid">
                <label>
                  <span>名前 <b>必須</b></span>
                  <input value={dogName} onChange={(e) => { setDogName(e.target.value); updateProfileField("name", e.target.value); }} placeholder="例：ココ" maxLength={50} />
                </label>
                <label>
                  <span>種類</span>
                  <input value={profileData.species || ""} onChange={(e) => updateProfileField("species", e.target.value)} placeholder="例：犬" maxLength={50} />
                </label>
                <label>
                  <span>犬種・猫種</span>
                  <input value={breed} onChange={(e) => { setBreed(e.target.value); updateProfileField("breed", e.target.value); }} placeholder="例：トイプードル" maxLength={100} />
                </label>
                <label>
                  <span>性別</span>
                  <select value={sex} onChange={(e) => { setSex(e.target.value); updateProfileField("sex", e.target.value); }}>
                    <option value="">選択してください</option><option>女の子</option><option>男の子</option><option>回答しない</option>
                  </select>
                </label>
                <label>
                  <span>投稿の目線</span>
                  <select value={voice} onChange={(e) => setVoice(e.target.value as Voice)}>
                    <option value="owner">飼い主目線</option><option value="dog">愛犬本人目線</option>
                  </select>
                </label>
                <label className="wide">
                  <span>性格</span>
                  <input value={personality} onChange={(e) => { setPersonality(e.target.value); updateProfileField("personality", e.target.value); }} placeholder="例：元気、食いしん坊、人懐っこい" maxLength={500} />
                </label>
              </div>
            ) : (
              <div className="field-grid category-profile-grid">
                {categoryConfig.fields.map((field) => (
                  <label key={field.key} className={field.kind === "textarea" ? "wide" : ""}>
                    <span>{field.label} {field.required && <b>必須</b>}</span>
                    {field.kind === "textarea" ? (
                      <textarea value={profileData[field.key] || ""} onChange={(e) => updateProfileField(field.key, e.target.value)} placeholder={field.placeholder} rows={3} maxLength={1000} />
                    ) : (
                      <input value={profileData[field.key] || (field.key === "account_name" ? accountName : "")} onChange={(e) => updateProfileField(field.key, e.target.value)} placeholder={field.placeholder} maxLength={500} />
                    )}
                  </label>
                ))}
              </div>
            )}
          </section>

          <section className="editor-section">
            <div className="section-title">
              <span>03</span>
              <div>
                <h2>今日のできごと</h2>
                <p>ここに書いた内容を写真の推測より優先します</p>
              </div>
            </div>

            <label className="stacked-label">
              <span>
                AIに伝えたいこと <small>任意</small>
              </span>
              <textarea
                value={userNote}
                onChange={(e) => setUserNote(e.target.value)}
                placeholder="例：今日は初めて海へ。波を少し怖がっていました。"
                rows={4}
                maxLength={2000}
              />
              <em>{userNote.length} / 2000</em>
            </label>

            <label className="stacked-label">
              <span>
                必ず入れたいハッシュタグ <small>任意</small>
              </span>
              <input
                value={requiredHashtags}
                onChange={(e) => setRequiredHashtags(e.target.value)}
                placeholder="#トイプードル #海デビュー"
                maxLength={1000}
              />
              <p className="field-help">
                スペース・改行・カンマで区切れます。AIの提案から漏れても必ず追加します。
              </p>
            </label>
          </section>

          <section className="editor-section">
            <div className="section-title">
              <span>04</span>
              <div>
                <h2>ことばの雰囲気</h2>
                <p>投稿のトーンを選んでください</p>
              </div>
            </div>

            <div className="style-grid">
              {categoryConfig.styles.map((item) => (
                <button
                  key={item.value}
                  className={style === item.value ? "active" : ""}
                  type="button"
                  onClick={() => setStyle(item.value as Style)}
                >
                  <span className="style-icon"><StyleIcon value={item.value} /></span>
                  {item.label}
                </button>
              ))}
            </div>

            <div className="template-settings" aria-label="投稿フォーマット">
              <label className="stacked-label">
                <span>投稿フォーマット</span>
                <select value={templateId} onChange={(e) => changeTemplate(e.target.value)}>
                  <option value="auto">AIおまかせ（カテゴリ標準）</option>
                  {categoryTemplates.map((template) => (
                    <option key={template.template_id} value={template.template_id}>{template.name}</option>
                  ))}
                  <option value="custom">新しいカスタムテンプレート</option>
                </select>
              </label>
              <p className="field-help">
                {isTemplatesLoading ? "保存済みテンプレートを読み込んでいます…" : selectedTemplate?.description || "テンプレートで投稿の構成を固定できます。"}
              </p>
              {isTemplateEditorOpen && (
                <div className="custom-template-editor">
                  <label className="stacked-label">
                    <span>テンプレート名</span>
                    <input value={customTemplateName} onChange={(e) => setCustomTemplateName(e.target.value)} placeholder="例：店舗通常投稿" maxLength={100} />
                  </label>
                  <label className="stacked-label">
                    <span>テンプレート本文</span>
                    <textarea value={customTemplate} onChange={(e) => setCustomTemplate(e.target.value)} placeholder={"{title}\n\n{caption}\n\n{hashtags}"} rows={7} maxLength={10000} />
                    <p className="field-help">
                      本文内の #タグは固定タグとして扱います。設定した合計数から固定タグ数を差し引き、残りをAIが生成します。
                    </p>
                  </label>
                  <div className="template-variable-list">
                    <small>利用できる項目（クリックで末尾へ追加）</small>
                    {[
                      "{title}", "{caption}", "{hashtags}", "{account_name}", "{shop_name}", "{address}", "{phone}", "{business_hours}", "{url}",
                    ].map((variable) => (
                      <button key={variable} type="button" onClick={() => setCustomTemplate((current) => `${current}${current && !current.endsWith("\n") ? " " : ""}${variable}`)}>{variable}</button>
                    ))}
                  </div>
                  {invalidTemplateVariables(customTemplate).length > 0 && (
                    <p className="template-error" role="alert">使用できないテンプレート変数があります: {invalidTemplateVariables(customTemplate).map((variable) => `{${variable}}`).join(", ")}</p>
                  )}
                  <div className="template-save-row">
                    <button className="secondary-button" type="button" onClick={saveCustomTemplate}>サーバーに保存</button>
                    {selectedSavedTemplate && (
                      <button className="template-delete-button" type="button" onClick={deleteSavedTemplate}>削除</button>
                    )}
                    {templateSaveMessage && <small role="status">{templateSaveMessage}</small>}
                  </div>
                </div>
              )}
            </div>

            <div className="content-settings" aria-label="投稿内容の設定">
              <div className="content-setting-group">
                <div className="setting-label">
                  <span>投稿文の長さ</span>
                  <small>{selectedCaptionLength.description}</small>
                </div>
                <div className="length-grid">
                  {captionLengthOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className={captionLength === option.value ? "active" : ""}
                      aria-pressed={captionLength === option.value}
                      onClick={() => setCaptionLength(option.value)}
                    >
                      <strong>{option.label}</strong>
                      <small>{option.range}</small>
                    </button>
                  ))}
                </div>
              </div>

              <div className="content-setting-group hashtag-setting">
                <div className="setting-label">
                  <span>ハッシュタグ</span>
                  <small>必須タグを優先してAIが選びます</small>
                </div>
                <div className="hashtag-count-grid">
                  {hashtagCountOptions.map((count) => (
                    <button
                      key={count}
                      type="button"
                      className={hashtagCount === count ? "active" : ""}
                      aria-pressed={hashtagCount === count}
                      onClick={() => setHashtagCount(count)}
                    >
                      {count}個
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <details className="ai-settings">
            <summary>
              <span><Icon name="sliders" /> AI設定</span>
              <small>外部AIを使わない公開デモ</small>
            </summary>

            <div className="ai-settings-body">
              <label>
                <span>画像解析AI</span>
                <select
                  value={imageProvider}
                  onChange={(e) =>
                    setImageProvider(e.target.value as Provider)
                  }
                >
                  {providerOptions.map((value) => (
                    <option key={value} value={value}>
                      {providerLabels[value]}
                    </option>
                  ))}
                </select>
              </label>

              <span className="flow-arrow">→</span>

              <label>
                <span>文章生成AI</span>
                <select
                  value={textProvider}
                  onChange={(e) =>
                    setTextProvider(e.target.value as Provider)
                  }
                >
                  {providerOptions.map((value) => (
                    <option key={value} value={value}>
                      {providerLabels[value]}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </details>

          {error && (
            <div className="error-box" role="alert">
              <strong>うまくいきませんでした</strong>
              <span>{error}</span>
            </div>
          )}

          <button
            className="generate-button"
            type="submit"
            disabled={isLoading}
          >
            <span className="button-icon">
              <Icon name="edit" />
            </span>

            <span>
              <strong>
                {isLoading
                  ? "AIが写真を読んでいます…"
                  : result
                    ? "AIでもう一度つくる"
                    : "この写真で投稿文をつくる"}
              </strong>

              <small>
                {isLoading
                  ? "少しだけお待ちください"
                  : `${providerLabels[imageProvider]} × ${providerLabels[textProvider]}`}
              </small>
            </span>

            <b>{result ? "↻" : "→"}</b>
          </button>

          {result && (
            <section className="result-editor">
              <div className="result-title">
                <div>
                  <span>EDIT CAPTION</span>
                  <h2>投稿文を整える</h2>
                </div>

                <button type="button" onClick={() => generate()}>
                  ↻ AIでもう一度
                </button>
              </div>

              <label className="stacked-label">
                <span>投稿文</span>
                <textarea
                  value={editedCaption}
                  onChange={(e) => setEditedCaption(e.target.value)}
                  rows={7}
                />
                <div className="caption-meta">
                  <span>{editedCaption.length}文字</span>
                  <small>目安 {selectedCaptionLength.range}</small>
                </div>
              </label>

              <div className="tag-list">
                {result.hashtags.map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>

              <details className="analysis-details">
                <summary>AIが写真から読み取った内容</summary>
                <p>{result.image_description}</p>
                <small>
                  画像：{providerLabels[result.providers.image]} / 文章：
                  {providerLabels[result.providers.text]}
                </small>
              </details>
            </section>
          )}
        </form>

        <aside id="post-preview">
          <InstagramPreview
            dogName={dogName}
            accountName={previewAccountName || result?.account_name || ""}
            category={category}
            imageUrl={imageUrl}
            imageUrls={imageUrls}
            mediaType={mediaType}
            videoUrl={videoUrl}
            caption={result ? editedCaption : userNote}
            hashtags={result?.hashtags || requiredTagsPreview}
            renderedPost={renderedPreview || result?.rendered_post || ""}
            generated={Boolean(result)}
          />
        </aside>
      </div>

      <footer>
        <div className="brand footer-brand">
          <span className="brand-mark"><PawMark small /></span>
          <span><b>PawPost</b><em>AI</em></span>
        </div>

        <p>
          つくるのは投稿案まで。あなたの大切な写真を、勝手に投稿することはありません。
        </p>

        <span>投稿案をつくるためのワークスペース · 2026</span>
      </footer>
    </main>
  );
}
