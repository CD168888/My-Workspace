# -*- coding: utf-8 -*-
"""今日可领 2026-11-17 封面渲染（霓虹拼贴，SOP 1.4）。

底图由 ImageGen 生成（2.35:1 科技底，已裁掉右下「AI生成」水印），
本脚本只负责文字层：三行混色标题 + 底部信息胶囊。
换期只改下方 LINES / PILL。
"""
import sys
import os
import cover_neon as cn

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "素材", "2026-11-17-ai-福利")
BG = os.path.join(BASE, "bg_clean.png")
OUT = os.path.join(BASE, "cover.png")

# 三行文案（SOP 1.4）：主数字/主文案锚定头条「Hy4 flash 免费到30日」；
# 副行讲标题没讲的那句（生图视频照样扣积分的坑）；尾行补另一条新福利（EdgeOne 50万）。
# 三层都不复读标题「免费用到30日 + 套餐中午收档」的完整说法。
cn.LINES = [
    dict(scale=1.00, segs=[("Hy4 flash", cn.WARM, 1.22, "hei"), (" 免费到 30 日", cn.WHITE, 1.00, "hei")]),
    dict(scale=0.88, segs=[("生图视频照样扣积分", cn.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("EdgeOne 每月送 50 万 Token", cn.WHITE, 1.00)]),
]

# 底部信息胶囊（固定三项 + >）
cn.PILL = ["截止时间整理", "领取方式", "避坑提醒 >"]

if __name__ == "__main__":
    sys.argv = ["cover_2026_11_17.py", "--bg", BG, "--out", OUT,
                "--base", "38", "--baseline0", "200", "--left", "36"]
    cn.main()
