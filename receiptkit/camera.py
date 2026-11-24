"""Webcam helpers (OpenCV)."""

import time

import cv2

# Average brightness (0-255) below which a frame counts as "black". Cameras that
# are opened but not really streaming (e.g. a locked iPhone Continuity Camera,
# which macOS often lists as index 0) return all-zero frames.
BLACK_THRESHOLD = 8


def is_black(frame):
    return frame is None or frame.mean() < BLACK_THRESHOLD


def _open_and_warm(index, warmup):
    """Open camera `index` and read until it gives a non-black frame or `warmup` seconds pass."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return None
    deadline = time.monotonic() + warmup
    while time.monotonic() < deadline:
        ok, frame = cap.read()
        if ok and not is_black(frame):
            return cap
    cap.release()
    return None


def find_camera(max_index=4, warmup=2.0):
    """Return the index of the first camera that delivers a real (non-black) picture."""
    for i in range(max_index):
        cap = _open_and_warm(i, warmup)
        if cap is not None:
            cap.release()
            return i
    raise RuntimeError("No working camera found (all cameras missing or returning black frames)")


class Camera:
    """Context-managed webcam that stays open between shots.

    index=None picks the first camera that returns a real picture, skipping
    ones that open but only send black frames. Cameras also return dark frames
    for a moment after opening while auto-exposure settles, so open() waits
    up to `warmup` seconds for a usable frame.
    """

    def __init__(self, index=None, warmup=3.0, width=None, height=None, max_index=4):
        self.index = index
        self.warmup = warmup
        self.width = width
        self.height = height
        self.max_index = max_index
        self.cap = None

    def open(self):
        indexes = [self.index] if self.index is not None else range(self.max_index)
        for i in indexes:
            cap = _open_and_warm(i, self.warmup)
            if cap is not None:
                self.cap, self.index = cap, i
                break
        else:
            which = f"camera {self.index}" if self.index is not None else "any camera"
            raise RuntimeError(
                f"Couldn't get a picture from {which} (missing or only black frames). Check camera permissions for your terminal "
                "(System Settings > Privacy & Security > Camera) and that the camera isn't in use."
            )
        if self.width:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if self.height:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        print(f"Using camera {self.index}")
        return self

    def read(self):
        """Return the latest BGR frame."""
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise RuntimeError("Failed to capture frame")
        return frame

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *exc):
        self.close()


def capture_frame(index=None, warmup=3.0):
    """One-shot capture: open the camera, grab a frame, close it."""
    with Camera(index, warmup=warmup) as cam:
        return cam.read()
