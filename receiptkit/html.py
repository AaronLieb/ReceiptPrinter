"""Render HTML templates to images via headless Chrome (html2image)."""

import os

from . import PAPER_WIDTH


def render_template(path, **values):
    """Read an HTML file and replace `{{key}}` placeholders with values."""
    with open(path) as f:
        html = f.read()
    for key, value in values.items():
        html = html.replace("{{" + key + "}}", str(value))
    return html


def html_to_image(html, output_path, width=PAPER_WIDTH, height=300):
    """Screenshot an HTML string to `output_path` and return that path."""
    from html2image import Html2Image

    out_dir, name = os.path.split(os.path.abspath(output_path))
    Html2Image(output_path=out_dir, size=(width, height)).screenshot(html_str=html, save_as=name)
    return output_path
