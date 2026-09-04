"""Validate and normalize user-provided image bytes before AI processing."""

from __future__ import annotations

import io
from pathlib import PurePosixPath, PureWindowsPath

from PIL import Image, ImageOps

SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "image/heic-sequence",
    "image/heif-sequence",
}
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
HEIC_TYPES = {
    "image/heic",
    "image/heif",
    "image/heic-sequence",
    "image/heif-sequence",
}
EXTENSION_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class ImageNormalizationError(ValueError):
    """Raised when an image cannot be decoded or converted safely."""


def _extension(filename: str) -> str:
    # PureWindowsPath handles filenames sent by Windows clients; PurePosixPath
    # also covers browser paths without touching the filesystem.
    name = PureWindowsPath(filename).name or PurePosixPath(filename).name
    return PurePosixPath(name.lower()).suffix


def is_heic_file(mime_type: str, filename: str = "") -> bool:
    return mime_type.lower().split(";", 1)[0].strip() in HEIC_TYPES or _extension(filename) in {
        ".heic",
        ".heif",
    }


def is_supported_image(mime_type: str, filename: str = "") -> bool:
    normalized_mime = mime_type.lower().split(";", 1)[0].strip()
    return normalized_mime in SUPPORTED_IMAGE_TYPES or _extension(filename) in SUPPORTED_IMAGE_EXTENSIONS


def _to_rgb(image: Image.Image) -> Image.Image:
    """Convert any alpha-bearing image onto a white RGB background."""
    transposed = ImageOps.exif_transpose(image)
    if transposed.mode in ("RGBA", "LA") or "transparency" in transposed.info:
        rgba = transposed.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return transposed.convert("RGB")


def normalize_image_bytes(
    *, image_bytes: bytes, mime_type: str, filename: str = ""
) -> tuple[bytes, str]:
    """Return bytes and MIME type suitable for an AI vision provider.

    JPEG, PNG, and WebP bytes remain untouched. HEIC/HEIF images are decoded
    with pillow-heif, EXIF-transposed, composited onto white when necessary,
    and encoded as a JPEG in memory. No upload is written to disk.
    """
    if not is_supported_image(mime_type, filename):
        raise ImageNormalizationError(
            "JPEG / PNG / WebP / HEIC / HEIF の画像を選択してください。"
        )
    if not is_heic_file(mime_type, filename):
        normalized_mime = mime_type.lower().split(";", 1)[0].strip()
        return image_bytes, normalized_mime or EXTENSION_MIME_TYPES.get(
            _extension(filename), "application/octet-stream"
        )

    try:
        from pillow_heif import register_heif_opener

        register_heif_opener()
        with Image.open(io.BytesIO(image_bytes)) as source:
            rgb_image = _to_rgb(source)
            output = io.BytesIO()
            rgb_image.save(output, format="JPEG", quality=90, optimize=True)
            return output.getvalue(), "image/jpeg"
    except Exception as error:
        if isinstance(error, ImageNormalizationError):
            raise
        raise ImageNormalizationError(
            "HEIC / HEIF画像をJPEGに変換できませんでした。"
        ) from error
