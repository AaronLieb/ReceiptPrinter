from escpos.printer import Usb
from html2image import Html2Image


WIDTH = 512
HEIGHT = 606
IMAGE_PATH = "stages_html.png"
HTML_PATH = "stages.html"


def html_to_image(html_content, output_path=IMAGE_PATH):
    hti = Html2Image(output_path=".", size=(WIDTH, HEIGHT))
    hti.screenshot(html_str=html_content, save_as=output_path)
    return output_path


with open(HTML_PATH) as f:
    template = f.read()

img_path = html_to_image(template)

p = Usb(0x04B8, 0x0202, 0, profile="TM-T88IV")
p.image(img_path)
p.cut()
