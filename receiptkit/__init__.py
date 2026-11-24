"""Shared helpers for driving the receipt printer.

Modules:
    printer  - connect to the Epson TM-T88IV and print images
    camera   - grab frames from a webcam
    imaging  - turn photos into something that looks good on thermal paper
    layout   - compose multiple images + text into one tall receipt image
    html     - render an HTML template to an image
"""

PAPER_WIDTH = 512  # printable width of the TM-T88IV in dots
