from app.services.image_normalizer import (
    is_heic_file,
    is_supported_image,
    normalize_image_bytes,
)


def test_supported_types_include_heic_and_extension_fallback() -> None:
    assert is_supported_image("image/heic", "iphone.heic")
    assert is_supported_image("", "iphone.HEIF")
    assert is_heic_file("image/heif-sequence", "photo.bin")
    assert is_heic_file("", "photo.heif")
    assert not is_supported_image("image/gif", "dog.gif")


def test_non_heic_image_bytes_are_not_reencoded() -> None:
    image_bytes = b"raw-webp-bytes"
    normalized_bytes, normalized_mime = normalize_image_bytes(
        image_bytes=image_bytes,
        mime_type="image/webp",
        filename="dog.webp",
    )
    assert normalized_bytes == image_bytes
    assert normalized_mime == "image/webp"
