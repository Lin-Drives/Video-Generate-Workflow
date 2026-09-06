# -*- coding: utf-8 -*-
"""产出《机器人怎么"看见"世界？》的 4 张分镜素材图（1920x1080，无文字）。

02/03 为真实素材裁剪修补，05/06 为 Pillow 绘制/合成。幂等：直接覆盖输出。
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    img.save(OUT_DIR / name)
    print(f'已输出 {OUT_DIR / name}')


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


def draw_02_camera():
    """传感器特写：优艾智合4.png 中部干净区域（黑色内凹传感器窗口 + 青绿灯带）。"""
    src = Image.open(ROOT / 'assets' / '优艾智合4.png').convert('RGB')
    crop = src.crop((370, 470, 1470, 1089))  # 1100x619，16:9，无水印无文字叠加
    out = crop.resize((W, H), Image.LANCZOS)
    out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    finish(out, '02-摄像头.png')


def draw_03_obstacle():
    """双目/避障分镜：优艾智合-避障演示.png，机器人与红色交通锥的对视构图。"""
    src = Image.open(ROOT / 'assets' / '优艾智合-避障演示.png').convert('RGB')
    # 左下 CE & SEMI 说明条，分两段重建：
    # 1) 地板部分（x 60-1080）：采样左侧干净列 x=30 逐行铺开
    floor = src.crop((30, 1420, 31, 1800)).resize((1020, 380))
    floor = floor.filter(ImageFilter.GaussianBlur(6))
    floor_mask = Image.new('L', floor.size, 0)
    ImageDraw.Draw(floor_mask).rectangle([0, 0, floor.width - 1, floor.height - 1], fill=255)
    floor_mask = floor_mask.filter(ImageFilter.GaussianBlur(30))
    src.paste(floor, (60, 1420), floor_mask)
    # 2) 底盘侧面 + 黑色防撞条（x 1080-1640）：防撞条是斜带，
    #    取右侧干净列 x=1670 按斜率逐列平移复制（剪切重建）
    slope = (1680 - 1420) / (1750 - 1060)  # 防撞条上沿斜率 ≈ 0.377
    col = Image.new('RGB', (1, 1000))
    col.paste(src.crop((1670, 1100, 1671, 1910)), (0, 0))
    col.paste(src.crop((1670, 1909, 1671, 1910)).resize((1, 90)), (0, 810))  # 底部地板行复制延展
    patch = Image.new('RGB', (560, 400))
    for i in range(560):
        shift = round(slope * (1080 + i - 1670))
        patch.paste(col, (i, shift - 280))  # patch 行 r ↔ 原图行 1380 + r - shift
    patch = patch.filter(ImageFilter.GaussianBlur(2))
    patch_mask = Image.new('L', patch.size, 0)
    ImageDraw.Draw(patch_mask).rectangle([0, 0, patch.width - 1, patch.height - 1], fill=255)
    patch_mask = patch_mask.filter(ImageFilter.GaussianBlur(25))
    src.paste(patch, (1080, 1380), patch_mask)
    # 机身丝印与警示贴纸
    for box, radius in [
        ((1155, 510, 1260, 605), 26),    # Y001 丝印
        ((1285, 330, 1340, 435), 20),    # 竖排警示贴纸（底部进入裁剪区）
        ((1095, 595, 1135, 655), 18),    # 警示贴纸
        ((1335, 800, 1430, 885), 20),
        ((1075, 1100, 1170, 1165), 18),
        ((1520, 1010, 1620, 1095), 20),  # 禁止手入警示贴纸
        ((1610, 1240, 1715, 1350), 20),  # 黄色三角警示贴纸
        ((2075, 915, 2205, 950), 16),    # 导轨小标签
    ]:
        soft_patch(src, box, radius)
    # 黑色标签屏：模糊会混入周围白色发灰，直接用深色填充模拟原屏幕
    screen = Image.new('RGB', (50, 95), (32, 35, 42))
    screen_mask = Image.new('L', screen.size, 0)
    ImageDraw.Draw(screen_mask).rectangle([0, 0, 49, 94], fill=255)
    screen_mask = screen_mask.filter(ImageFilter.GaussianBlur(10))
    src.paste(screen, (1505, 1215), screen_mask)
    # 16:9 裁剪：上方避开 YOUIBOT 水印与右上型号条，右侧留全交通锥
    crop = src.crop((324, 380, 3044, 1910))  # 2720x1530，0.71 倍缩小不损失锐度
    out = crop.resize((W, H), Image.LANCZOS)
    out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    finish(out, '03-双目深度.png')


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


def draw_07_compute_board():
    """实时性与算力：RK3588 边缘计算板与输入/输出外设的无文字图标关系图。"""
    img, d = new_canvas()
    # 中央嵌入式计算板：只保留型号文字，其他关系全部由图标表达。
    board = (610, 230, 1310, 850)
    d.rounded_rectangle([S(board[0]), S(board[1]), S(board[2]), S(board[3])], radius=S(38), fill=(25, 46, 71, 255), outline=TEAL + (220,), width=S(5))
    for x in range(670, 1280, 74):
        d.rectangle([S(x), S(214), S(x + 34), S(232)], fill=(218, 174, 80, 230))
        d.rectangle([S(x), S(850), S(x + 34), S(868)], fill=(218, 174, 80, 230))
    for y in range(292, 810, 74):
        d.rectangle([S(592), S(y), S(610), S(y + 34)], fill=(218, 174, 80, 230))
        d.rectangle([S(1310), S(y), S(1328), S(y + 34)], fill=(218, 174, 80, 230))
    # SoC、内存和散热片。
    d.rounded_rectangle([S(785), S(390), S(1135), S(650)], radius=S(24), fill=(10, 22, 40, 255), outline=ORANGE + (255,), width=S(6))
    soc_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', S(52))
    text = 'RK3588'
    bbox = d.textbbox((0, 0), text, font=soc_font)
    d.text((S(960) - (bbox[2] - bbox[0]) // 2, S(490)), text, font=soc_font, fill=(243, 248, 255, 255))
    for y in range(300, 370, 18):
        d.line([P((785, y)), P((1135, y))], fill=(126, 157, 190, 160), width=S(6))
    for x in (690, 1190):
        d.rounded_rectangle([S(x), S(690), S(x + 70), S(760)], radius=S(10), fill=(35, 66, 95, 255), outline=LINE_DIM + (200,), width=S(3))

    def link(a, b, color):
        d.line([P(a), P(b)], fill=color + (180,), width=S(5))
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max((dx * dx + dy * dy) ** 0.5, 1)
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        tip = b
        base = (b[0] - ux * 22, b[1] - uy * 22)
        d.polygon([P(tip), P((base[0] + px * 10, base[1] + py * 10)), P((base[0] - px * 10, base[1] - py * 10))], fill=color + (245,))

    def node(cx, cy, color):
        d.ellipse([S(cx - 76), S(cy - 76), S(cx + 76), S(cy + 76)], fill=(15, 31, 54, 245), outline=color + (255,), width=S(5))

    # 左侧输入：相机、激光雷达、深度点阵。
    for cx, cy, target, color in ((230, 330, (610, 380), LINE), (230, 540, (610, 540), ORANGE), (230, 750, (610, 700), TEAL)):
        node(cx, cy, color); link((cx + 78, cy), target, color)
    draw_lens(d, 230, 330, 38)
    for r in (30, 52):
        d.arc([S(230 - r), S(540 - r), S(230 + r), S(540 + r)], start=-55, end=55, fill=ORANGE + (255,), width=S(5))
    d.ellipse([S(218), S(528), S(242), S(552)], fill=ORANGE + (255,))
    for gy in range(3):
        for gx in range(3):
            x, y = 204 + gx * 26, 724 + gy * 26
            d.ellipse([S(x), S(y), S(x + 12), S(y + 12)], fill=TEAL + (255,))

    # 右侧输出：机械臂、网络、供电。
    for cx, cy, target, color in ((1690, 330, (1310, 380), LINE), (1690, 540, (1310, 540), TEAL), (1690, 750, (1310, 700), ORANGE)):
        node(cx, cy, color); link(target, (cx - 78, cy), color)
    d.line([P((1644, 370)), P((1680, 320)), P((1720, 360)), P((1742, 304))], fill=LINE + (255,), width=S(14), joint='curve')
    d.ellipse([S(1630), S(356), S(1658), S(384)], fill=LINE + (255,))
    d.arc([S(1644), S(494), S(1736), S(586)], start=210, end=330, fill=TEAL + (255,), width=S(6))
    d.arc([S(1660), S(510), S(1720), S(570)], start=210, end=330, fill=TEAL + (255,), width=S(6))
    d.line([P((1688, 526)), P((1688, 556))], fill=TEAL + (255,), width=S(7))
    d.rectangle([S(1654), S(724), S(1724), S(776)], outline=ORANGE + (255,), width=S(5))
    d.polygon([P((1692, 730)), P((1670, 752)), P((1688, 752)), P((1678, 772)), P((1710, 746)), P((1692, 746))], fill=ORANGE + (255,))
    finish(img, '07-实时性.png')


if __name__ == '__main__':
    draw_02_camera()
    draw_03_obstacle()
    draw_05_fusion()
    draw_06_semantics()
    draw_07_compute_board()
