"""Image processing for thermal printing.

Everything here takes OpenCV-style numpy arrays (BGR or grayscale) and the
`render_*` functions return a 1-bit PIL image sized for the paper, ready to
hand to `printer.print_image` or `layout.compose_strip`.

Always resize *before* dithering: scaling a dithered image destroys the dot
pattern and turns it to mush.
"""

import cv2
import numpy as np
from PIL import Image

from . import PAPER_WIDTH


# --- geometry ---------------------------------------------------------------


def crop_to_aspect(img, aspect):
    """Center-crop to width/height ratio `aspect` (e.g. 4/3, 1.0)."""
    h, w = img.shape[:2]
    if w / h > aspect:
        new_w = int(h * aspect)
        x = (w - new_w) // 2
        return img[:, x : x + new_w]
    new_h = int(w / aspect)
    y = (h - new_h) // 2
    return img[y : y + new_h, :]


def resize_to_width(img, width=PAPER_WIDTH):
    h, w = img.shape[:2]
    height = round(width * h / w)
    interp = cv2.INTER_AREA if width < w else cv2.INTER_CUBIC
    return cv2.resize(img, (width, height), interpolation=interp)


def mirror(img):
    """Flip horizontally, so output matches what people saw in the preview."""
    return cv2.flip(img, 1)


# --- tone -------------------------------------------------------------------


def to_gray(img):
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def adjust_tone(gray, contrast=1.0, brightness=0, gamma=1.0, equalize=True):
    """Tone-map a grayscale image for thermal paper.

    equalize:   local contrast (CLAHE) so faces don't go flat in dim venues
    gamma > 1:  lifts midtones; thermal heads print dark, so ~1.2-1.5 helps
    """
    if equalize:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
    # Pivot around mid-gray so contrast pushes darks darker and lights lighter
    # (plain scaling would just brighten everything).
    gray = cv2.convertScaleAbs(gray, alpha=contrast, beta=128 * (1 - contrast) + brightness)
    if gamma != 1.0:
        lut = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in range(256)], np.uint8)
        gray = cv2.LUT(gray, lut)
    return gray


def sharpen(gray, amount=1.0, radius=3):
    """Unsharp mask. Dithering softens edges, so a little sharpening helps."""
    blurred = cv2.GaussianBlur(gray, (0, 0), radius)
    return cv2.addWeighted(gray, 1 + amount, blurred, -amount, 0)


# --- final renderers (return 1-bit PIL images) -----------------------------


def render_dither(img, width=PAPER_WIDTH, contrast=1.4, brightness=10, gamma=1.3, sharpness=0.8):
    """Photo-style output: Floyd-Steinberg dithered grayscale."""
    gray = to_gray(resize_to_width(img, width))
    gray = adjust_tone(gray, contrast=contrast, brightness=brightness, gamma=gamma)
    if sharpness:
        gray = sharpen(gray, amount=sharpness)
    return Image.fromarray(gray).convert("1", dither=Image.Dither.FLOYDSTEINBERG)


def edge_mask(img, low=30, high=70, thickness=2, contrast=1.5, blur=7):
    """Boolean mask (True = edge) from Canny, at the input's resolution."""
    gray = to_gray(img)
    gray = cv2.convertScaleAbs(gray, alpha=contrast, beta=0)
    if blur:
        gray = cv2.GaussianBlur(gray, (blur, blur), 0)
    edges = cv2.Canny(gray, low, high)
    if thickness:
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=thickness)
    return edges > 0


def render_line_art(img, width=PAPER_WIDTH, low=30, high=70, thickness=2, contrast=1.5):
    """Sketch-style output: black Canny edges on white (the original photo_print look)."""
    lines = np.where(edge_mask(img, low, high, thickness, contrast), 0, 255).astype(np.uint8)
    lines = resize_to_width(lines, width)
    _, lines = cv2.threshold(lines, 127, 255, cv2.THRESH_BINARY)
    return Image.fromarray(lines).convert("1", dither=Image.Dither.NONE)


def render_combo(
    img,
    width=PAPER_WIDTH,
    contrast=1.5,
    gamma=1.6,
    brightness=20,
    sharpness=0.5,
    low=40,
    high=100,
    thickness=1,
    edge_scale=2,
):
    """Dithered photo with black edge outlines drawn on top.

    The dither is printed a little lighter than `render_dither` (higher gamma
    and brightness) so the outlines stand out. Edges are found at
    `edge_scale` x the output width and then shrunk, which gives thinner,
    cleaner lines than running Canny on the small image.
    """
    shaded = np.array(
        render_dither(
            img, width=width, contrast=contrast, gamma=gamma, brightness=brightness, sharpness=sharpness
        ).convert("L")
    )

    big = resize_to_width(img, width * edge_scale)
    mask = edge_mask(big, low=low, high=high, thickness=thickness).astype(np.uint8) * 255
    mask = cv2.resize(mask, (shaded.shape[1], shaded.shape[0]), interpolation=cv2.INTER_AREA) > 96

    shaded[mask] = 0
    return Image.fromarray(shaded).convert("1", dither=Image.Dither.NONE)


RENDERERS = {
    "dither": render_dither,
    "lines": render_line_art,
    "combo": render_combo,
}


def render(img, style="dither", width=PAPER_WIDTH, **kwargs):
    """Render with a named style from RENDERERS."""
    try:
        fn = RENDERERS[style]
    except KeyError:
        raise ValueError(f"Unknown style {style!r}; choose from {sorted(RENDERERS)}")
    return fn(img, width=width, **kwargs)
