# -*- coding: utf-8 -*-
"""封面渲染器 · 霓虹拼贴风（SOP 1.4 定稿版）。

对应样张：素材/2026-10-26-ai-福利/ai_cover_v2/五亿 Tokens 清零倒计时.png
本脚本只负责**文字层**（三行逐段混色 + 数字放大 + 描边发光 + 底部胶囊），
底图（科技底 + 3D 大数字 + 日历沙漏 + 图标卡片）由 ImageGen 或拼贴产出后经 --bg 传入。

用法：
    python cover_neon.py                                   # 用内置占位底，校验排版
    python cover_neon.py --bg 底图.png --out 封面.png       # 正式出图

换期只改下面 LINES / PILL / 主数字，不动渲染逻辑。
字号按 900×383 设计；画布内部 3 倍渲染再缩回，保证描边和发光不出锯齿。
"""
import argparse
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 3
W, H = 900, 383

# ---- 配色 token（与 SOP 1.4 一致）----
WHITE = (255, 255, 255)
WARM = ("grad", (0xFF, 0x8A, 0x2B), (0xFF, 0xD2, 0x4A))   # 橙 → 金，横向渐变
COOL = (0x5B, 0xC8, 0xF5)                                  # 冷青，技术词/数字
DARK = (0x01, 0x04, 0x12)                                  # 描边用近黑
NAVY = (0x01, 0x08, 0x2F)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"   # 极粗黑体，本机最接近普惠体 Heavy
FONT_UI = r"C:\Windows\Fonts\msyh.ttc"

# ---- 本期文案：三行，每行若干段 (文字, 颜色, 字号倍数) ----
# 规则：白打底 → 硬词换暖色 → 技术词换冷色；数字必须放大 1.2–1.3 倍
LINES = [
    [("5亿", WHITE, 1.0), ("Tokens", WARM, 1.0), ("今早清零！", WARM, 1.0)],
    [("还有", WHITE, 1.0), ("10", COOL, 1.28), ("项", WHITE, 1.0),
     ("AI", WHITE, 1.0), ("免费福利", WHITE, 1.0)],
    [("最晚", WHITE, 1.0), ("12", WARM, 1.28), ("月底", WHITE, 1.0), ("到期", WHITE, 1.0)],
]

PILL = ["截止时间整理", "领取方式", "避坑提醒"]

BASE_SIZE = 44      # 正文字号（1 倍段）
LINE_H = 1.06       # 行高倍数，紧排
LEFT = 42           # 标题左边距
BASELINE0 = 196     # 第一行基线（900×383 坐标）
STROKE = 2.0        # 深色外描边宽度（1 倍像素）
GLOW = 6.0          # 外发光半径（1 倍像素）


# ---------------------------------------------------------------- 工具

def solid(c):
    """纯色返回 RGB 三元组，渐变色返回 None。"""
    if isinstance(c, tuple) and len(c) == 3 and all(isinstance(v, int) for v in c):
        return c
    return None


def hgrad(w, h, c1, c2):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = x / max(1, w - 1)
        d.line([(x, 0), (x, h)],
               fill=(int(c1[0] + (c2[0] - c1[0]) * t),
                     int(c1[1] + (c2[1] - c1[1]) * t),
                     int(c1[2] + (c2[2] - c1[2]) * t)))
    return img


def draw_segment(layer, xy, text, font, color):
    """在 layer 上画一段字。color 为 RGB 或 WARM 那种 ("grad", c1, c2)。"""
    d = ImageDraw.Draw(layer)
    if solid(color):
        d.text(xy, text, font=font, fill=solid(color) + (255,), anchor="ls")
    else:
        _, c1, c2 = color
        w = int(font.getlength(text)) + int(font.size * 0.4)
        h = int(font.size * 1.4)
        grad = hgrad(w, h, c1, c2)
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).text((0, h * 0.78), text, font=font, fill=255, anchor="ls")
        layer.paste(grad, (int(xy[0]), int(xy[1] - h * 0.78)), mask)


