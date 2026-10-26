"""2026-10-26《今日可领》封面：沙漏倒计时生图 + PIL 叠字。

规矩：不加色块 / 色条 / 遮罩 / 装饰边框；文字靠偏移 (1,2) 黑色 alpha190 + 高斯模糊投影。
画布 3 倍渲染再缩回 900x383。
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-10-26-ai-福利"))
AI = os.path.join(BASE, "ai_cover")
SRC = os.path.join(AI, "Wide_cinematic_banner__photore_2026-10-26T01-20-09.png")
OUT = os.path.join(BASE, "cover_news.png")

YHB = r"C:\Windows\Fonts\msyhbd.ttc"
YH = r"C:\Windows\Fonts\msyh.ttc"

S = 3
W, H = 900 * S, 383 * S

TITLE1 = "十条 AI 额度还在送"
TITLE2 = "最急的 4 天后到期"
DATA = "10.26 已核验 · 最晚一档到 12 月 31 日"

LEFT = 452
Y1, Y2, YD = 74, 142, 236
F1, FD = 41, 19


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
    top = 300
    if top + ch > sh:
        top = sh - ch
    cov = src.crop((0, top, sw, top + ch)).resize((W, H), Image.LANCZOS)
    print("源 %dx%d ｜ 裁切 top=%d h=%d ｜ 均亮 %.1f"
          % (sw, sh, top, ch, ImageStat.Stat(cov.convert("L")).mean[0]))

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
    for label, s, fsz, y in (("T1", TITLE1, F1, Y1), ("T2", TITLE2, F1, Y2), ("D", DATA, FD, YD)):
        ff = ImageFont.truetype(YHB if fsz == F1 else YH, fsz)
        bb = d.textbbox((LEFT, y), s, font=ff)
        print("  %-2s 左 %d 右 %d 顶 %d 底 %d（画布 900x383）" % (label, bb[0], bb[2], bb[1], bb[3]))


if __name__ == "__main__":
    main()
