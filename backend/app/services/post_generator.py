from ..config import ProviderName
from ..content_settings import (
    CaptionLength,
    caption_length_within_tolerance,
    caption_needs_format_adjustment,
)
from ..category_settings import Category
from ..schemas import AccountProfile, DogProfile, GeneratedPost, MediaType, PostStyle, ProvidersUsed, account_profile_from_dog
from .ai.manager import AIManager
from .ai.utils import ensure_required_hashtags, format_caption_fallback, parse_hashtags
from .media_analyzer import MediaAnalyzer
from .template_renderer import extract_template_hashtags, render_template, resolve_template


class PostGenerator:
    def __init__(self, ai_manager: AIManager | None = None) -> None:
        self.ai_manager = ai_manager or AIManager()
        self.media_analyzer = MediaAnalyzer(self.ai_manager)

    async def generate(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        dog_profile: DogProfile,
        user_note: str,
        required_hashtags: list[str],
        style: PostStyle,
        image_provider: ProviderName,
        text_provider: ProviderName,
        caption_length: CaptionLength = "standard",
        hashtag_count: int = 5,
        media_type: MediaType = "single_image",
        category: Category = "pet",
        account_profile: AccountProfile | None = None,
        template_id: str = "auto",
        custom_template: str = "",
        custom_template_name: str = "",
    ) -> GeneratedPost:
        image_description = await self.ai_manager.analyze_image(
            image_provider, image_bytes, mime_type
        )
        return await self._generate_from_description(
            image_description=image_description,
            dog_profile=dog_profile,
            user_note=user_note,
            required_hashtags=required_hashtags,
            style=style,
            image_provider=image_provider,
            text_provider=text_provider,
            caption_length=caption_length,
            hashtag_count=hashtag_count,
            media_type=media_type,
            category=category,
            account_profile=account_profile,
            media_count=1,
            template_id=template_id,
            custom_template=custom_template,
            custom_template_name=custom_template_name,
        )

    async def generate_media(
        self,
        *,
        media_type: MediaType,
        images: list[tuple[bytes, str]] | None,
        video_bytes: bytes | None,
        video_filename: str,
        dog_profile: DogProfile,
        user_note: str,
        required_hashtags: list[str],
        style: PostStyle,
        image_provider: ProviderName,
        text_provider: ProviderName,
        caption_length: CaptionLength = "standard",
        hashtag_count: int = 5,
        category: Category = "pet",
        account_profile: AccountProfile | None = None,
        template_id: str = "auto",
        custom_template: str = "",
        custom_template_name: str = "",
    ) -> GeneratedPost:
        if media_type == "video":
            if video_bytes is None:
                raise ValueError("動画ファイルがありません。")
            analysis = await self.media_analyzer.analyze_video(
                video_bytes,
                filename=video_filename,
                provider_name=image_provider,
            )
        else:
            analysis = await self.media_analyzer.analyze_images(
                images or [],
                provider_name=image_provider,
                media_type=media_type,
            )
        return await self._generate_from_description(
            image_description=analysis.description,
            dog_profile=dog_profile,
            user_note=user_note,
            required_hashtags=required_hashtags,
            style=style,
            image_provider=image_provider,
            text_provider=text_provider,
            caption_length=caption_length,
            hashtag_count=hashtag_count,
            media_type=media_type,
            category=category,
            account_profile=account_profile,
            media_count=analysis.media_count,
            video_frame_count=analysis.video_frame_count,
            template_id=template_id,
            custom_template=custom_template,
            custom_template_name=custom_template_name,
        )

    async def _generate_from_description(
        self,
        *,
        image_description: str,
        dog_profile: DogProfile,
        user_note: str,
        required_hashtags: list[str],
        style: PostStyle,
        image_provider: ProviderName,
        text_provider: ProviderName,
        caption_length: CaptionLength,
        hashtag_count: int,
        media_type: MediaType,
        media_count: int,
        video_frame_count: int = 0,
        category: Category = "pet",
        account_profile: AccountProfile | None = None,
        template_id: str = "auto",
        custom_template: str = "",
        custom_template_name: str = "",
    ) -> GeneratedPost:
        resolved_template_id, template_body = resolve_template(
            category,
            template_id,
            custom_template=custom_template,
            custom_template_name=custom_template_name,
        )
        template_fixed_hashtags = extract_template_hashtags(template_body)
        effective_required_hashtags = parse_hashtags(
            [*template_fixed_hashtags, *required_hashtags]
        )
        if len(effective_required_hashtags) > hashtag_count:
            raise ValueError(
                "テンプレート内の固定ハッシュタグと必須ハッシュタグの合計が設定数を超えています。"
            )

        if category == "pet" and account_profile is None:
            generated = await self.ai_manager.generate_post(
                text_provider,
                image_description,
                dog_profile,
                user_note,
                effective_required_hashtags,
                style,
                caption_length,
                hashtag_count,
                media_type=media_type,
            )
        else:
            generated = await self.ai_manager.generate_post(
                text_provider,
                image_description,
                dog_profile,
                user_note,
                effective_required_hashtags,
                style,
                caption_length,
                hashtag_count,
                media_type=media_type,
                category=category,
                account_profile=account_profile,
            )
        needs_adjustment = (
            not caption_length_within_tolerance(generated.caption, caption_length)
            or caption_needs_format_adjustment(generated.caption, caption_length)
        )
        if needs_adjustment:
            if category == "pet" and account_profile is None:
                generated = await self.ai_manager.generate_post(
                    text_provider,
                    image_description,
                    dog_profile,
                    user_note,
                    effective_required_hashtags,
                    style,
                    caption_length,
                    hashtag_count,
                    True,
                    media_type,
                )
            else:
                generated = await self.ai_manager.generate_post(
                    text_provider,
                    image_description,
                    dog_profile,
                    user_note,
                    effective_required_hashtags,
                    style,
                    caption_length,
                    hashtag_count,
                    True,
                    media_type,
                    category,
                    account_profile,
                )
        generated.caption = format_caption_fallback(generated.caption, caption_length)
        hashtags = ensure_required_hashtags(
            generated.hashtags,
            effective_required_hashtags,
            limit=hashtag_count,
        )
        fixed_keys = {tag.casefold() for tag in template_fixed_hashtags}
        ai_hashtags = [tag for tag in hashtags if tag.casefold() not in fixed_keys]
        effective_profile = account_profile or account_profile_from_dog(dog_profile)
        template_values = {
            **effective_profile.profile_data,
            "account_name": effective_profile.account_name,
            "title": generated.title or generated.caption.split("。", 1)[0][:40],
            "caption": generated.caption,
            "hashtags": " ".join(ai_hashtags if template_fixed_hashtags else hashtags),
        }
        rendered_post = render_template(
            template_body,
            template_values,
            fixed_hashtags=template_fixed_hashtags,
            ai_hashtags=ai_hashtags,
        )
        return GeneratedPost(
            caption=generated.caption,
            hashtags=hashtags,
            image_description=image_description,
            title=generated.title or template_values["title"],
            rendered_post=rendered_post,
            template_id=resolved_template_id,
            category=category,
            account_name=effective_profile.account_name,
            style=style,
            caption_length=caption_length,
            caption_char_count=len(generated.caption),
            hashtag_count=hashtag_count,
            media_type=media_type,
            media_count=media_count,
            video_frame_count=video_frame_count,
            providers=ProvidersUsed(image=image_provider, text=text_provider),
        )
