# -*- coding: utf-8 -*-
"""2026-11-04 反着看封面 · iPhone天气-32℃误报（霓虹拼贴）。
只覆盖 LINES / PILL，不改共享 cover_neon.py 的任何常量。
底图右下有「AI生成」水印：先下裁 52px 再重采样回 1536x653。
"""
import os
import sys

from PIL import Image

import cover_neon as C

ASSET = r"C:\Users\Administrator\Desktop\My-Workspace\公众号\素材\2026-11-04-iphone-weather"
RAW = os.path.join(ASSET, "cyberpunk_tech_background__dar_2026-11-04T06-19-40.png")
BG = os.path.join(ASSET, "bg_cover.png")
OUT = os.path.join(ASSET, "cover_news.png")

# 1) 去水印：下裁 52px，重采样回 1536x653（2.35:1）
im = Image.open(RAW).convert("RGB")
w, h = im.size
im = im.crop((0, 0, w, h - 52)).resize((1536, 653), Image.LANCZOS)
im.save(BG, quality=95)
print("bg: %dx%d -> %s 1536x653（下裁52px去水印）" % (w, h, os.path.basename(BG)))

# 2) 三行混色标题：主数字 50℃（温差，WARM 放大）；副标/尾线给标题没讲的新信息
C.LINES = [
    dict(scale=1.00, segs=[("50", C.WARM, 1.18), ("℃的温差", C.WHITE, 1.00)]),
    dict(scale=0.88, segs=[("中国天气", C.COOL, 1.00), ("说根本没有", C.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("看气象台别看App", C.WHITE, 1.00)]),
]
# 右下信息胶囊三项（对应正文三处）
C.PILL = ["显示-32℃", "实际十几度", "信气象台 >"]

sys.argv = ["cover_neon.py",
            "--bg", BG,
            "--out", OUT,
            "--base", "40",
            "--baseline0", "168",
            "--left", "36"]

if __name__ == "__main__":
    C.main()
