"""
ETSAI Growth Bot — Video Engine
Assembles short-form vertical videos with Hum mascot overlay.
Pipeline: script → TTS → MoviePy assembly → output MP4.
"""
import logging
import os
import tempfile
import time
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth.growth_config import (
    VIDEO_OUTPUT_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    TTS_ENGINE, EDGE_TTS_VOICE, ELEVENLABS_API_KEY,
    HUM_ASSETS_DIR,
)

logger = logging.getLogger("etsai.growth.video_engine")

# Ensure output directories exist
os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)
os.makedirs(HUM_ASSETS_DIR, exist_ok=True)

# Brand colors
BRAND_GREEN = (74, 103, 65)       # #4a6741
BRAND_PEACH = (244, 132, 95)      # #f4845f
BRAND_CREAM = (253, 249, 243)     # #fdf9f3
BRAND_DARK = (28, 25, 23)         # #1c1917


# =============================================================
# TEXT-TO-SPEECH
# =============================================================

def generate_voiceover_edge(text, output_path):
    """Generate voiceover using Edge TTS (free, Microsoft voices)."""
    try:
        import edge_tts
        import asyncio

        async def _gen():
            communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
            await communicate.save(output_path)

        asyncio.run(_gen())
        logger.info(f"Video engine: Edge TTS voiceover saved to {output_path}")
        return output_path
    except ImportError:
        logger.error("edge-tts not installed: pip install edge-tts")
        return None
    except Exception as e:
        logger.error(f"Edge TTS error: {e}")
        return None


