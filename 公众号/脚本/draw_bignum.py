# -*- coding: utf-8 -*-
"""把主数字叠到底图上（3D 感靠描边 + 外发光 + 投影三层，不用生图写字）。

用法：
    python draw_bignum.py --bg in.png --out out.png --text 86 --x 30 --y 10 --size 210
坐标与字号按 900x383 画布设计，内部 3 倍渲染再缩回。
"""
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 3
W, H = 900, 383
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
WARM_TOP = (0xFF, 0x8A, 0x2B)
WARM_BOT = (0xFF, 0xD2, 0x4A)
DARK = (0x01, 0x04, 0x12)


def gradient_mask(size, mask):
    """把竖直渐变涂进 mask 区域，返回 RGBA 层。"""
    w, h = size
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        grad.putpixel((0, y), tuple(
            int(WARM_TOP[i] + (WARM_BOT[i] - WARM_TOP[i]) * t) for i in range(3)))
    grad = grad.resize((w, h))
    layer = Image.new("RGBA", (w, h))
    layer.paste(grad, (0, 0), mask)
    return layer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="86")
    ap.add_argument("--x", type=int, default=28)
    ap.add_argument("--y", type=int, default=6)
    ap.add_argument("--size", type=int, default=210)
    a = ap.parse_args()

    bg = Image.open(a.bg).convert("RGB").resize((W * S, H * S), Image.LANCZOS)
    cw, ch = bg.size
    canvas = bg.copy()

    font = ImageFont.truetype(FONT_BOLD, a.size * S)
    # 先量宽度，按 x 左对齐
    tmp = Image.new("L", (10, 10))
    tw = ImageDraw.Draw(tmp).textlength(a.text, font=font)

    mask = Image.new("L", (cw, ch), 0)
    d = ImageDraw.Draw(mask)
    d.text((a.x * S, a.y * S), a.text, font=font, fill=255,
           stroke_width=0)

    # 1) 投影
    shadow = mask.filter(ImageFilter.GaussianBlur(10 * S / 3))
    shadow = shadow.point(lambda v: int(v * 0.55))
    sh_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 255))
    sh_layer.putalpha(shadow)
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(sh_layer, (2 * S, 5 * S))

    # 2) 外发光（暖色，范围大、透明度低）
    glow = mask.filter(ImageFilter.GaussianBlur(14 * S / 3))
    glow = glow.point(lambda v: int(v * 0.75))
    gl_layer = Image.new("RGBA", (cw, ch), (0xFF, 0x8A, 0x2B, 255))
    gl_layer.putalpha(glow)
    canvas.alpha_composite(gl_layer)

    # 3) 挤出侧壁（伪 3D：朝右下叠若干层暗橙，光从左上来）
    ext = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    wall = Image.new("RGBA", (cw, ch), (0xC2, 0x5A, 0x14, 255))
    wall.putalpha(mask)
    for i in range(12, 0, -1):
        ext.alpha_composite(wall, (int(i * 1.5 * S / 3), int(i * 2.0 * S / 3)))
    canvas.alpha_composite(ext)

    # 4) 深色描边（把数字和背景切开）
    stroke = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(stroke).text((a.x * S, a.y * S), a.text, font=font, fill=255,
                                stroke_width=5 * S // 2, stroke_fill=255)
    sl = Image.new("RGBA", (cw, ch), DARK + (255,))
    sl.putalpha(stroke)
    canvas.alpha_composite(sl)

    # 5) 渐变填充
    canvas.alpha_composite(gradient_mask((cw, ch), mask))

    out = canvas.convert("RGB").resize((W, H), Image.LANCZOS)
    out.save(a.out)
    print("saved", a.out, out.size, "text width(px@900):", round(tw / S))


if __name__ == "__main__":
    main()
