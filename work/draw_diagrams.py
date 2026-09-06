# -*- coding: utf-8 -*-
"""绘制《机器人怎么"看见"世界？》的 3 张图形化分镜示意图（1920x1080，无文字）。"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'assets' / 'ow12'
W, H = 1920, 1080
SS = 2  # 超采样抗锯齿

BG_TOP = (11, 22, 41)
BG_BOTTOM = (18, 38, 66)
ORANGE = (245, 160, 76)
TEAL = (57, 197, 176)
LINE = (198, 214, 238)
LINE_DIM = (140, 160, 190)


def S(v):
    return int(round(v * SS))


def P(p):
    return (S(p[0]), S(p[1]))


def new_canvas():
    img = Image.new('RGB', (W * SS, H * SS))
    px = img.load()
    for y in range(H * SS):
        t = y / (H * SS - 1)
        row = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3))
        for x in range(W * SS):
            px[x, y] = row
    # 中央轻微径向提亮，避免背景死板
    glow = Image.new('L', (W * SS, H * SS), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([S(360), S(120), S(1560), S(960)], fill=26)
    glow = glow.filter(ImageFilter.GaussianBlur(S(220)))
    img = Image.composite(Image.new('RGB', img.size, (36, 62, 100)), img, glow)
    return img, ImageDraw.Draw(img, 'RGBA')


def finish(img, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = img.resize((W, H), Image.LANCZOS)
    out.save(OUT_DIR / name)
    print(f'已输出 {OUT_DIR / name}')


def dash_line(d, p0, p1, color, width, dash=14, gap=10):
    x0, y0, x1, y1 = p0[0], p0[1], p1[0], p1[1]
    length = math.hypot(x1 - x0, y1 - y0)
    if length == 0:
        return
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        d.line([P((x0 + ux * pos, y0 + uy * pos)), P((x0 + ux * end, y0 + uy * end))],
               fill=color, width=S(width))
        pos += dash + gap


def cubic_points(p0, p1, p2, p3, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        pts.append(P((x, y)))
    return pts


def draw_lens(d, cx, cy, r):
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)],
              outline=LINE + (255,), width=S(5))
    d.ellipse([S(cx - r * 0.62), S(cy - r * 0.62), S(cx + r * 0.62), S(cy + r * 0.62)],
              fill=(10, 18, 34, 255), outline=TEAL + (255,), width=S(4))
    d.ellipse([S(cx - r * 0.30), S(cy - r * 0.30), S(cx + r * 0.30), S(cy + r * 0.30)],
              fill=(16, 30, 52, 255), outline=TEAL + (160,), width=S(2))
    # 镜片高光
    d.arc([S(cx - r * 0.48), S(cy - r * 0.48), S(cx + r * 0.48), S(cy + r * 0.48)],
          start=200, end=280, fill=(235, 242, 252, 220), width=S(5))
    d.ellipse([S(cx - r * 0.13), S(cy - r * 0.42), S(cx + r * 0.07), S(cy - r * 0.22)],
              fill=(220, 235, 245, 90))


def iso_cube(d, cx, cy, size, color, width, fill=None):
    """等距线框立方体，cx/cy 为前表面中心。"""
    hw = size / 2
    dx, dy = size * 0.42, -size * 0.32
    front = [(cx - hw, cy - hw), (cx + hw, cy - hw), (cx + hw, cy + hw), (cx - hw, cy + hw)]
    back = [(x + dx, y + dy) for x, y in front]
    if fill:
        d.polygon([P(p) for p in front], fill=fill)
    for quad in (front, back):
        d.line([P(p) for p in quad + [quad[0]]], fill=color, width=S(width), joint='curve')
    for a, b in zip(front, back):
        d.line([P(a), P(b)], fill=color, width=S(width))


def draw_03_stereo():
    img, d = new_canvas()
    lens_l, lens_r = (620, 240), (1300, 240)
    target = (960, 800)
    plane_y = 400
    plane_half = 150

    # 基线（两镜头之间的虚线）
    dash_line(d, (lens_l[0] + 105, lens_l[1]), (lens_r[0] - 105, lens_r[1]),
              TEAL + (120,), 3, dash=10, gap=12)

    # 视线：每个镜头向目标立方体张开的两条边线 + 一条中心视线
    cube_hw = 62
    for lens in (lens_l, lens_r):
        for edge in ((target[0] - cube_hw, target[1] - cube_hw * 0.6),
                     (target[0] + cube_hw, target[1] + cube_hw * 0.6)):
            d.line([P(lens), P(edge)], fill=LINE_DIM + (110,), width=S(2))
        d.line([P(lens), P(target)], fill=LINE + (200,), width=S(3))

    # 成像面线段 + 中心刻度 + 投影点（左右投影位置不同 = 视差）
    for lens in (lens_l, lens_r):
        cx = lens[0]
        d.line([P((cx - plane_half, plane_y)), P((cx + plane_half, plane_y))],
               fill=LINE + (230,), width=S(4))
        for sx in (-plane_half, plane_half):
            d.line([P((cx + sx, plane_y - 9)), P((cx + sx, plane_y + 9))],
                   fill=LINE + (230,), width=S(3))
        d.line([P((cx, plane_y - 12)), P((cx, plane_y + 12))], fill=TEAL + (255,), width=S(3))
        t = (plane_y - lens[1]) / (target[1] - lens[1])
        px = lens[0] + (target[0] - lens[0]) * t
        dash_line(d, (cx, plane_y), (px, plane_y), ORANGE + (220,), 5, dash=12, gap=8)
        d.ellipse([S(px - 10), S(plane_y - 10), S(px + 10), S(plane_y + 10)],
                  fill=ORANGE + (255,))

    for lens in (lens_l, lens_r):
        draw_lens(d, lens[0], lens[1], 92)

    # 目标：等距线框立方体（晶圆盒轮廓感）
    iso_cube(d, target[0], target[1], 124, ORANGE + (255,), 4, fill=(245, 160, 76, 26))
    d.ellipse([S(target[0] - 7), S(target[1] - 7), S(target[0] + 7), S(target[1] + 7)],
              fill=(255, 220, 180, 255))

    finish(img, '03-双目深度.png')


def draw_05_fusion():
    img, d = new_canvas()
    rng = random.Random(12)

    icon_x = 300
    entries = [
        ((icon_x, 280), LINE),    # 摄像头
        ((icon_x, 560), ORANGE),  # 激光雷达
        ((icon_x, 840), TEAL),    # 深度点阵
    ]

    # 摄像头符号：镜头圆
    draw_lens(d, icon_x, 280, 74)
    # 激光雷达符号：向右的三层扇形扫描弧 + 中心点
    for r, wd in ((46, 4), (78, 4), (110, 3)):
        d.arc([S(icon_x - r), S(560 - r), S(icon_x + r), S(560 + r)],
              start=-52, end=52, fill=ORANGE + (255,), width=S(wd))
    d.ellipse([S(icon_x - 12), S(560 - 12), S(icon_x + 12), S(560 + 12)],
              fill=ORANGE + (255,))
    # 深度符号：4x4 点阵
    for gy in range(4):
        for gx in range(4):
            x = icon_x - 51 + gx * 34
            y = 840 - 51 + gy * 34
            fade = 255 - (gx + gy) * 12
            d.ellipse([S(x - 7), S(y - 7), S(x + 7), S(y + 7)], fill=TEAL + (fade,))

    # 世界模型：等距线框房间（右侧）
    fx0, fy0, fx1, fy1 = 1260, 400, 1660, 700  # 前面矩形
    dx, dy = 100, -80                            # 深度偏移
    front = [(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)]
    back = [(x + dx, y + dy) for x, y in front]
    for quad, col in ((front, LINE + (235,)), (back, LINE_DIM + (150,))):
        d.line([P(p) for p in quad + [quad[0]]], fill=col, width=S(4), joint='curve')
    for a, b in zip(front, back):
        d.line([P(a), P(b)], fill=LINE + (200,), width=S(3))

    def iso_project(u, v, w):
        """u,v,w ∈ [0,1]：盒内点投影到等距平面"""
        x = fx0 + (fx1 - fx0) * u + dx * w
        y = fy0 + (fy1 - fy0) * v + dy * w
        return x, y

    # 盒内点云
    cloud_colors = [(235, 242, 252), ORANGE, TEAL]
    for _ in range(70):
        u, v, w = rng.random(), rng.random(), rng.random() * 0.9
        x, y = iso_project(u, v, w)
        c = cloud_colors[rng.randrange(3)]
        r = rng.choice((3, 3, 4, 5))
        d.ellipse([S(x - r), S(y - r), S(x + r), S(y + r)], fill=c + (rng.randint(150, 235),))

    # 三条传感器数据流，汇聚进世界模型左缘
    merge = (fx0 + 6, (fy0 + fy1) / 2)
    for (pos, color) in entries:
        p0 = (pos[0] + 130, pos[1])
        pts = cubic_points(p0, (p0[0] + 260, p0[1]), (merge[0] - 300, merge[1]), merge)
        d.line(pts, fill=color + (150,), width=S(3), joint='curve')
        mid = pts[len(pts) * 3 // 5]
        d.ellipse([mid[0] - S(7), mid[1] - S(7), mid[0] + S(7), mid[1] + S(7)],
                  fill=color + (230,))
    d.ellipse([S(merge[0] - 9), S(merge[1] - 9), S(merge[0] + 9), S(merge[1] + 9)],
              fill=(255, 230, 200, 255))

    finish(img, '05-多传感器融合.png')


def soft_patch(img, box, radius, desat=0.0, feather=18):
    """模糊遮盖补丁；羽化边缘避免矩形边界，desat 用于消除叠加文字的橙色残留。"""
    region = img.crop(box).filter(ImageFilter.GaussianBlur(radius))
    if desat:
        gray = region.convert('L').convert('RGB')
        region = Image.blend(region, gray, desat)
    mask = Image.new('L', region.size, 0)
    ImageDraw.Draw(mask).rectangle([0, 0, region.width - 1, region.height - 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather))
    img.paste(region, box, mask)


def corner_brackets(d, box, color, arm=52, width=6, fill_alpha=22):
    x0, y0, x1, y1 = box
    d.rectangle([S(x0), S(y0), S(x1), S(y1)], fill=color + (fill_alpha,))
    for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([P((cx, cy)), P((cx + sx * arm, cy))], fill=color + (255,), width=S(width))
        d.line([P((cx, cy)), P((cx, cy + sy * arm))], fill=color + (255,), width=S(width))


def draw_06_semantics():
    src = Image.open(ROOT / 'assets' / '优艾智合3.png').convert('RGB')
    # 遮盖源图中的可读文字与叠加层（右上/左下橙色说明、机身丝印、警示贴纸）
    for box in [(890, 0, 1180, 245), (0, 990, 300, 1320)]:
        soft_patch(src, box, 60, desat=0.72, feather=28)
    for box, radius in [
        ((296, 730, 424, 775), 30),     # 机身 YOUIBOT 丝印
        ((320, 835, 400, 885), 30),     # 机身 Y001 丝印
        ((322, 58, 380, 118), 22),      # 机械臂关节标志
        ((412, 748, 448, 792), 18),     # 警示贴纸
        ((428, 958, 478, 1002), 18),
        ((566, 1050, 640, 1072), 16),
        ((262, 1088, 322, 1138), 18),
        ((620, 1138, 672, 1170), 16),
    ]:
        soft_patch(src, box, radius)

    # 背景：同图放大铺满、重度模糊 + 压暗，作为氛围底
    cover = max(W * SS / src.width, H * SS / src.height)
    bg = src.resize((int(src.width * cover), int(src.height * cover)), Image.LANCZOS)
    bx = (bg.width - W * SS) // 2
    by = (bg.height - H * SS) // 2
    bg = bg.crop((bx, by, bx + W * SS, by + H * SS)).filter(ImageFilter.GaussianBlur(60))
    deep = Image.new('RGB', bg.size, (12, 24, 44))
    bg = Image.blend(bg, deep, 0.68)
    img = Image.new('RGB', (W * SS, H * SS))
    img.paste(bg, (0, 0))

    # 主体：全高清晰照片带，左右羽化融入背景
    scale = H / src.height  # 逻辑坐标（1x）缩放比
    scaled = src.resize((int(src.width * scale * SS), H * SS), Image.LANCZOS)
    fade = 120
    band_mask = Image.new('L', scaled.size, 255)
    md = ImageDraw.Draw(band_mask)
    for x in range(fade):
        a = int(255 * (x / fade))
        md.line([(x, 0), (x, scaled.height)], fill=a)
        md.line([(scaled.width - 1 - x, 0), (scaled.width - 1 - x, scaled.height)], fill=a)
    band_mask = band_mask.filter(ImageFilter.GaussianBlur(24))
    img.paste(scaled, ((W * SS - scaled.width) // 2, 0), band_mask)

    # 半透明深蓝压暗层
    shade = Image.new('RGBA', img.size, (9, 18, 36, 135))
    img = Image.alpha_composite(img.convert('RGBA'), shade).convert('RGB')
    d = ImageDraw.Draw(img, 'RGBA')

    def T(box):
        x0, y0, x1, y1 = box
        ox = (W - src.width * scale) / 2
        return (ox + x0 * scale, y0 * scale, ox + x1 * scale, y1 * scale)

    # 三个部位的检测框（四角括号 + 极淡填充），橙/青绿交替
    corner_brackets(d, T((300, 40, 790, 500)), ORANGE)      # 机械臂
    corner_brackets(d, T((520, 460, 1030, 1060)), TEAL)     # 晶圆承载舱
    corner_brackets(d, T((270, 1100, 1010, 1365)), ORANGE)  # 底盘

    finish(img, '06-像素到语义.png')


if __name__ == '__main__':
    draw_03_stereo()
    draw_05_fusion()
    draw_06_semantics()
