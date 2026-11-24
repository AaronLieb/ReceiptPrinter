import webbrowser

import cv2

from receiptkit import imaging
from receiptkit.camera import capture_frame
from receiptkit.printer import get_printer

webbrowser.open(
    "data:text/html,<body style='background:white'><h1><center>Say Cheese!</center></h1></body>"
)

frame = capture_frame()
cv2.imwrite("photo.png", frame)

art = imaging.render_line_art(frame)
art.save("photo_receipt.png")

p = get_printer()
p.text("Ummm.. I don't know man\n")
p.image(art.convert("L"))
p.text("--SuperKernel\n")
p.cut()
