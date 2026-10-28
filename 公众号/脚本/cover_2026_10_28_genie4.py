# -*- coding: utf-8 -*-
"""2026-10-28《反着看》封面：Genie 4 的「两分钟」。

霓虹拼贴风（SOP 1.4）。底图 ImageGen 直出 1536x653，裁掉右下「AI生成」水印后重采样回 1536x653。
文字全部本脚本叠：左上 3D 主数字 120 秒 + 左下三行混色标题 + 右下信息胶囊。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover_neon as cn
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-10-28-genie4"))
BG_SRC = os.path.join(BASE_DIR, "bg", "cyberpunk_tech_background__dar_2026-10-28T08-27-53.png")
OUT = os.path.join(BASE_DIR, "cover_news.png")

# 左上 3D 主数字：标题里最硬的那个数，120 秒就是两分钟
NUM = [dict(scale=1.00, segs=[("120", cn.WARM, 1.00), ("秒", cn.WARM, 0.52)])]

# 左下三行：主线 1.02 / 副线 0.88 / 尾线 0.80，成阶梯
LINES = [
    dict(scale=1.02, segs=[("卡在", cn.WHITE, 1.00), ("两分钟", cn.WARM, 1.05)]),
    dict(scale=0.88, segs=[("分辨率帧率跑分", cn.WHITE, 1.00), ("0个", cn.COOL, 1.18)]),
    dict(scale=0.80, segs=[("研究预览 还没开卖", cn.WHITE, 1.00)]),
]

cn.PILL = ["七项短板", "硬参数", "能不能重来"]


def load_bg():
    bg = Image.open(BG_SRC).convert("RGB")
    # 右下「AI生成」水印在下 52px 内，裁掉后重采样回 2.35:1
    bg = bg.crop((0, 0, bg.width, bg.height - 52))
    return bg.resize((cn.W * cn.S, cn.H * cn.S), Image.LANCZOS)


def main():
    bg = load_bg()

    im = cn.render_text(bg, NUM, 34, 116, 78, "hei")
    im = cn.render_text(im, LINES, 34, 190, 44, "hei")
    im = cn.render_pill(im, cn.PILL)

    out = im.convert("RGB").resize((cn.W, cn.H), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("→ %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))

    pill_top = cn.H - 22 - 37
    for name, lines, left, b0, base in (("数字", NUM, 34, 116, 78), ("标题", LINES, 34, 190, 44)):
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
                x += cn.ImageFont.truetype(cn.FONTS["hei"], int(base * line["scale"] * seg[2])).getlength(seg[0])
                prev_text = seg[0]
            print("  %s 字号 %2d 基线 %3d 右端 %3d %s"
                  % (name, int(max_px), int(y), int(x), "右侧出界" if x > 878 else "ok"))
        if name == "标题":
            print("  末行基线 %d，胶囊上沿 %d %s"
                  % (int(baselines[-1]), pill_top,
                     "压到胶囊!" if baselines[-1] > pill_top - 30 else "留白 %dpx" % (pill_top - baselines[-1])))


if __name__ == "__main__":
    main()
