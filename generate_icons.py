"""Generate PWA PNG icons matching the ETSAI hummingbird favicon. Run once."""
from PIL import Image, ImageDraw
import math
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "static", "icons")
os.makedirs(OUT_DIR, exist_ok=True)

# Colors matching the SVG favicon exactly
BG = (245, 239, 228)           # cream #f5efe4
WING = (92, 125, 82)           # #5c7d52
BODY = (74, 103, 65)           # #4a6741
BELLY = (244, 132, 95)         # #f4845f
BEAK = (212, 132, 106)         # #d4846a
EYE_WHITE = (255, 255, 255)
PUPIL = (44, 24, 16)           # #2c1810
TAIL = (61, 90, 55)            # #3d5a37


def draw_hummingbird(size):
    """Draw the ETSAI hummingbird at the given icon size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rect background
    r = int(size * 0.188)  # ~96/512
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=BG)

    # The original SVG bird is in a 48x48 viewBox.
    # Key coordinates (in SVG space):
    #   Wing:  ellipse cx=12 cy=22 rx=9 ry=5 rotated -25deg
    #   Body:  ellipse cx=20 cy=27 rx=10 ry=7
    #   Belly: ellipse cx=23 cy=29 rx=7 ry=5
    #   Head:  circle cx=27 cy=15 r=9
    #   Beak:  triangle (35,13) (48,11.5) (35,16.5)
    #   Eye white: circle cx=31 cy=13 r=3
    #   Pupil: circle cx=32 cy=13 r=1.8
    #   Highlight: circle cx=32.5 cy=12 r=0.7
    #   Tail:  lines from (8,31) down

    # Scale factor: map 48x48 SVG to fill icon with padding
    # Center the bird in the icon
    scale = size / 48 * 0.78
    ox = size * 0.12  # offset x
    oy = size * 0.12  # offset y

    def s(x, y):
        """Scale SVG coords to icon coords."""
        return (x * scale + ox, y * scale + oy)

    def ellipse(cx, cy, rx, ry, fill, rotation=0):
        """Draw an ellipse, optionally rotated."""
        if rotation == 0:
            x1, y1 = s(cx - rx, cy - ry)
            x2, y2 = s(cx + rx, cy + ry)
            draw.ellipse([x1, y1, x2, y2], fill=fill)
        else:
            # For rotated ellipse, draw as polygon approximation
            points = []
            rad = math.radians(rotation)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            for i in range(64):
                angle = 2 * math.pi * i / 64
                px = rx * math.cos(angle)
                py = ry * math.sin(angle)
                # Rotate
                rpx = px * cos_r - py * sin_r + cx
                rpy = px * sin_r + py * cos_r + cy
                points.append(s(rpx, rpy))
            draw.polygon(points, fill=fill)

    def circle(cx, cy, r, fill):
        x1, y1 = s(cx - r, cy - r)
        x2, y2 = s(cx + r, cy + r)
        draw.ellipse([x1, y1, x2, y2], fill=fill)

    def triangle(p1, p2, p3, fill):
        draw.polygon([s(*p1), s(*p2), s(*p3)], fill=fill)

    # Draw in order (back to front):
    # 1. Wing (rotated ellipse)
    ellipse(12, 22, 9, 5, WING, rotation=-25)

    # 2. Body
    ellipse(20, 27, 10, 7, BODY)

    # 3. Belly
    ellipse(23, 29, 7, 5, BELLY)

    # 4. Head
    circle(27, 15, 9, BODY)

    # 5. Beak
    triangle((35, 13), (48, 11.5), (35, 16.5), BEAK)

    # 6. Eye white
    circle(31, 13, 3, EYE_WHITE)

    # 7. Pupil
    circle(32, 13, 1.8, PUPIL)

    # 8. Eye highlight
    circle(32.5, 12, 0.7, EYE_WHITE)

    # 9. Tail feathers (simplified as small triangles)
    tail_points = [
        ((8, 31), (3, 38), (7, 34)),
        ((7, 34), (4, 41), (9, 33)),
    ]
    for p1, p2, p3 in tail_points:
        triangle(p1, p2, p3, TAIL)

    return img


# Generate all sizes
for icon_size, filename in [(192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")]:
    img = draw_hummingbird(icon_size)
    img.save(os.path.join(OUT_DIR, filename), "PNG")
    print(f"Generated {filename} ({icon_size}x{icon_size})")

print("Done!")
