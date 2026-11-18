# -*- coding: utf-8 -*-
"""今日可领 2026-11-18 封面渲染（霓虹拼贴，SOP 1.4）。

底图由 ImageGen 生成（2.35:1 科技底，已下裁 55px 去掉右下「AI生成」水印，
重采样回 1536x653 → bg_clean.png）。本脚本只负责文字层：
三行混色标题 + 底部信息胶囊。换期只改 LINES / PILL。
"""
import sys
import os
import cover_neon as cn

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "素材", "2026-11-18-ai-福利")
BG = os.path.join(BASE, "bg_clean.png")
OUT = os.path.join(BASE, "cover.png")

# 三行文案（SOP 1.4）：主行数字「1%」锚定头条书生 S2.1 Flash 的最大羊毛；
# 副行讲标题没讲的那句（另两条 0 元窗口明后天关窗）；尾行给硬截止日（12-09）。
# 三层都不复读标题完整说法「书生新模型按1%收费，别急着给API充值」。
cn.LINES = [
    dict(scale=1.00, segs=[("书生新模型按 ", cn.WHITE, 1.00, "hei"),
                           ("1%", cn.WARM, 1.22, "hei"),
                           (" 收费", cn.WHITE, 1.00, "hei")]),
    dict(scale=0.88, segs=[("百灵与 Watt 云明后天关窗", cn.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("1% 价收到 12 月 9 日", cn.WHITE, 1.00)]),
]

# 底部信息胶囊（固定三项 + >）
cn.PILL = ["截止时间整理", "领取方式", "避坑提醒 >"]

if __name__ == "__main__":
    sys.argv = ["cover_2026_11_18.py", "--bg", BG, "--out", OUT,
                "--base", "38", "--baseline0", "196", "--left", "36"]
    cn.main()
