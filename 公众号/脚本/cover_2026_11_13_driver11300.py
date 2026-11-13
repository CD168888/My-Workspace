# -*- coding: utf-8 -*-
"""2026-11-13《反着看》封面：日入800元的司机招聘，6小时只挣140元。

底图 ImageGen 一次直出（实得 1536x640），深蓝电路 + 右侧 3D 玻璃厢式货车
+ 悬浮图标卡 + 空白汽车租赁合同 + 逆向资金箭头 + 硬币，左侧暗色留白；
右下「AI生成」水印已下裁 52px 再重采样 1536x653 存 cover_bg.png。

文字全部由本脚本叠：左上 3D 主数字 + 左下三行混色标题 + 右下信息胶囊。
不修改共享 cover_neon.py 的 LINES，只在本 wrapper 里覆盖。

文案口径（封面不复读标题「日入800元的司机招聘，6小时只挣140元」，
也不复读摘要「11300元租金押金 / 14190元违约金 / 70余人 / 300余万元」的三项事实）：
  主数字 11300 —— 招工先收的那笔钱，是「资金方向反转」的一手起点。
  主线「先交11300元」—— 与主数字绑定，讲这笔钱发生在上岗之前。
  副线「合同没一条写工作内容」—— 标题没讲的那句，第二节核心落差。
  尾线「没有一分物流收入」—— 第三节警方查资金流水的一手硬数。
  胶囊三项对应正文：谁先掏钱（第五节）、口头不落纸（第二节）、民警只能调解（第三/四节）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover_neon as cn
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-11-13-driver-scam"))
BG_SRC = os.path.join(BASE_DIR, "cover_bg.png")
BG = os.path.join(BASE_DIR, "bg_cover.png")
OUT = os.path.join(BASE_DIR, "cover_news.png")

# 左上 3D 主数字：先交的 11300 元
NUM = [dict(scale=1.00, segs=[("11300", cn.WARM, 1.00)])]

# 左下三行：主线 1.00 / 副线 0.88 / 尾线 0.80，成阶梯
LINES = [
    dict(scale=1.00, segs=[("先交", cn.WHITE, 1.00), ("11300", cn.WARM, 1.10),
                           ("元", cn.WHITE, 1.00)]),
    dict(scale=0.88, segs=[("合同没一条", cn.WHITE, 1.00), ("写工作内容", cn.COOL, 1.00)]),
    dict(scale=0.80, segs=[("没有", cn.WHITE, 1.00), ("一分物流收入", cn.COOL, 1.00)]),
]

cn.PILL = ["谁先掏钱", "口头不落纸", "民警只能调解"]


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
    im = cn.render_text(bg, NUM, 34, 112, 88, "hei")
    im = cn.render_text(im, LINES, 36, 168, 40, "hei")
    im = cn.render_pill(im, cn.PILL)
    out = im.convert("RGB").resize((cn.W, cn.H), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("→ %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))
    selfcheck("数字", NUM, 34, 112, 88)
    selfcheck("标题", LINES, 36, 168, 40)


if __name__ == "__main__":
    main()
