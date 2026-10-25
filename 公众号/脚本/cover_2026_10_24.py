"""2026-10-24《反着看》信息图式封面。

用户定稿规矩：不加色块 / 色条 / 遮罩面板 / 装饰边框，文字靠柔和投影保证可读。
画布按 3 倍渲染再缩回 900x383，字形边缘更干净。
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-10-24-lixiang-i6"))
AI = os.path.join(BASE, "ai_cover")
SRC = os.path.join(AI, "Wide_cinematic_aerial_photogra_2026-10-24T06-12-04.png")
OUT = os.path.join(BASE, "cover_news.png")

YHB = r"C:\Windows\Fonts\msyhbd.ttc"
YH = r"C:\Windows\Fonts\msyh.ttc"

S = 3
W, H = 900 * S, 383 * S

TITLE1 = "理想i6跑出104%续航"
TITLE2 = "平均时速只有45公里"
DATA = "811.4 公里  ·  达成率 104%  ·  高速 0 公里"

LEFT = 40
Y1, Y2, YD = 62, 130, 312
F1, FD = 56, 26


def shadow_text(im, xy, s, font, fill=(255, 255, 255), blur=4, alpha=190):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((xy[0] + 1 * S, xy[1] + 2 * S), s, font=font,
                               fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur * S))
    im = Image.alpha_composite(im.convert("RGBA"), layer)
    ImageDraw.Draw(im).text(xy, s, font=font, fill=fill + (255,))
    return im


def main():
    src = Image.open(SRC).convert("RGB")
    sw, sh = src.size
    ch = int(sw / 2.35)
    top = 190
    if top + ch > sh:
        top = sh - ch
    cov = src.crop((0, top, sw, top + ch)).resize((W, H), Image.LANCZOS)
    print("裁切 top=%d h=%d ｜ 均亮 %.1f"
          % (top, ch, ImageStat.Stat(cov.convert("L")).mean[0]))

    f1 = ImageFont.truetype(YHB, F1 * S)
    fd = ImageFont.truetype(YH, FD * S)

    im = cov
    im = shadow_text(im, (LEFT * S, Y1 * S), TITLE1, f1)
    im = shadow_text(im, (LEFT * S, Y2 * S), TITLE2, f1)
    im = shadow_text(im, (LEFT * S, YD * S), DATA, fd,
                     fill=(226, 232, 240), alpha=205, blur=3)

    out = im.convert("RGB").resize((900, 383), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("封面 → %s %dx%d %dKB" % (OUT, out.width, out.height,
                                    os.path.getsize(OUT) // 1024))

    d = ImageDraw.Draw(out)
    for label, s, f, y in (("T1", TITLE1, f1, Y1), ("T2", TITLE2, f1, Y2), ("D", DATA, fd, YD)):
        bb = d.textbbox((LEFT, y), s, font=ImageFont.truetype(YHB if f is f1 else YH, F1 if f is f1 else FD))
        print("  %-2s 左 %d 右 %d 顶 %d 底 %d（画布 900x383）" % (label, bb[0], bb[2], bb[1], bb[3]))


if __name__ == "__main__":
    main()
