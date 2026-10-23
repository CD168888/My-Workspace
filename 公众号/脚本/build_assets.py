"""整理本轮成稿的最终图片集，并给关键图加轻量标注。

规则（用户定稿）：
  - 不加任何色块 / 色条 / 遮罩面板
  - 标注只用细线 + 小字，白线白字配柔和投影
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-10-23-tesla-fly"))
OUT = os.path.join(BASE, "assets")
os.makedirs(OUT, exist_ok=True)

YH = r"C:\Windows\Fonts\msyh.ttc"
YHB = r"C:\Windows\Fonts\msyhbd.ttc"


def load(rel, w=None):
    im = Image.open(os.path.join(BASE, rel)).convert("RGB")
    if w and im.width != w:
        h = int(im.height * w / im.width)
        im = im.resize((w, h), Image.LANCZOS)
    return im


def save(im, name):
    p = os.path.join(OUT, name)
    im.save(p, quality=92)
    print("%-22s %sx%s  %dKB" % (name, im.width, im.height, os.path.getsize(p) // 1024))
    return p


def draw_text_with_shadow(im, xy, s, font, fill=(255, 255, 255, 255), blur=3):
    W, H = im.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((xy[0] + 1, xy[1] + 1), s, font=font, fill=(0, 0, 0, 210))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    im = Image.alpha_composite(im.convert("RGBA"), layer)
    ImageDraw.Draw(im).text(xy, s, font=font, fill=fill)
    return im


def line_with_shadow(im, pts, width=2):
    W, H = im.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(pts, fill=(0, 0, 0, 170), width=width + 2, joint="curve")
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    im = Image.alpha_composite(im.convert("RGBA"), layer)
    ImageDraw.Draw(im).line(pts, fill=(255, 255, 255, 245), width=width, joint="curve")
    return im


def main():
    # 01 飞越车队（封面与正文共用，正文用 1400 宽）
    save(load("photo_toutiao/001_9deae95c5fec.jpg", 1400), "01_flight.jpg")

    # 02 腾空 + C 形坡道
    save(load("photo_sznews/001.jpg", 900), "02_ramp.jpg")

    # 03 倒挂悬停
    save(load("photo_163_all/002_dee20b76d7fc.jpg", 900), "03_upside.jpg")

    # 04 尾部推进器（细线圈出四个喷口）
    im = load("photo_163_all/007_bc2457f3f2bd.jpg", 900).convert("RGBA")
    im = line_with_shadow(im, [(0, 0), (0, 0)], 2)  # 占位，保证图层初始化
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([556, 356, 800, 424], outline=(0, 0, 0, 170), width=4)
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    im = Image.alpha_composite(im, layer)
    ImageDraw.Draw(im).ellipse([556, 356, 800, 424], outline=(255, 255, 255, 240), width=2)
    im = draw_text_with_shadow(im, (40, 448), "圈内是车尾的推进器组", ImageFont.truetype(YH, 16))
    save(im.convert("RGB"), "04_nozzles.jpg")

    # 05 官网订单页：用宽版截图，不加标注
    save(load("photo_sznews/003.jpg", 1080), "05_config.jpg")

    # 06 小鹏汇天工厂（新华社）
    save(load("photo_toutiao/002_f931dbc37b7b.jpg", 1400), "06_xpeng_factory.jpg")

    # 07 小鹏 X2 飞行
    save(load("photo_sznews/005.jpg", 900), "07_xpeng_fly.jpg")

    # 08 加速/喷流俯拍
    save(load("photo_sznews/002.jpg", 900), "08_burst.jpg")


if __name__ == "__main__":
    main()
