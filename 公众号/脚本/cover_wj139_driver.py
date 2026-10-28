# -*- coding: utf-8 -*-
"""问界139.1 封面驱动：复用 cover_neon 渲染逻辑，按本稿文案覆盖 LINES/PILL，不改共享脚本。"""
import importlib.util, sys

# 底图：10-26 起火现场实拍（用户指定），预裁 2.35:1
BASE = r"C:/Users/Administrator/Desktop/My-Workspace/公众号/素材/2026-10-26-问界139.1/fire_scene_base.png"
OUT  = r"C:/Users/Administrator/Desktop/My-Workspace/公众号/素材/2026-10-26-问界139.1/cover_fire.png"
SCRIPT = r"C:/Users/Administrator/Desktop/My-Workspace/公众号/脚本/cover_neon.py"

spec = importlib.util.spec_from_file_location("cover_neon", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 三行混色标题：主数字 + 主文案 / 副标（标题没讲的那句）/ 副文案（硬信息）
m.LINES = [
    dict(scale=1.00, segs=[("139.1", m.WARM, 1.33), ("km/h", m.COOL, 0.58),
                           ("问界撞柱起火", m.WHITE, 0.82)]),
    dict(scale=0.86, segs=[("小米给的是", m.WHITE, 1.00), ("整条时间轴", m.COOL, 1.04)]),
    dict(scale=0.80, segs=[("两起起火，", m.WHITE, 1.00), ("两种回应", m.WARM, 1.00)]),
]
# 底部信息胶囊：三项均在正文中对应段落
m.PILL = ["139.1 怎么来", "小米怎么答", "数据谁手里"]

sys.argv = ["cover_neon.py", "--bg", BASE, "--out", OUT,
            "--base", "44", "--baseline0", "196", "--left", "42"]
m.main()