def render_text(bg, lines, left, baseline0, base_size):
    """三行逐段混色，每段独立字号，按基线对齐；先暗描边，再外发光，最后填色。"""
    # 1) 统一定位：算出每段的位置
    placed = []
    for li, segs in enumerate(lines):
        y = baseline0 + li * base_size * LINE_H
        x = left
        for text, color, scale in segs:
            f = ImageFont.truetype(FONT_BOLD, int(base_size * scale * S))
            placed.append((x * S, y * S, text, f, color))
            x += f.getlength(text) / S

    # 2) 深色外描边（保证压在杂底上不糊）
    stroke = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    for x, y, text, f, _ in placed:
        ImageDraw.Draw(stroke).text((x, y), text, font=f, fill=DARK + (255,),
                                    anchor="ls", stroke_width=int(STROKE * S),
                                    stroke_fill=DARK + (255,))
    out = Image.alpha_composite(bg.convert("RGBA"), stroke)

    # 3) 外发光：同色系、模糊后叠加（暖字暖光、冷字冷光）
    glow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    for x, y, text, f, color in placed:
        c = solid(color) or color[1]          # 渐变取起始色做光晕
        ImageDraw.Draw(glow).text((x, y), text, font=f, fill=c + (150,),
                                  anchor="ls", stroke_width=int(STROKE * S),
                                  stroke_fill=c + (150,))
    glow = glow.filter(ImageFilter.GaussianBlur(GLOW * S))
    out = Image.alpha_composite(out, glow)

    # 4) 填色
    fill = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    for x, y, text, f, color in placed:
        draw_segment(fill, (x, y), text, f, color)
    return Image.alpha_composite(out, fill)


def render_pill(im, items, font_size=15, margin=22):
    """右下角信息胶囊：黑 60% 填充 + 1px 亮边 + 白字 + 分隔 + 箭头。"""
    f = ImageFont.truetype(FONT_UI, font_size * S)
    arrow = "  >"
    parts, sep = [], "  |  "
    tw = sum(f.getlength(t) for t in items) + f.getlength(sep) * (len(items) - 1) + f.getlength(arrow)
    padx, pady = 16, 11
    w, h = tw / S + padx * 2, font_size + pady * 2
    x1, y1 = W - margin - w, H - margin - h

    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x1 * S, y1 * S, (x1 + w) * S, (y1 + h) * S],
                        radius=h / 2 * S, fill=(4, 10, 24, 165), outline=(0x8F, 0xE9, 0xFF, 210),
                        width=max(1, int(1 * S)))
    d.text(((x1 + padx) * S, (y1 + h / 2) * S), sep.join(items) + arrow,
           font=f, fill=(255, 255, 255, 245), anchor="lm")
    return Image.alpha_composite(im.convert("RGBA"), layer)


def placeholder_bg():
    """占位底：深海军蓝 + 两团霓虹光。正式出图请用 --bg 传生图。"""
    bg = Image.new("RGB", (W * S, H * S), NAVY)
    d = ImageDraw.Draw(bg)
    for y in range(H * S):
        t = y / (H * S)
        d.line([(0, y), (W * S, y)],
               fill=(int(0x0A + (0x01 - 0x0A) * t), int(0x1A + (0x08 - 0x1A) * t),
                     int(0x4A + (0x2F - 0x4A) * t)))
    for cx, cy, r, c in ((int(W * S * .16), int(H * S * .22), int(H * S * .55), (0x2A, 0x6B, 0xFF)),
                         (int(W * S * .86), int(H * S * .30), int(H * S * .45), (0xFF, 0x7A, 0x1E))):
        g = Image.new("RGB", bg.size, (0, 0, 0))
        ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
        bg = Image.composite(g.filter(ImageFilter.GaussianBlur(r * 0.35)), bg,
                             g.filter(ImageFilter.GaussianBlur(r * 0.35)).convert("L").point(lambda v: v // 3))
    return bg


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", default=None, help="底图，建议已是 2.35:1；不给就用占位底")
    ap.add_argument("--out", default="cover_neon.png")
    ap.add_argument("--base", type=int, default=BASE_SIZE, help="正文基准字号")
    ap.add_argument("--baseline0", type=int, default=BASELINE0, help="第一行基线 y")
    ap.add_argument("--left", type=int, default=LEFT, help="标题左边距 x")
    args = ap.parse_args()

    if args.bg:
        bg = Image.open(args.bg).convert("RGB")
        ch = int(bg.width / 2.35)
        if abs(bg.height - ch) > 2:
            top = max(0, (bg.height - ch) // 2)
            bg = bg.crop((0, top, bg.width, top + ch))
        bg = bg.resize((W * S, H * S), Image.LANCZOS)
    else:
        bg = placeholder_bg()

    im = render_text(bg, LINES, args.left, args.baseline0, args.base)
    im = render_pill(im, PILL)

    out = im.convert("RGB").resize((W, H), Image.LANCZOS)
    out.save(args.out, quality=95)
    print("→ %s  %dx%d  %dKB" % (args.out, out.width, out.height,
                                 os.path.getsize(args.out) // 1024))

    # 出界自检
    d = ImageDraw.Draw(out)
    for li, segs in enumerate(LINES):
        y = args.baseline0 + li * args.base * LINE_H
        x = args.left
        for text, _, scale in segs:
            f = ImageFont.truetype(FONT_BOLD, int(args.base * scale))
            x += f.getlength(text)
        print("  行%d 右端 %d %s" % (li + 1, int(x), "出界!" if x > 878 else "ok"))


if __name__ == "__main__":
    main()
