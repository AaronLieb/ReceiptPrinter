"""Compose images and text into a single tall receipt image."""

import os

from PIL import Image, ImageDraw, ImageFont

from . import PAPER_WIDTH

# Tried in order by find_font(). First one that exists wins.
SERIF_FONTS = [
    "/System/Library/Fonts/Supplemental/Didot.ttc",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/Library/Fonts/Georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]
SANS_FONTS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def find_font(size, candidates=SERIF_FONTS):
    """Load the first available TrueType font, falling back to Pillow's default."""
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def text_block(lines, width=PAPER_WIDTH, font=None, size=32, line_spacing=8, padding=10):
    """Render centered lines of text to a white image `width` wide.

    `lines` may be a string or a list. Each entry can also be a
    (text, size) tuple to mix sizes, e.g. [("Sam & Alex", 48), ("06.20.2027", 24)].
    """
    if isinstance(lines, str):
        lines = [lines]
    rendered = []
    for line in lines:
        text, line_size = line if isinstance(line, tuple) else (line, size)
        f = font if font and line_size == size else find_font(line_size)
        bbox = f.getbbox(text) if text else (0, 0, 0, line_size)
        rendered.append((text, f, bbox))

    height = padding * 2 + sum(b[3] - b[1] for _, _, b in rendered) + line_spacing * (len(rendered) - 1)
    img = Image.new("L", (width, max(height, 1)), 255)
    draw = ImageDraw.Draw(img)
    y = padding
    for text, f, (x0, y0, x1, y1) in rendered:
        draw.text(((width - (x1 - x0)) / 2 - x0, y - y0), text, font=f, fill=0)
        y += (y1 - y0) + line_spacing
    return img


def rule(width=PAPER_WIDTH, thickness=2, margin=60, padding=8):
    """A thin horizontal divider line."""
    img = Image.new("L", (width, thickness + padding * 2), 255)
    ImageDraw.Draw(img).rectangle([margin, padding, width - margin, padding + thickness - 1], fill=0)
    return img


def stack(parts, width=PAPER_WIDTH, gap=0):
    """Vertically stack images (centered) into one image `width` wide."""
    parts = [p for p in parts if p is not None]
    height = sum(p.height for p in parts) + gap * max(len(parts) - 1, 0)
    out = Image.new("L", (width, height), 255)
    y = 0
    for p in parts:
        out.paste(p.convert("L"), ((width - p.width) // 2, y))
        y += p.height + gap
    return out


def compose_strip(photos, header=None, footer=None, width=PAPER_WIDTH, gap=16, border=0):
    """Classic photobooth strip: optional header, photos top-to-bottom, optional footer.

    photos: PIL images, ideally already rendered at `width - 2*border`.
    header/footer: anything `text_block` accepts, or a ready-made PIL image.
    border: white margin on the left/right of each photo.
    """

    def as_block(x):
        if x is None or isinstance(x, Image.Image):
            return x
        return text_block(x, width=width)

    framed = []
    for p in photos:
        if border:
            target = width - 2 * border
            if p.width != target:
                p = p.resize((target, round(p.height * target / p.width)))
        framed.append(p)

    parts = [as_block(header)] + framed + [as_block(footer)]
    return stack(parts, width=width, gap=gap)
