# -*- coding: utf-8 -*-
"""2026-11-03 反着看封面 · 麦芽糊精保健品诈骗（霓虹拼贴）。
只覆盖 LINES / PILL，不改共享 cover_neon.py 的任何常量。
"""
import os
import sys

import cover_neon as C

ASSET = r"C:\Users\Administrator\Desktop\My-Workspace\公众号\素材\2026-11-03-maltodextrin-fraud"
BG = os.path.join(ASSET, "bg_cover.png")
OUT = os.path.join(ASSET, "cover_news.png")

# 三行混色标题：主数字 200× 绑定 WARM 放大段；副标/尾线给标题没讲的新信息
C.LINES = [
    dict(scale=1.00, segs=[("200", C.WARM, 1.18), ("倍的价差", C.WHITE, 1.00)]),
    dict(scale=0.88, segs=[("出厂", C.WHITE, 1.00), ("1元", C.WARM, 1.12), ("的成本", C.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("蓝帽子才是真门槛", C.WHITE, 1.00)]),
]
# 右下信息胶囊三项（对应正文三处）
C.PILL = ["成本30元", "售价6000元", "认准蓝帽子"]

sys.argv = ["cover_neon.py",
            "--bg", BG,
            "--out", OUT,
            "--base", "40",
            "--baseline0", "168",
            "--left", "36"]

if __name__ == "__main__":
    C.main()
