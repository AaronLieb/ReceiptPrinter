"""Printer connection and output helpers."""

from PIL import Image

EPSON_VENDOR_ID = 0x04B8
TM_T88IV_PRODUCT_ID = 0x0202
PROFILE = "TM-T88IV"


def get_printer():
    """Open a USB connection to the receipt printer."""
    from escpos.printer import Usb

    return Usb(EPSON_VENDOR_ID, TM_T88IV_PRODUCT_ID, 0, profile=PROFILE)


def print_image(image, printer=None, cut=True):
    """Print a PIL image or image path. Opens (and closes) a printer if none is given."""
    owns_printer = printer is None
    printer = printer or get_printer()
    try:
        if isinstance(image, Image.Image):
            image = image.convert("L")
        printer.image(image)
        if cut:
            printer.cut()
    finally:
        if owns_printer:
            printer.close()
