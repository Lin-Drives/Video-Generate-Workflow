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
    font = ImageFont.truetype(FONT, 104, index=2)
    lines = ['机器人如何', '看见世界？']
    x, y = 132, 360
    for line in lines:
        draw.text((x, y), line, font=font, fill=(245, 249, 255), stroke_width=3, stroke_fill=(3, 14, 31))
        y += 132
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, quality=95)
    print(OUTPUT)


if __name__ == '__main__':
    main()
