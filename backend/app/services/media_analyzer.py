"""Media-to-description orchestration shared by image and video posts."""

from __future__ import annotations

from dataclasses import dataclass

from ..config import ProviderName
from ..schemas import MediaType
from .ai.manager import AIManager
from .video_utils import extract_video_frames


@dataclass(frozen=True)
class MediaAnalysis:
    description: str
    media_count: int
    video_frame_count: int = 0


class MediaAnalyzer:
    def __init__(self, ai_manager: AIManager | None = None) -> None:
        self.ai_manager = ai_manager or AIManager()

    async def analyze_images(
        self,
        images: list[tuple[bytes, str]],
        *,
        provider_name: ProviderName,
        media_type: MediaType,
    ) -> MediaAnalysis:
        descriptions: list[str] = []
        for image_bytes, mime_type in images:
            descriptions.append(
                await self.ai_manager.analyze_image(
                    provider_name, image_bytes, mime_type, media_type
                )
            )

        if media_type == "single_image" or len(descriptions) == 1:
            return MediaAnalysis(descriptions[0], len(images))

        joined = "\n".join(
            f"画像{i + 1}の説明:\n{description}" for i, description in enumerate(descriptions)
        )
        return MediaAnalysis(
            "これは複数画像のカルーセル投稿です。各画像の説明を順番に示します。\n"
            + joined
            + "\n各画像の内容を一つの投稿全体の流れとして扱ってください。",
            len(images),
        )

    async def analyze_video(
        self,
        video_bytes: bytes,
        *,
        filename: str,
        provider_name: ProviderName,
    ) -> MediaAnalysis:
        frames = extract_video_frames(video_bytes, filename=filename)
        descriptions: list[str] = []
        for frame in frames:
            descriptions.append(
                await self.ai_manager.analyze_image(
                    provider_name, frame, "image/jpeg", "video"
                )
            )
        joined = "\n".join(
            f"代表フレーム{i + 1}の説明:\n{description}"
            for i, description in enumerate(descriptions)
        )
        return MediaAnalysis(
            "これは動画投稿です。抽出された代表フレームから、動画全体の内容・行動・雰囲気を要約してください。\n"
            + joined,
            1,
            len(frames),
        )
