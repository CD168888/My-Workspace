# -*- coding: utf-8 -*-
"""今日可领 2026-11-14 封面渲染（霓虹拼贴，SOP 1.4）。

底图由 ImageGen 生成（2.35:1 科技底），本脚本只负责文字层：
三行混色标题 + 3D 主数字「词元不限量」+ 底部信息胶囊。
换期只改下方 LINES / PILL。
"""
import sys
import os
import cover_neon as cn

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "素材", "2026-11-14-ai-福利", "assets")
BG = os.path.join(ASSETS, "bg_clean.png")
OUT = os.path.join(HERE, "..", "素材", "2026-11-14-ai-福利", "cover.png")

# 三行文案（SOP 1.4）：主数字=本期最大羊毛「词元不限量」；副标讲标题没讲的那句；尾行给硬截止
cn.LINES = [
    dict(scale=1.00, segs=[("词元不限量", cn.WARM, 1.30, "hei")]),
    dict(scale=0.88, segs=[("0.1 元秒 5000 万", cn.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("11 月 30 日关窗", cn.WHITE, 1.00)]),
]

# 底部信息胶囊（固定三项）
cn.PILL = ["截止时间整理", "领取方式", "避坑提醒 >"]

if __name__ == "__main__":
    sys.argv = ["cover_2026_11_14.py", "--bg", BG, "--out", OUT,
                "--base", "40", "--baseline0", "168", "--left", "36"]
    cn.main()
