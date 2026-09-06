# -*- coding: utf-8 -*-
"""Overlay the approved title on the generated second-video cover background."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'work' / 'build' / '封面-机器人如何看见世界-无文字.png'
OUTPUT = ROOT / 'outputs' / '封面-机器人如何看见世界.png'
W, H = 1920, 1080
FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'


def main():
    image = Image.open(SOURCE).convert('RGB')
    scale = max(W / image.width, H / image.height)
    scaled = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left = (scaled.width - W) // 2
    top = (scaled.height - H) // 2
    canvas = scaled.crop((left, top, left + W, top + H))
    draw = ImageDraw.Draw(canvas)
    # Match the first film: oversized W6 white title, a tight dark shadow,
    # and one warm engineering-orange underline.
    font = ImageFont.truetype(FONT, 142, index=2)
    lines = ['机器人如何', '看见世界？']
    x, y = 126, 252
    for line in lines:
        draw.text((x + 8, y + 10), line, font=font, fill=(2, 10, 22), stroke_width=5, stroke_fill=(2, 10, 22))
        draw.text((x, y), line, font=font, fill=(252, 252, 250), stroke_width=1, stroke_fill=(252, 252, 250))
        y += 166
    draw.polygon([(126, 603), (825, 571), (830, 592), (121, 624)], fill=(255, 72, 30))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, quality=95)
    print(OUTPUT)


if __name__ == '__main__':
    main()
