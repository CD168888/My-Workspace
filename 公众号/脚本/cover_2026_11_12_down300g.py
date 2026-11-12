# -*- coding: utf-8 -*-
"""2026-11-12《反着看》封面：山姆399元羽绒服断货：300克是L码，绒子约240克。

底图 ImageGen 一次直出（实得 1536x640），深蓝电路 + 右侧 3D 玻璃羽绒服剖面
（可见绒朵）、放大镜、空白吊牌与图标卡，左侧留白；右下「AI生成」水印已下裁
52px 并重采样到 1536x653，存为 cover_bg.png。

文字全部由本脚本叠：左上 3D 主数字 + 左下三行混色标题 + 右下信息胶囊。
不修改共享 cover_neon.py 的 LINES，只在本 wrapper 里覆盖。

文案口径（封面不复读标题「山姆399元羽绒服断货：300克是L码，绒子约240克」）：
  主数字 80% —— 吊牌明示的绒子含量，是折算 240 克的那个分母，标题没给。
  主线「绒子含量80%」—— 与主数字绑定，讲这一栏写的是什么。
  副线「帽子等部位填聚酯纤维」—— 标题没讲的那句，部位落差。
  尾线「70款送检22款不达标」—— 安徽省消保委比较试验的一手硬数，
  与摘要用词一致；短一档可让右端完全落在左侧留白，不压放大镜。
  胶囊三项对应正文：L码限定（第一节）、允差-5.0%（第三节）、代购加价（第四节）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover_neon as cn
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-11-12-down300g"))
BG_SRC = os.path.join(BASE_DIR, "cover_bg.png")
BG = os.path.join(BASE_DIR, "bg_cover.png")
OUT = os.path.join(BASE_DIR, "cover_news.png")

# 左上 3D 主数字：80%
NUM = [dict(scale=1.00, segs=[("80", cn.WARM, 1.00), ("%", cn.WARM, 0.72)])]

# 左下三行：主线 1.00 / 副线 0.88 / 尾线 0.80，成阶梯
LINES = [
    dict(scale=1.00, segs=[("绒子含量", cn.WHITE, 1.00), ("80%", cn.WARM, 1.10)]),
    dict(scale=0.88, segs=[("帽子等部位", cn.WHITE, 1.00), ("填聚酯纤维", cn.COOL, 1.00)]),
    dict(scale=0.80, segs=[("70", cn.COOL, 1.12), ("款送检", cn.WHITE, 1.00),
                           ("22", cn.WARM, 1.12), ("款不达标", cn.WHITE, 1.00)]),
]

cn.PILL = ["L码限定", "允差-5.0%", "代购加价"]


def load_bg():
    im = Image.open(BG_SRC).convert("RGB")
    w, h = im.size
    im = im.resize((cn.W * cn.S, cn.H * cn.S), Image.LANCZOS)
    im.save(BG, quality=95)
    print("bg: %dx%d -> %dx%d（水印已在 cover_bg.png 裁除）" % (w, h, im.width, im.height))
    return im


def selfcheck(name, lines, left, b0, base):
    baselines, prev_max = [], None
    for line in lines:
        max_px = max(base * line["scale"] * s[2] for s in line["segs"])
        y = b0 if prev_max is None else baselines[-1] + (prev_max + max_px) / 2 * 1.18
        baselines.append(y)
        prev_max = max_px
        x = left
        prev_text = ""
        for seg in line["segs"]:
            x += cn.gap_after(prev_text, seg[0], 0.10 * base)
            x += cn.ImageFont.truetype(
                cn.FONTS["hei"], int(base * line["scale"] * seg[2])).getlength(seg[0])
            prev_text = seg[0]
        print("  %s 基准字号 %2d 最大字号 %2d 基线 %3d 右端 %3d %s"
              % (name, int(base * line["scale"]), int(max_px), int(y), int(x),
                 "右侧出界" if x > 878 else "ok"))
    if name == "标题":
        pill_top = cn.H - 22 - 37
        print("  末行基线 %d，胶囊上沿 %d %s"
              % (int(baselines[-1]), pill_top,
                 "压到胶囊!" if baselines[-1] > pill_top - 30
                 else "留白 %dpx" % (pill_top - baselines[-1])))


def main():
    bg = load_bg()
    im = cn.render_text(bg, NUM, 34, 112, 96, "hei")
    im = cn.render_text(im, LINES, 36, 168, 40, "hei")
    im = cn.render_pill(im, cn.PILL)
    out = im.convert("RGB").resize((cn.W, cn.H), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("→ %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))
    selfcheck("数字", NUM, 34, 112, 96)
    selfcheck("标题", LINES, 36, 168, 40)


if __name__ == "__main__":
    main()
