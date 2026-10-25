"""2026-10-25《反着看》封面：尊界V800 制动踏板事件。

底图用撕裂痕迹特写（懂车帝视频截图，暗色调），取下部窗口避开原图左上标注。
信息图式：标题两行 + 数据带，白字柔和投影，不加色块 / 色条 / 遮罩 / 边框。
画布 3 倍渲染再缩回 900x383。
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-10-25-zunjie-brake"))
SRC = os.path.join(BASE, "assets", "03_tear.png")
OUT = os.path.join(BASE, "cover_news.png")

YHB = r"C:\Windows\Fonts\msyhbd.ttc"
YH = r"C:\Windows\Fonts\msyh.ttc"

S = 3
W, H = 900 * S, 383 * S

TITLE1 = "三台尊界刹车踏板断裂"
TITLE2 = "4589牛那个数是假的"
DATA = "行标 1500N  ·  实测断裂 1612N  ·  网传残影 4589N"

LEFT = 40
Y1, Y2, YD = 56, 126, 318
F1, FD = 52, 25


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
    # 原图上部有节目自带的金白标注，往下取更小的 2.35:1 窗口避开
    ch = 360
    cw = int(ch * 2.35)
    x0 = max(0, (sw - cw) // 2 - 40)
    top = sh - ch + 4
    cov = src.crop((x0, top, x0 + cw, top + ch)).resize((W, H), Image.LANCZOS)
    g = cov.convert("L")
    print("裁切 x0=%d top=%d %dx%d ｜ 全图均亮 %.1f ｜ 左侧45%%均亮 %.1f"
          % (x0, top, cw, ch, ImageStat.Stat(g).mean[0],
             ImageStat.Stat(g.crop((0, 0, int(W * 0.45), H))).mean[0]))

    f1 = ImageFont.truetype(YHB, F1 * S)
    fd = ImageFont.truetype(YH, FD * S)

    im = cov
    im = shadow_text(im, (LEFT * S, Y1 * S), TITLE1, f1)
    im = shadow_text(im, (LEFT * S, Y2 * S), TITLE2, f1)
    im = shadow_text(im, (LEFT * S, YD * S), DATA, fd,
                     fill=(226, 232, 240), alpha=205, blur=3)

    out = im.convert("RGB").resize((900, 383), Image.LANCZOS)
    out.save(OUT)
    print("封面 → %s %dx%d %dKB" % (OUT, out.width, out.height,
                                    os.path.getsize(OUT) // 1024))

    d = ImageDraw.Draw(out)
    for label, s, y, bold in (("T1", TITLE1, Y1, True), ("T2", TITLE2, Y2, True), ("D", DATA, YD, False)):
        f = ImageFont.truetype(YHB if bold else YH, F1 if bold else FD)
        bb = d.textbbox((LEFT, y), s, font=f)
        print("  %-2s 左 %d 右 %d 顶 %d 底 %d（画布 900x383）" % (label, bb[0], bb[2], bb[1], bb[3]))


if __name__ == "__main__":
    main()
