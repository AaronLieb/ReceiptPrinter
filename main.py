from datetime import datetime

from receiptkit.html import html_to_image, render_template
from receiptkit.printer import print_image

task_title = input("Title: ")

html = render_template(
    "receipt.html",
    task=task_title,
    stars="***",
    date=datetime.now().strftime("%B %d"),
)
print_image(html_to_image(html, "receipt.png", height=300))
