# -*- coding: utf-8 -*-
"""2026-10-30 《今日可领》封面文字层：4,096 今天清零 / 超算夜间只剩今晚 / 13 项在架。

底图由 ImageGen 出 1536x641（2.35:1），下裁 76px 去掉右下「AI生成」水印后
重采样回 1536x653，存 bg_clean.png。本脚本只叠文字与胶囊。

用法：
    python 脚本/cover_2026_10_30.py --bg 素材/2026-10-30-ai-福利/bg_clean.png \
        --out 素材/2026-10-30-ai-福利/cover_news.png \
        --base 34 --baseline0 208 --left 34
"""
import sys

import cover_neon as cn

cn.LINES = [
    # 主线 1.00：主数字绑定今天清零的那份额度
    dict(scale=1.00, segs=[("4,096", cn.WARM, 1.15), ("今天清零", cn.WHITE, 1.00)]),
    # 副线 0.88：标题没提的那件事（超算夜间免费同时收口）
    dict(scale=0.88, segs=[("超算夜间免费", cn.WHITE, 1.00), ("只剩今晚", cn.WARM, 1.00)]),
    # 尾线 0.80：硬信息，和胶囊呼应
    dict(scale=0.80, segs=[("13", cn.COOL, 1.10), ("项在架", cn.WHITE, 1.00),
                           ("，", cn.WHITE, 1.00), ("5", cn.COOL, 1.08),
                           ("项已停", cn.WHITE, 1.00)]),
]

cn.PILL = ["截止时间整理", "领取方式", "避坑提醒"]

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv += ["--out", "cover_neon.png"]
    cn.main()
