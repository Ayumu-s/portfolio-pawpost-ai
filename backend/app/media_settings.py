"""Upload limits and MIME helpers shared by the media API."""

from pathlib import PurePosixPath, PureWindowsPath

SUPPORTED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "video/x-m4v",
}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}
MAX_MEDIA_IMAGES = 10
MAX_VIDEO_SIZE_MB = 100
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024


def filename_extension(filename: str) -> str:
    name = PureWindowsPath(filename).name or PurePosixPath(filename).name
    return PurePosixPath(name.lower()).suffix


def is_supported_video(mime_type: str, filename: str = "") -> bool:
    normalized = mime_type.lower().split(";", 1)[0].strip()
    return normalized in SUPPORTED_VIDEO_TYPES or filename_extension(filename) in SUPPORTED_VIDEO_EXTENSIONS
