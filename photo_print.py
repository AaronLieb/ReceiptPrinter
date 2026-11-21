import cv2
import webbrowser
import numpy as np
from escpos.printer import Usb

WIDTH = 512

webbrowser.open(
    "data:text/html,<body style='background:white'><h1><center>Say Cheese!</center></h1></body>"
)

cap = cv2.VideoCapture(0)
frame = None
for x in range(10):
    ret, frame = cap.read()
cap.release()

cv2.imwrite("photo.png", frame)

if not ret:
    raise Exception("Failed to capture image")

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
gray = cv2.GaussianBlur(gray, (7, 7), 0)
edges = cv2.Canny(gray, 30, 70)
kernel = np.ones((3, 3), np.uint8)
edges = cv2.dilate(edges, kernel, iterations=2)
edges = cv2.bitwise_not(edges)

aspect = edges.shape[0] / edges.shape[1]
new_height = int(WIDTH * aspect)
edges = cv2.resize(edges, (WIDTH, new_height))
cv2.imwrite("photo_receipt.png", edges)


p = Usb(0x04B8, 0x0202, 0, profile="TM-T88IV")
p.text("Ummm.. I don't know man\n")
p.image("photo_receipt.png")
p.text("--SuperKernel\n")
p.cut()
