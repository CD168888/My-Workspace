# -*- coding: utf-8 -*-
"""2026-11-06 今日可领封面：去水印 + 叠字（复用 cover_neon 渲染逻辑）。"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MAT = os.path.join(HERE, "..", "素材", "2026-11-06-ai-福利")
RAW = os.path.join(MAT, "cyberpunk_tech_background__dar_2026-11-06T01-17-36.png")
BG_CLEAN = os.path.join(MAT, "bg_clean.png")
OUT = os.path.join(MAT, "cover.png")

# 1) 去右下角「AI生成」水印：下裁 76px，再重采样回 1536x653
im = Image.open(RAW).convert("RGB")
w, h = im.size
im = im.crop((0, 0, w, max(1, h - 76)))
im = im.resize((1536, 653), Image.LANCZOS)
im.save(BG_CLEAN)
print("bg_clean:", im.size)

# 2) 叠字
import cover_neon

W = cover_neon.WHITE
WARM = cover_neon.WARM
COOL = cover_neon.COOL

cover_neon.LINES = [
    dict(scale=1.00, segs=[("阿里云", W, 1.00, "hei"), ("双11", WARM, 1.20, "hei"), ("会场开", W, 1.00, "hei")]),
    dict(scale=0.88, segs=[("新户领", W, 0.88), ("7000万", WARM, 1.18), ("免费额度", W, 0.88)]),
    dict(scale=0.80, segs=[("Lite 档", COOL, 0.80), ("19.5 元/月", WARM, 0.95), ("，五折起", W, 0.80)]),
]
cover_neon.PILL = ["截止时间整理", "领取方式", "避坑提醒"]

sys.argv = ["cover_neon.py", "--bg", BG_CLEAN, "--out", OUT,
            "--base", "40", "--baseline0", "168", "--left", "36"]
cover_neon.main()
