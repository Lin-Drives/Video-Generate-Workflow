# -*- coding: utf-8 -*-
"""Overlay regular or tech-style titles on the approved second-video cover background."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'work' / 'build' / '封面-机器人如何看见世界-无文字.png'
OUTPUT = ROOT / 'outputs' / '封面-机器人如何看见世界.png'
TECH_OUTPUT = ROOT / 'outputs' / '封面-机器人如何看见世界-科技字体.png'
W, H = 1920, 1080
FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'


def cover_background():
    image = Image.open(SOURCE).convert('RGB')
    scale = max(W / image.width, H / image.height)
    scaled = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left = (scaled.width - W) // 2
    top = (scaled.height - H) // 2
    canvas = scaled.crop((left, top, left + W, top + H))
    return scaled.crop((left, top, left + W, top + H)).convert('RGBA')


def add_regular_title(canvas):
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


def add_tech_title(canvas):
    """Use the first video tech-cover language without changing the approved background."""
    font = ImageFont.truetype(FONT, 142, index=2)
    lines = ['机器人如何', '看见世界？']
    x, y = 126, 252

    # Layered cyan glow gives the otherwise neutral system font a technical edge.
    mask = Image.new('L', (W, H), 0)
    mask_draw = ImageDraw.Draw(mask)
    text_y = y
    for line in lines:
        mask_draw.text((x, text_y), line, font=font, fill=255, stroke_width=2, stroke_fill=255)
        text_y += 166
    for radius, opacity in ((28, 105), (9, 180)):
        glow = Image.new('RGBA', (W, H), (18, 129, 255, 0))
        blurred = mask.filter(ImageFilter.GaussianBlur(radius))
        glow.putalpha(blurred.point(lambda value: value * opacity // 255))
        canvas.alpha_composite(glow)

    draw = ImageDraw.Draw(canvas)
    # Energy rail and slanted micro accents echo the earlier blue tech cover.
    draw.line((112, 242, 875, 207), fill=(33, 148, 255, 160), width=3)
    draw.line((112, 246, 790, 215), fill=(170, 228, 255, 120), width=1)
    draw.polygon([(105, 235), (142, 233), (128, 248)], fill=(106, 204, 255, 230))
    draw.polygon([(842, 209), (876, 207), (862, 221)], fill=(106, 204, 255, 190))

    text_y = y
    for line in lines:
        draw.text(
            (x, text_y), line, font=font, fill=(248, 253, 255, 255),
            stroke_width=3, stroke_fill=(67, 170, 255, 255),
        )
        # Thin offset highlight makes the title feel engineered rather than bubbly.
        draw.text((x + 3, text_y - 2), line, font=font, fill=(255, 255, 255, 255))
        text_y += 166

    draw.polygon([(126, 603), (825, 571), (830, 592), (121, 624)], fill=(255, 72, 30, 255))
    for offset in range(0, 70, 14):
        draw.line((740 + offset, 582 - offset // 3, 752 + offset, 577 - offset // 3), fill=(255, 184, 114, 255), width=2)


def main():
    tech_style = '--tech' in sys.argv
    canvas = cover_background()
    if tech_style:
        add_tech_title(canvas)
        output = TECH_OUTPUT
    else:
        add_regular_title(canvas)
        output = OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert('RGB').save(output, quality=95)
    print(output)


if __name__ == '__main__':
    main()
