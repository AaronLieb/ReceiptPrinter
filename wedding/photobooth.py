"""Wedding photobooth: live preview, countdown, 4 shots, printed as a strip.

Run from the repo root:
    python -m wedding.photobooth --title "Sam & Alex" --subtitle "June 20, 2027"
    python -m wedding.photobooth --no-print      # test without the printer

Controls (in the preview window):
    SPACE / ENTER   start a session (a USB "big button" that sends a key works too)
    Q / ESC         quit
"""

import argparse
import math
import os
import time
from datetime import datetime

import cv2
import numpy as np

from receiptkit import PAPER_WIDTH, imaging, layout, printer
from receiptkit.camera import Camera

WINDOW = "Photobooth"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

START_KEYS = {ord(" "), 13}
QUIT_KEYS = {ord("q"), 27}


# --- on-screen overlays -----------------------------------------------------


def draw_text(frame, text, scale, y_frac=0.5, thickness=None):
    """Centered white text with a black outline so it reads on any background."""
    thickness = thickness or max(2, int(scale * 2.5))
    font = cv2.FONT_HERSHEY_DUPLEX
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    h, w = frame.shape[:2]
    org = ((w - tw) // 2, int(h * y_frac + th / 2))
    cv2.putText(frame, text, org, font, scale, (0, 0, 0), thickness * 3, cv2.LINE_AA)
    cv2.putText(frame, text, org, font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
    return frame


def show(frame):
    cv2.imshow(WINDOW, frame)
    return cv2.waitKey(1) & 0xFF


class Quit(Exception):
    pass


# --- photobooth -------------------------------------------------------------


class Photobooth:
    def __init__(self, args):
        self.args = args
        self.cam = Camera(args.camera)

    def preview(self):
        frame = self.cam.read()
        if self.args.mirror:
            frame = imaging.mirror(frame)
        return frame

    def wait_for_start(self):
        while True:
            frame = draw_text(self.preview(), self.args.title, 2.0, 0.15)
            draw_text(frame, "Press the button to start!", 1.4, 0.85)
            key = show(frame)
            if key in QUIT_KEYS:
                raise Quit
            if key in START_KEYS:
                return

    def countdown(self, seconds, shot, total):
        end = time.monotonic() + seconds
        while (remaining := end - time.monotonic()) > 0:
            frame = draw_text(self.preview(), str(math.ceil(remaining)), 8.0, 0.5)
            draw_text(frame, f"Photo {shot} of {total}", 1.2, 0.9)
            if show(frame) in QUIT_KEYS:
                raise Quit

    def flash_and_capture(self):
        frame = self.preview()  # grab before the screen goes white
        white = np.full_like(frame, 255)
        show(white)
        cv2.waitKey(120)
        return frame

    def review(self, frame, seconds):
        """Freeze-frame on the photo that was just taken."""
        still = frame.copy()
        draw_text(still, "Nice!", 2.0, 0.9)
        show(still)
        cv2.waitKey(int(seconds * 1000))

    def message(self, text, frame=None):
        frame = frame if frame is not None else self.preview()
        frame = (frame * 0.4).astype(np.uint8)
        show(draw_text(frame, text, 2.0, 0.5))
        cv2.waitKey(1)

    def run_session(self):
        a = self.args
        shots = []
        for i in range(1, a.shots + 1):
            self.countdown(a.countdown if i == 1 else a.delay, i, a.shots)
            frame = self.flash_and_capture()
            shots.append(frame)
            self.review(frame, a.review)

        self.message("Printing...", shots[-1])
        strip = self.build_strip(shots)
        self.save(shots, strip)
        if not a.no_print:
            try:
                printer.print_image(strip)
            except Exception as e:  # keep the booth running if the printer hiccups
                print(f"Print failed: {e}")
                self.message("Printer problem - get help!")
                cv2.waitKey(3000)
                return
        self.message("Grab your photos below!")
        cv2.waitKey(int(a.thanks * 1000))

    def build_strip(self, shots):
        a = self.args
        photo_width = PAPER_WIDTH - 2 * a.border
        photos = [imaging.crop_to_aspect(s, a.aspect) for s in shots]
        rendered = [imaging.render(p, style=a.style, width=photo_width) for p in photos]
        header = [(a.title, 44)]
        if a.subtitle:
            header.append((a.subtitle, 26))
        footer = [(a.footer, 24)] if a.footer else None
        return layout.compose_strip(
            rendered,
            header=layout.stack([layout.text_block(header), layout.rule()]),
            footer=footer,
            gap=a.gap,
            border=a.border,
        )

    def save(self, shots, strip):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        folder = os.path.join(OUTPUT_DIR, stamp)
        os.makedirs(folder, exist_ok=True)
        for i, s in enumerate(shots, 1):
            cv2.imwrite(os.path.join(folder, f"shot{i}.jpg"), s)
        strip.save(os.path.join(folder, "strip.png"))
        print(f"Saved {folder}")

    def run(self):
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        if self.args.fullscreen:
            cv2.setWindowProperty(
                WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
            )
        with self.cam:
            try:
                while True:
                    self.wait_for_start()
                    self.run_session()
            except (Quit, KeyboardInterrupt):
                pass
            finally:
                cv2.destroyAllWindows()


def parse_aspect(s):
    if ":" in s:
        w, h = s.split(":")
        return float(w) / float(h)
    return float(s)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--title", default="Josh and Esme", help="big header text, e.g. 'Sam & Alex'"
    )
    p.add_argument(
        "--subtitle",
        default=datetime.now().strftime("%B %d, %Y"),
        help="line under the title ('' to hide)",
    )
    p.add_argument("--footer", default="", help="optional text under the photos")
    p.add_argument("--shots", type=int, default=4, help="photos per strip")
    p.add_argument(
        "--countdown", type=float, default=5, help="seconds before the first photo"
    )
    p.add_argument("--delay", type=float, default=3, help="seconds between photos")
    p.add_argument(
        "--review",
        type=float,
        default=1.0,
        help="seconds to show each photo after it's taken",
    )
    p.add_argument(
        "--thanks", type=float, default=4, help="seconds to show the end screen"
    )
    p.add_argument(
        "--style",
        choices=sorted(imaging.RENDERERS),
        default="dither",
        help="dither=photo, lines=sketch, combo=photo with sketch outlines",
    )
    p.add_argument(
        "--aspect",
        type=parse_aspect,
        default=4 / 3,
        help="photo crop, e.g. 4:3, 1:1, 16:9",
    )
    p.add_argument(
        "--gap", type=int, default=16, help="white space between photos (dots)"
    )
    p.add_argument(
        "--border",
        type=int,
        default=16,
        help="white margin left/right of photos (dots)",
    )
    p.add_argument(
        "--camera",
        type=int,
        default=None,
        help="camera index (default: first one with a picture)",
    )
    p.add_argument(
        "--no-mirror",
        dest="mirror",
        action="store_false",
        help="don't mirror the preview/photos",
    )
    p.add_argument(
        "--windowed",
        dest="fullscreen",
        action="store_false",
        help="don't go fullscreen",
    )
    p.add_argument(
        "--no-print", action="store_true", help="save strips without printing"
    )
    Photobooth(p.parse_args()).run()


if __name__ == "__main__":
    main()