def generate_voiceover_elevenlabs(text, output_path):
    """Generate voiceover using ElevenLabs API (premium quality)."""
    if not ELEVENLABS_API_KEY:
        logger.warning("ElevenLabs API key not set")
        return None

    try:
        import requests
        resp = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=30,
        )
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
        else:
            logger.error(f"ElevenLabs error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"ElevenLabs error: {e}")
        return None


def generate_voiceover(text, output_path=None):
    """Generate voiceover using configured TTS engine."""
    if not output_path:
        output_path = os.path.join(VIDEO_OUTPUT_DIR, f"vo_{int(time.time())}.mp3")

    if TTS_ENGINE == "elevenlabs" and ELEVENLABS_API_KEY:
        return generate_voiceover_elevenlabs(text, output_path)
    return generate_voiceover_edge(text, output_path)


# =============================================================
# VIDEO ASSEMBLY (MoviePy)
# =============================================================

def _create_text_clip(text, fontsize=48, color="white", duration=5, position="center"):
    """Create a text clip with the given properties."""
    from moviepy.editor import TextClip
    return TextClip(
        text,
        fontsize=fontsize,
        color=color,
        font="Arial",
        size=(VIDEO_WIDTH - 100, None),
        method="caption",
    ).set_duration(duration).set_position(position)


def _create_gradient_background(duration, color1=BRAND_GREEN, color2=BRAND_DARK):
    """Create a vertical gradient background clip."""
    from moviepy.editor import ColorClip
    import numpy as np

    def make_frame(t):
        frame = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
        for y in range(VIDEO_HEIGHT):
            ratio = y / VIDEO_HEIGHT
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            frame[y, :] = [r, g, b]
        return frame

    from moviepy.editor import VideoClip
    return VideoClip(make_frame, duration=duration).set_fps(VIDEO_FPS)


def _create_solid_background(duration, color=BRAND_GREEN):
    """Create a solid color background."""
    from moviepy.editor import ColorClip
    return ColorClip(
        size=(VIDEO_WIDTH, VIDEO_HEIGHT),
        color=color,
        duration=duration,
    )


def _load_hum_image(pose="waving"):
    """Load a Hum mascot PNG overlay. Falls back to generating one via Pillow."""
    png_path = os.path.join(HUM_ASSETS_DIR, f"hum_{pose}.png")
    if os.path.exists(png_path):
        from moviepy.editor import ImageClip
        return ImageClip(png_path)

    # Generate a simple Hum placeholder via Pillow
    return _generate_hum_placeholder(pose)


def _generate_hum_placeholder(pose="waving"):
    """Generate a simple Hum mascot PNG using Pillow (placeholder until real art)."""
    try:
        from PIL import Image, ImageDraw

        size = 200
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Simple hummingbird shape
        # Body (forest green oval)
        draw.ellipse([50, 60, 150, 140], fill=(74, 103, 65, 255))
        # Breast (peach)
        draw.ellipse([70, 80, 130, 130], fill=(244, 132, 95, 255))
        # Head (green circle)
        draw.ellipse([90, 30, 140, 80], fill=(74, 103, 65, 255))
        # Eye (white + black)
        draw.ellipse([108, 42, 128, 62], fill=(255, 255, 255, 255))
        draw.ellipse([113, 47, 123, 57], fill=(0, 0, 0, 255))
        # Eye sparkle
        draw.ellipse([116, 48, 120, 52], fill=(255, 255, 255, 255))
        # Beak
        draw.polygon([(140, 55), (180, 50), (140, 65)], fill=(212, 132, 106, 255))
        # Wing
        draw.ellipse([40, 70, 90, 120], fill=(92, 125, 82, 255))
        # Tail
        draw.polygon([(50, 100), (20, 130), (30, 140), (60, 120)], fill=(61, 90, 55, 255))

        png_path = os.path.join(HUM_ASSETS_DIR, f"hum_{pose}.png")
        os.makedirs(os.path.dirname(png_path), exist_ok=True)
        img.save(png_path, "PNG")

        from moviepy.editor import ImageClip
        return ImageClip(png_path)
    except ImportError:
        logger.warning("Pillow not available for Hum generation")
        return None


def assemble_video(script_segments, voiceover_path=None, template="gradient",
                   hum_pose="waving", output_path=None):
    """
    Assemble a short-form vertical video.

    Args:
        script_segments: list of {"text": str, "duration": float}
        voiceover_path: path to audio file (optional)
        template: "gradient", "solid_green", "solid_dark"
        hum_pose: which Hum image to overlay
        output_path: where to save MP4

    Returns: output_path or None on error
    """
    try:
        from moviepy.editor import (
            CompositeVideoClip, AudioFileClip, concatenate_videoclips
        )
    except ImportError:
        logger.error("moviepy not installed: pip install moviepy")
        return None

    if not output_path:
        output_path = os.path.join(VIDEO_OUTPUT_DIR, f"video_{int(time.time())}.mp4")

    try:
        total_duration = sum(s.get("duration", 3) for s in script_segments)

        # Background
        if template == "gradient":
            bg = _create_gradient_background(total_duration)
        elif template == "solid_dark":
            bg = _create_solid_background(total_duration, BRAND_DARK)
        else:
            bg = _create_solid_background(total_duration, BRAND_GREEN)

        # Text overlays
        clips = [bg]
        current_time = 0
        for segment in script_segments:
            text = segment.get("text", "")
            duration = segment.get("duration", 3)
            fontsize = segment.get("fontsize", 48)

            text_clip = _create_text_clip(
                text, fontsize=fontsize, duration=duration,
                position=("center", VIDEO_HEIGHT // 3),
            ).set_start(current_time)

            clips.append(text_clip)
            current_time += duration

        # Hum mascot overlay (bottom-right, with bounce animation)
        hum = _load_hum_image(hum_pose)
        if hum:
            hum_sized = hum.resize(height=150).set_duration(total_duration)

            def hum_position(t):
                import math
                y_offset = int(10 * math.sin(t * 2))
                return (VIDEO_WIDTH - 200, VIDEO_HEIGHT - 250 + y_offset)

            hum_animated = hum_sized.set_position(hum_position)
            clips.append(hum_animated)

        # Composite
        video = CompositeVideoClip(clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT))

        # Audio
        if voiceover_path and os.path.exists(voiceover_path):
            audio = AudioFileClip(voiceover_path)
            video = video.set_audio(audio)

        # Export
        video.write_videofile(
            output_path,
            fps=VIDEO_FPS,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            logger=None,
        )

        # Cleanup
        video.close()
        logger.info(f"Video engine: Video saved to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Video assembly error: {e}")
        return None


# =============================================================
# THUMBNAIL GENERATION
# =============================================================

def create_thumbnail(title, hum_pose="waving", output_path=None):
    """Create a video thumbnail using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not available for thumbnail generation")
        return None

    if not output_path:
        output_path = os.path.join(VIDEO_OUTPUT_DIR, f"thumb_{int(time.time())}.png")

    try:
        # Create thumbnail (1280x720 for YouTube)
        img = Image.new("RGB", (1280, 720), BRAND_GREEN)
        draw = ImageDraw.Draw(img)

        # Title text
        try:
            font = ImageFont.truetype("arial.ttf", 56)
        except OSError:
            font = ImageFont.load_default()

        # Word wrap
        words = title.split()
        lines = []
        current_line = ""
        for word in words:
            test = f"{current_line} {word}".strip()
            if len(test) > 30:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test
        if current_line:
            lines.append(current_line)

        y = 200
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            draw.text(((1280 - w) // 2, y), line, fill="white", font=font)
            y += 70

        # Add Hum
        hum_path = os.path.join(HUM_ASSETS_DIR, f"hum_{hum_pose}.png")
        if os.path.exists(hum_path):
            hum_img = Image.open(hum_path).resize((150, 150))
            img.paste(hum_img, (1100, 540), hum_img if hum_img.mode == "RGBA" else None)

        img.save(output_path, "PNG")
        return output_path

    except Exception as e:
        logger.error(f"Thumbnail error: {e}")
        return None


# =============================================================
# YOUTUBE UPLOAD
# =============================================================

def upload_to_youtube(video_path, title, description, tags=None):
    """Upload a video to YouTube Shorts."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        logger.error("google-api-python-client not installed")
        return None

    from growth.growth_config import YOUTUBE_CREDENTIALS_FILE
    if not os.path.exists(YOUTUBE_CREDENTIALS_FILE):
        logger.warning("YouTube credentials not found — cannot upload")
        return None

    try:
        creds = Credentials.from_authorized_user_file(YOUTUBE_CREDENTIALS_FILE)
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or ["etsy", "custom orders", "etsai", "small business"],
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": "public",
                "madeForKids": False,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()

        video_id = response.get("id")
        video_url = f"https://youtube.com/shorts/{video_id}" if video_id else None
        logger.info(f"Video engine: Uploaded to YouTube — {video_url}")
        return {"video_id": video_id, "url": video_url}

    except Exception as e:
        logger.error(f"YouTube upload error: {e}")
        return None
