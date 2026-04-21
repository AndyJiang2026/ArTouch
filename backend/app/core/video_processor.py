# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create FFmpeg video processor module
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

import json
import os
import subprocess


class VideoProcessor:
    """FFmpeg wrapper for video preprocessing."""

    @staticmethod
    def get_video_info(file_path: str) -> dict[str, any] | None:
        """
        Get video information using ffprobe.
        Returns dict with duration, size, resolution, etc.
        """
        if not os.path.exists(file_path):
            return None

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]

        try:
            # check=False: ffprobe returns non-zero when file not found or format error, we handle returncode separately
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)

            # Find video stream
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            else:
                return None

            duration = float(data.get("format", {}).get("duration", 0))
            file_size = int(data.get("format", {}).get("size", 0))
            width = video_stream.get("width", 0)
            height = video_stream.get("height", 0)
            resolution = f"{width}x{height}" if width and height else None
        except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
            return None
        else:
            return {
                "duration": duration,
                "file_size": file_size,
                "resolution": resolution,
                "width": width,
                "height": height,
            }

    @staticmethod
    def process_video(
        input_path: str,
        output_path: str | None = None,
        max_resolution: tuple[int, int] | None = None,
    ) -> bool:
        """
        Process video with optional resizing.
        Returns True if successful.
        """
        if not os.path.exists(input_path):
            return False

        if output_path is None:
            output_path = input_path

        cmd = ["ffmpeg", "-i", input_path, "-y"]

        if max_resolution:
            width, height = max_resolution
            cmd.extend(["-vf", f"scale='min({width},iw)':min'({height},ih)':force_original_aspect_ratio=decrease"])

        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                output_path,
            ]
        )

        try:
            # check=False: ffmpeg returns non-zero on encoding issues but we check returncode separately
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False
        else:
            return result.returncode == 0

    @staticmethod
    def generate_thumbnail(
        video_path: str,
        output_path: str,
        time_offset: float = 1.0,
    ) -> bool:
        """Generate thumbnail from video at specified time offset."""
        if not os.path.exists(video_path):
            return False

        cmd = [
            "ffmpeg",
            "-ss",
            str(time_offset),
            "-i",
            video_path,
            "-vframes",
            "1",
            "-y",
            output_path,
        ]

        try:
            # check=False: ffmpeg returns non-zero on thumbnail gen failure but we check returncode separately
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False
        else:
            return result.returncode == 0
