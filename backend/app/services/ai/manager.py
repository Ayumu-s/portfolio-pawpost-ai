from ...config import ProviderName, Settings, get_settings
from ...content_settings import CaptionLength
from ...category_settings import Category
from ...schemas import AccountProfile, DogProfile, MediaType, ProviderPostResult, PostStyle
from .base import AIProvider, AIProviderError
from .mock_provider import MockProvider


class AIManager:
    """Routes the portfolio demo through its deterministic MockProvider."""

    def __init__(self, settings: Settings | None = None) -> None:
        config = settings or get_settings()
        self.providers: dict[ProviderName, AIProvider] = {
            "mock": MockProvider(config),
        }

    def get_provider(self, name: ProviderName) -> AIProvider:
        try:
            return self.providers[name]
        except KeyError as error:
            raise AIProviderError(f"未対応のAI Providerです: {name}") from error

    async def analyze_image(
        self,
        provider_name: ProviderName,
        image_bytes: bytes,
        mime_type: str,
        media_type: MediaType = "single_image",
    ) -> str:
        return await self.get_provider(provider_name).analyze_image(
            image_bytes, mime_type, media_type
        )

    async def generate_post(
        self,
        provider_name: ProviderName,
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
        return await self.get_provider(provider_name).generate_post(
            image_description,
            dog_profile,
            user_note,
            required_hashtags,
            style,
            caption_length,
            hashtag_count,
            adjustment,
            media_type,
            category,
            account_profile,
        )
