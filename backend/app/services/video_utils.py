"""Small, bounded video frame extraction helper for the MVP."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


class VideoProcessingError(ValueError):
    """Raised when a video cannot be opened or sampled."""


def extract_video_frames(
    video_bytes: bytes,
    *,
    filename: str = "video.mp4",
    max_frames: int = 12,
    interval_seconds: float = 2.0,
) -> list[bytes]:
    """Extract representative JPEG frames without persisting user media."""
    if not video_bytes:
        raise VideoProcessingError("動画ファイルが空です。")
    if max_frames < 1:
        raise VideoProcessingError("動画フレーム数の設定が不正です。")

    try:
        import cv2
    except ImportError as error:
        raise VideoProcessingError(
            "動画解析にはOpenCVが必要です。backendの依存関係をインストールしてください。"
        ) from error

    suffix = Path(filename).suffix.lower() or ".mp4"
    temp_path: str | None = None
    capture = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(video_bytes)
            temp_path = temp_file.name

        capture = cv2.VideoCapture(temp_path)
        if not capture.isOpened():
            raise VideoProcessingError("動画を読み込めませんでした。対応形式か確認してください。")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps <= 0 or frame_count <= 0:
            raise VideoProcessingError("動画のフレーム情報を取得できませんでした。")

        interval_frames = max(1, int(fps * interval_seconds))
        indices = list(range(0, frame_count, interval_frames))
        if (frame_count - 1) not in indices:
            indices.append(frame_count - 1)
        if len(indices) > max_frames:
            if max_frames == 1:
                indices = [0]
            else:
                indices = [
                    round(index * (frame_count - 1) / (max_frames - 1))
                    for index in range(max_frames)
                ]

        frames: list[bytes] = []
        for frame_index in indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                continue
            encoded, buffer = cv2.imencode(".jpg", frame)
            if encoded:
                frames.append(buffer.tobytes())

        if not frames:
            raise VideoProcessingError("動画から代表フレームを抽出できませんでした。")
        return frames
    except VideoProcessingError:
        raise
    except Exception as error:
        raise VideoProcessingError("動画のフレーム抽出に失敗しました。") from error
    finally:
        if capture is not None:
            capture.release()
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
