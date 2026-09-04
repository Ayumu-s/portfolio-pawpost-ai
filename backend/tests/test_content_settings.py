from app.content_settings import (
    CAPTION_LENGTHS,
    caption_length_within_tolerance,
    caption_needs_format_adjustment,
)
from app.services.ai.utils import ensure_required_hashtags


def test_caption_length_ranges_are_centralized() -> None:
    assert CAPTION_LENGTHS["one_liner"]["min"] == 30
    assert CAPTION_LENGTHS["one_liner"]["max"] == 60
    assert CAPTION_LENGTHS["short"]["min"] == 60
    assert CAPTION_LENGTHS["short"]["max"] == 100
    assert CAPTION_LENGTHS["standard"]["min"] == 100
    assert CAPTION_LENGTHS["standard"]["max"] == 160
    assert CAPTION_LENGTHS["detailed"]["min"] == 160
    assert CAPTION_LENGTHS["detailed"]["max"] == 250
    assert CAPTION_LENGTHS["long"]["min"] == 250
    assert CAPTION_LENGTHS["long"]["max"] == 400
    assert caption_length_within_tolerance("あ" * 120, "standard")
    assert not caption_length_within_tolerance("あ" * 10, "standard")


def test_long_caption_requires_visual_format_quality_retry() -> None:
    assert caption_needs_format_adjustment("一文だけです。", "long")
    assert not caption_needs_format_adjustment(
        "導入です✨。\n\n出来事です。\n\n締めです🐾。", "long"
    )


def test_required_tags_are_deduplicated_and_capped() -> None:
    assert ensure_required_hashtags(
        ["#柴犬", "#柴犬", "#犬のいる暮らし", "#dogstagram"],
        ["#柴犬", "#海デビュー"],
        limit=3,
    ) == ["#柴犬", "#海デビュー", "#犬のいる暮らし"]
