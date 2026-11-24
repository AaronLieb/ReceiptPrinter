from receiptkit.html import html_to_image, render_template
from receiptkit.printer import print_image

html = render_template("stages.html")
print_image(html_to_image(html, "stages_html.png", height=606))
