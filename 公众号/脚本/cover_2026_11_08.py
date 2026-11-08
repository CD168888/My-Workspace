# -*- coding: utf-8 -*-
"""2026-11-08 今日可领封面 · 霓虹拼贴（SOP 1.4 / 栏目规范 六）。
复用 cover_neon.py 的文字层与排版自检，只换本期 LINES / PILL / 主数字，不改动共享脚本。
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import cover_neon as cn

BG = r"C:\Users\Administrator\Desktop\My-Workspace\公众号\素材\2026-11-08-ai-福利\Dark_futuristic_tech_backgroun_2026-11-08T01-19-08.png"
OUT = r"C:\Users\Administrator\Desktop\My-Workspace\公众号\素材\2026-11-08-ai-福利\cover_news.png"

# 主数字 "5亿"（主文案首段放大，暖色）；副标讲标题没提的百川/电信；副文案给硬信息
cn.LINES = [
    dict(scale=1.00, segs=[("5亿", cn.WARM, 1.15, "hei"), (" Tokens 明早清零", cn.WHITE, 1.00)]),
    dict(scale=0.88, segs=[("百川 1000 万、电信 TeleAgent 也免费", cn.WHITE, 0.88)]),
    dict(scale=0.80, segs=[("本周还新收 4 条 AI 福利", cn.WHITE, 0.80)]),
]
# 信息胶囊固定三项（栏目规范 六）
cn.PILL = ["截止时间整理", "领取方式", "避坑提醒 >"]

sys.argv = ["cover_neon.py", "--bg", BG, "--out", OUT,
            "--base", "40", "--baseline0", "212", "--left", "38"]
cn.main()
