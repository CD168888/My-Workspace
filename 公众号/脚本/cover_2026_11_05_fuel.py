# -*- coding: utf-8 -*-
"""2026-11-05 反着看封面 · 燃油附加费 11 月 5 日上调（霓虹拼贴 SOP 1.4）。

只覆盖 LINES / PILL，不改共享 cover_neon.py 的任何常量。
底图右下有「AI生成」水印：先下裁 52px 再重采样回 1536x653（精确 2.35:1）。

封面讲的是标题没给的新东西：票面价之外还有 130/190 元，票面 200 元实付 390 元。
主数字 190 = 长途机建燃油合计（湖南日报 11-05 给出的数，可追一级源）。
"""
import os
import sys

from PIL import Image

import cover_neon as C

ASSET = r"C:\Users\Administrator\Desktop\My-Workspace\公众号\素材\2026-11-05-fuel-surcharge"
RAW = os.path.join(ASSET, "Wide_2_35_1_cinematic_cyberpun_2026-11-05T06-20-27.png")
BG = os.path.join(ASSET, "bg_cover.png")
OUT = os.path.join(ASSET, "cover_news.png")

# 1) 去水印：下裁 52px，重采样回 1536x653（2.35:1）
im = Image.open(RAW).convert("RGB")
w, h = im.size
im = im.crop((0, 0, w, h - 52)).resize((1536, 653), Image.LANCZOS)
im.save(BG, quality=95)
print("bg: %dx%d -> %s 1536x653（下裁52px去水印）" % (w, h, os.path.basename(BG)))

# 2) 三行混色标题，字号成阶梯 1.00 / 0.88 / 0.80，数字放大但主线仍是全图最大字号
C.LINES = [
    dict(scale=1.00, segs=[("190", C.WARM, 1.15), ("元不在票价里", C.WHITE, 1.00)]),
    dict(scale=0.88, segs=[("票面", C.WHITE, 1.00), ("200", C.COOL, 1.15),
                           ("元实付", C.WHITE, 1.00), ("390", C.WARM, 1.15),
                           ("元", C.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("11月4日前出票改签不补", C.WHITE, 1.00)]),
]
# 右下信息胶囊三项，正文均有对应段落
C.PILL = ["80 / 140元", "机建费50元", "按实付算"]

sys.argv = ["cover_neon.py",
            "--bg", BG,
            "--out", OUT,
            "--base", "40",
            "--baseline0", "168",
            "--left", "36"]

if __name__ == "__main__":
    C.main()
