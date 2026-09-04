import re
from collections.abc import Iterable


_TAG_SPLIT = re.compile(r"[\s,、，]+")
_INVALID_TAG_CHARS = re.compile(r"[^\w\u3040-\u30ff\u3400-\u9fffー]", re.UNICODE)
_CAPTION_SENTENCE_END = re.compile(r"(?<=[。！？!?])\s*")
_CAPTION_EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]")


def normalize_hashtag(value: str) -> str | None:
    cleaned = value.strip().lstrip("#＃")
    cleaned = _INVALID_TAG_CHARS.sub("", cleaned)
    return f"#{cleaned}" if cleaned else None


def parse_hashtags(raw: str | Iterable[str]) -> list[str]:
    values = _TAG_SPLIT.split(raw) if isinstance(raw, str) else raw
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = normalize_hashtag(str(value))
        if tag and tag.casefold() not in seen:
            seen.add(tag.casefold())
            unique.append(tag)
    return unique


def ensure_required_hashtags(
    generated: Iterable[str], required: Iterable[str], limit: int = 5
) -> list[str]:
    """Required tags are first, unique, and never silently removed."""
    required_tags = parse_hashtags(required)
    if len(required_tags) > limit:
        raise ValueError("ハッシュタグは最大5個まで指定できます。")
    generated_tags = parse_hashtags(generated)
    combined = parse_hashtags([*required_tags, *generated_tags])
    return combined[:limit]


def normalize_caption_text(caption: str) -> str:
    """Normalize line endings and literal escaped newlines from model JSON."""
    return (
        caption.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )


def format_caption_fallback(caption: str, caption_length: str) -> str:
    """Make a usable visual layout when a provider ignores layout instructions."""
    normalized = normalize_caption_text(caption)
    if caption_length in {"one_liner", "short"} or not normalized:
        return normalized

    target_paragraphs = 3 if caption_length == "long" else 2
    sentences = [part.strip() for part in _CAPTION_SENTENCE_END.split(normalized) if part.strip()]
    if len(sentences) >= target_paragraphs and "\n\n" not in normalized:
        groups: list[str] = []
        for index in range(target_paragraphs):
            start = round(len(sentences) * index / target_paragraphs)
            end = round(len(sentences) * (index + 1) / target_paragraphs)
            groups.append("".join(sentences[start:end]))
        normalized = "\n\n".join(group for group in groups if group)

    if (
        _CAPTION_EMOJI.search(normalized) is None
        and sentences
        and any(mark in normalized for mark in "。！？!?")
    ):
        normalized = f"{normalized} ✨"
    return normalized

