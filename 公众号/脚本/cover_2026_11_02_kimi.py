# -*- coding: utf-8 -*-
"""2026-11-02《反着看》封面：Kimi K3.1 Pro 单价降三成，实测多烧一倍 Token。

霓虹拼贴风（SOP 1.4）。底图 ImageGen 直出 1536x653，裁掉右下「AI生成」水印后重采样。
文字全部本脚本叠：左上 3D 主数字 2.4× + 左下三行混色标题 + 右下信息胶囊。
不修改共享 cover_neon.py 的 LINES，只在本 wrapper 里覆盖。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover_neon as cn
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-11-02-kimi-k3.1-pro"))
BG_SRC = os.path.join(
    BASE_DIR, "bg", "Cyberpunk_tech_poster_backgrou_2026-11-02T06-12-26.png")
OUT = os.path.join(BASE_DIR, "cover_news.png")

# 左上 3D 主数字：标题里最硬的那个数——同一任务 token 消耗倍数（144/61）
NUM = [dict(scale=1.00, segs=[("2.4", cn.WARM, 1.00), ("×", cn.WARM, 0.55)])]

# 左下三行：主线 1.00 / 副线 0.88 / 尾线 0.80，成阶梯；不复读标题
LINES = [
    dict(scale=1.00, segs=[("一句指令，", cn.WHITE, 1.00), ("5", cn.COOL, 1.15),
                           ("个子", cn.WHITE, 1.00), ("Agent", cn.COOL, 0.85)]),
    dict(scale=0.88, segs=[("9 分钟烧光", cn.WHITE, 1.00), ("5", cn.WARM, 1.12),
                           ("小时额度", cn.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("单价降了，", cn.WHITE, 1.00), ("账单没降", cn.WARM, 1.02)]),
]

cn.PILL = ["单价降幅", "用量倍数", "真实账单"]


def load_bg():
    bg = Image.open(BG_SRC).convert("RGB")
    bg = bg.crop((0, 0, bg.width, bg.height - 52))
    return bg.resize((cn.W * cn.S, cn.H * cn.S), Image.LANCZOS)


def main():
    bg = load_bg()

    im = cn.render_text(bg, NUM, 34, 112, 96, "hei")
    im = cn.render_text(im, LINES, 36, 175, 40, "hei")
    im = cn.render_pill(im, cn.PILL)

    out = im.convert("RGB").resize((cn.W, cn.H), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("→ %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))

    pill_top = cn.H - 22 - 37
    for name, lines, left, b0, base in (("数字", NUM, 34, 112, 96), ("标题", LINES, 36, 175, 40)):
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
            print("  %s 字号 %2d 基线 %3d 右端 %3d %s"
                  % (name, int(max_px), int(y), int(x),
                     "右侧出界" if x > 878 else "ok"))
        if name == "标题":
            print("  末行基线 %d，胶囊上沿 %d %s"
                  % (int(baselines[-1]), pill_top,
                     "压到胶囊!" if baselines[-1] > pill_top - 30
                     else "留白 %dpx" % (pill_top - baselines[-1])))


if __name__ == "__main__":
    main()
