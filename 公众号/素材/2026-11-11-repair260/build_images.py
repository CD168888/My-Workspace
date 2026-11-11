# -*- coding: utf-8 -*-
"""2026-11-11 反着看：上门维修 260 元 · 正文配图整理。

只做裁切（去掉重复标题条 / 侧栏推荐位）、转 RGB、缩放、转 JPEG q88。
不叠加任何色块、色条、遮罩、边框，也不写文字。
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

# (输出名, 源文件相对 ROOT, 裁切盒(left, top, right, bottom) 或 None, 目标最大宽)
JOBS = [
    ("01_weibo.jpg",           "raw_163/001_e8bcb44dca19.jpg",          None, 1080),
    ("02_stove.jpg",           "raw_toutiao/001_1dbba668094c.jpg",      None, 750),
    ("03_fault.jpg",           "raw_china/001_355e77e7bd3b.jpg", (0, 400, 650, 1313), 750),
    ("04_bill.jpg",            "raw_china/002_979d5ba72176.jpg", (0, 400, 650, 1313), 750),
    ("05_truth.jpg",           "raw_china/003_bc55c045dcc6.jpg", (0, 400, 650, 1313), 750),
    ("06_rectify_notice.jpg",  "raw_mrjjxw/001_fe0b96c3619c.png",       None, 1080),
    # shot_anchor 输出为 2x DPR 的 2200x1240；只裁掉右侧推荐位 / 左侧工具栏，保留正文整行
    ("07_rule_text.jpg",       "raw_shots/rectify2025.png",      (0, 0, 1680, 1240), 1080),
    ("08_prospectus.jpg",      "raw_shots/prospectus40.png",     (200, 150, 2200, 1240), 1080),
]

for name, src, box, maxw in JOBS:
    p = os.path.join(ROOT, src)
    im = Image.open(p)
    if im.mode != "RGB":
        im = im.convert("RGB")
    if box:
        im = im.crop(box)
    if im.width > maxw:
        h = round(im.height * maxw / im.width)
        im = im.resize((maxw, h), Image.LANCZOS)
    out = os.path.join(ASSETS, name)
    im.save(out, "JPEG", quality=88, optimize=True)
    kb = os.path.getsize(out) // 1024
    print("%-24s %4dx%-4d %4dKB" % (name, im.width, im.height, kb))
    assert kb < 1024, "too big: " + name

print("OK", len(JOBS), "images ->", ASSETS)
