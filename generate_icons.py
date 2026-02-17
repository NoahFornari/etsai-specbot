"""Generate PWA PNG icons from the ETSAI brand colors. Run once."""
from PIL import Image, ImageDraw, ImageFont
import os

SIZES = [192, 512]
OUT_DIR = os.path.join(os.path.dirname(__file__), "static", "icons")
os.makedirs(OUT_DIR, exist_ok=True)

BG_COLOR = (74, 103, 65)       # forest green #4a6741
BIRD_BODY = (107, 148, 96)     # lighter green
BIRD_BELLY = (244, 132, 95)    # coral #f4845f
TEXT_COLOR = (255, 255, 255)

for size in SIZES:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rect background
    r = size // 5
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=BG_COLOR)

    # Draw a simple bird silhouette (circle head + ellipse body)
    cx, cy = size * 0.5, size * 0.32
    head_r = size * 0.12
    draw.ellipse([cx - head_r, cy - head_r, cx + head_r, cy + head_r], fill=BIRD_BODY)

    # Body
    bx, by = size * 0.45, size * 0.42
    bw, bh = size * 0.22, size * 0.14
    draw.ellipse([bx - bw, by - bh, bx + bw, by + bh], fill=BIRD_BODY)

    # Belly
    draw.ellipse([bx - bw * 0.6, by - bh * 0.5, bx + bw * 0.6, by + bh * 0.7], fill=BIRD_BELLY)

    # Eye
    eye_r = size * 0.025
    ex, ey = cx + size * 0.03, cy - size * 0.01
    draw.ellipse([ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r], fill=(255, 255, 255))
    pupil_r = eye_r * 0.6
    draw.ellipse([ex - pupil_r + 1, ey - pupil_r, ex + pupil_r + 1, ey + pupil_r], fill=(44, 24, 16))

    # Beak
    beak_x = cx + head_r * 0.8
    beak_y = cy + size * 0.01
    draw.polygon([
        (beak_x, beak_y - size * 0.015),
        (beak_x + size * 0.06, beak_y),
        (beak_x, beak_y + size * 0.015),
    ], fill=(212, 132, 106))

    # "ETSAI" text
    text = "ETSAI"
    font_size = int(size * 0.18)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) / 2
    ty = size * 0.68
    draw.text((tx, ty), text, fill=TEXT_COLOR, font=font)

    out_path = os.path.join(OUT_DIR, f"icon-{size}.png")
    img.save(out_path, "PNG")
    print(f"Generated {out_path}")

# Also generate apple-touch-icon (180x180)
size = 180
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
r = size // 5
draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=BG_COLOR)
cx, cy = size * 0.5, size * 0.32
head_r = size * 0.12
draw.ellipse([cx - head_r, cy - head_r, cx + head_r, cy + head_r], fill=BIRD_BODY)
bx, by = size * 0.45, size * 0.42
bw, bh = size * 0.22, size * 0.14
draw.ellipse([bx - bw, by - bh, bx + bw, by + bh], fill=BIRD_BODY)
draw.ellipse([bx - bw * 0.6, by - bh * 0.5, bx + bw * 0.6, by + bh * 0.7], fill=BIRD_BELLY)
eye_r = size * 0.025
ex, ey = cx + size * 0.03, cy - size * 0.01
draw.ellipse([ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r], fill=(255, 255, 255))
pupil_r = eye_r * 0.6
draw.ellipse([ex - pupil_r + 1, ey - pupil_r, ex + pupil_r + 1, ey + pupil_r], fill=(44, 24, 16))
draw.polygon([
    (cx + head_r * 0.8, cy + size * 0.01 - size * 0.015),
    (cx + head_r * 0.8 + size * 0.06, cy + size * 0.01),
    (cx + head_r * 0.8, cy + size * 0.01 + size * 0.015),
], fill=(212, 132, 106))
text = "ETSAI"
font_size = int(size * 0.18)
try:
    font = ImageFont.truetype("arial.ttf", font_size)
except (OSError, IOError):
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()
bbox = draw.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((size - tw) / 2, size * 0.68), text, fill=TEXT_COLOR, font=font)
img.save(os.path.join(OUT_DIR, "apple-touch-icon.png"), "PNG")
print(f"Generated apple-touch-icon.png")
