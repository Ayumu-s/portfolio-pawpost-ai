from abc import ABC, abstractmethod

from ...content_settings import CaptionLength
from ...category_settings import Category
from ...schemas import AccountProfile, DogProfile, MediaType, ProviderPostResult, PostStyle


class AIProviderError(RuntimeError):
    """A user-actionable provider failure."""


class AIProvider(ABC):
    """Common boundary for interchangeable vision and text providers."""

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        media_type: MediaType = "single_image",
    ) -> str:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
