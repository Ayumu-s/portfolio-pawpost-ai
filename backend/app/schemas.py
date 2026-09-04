from typing import Literal

from pydantic import BaseModel, Field

from .content_settings import CaptionLength
from .category_settings import Category
from .config import ProviderName

PostStyle = Literal[
    "auto", "cute", "funny", "diary", "simple", "owner", "dog",
    "friendly", "casual", "polite", "recommend", "premium", "official",
    "recruit", "expert",
]
DogVoice = Literal["owner", "dog"]
MediaType = Literal["single_image", "multi_image", "video"]


class DogProfile(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    breed: str = Field(default="", max_length=100)
    sex: str = Field(default="", max_length=30)
    personality: str = Field(default="", max_length=500)
    voice: DogVoice = "owner"


class AccountProfile(BaseModel):
    """Category-neutral account profile passed through the generation pipeline."""

    account_name: str = Field(default="", max_length=100)
    category: Category = "pet"
    profile_data: dict[str, str] = Field(default_factory=dict)


def account_profile_from_dog(profile: DogProfile, account_name: str = "") -> AccountProfile:
    return AccountProfile(
        account_name=account_name or f"{profile.name}のまいにち",
        category="pet",
        profile_data={
            "name": profile.name,
            "species": "dog",
            "breed": profile.breed,
            "sex": profile.sex,
            "personality": profile.personality,
            "voice": profile.voice,
        },
    )


class AIConfigResponse(BaseModel):
    image_provider: ProviderName
    text_provider: ProviderName


class ProvidersUsed(BaseModel):
    image: ProviderName
    text: ProviderName


class GeneratedPost(BaseModel):
    caption: str
    hashtags: list[str]
    image_description: str
    title: str = ""
    rendered_post: str = ""
    template_id: str = "auto"
    category: Category = "pet"
    account_name: str = ""
    style: PostStyle
    caption_length: CaptionLength = "standard"
    caption_char_count: int = 0
    hashtag_count: int = 5
    media_type: MediaType = "single_image"
    media_count: int = 1
    video_frame_count: int = 0
    providers: ProvidersUsed


class ProviderPostResult(BaseModel):
    title: str = ""
    caption: str
    hashtags: list[str] = Field(default_factory=list)


class TemplateUpsertRequest(BaseModel):
    """User-owned template data accepted by the persistent template API."""

    template_id: str | None = Field(default=None, max_length=100)
    category: Category
    name: str = Field(min_length=1, max_length=100)
    template_body: str = Field(min_length=1, max_length=10000)


class SavedTemplate(BaseModel):
    """A persisted custom template returned to the Frontend."""

    template_id: str
    category: Category
    name: str
    description: str = "ユーザーが保存したテンプレート"
    template_body: str
    is_default: bool = False
    is_builtin: bool = False
    created_at: str
    updated_at: str
