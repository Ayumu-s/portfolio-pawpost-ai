"""Shared content settings used by the API and result shaping."""

import re

from typing import Literal, TypedDict


CaptionLength = Literal["one_liner", "short", "standard", "detailed", "long"]


class CaptionLengthSpec(TypedDict):
    min: int
    max: int
    label: str
    description: str


CAPTION_LENGTHS: dict[CaptionLength, CaptionLengthSpec] = {
    "one_liner": {
        "min": 30,
        "max": 60,
        "label": "一言",
        "description": "写真を主役にした短い投稿",
    },
    "short": {
        "min": 60,
        "max": 100,
        "label": "短め",
        "description": "日常の一コマを簡潔に",
    },
    "standard": {
        "min": 100,
        "max": 160,
        "label": "標準",
        "description": "おすすめ。出来事と気持ちを自然に",
    },
    "detailed": {
        "min": 160,
        "max": 250,
        "label": "しっかり",
        "description": "出来事を少し詳しく残す",
    },
    "long": {
        "min": 250,
        "max": 400,
        "label": "長め",
        "description": "旅行・誕生日・思い出など",
    },
}

HASHTAG_COUNTS = (3, 4, 5)
MAX_HASHTAG_COUNT = max(HASHTAG_COUNTS)

_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]")


def caption_needs_format_adjustment(caption: str, caption_length: CaptionLength) -> bool:
    """Return whether a multi-line caption needs one quality retry."""
    if caption_length in {"one_liner", "short"}:
        return False
    required_blank_lines = 2 if caption_length == "long" else 1
    return (
        caption.count("\n\n") < required_blank_lines
        or _EMOJI_RE.search(caption) is None
    )


def caption_spec(caption_length: CaptionLength) -> CaptionLengthSpec:
    return CAPTION_LENGTHS[caption_length]


def caption_length_within_tolerance(caption: str, caption_length: CaptionLength) -> bool:
    """Allow a natural AI response to drift by roughly 20 percent."""
    spec = caption_spec(caption_length)
    return len(caption) >= spec["min"] * 0.8 and len(caption) <= spec["max"] * 1.2
