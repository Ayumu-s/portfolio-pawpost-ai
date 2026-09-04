import json
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from ..content_settings import CaptionLength, MAX_HASHTAG_COUNT
from ..category_settings import CATEGORY_REQUIRED_FIELDS, Category
from ..config import ProviderName, get_settings
from ..media_settings import MAX_MEDIA_IMAGES, MAX_VIDEO_SIZE_BYTES, is_supported_video
from ..schemas import AccountProfile, DogProfile, GeneratedPost, MediaType, PostStyle
from ..services.ai import AIProviderError
from ..services.ai.utils import parse_hashtags
from ..services.image_normalizer import (
    ImageNormalizationError,
    is_supported_image,
    normalize_image_bytes,
)
from ..services.post_generator import PostGenerator
from ..services.template_renderer import (
    TemplateValidationError,
    extract_template_hashtags,
    resolve_template,
)

router = APIRouter(prefix="/api/posts", tags=["posts"])
post_generator = PostGenerator()
@router.post("/generate", response_model=GeneratedPost)
async def generate_post(
    dog_name: Annotated[str | None, Form(max_length=50)] = None,
    image: Annotated[
        UploadFile | None, File(description="JPEG, PNG, WebP, HEIC, or HEIF post image")
    ] = None,
    breed: Annotated[str, Form(max_length=100)] = "",
    sex: Annotated[str, Form(max_length=30)] = "",
    personality: Annotated[str, Form(max_length=500)] = "",
    voice: Annotated[str, Form()] = "owner",
    user_note: Annotated[str, Form(max_length=2000)] = "",
    required_hashtags: Annotated[str, Form(max_length=1000)] = "",
    style: Annotated[PostStyle, Form()] = "auto",
    image_provider: Annotated[ProviderName | None, Form()] = None,
    text_provider: Annotated[ProviderName | None, Form()] = None,
    caption_length: Annotated[CaptionLength, Form()] = "standard",
    hashtag_count: Annotated[int, Form(ge=3, le=5)] = 5,
    media_type: Annotated[MediaType, Form()] = "single_image",
    images: Annotated[list[UploadFile] | None, File(description="Carousel images")] = None,
    video: Annotated[UploadFile | None, File(description="Video upload")] = None,
    category: Annotated[Category, Form()] = "pet",
    account_name: Annotated[str, Form(max_length=100)] = "",
    profile_data: Annotated[str, Form(max_length=10000)] = "{}",
    template_id: Annotated[str, Form(max_length=100)] = "auto",
    custom_template: Annotated[str, Form(max_length=10000)] = "",
    custom_template_name: Annotated[str, Form(max_length=100)] = "",
) -> GeneratedPost:
    settings = get_settings()
    try:
        decoded_profile = json.loads(profile_data or "{}")
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=422, detail="profile_dataはJSON形式で指定してください。") from error
    if not isinstance(decoded_profile, dict) or any(
        not isinstance(key, str) or not isinstance(value, (str, int, float, bool))
        for key, value in decoded_profile.items()
    ):
        raise HTTPException(status_code=422, detail="profile_dataは文字列中心のオブジェクトで指定してください。")
    profile_values = {str(key): str(value) for key, value in decoded_profile.items()}
    if account_name.strip():
        profile_values["account_name"] = account_name.strip()
    if category == "pet":
        pet_name = (dog_name or profile_values.get("name", "")).strip()
        if not pet_name:
            raise HTTPException(status_code=422, detail="ペットカテゴリでは名前を入力してください。")
        profile_values.update(
            {
                "name": pet_name,
                "species": profile_values.get("species", "dog"),
                "breed": breed.strip() or profile_values.get("breed", ""),
                "sex": sex.strip() or profile_values.get("sex", ""),
                "personality": personality.strip() or profile_values.get("personality", ""),
                "voice": voice,
            }
        )
        resolved_account_name = account_name.strip() or f"{pet_name}のまいにち"
    else:
        resolved_account_name = (
            account_name.strip()
            or profile_values.get("account_name", "").strip()
            or profile_values.get("shop_name", "").strip()
            or profile_values.get("company_name", "").strip()
            or profile_values.get("brand_name", "").strip()
        )
        profile_values["account_name"] = resolved_account_name
        missing_fields = [
            field for field in CATEGORY_REQUIRED_FIELDS[category]
            if not profile_values.get(field, "").strip()
        ]
        if category == "pr" and not (
            profile_values.get("company_name", "").strip()
            or profile_values.get("brand_name", "").strip()
        ):
            missing_fields = ["company_nameまたはbrand_name"]
        if missing_fields:
            raise HTTPException(
                status_code=422,
                detail=f"{category}カテゴリの必須プロフィールを入力してください: {', '.join(missing_fields)}",
            )
        if category in {"food", "travel", "custom"} and not resolved_account_name:
            raise HTTPException(status_code=422, detail="アカウント名を入力してください。")
    try:
        account_profile = AccountProfile(
            account_name=resolved_account_name,
            category=category,
            profile_data=profile_values,
        )
        _, template_body = resolve_template(
            category,
            template_id,
            custom_template=custom_template,
            custom_template_name=custom_template_name,
        )
    except (TemplateValidationError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    required_tags = parse_hashtags(required_hashtags)
    template_tags = extract_template_hashtags(template_body)
    effective_required_tags = parse_hashtags([*template_tags, *required_tags])
    if len(effective_required_tags) > MAX_HASHTAG_COUNT:
        if template_tags:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="テンプレート内の固定ハッシュタグと必須ハッシュタグは最大5個まで指定できます。",
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ハッシュタグは最大5個まで指定できます。",
        )
    if len(effective_required_tags) > hashtag_count:
        if template_tags:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="テンプレート内の固定ハッシュタグと必須ハッシュタグが設定数を超えています。ハッシュタグ数を増やしてください。",
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="必須ハッシュタグが設定数を超えています。ハッシュタグ数を増やすか、必須タグを減らしてください。",
        )

    try:
        normalized_images: list[tuple[bytes, str]] = []
        video_bytes: bytes | None = None
        video_filename = ""

        if media_type == "single_image":
            if image is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="まず投稿する写真を選択してください。" if category != "pet" else "まず愛犬の写真を選択してください。",
                )
            uploads = [image]
        elif media_type == "multi_image":
            uploads = list(images or [])
            if not uploads and image is not None:
                uploads = [image]
            if not uploads:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="複数画像を1枚以上選択してください。",
                )
            if len(uploads) > MAX_MEDIA_IMAGES:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="複数画像は最大10枚までです。",
                )
        else:
            uploads = []
            if video is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="動画を1本選択してください。",
                )
            video_filename = video.filename or ""
            video_mime = video.content_type or ""
            if not is_supported_video(video_mime, video_filename):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="対応していない動画形式です。mp4 / mov / webm / m4vを選択してください。",
                )
            video_bytes = await video.read(MAX_VIDEO_SIZE_BYTES + 1)
            if len(video_bytes) > MAX_VIDEO_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="動画サイズは100MB以下にしてください。",
                )
            if not video_bytes:
                raise HTTPException(status_code=400, detail="動画ファイルが空です。")

        for upload in uploads:
            mime_type = upload.content_type or ""
            filename = upload.filename or ""
            if not is_supported_image(mime_type, filename):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="JPEG / PNG / WebP / HEIC / HEIF の画像を選択してください。",
                )
            image_bytes = await upload.read(settings.max_image_size_bytes + 1)
            if len(image_bytes) > settings.max_image_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"画像サイズは{settings.max_image_size_mb}MB以下にしてください。",
                )
            if not image_bytes:
                raise HTTPException(status_code=400, detail="画像ファイルが空です。")
            normalized_images.append(
                normalize_image_bytes(
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    filename=filename,
                )
            )

        profile = DogProfile(
            name=profile_values.get("name", resolved_account_name or category),
            breed=profile_values.get("breed", ""),
            sex=profile_values.get("sex", ""),
            personality=profile_values.get("personality", ""),
            voice=voice if category == "pet" else "owner",
        )
        provider_kwargs = {
            "dog_profile": profile,
            "user_note": user_note.strip(),
            "required_hashtags": required_tags,
            "style": style,
            "image_provider": image_provider or settings.image_ai_provider,
            "text_provider": text_provider or settings.text_ai_provider,
            "caption_length": caption_length,
            "hashtag_count": hashtag_count,
            "media_type": media_type,
            "category": category,
            "account_profile": account_profile,
            "template_id": template_id,
            "custom_template": custom_template,
            "custom_template_name": custom_template_name,
        }
        if media_type == "single_image":
            image_bytes, normalized_mime_type = normalized_images[0]
            return await post_generator.generate(
                image_bytes=image_bytes,
                mime_type=normalized_mime_type,
                **provider_kwargs,
            )
        return await post_generator.generate_media(
            images=normalized_images or None,
            video_bytes=video_bytes,
            video_filename=video_filename,
            **provider_kwargs,
        )
    except AIProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ImageNormalizationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
