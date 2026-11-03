# -*- coding: utf-8 -*-
"""驱动 cover_neon 出今日封面（不改共享脚本，仅覆盖 LINES/PILL）。"""
import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "公众号", "脚本"))
import cover_neon as cn

cn.LINES = [
    dict(scale=1.00, segs=[("1400", cn.WARM, 1.12), ("倍", cn.WHITE, 1.00), ("市销率", cn.WHITE, 1.00)]),
    dict(scale=0.88, segs=[("营收只有", cn.WHITE, 1.00), ("180", cn.WARM, 1.15), ("万美元", cn.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("11 月 5 日", cn.COOL, 1.05), ("纳斯达克挂牌", cn.WHITE, 1.00)]),
]
cn.PILL = ["市值 25 亿", "订单簿 8 倍", "11/5 挂牌"]

HERE = os.path.dirname(os.path.abspath(__file__))
BG = os.path.join(HERE, "cyberpunk_tech_background__dar_2026-11-03T00-09-32.png")
OUT = os.path.join(HERE, "cover_ai_news.png")
sys.argv = ["cover_neon.py", "--bg", BG, "--out", OUT, "--base", "40", "--baseline0", "168", "--left", "36"]
cn.main()
