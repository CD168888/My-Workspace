# -*- coding: utf-8 -*-
"""2026-11-08《反着看》封面：棉服「0 克棉花」口径核验（霓虹拼贴 SOP 1.4）。

底图 ImageGen 直出 1536x653：深蓝电路 + 右侧 3D 玻璃棉服剖面（螺旋化纤填充）、
空白吊牌、放大镜；左侧留白。右下「AI生成」水印下裁 52px 后重采样回 2.35:1。
文字全部本脚本叠：左上 3D 主数字 + 左下三行混色标题 + 右下信息胶囊。
不修改共享 cover_neon.py 的 LINES，只在本 wrapper 里覆盖。

文案口径：
  主数字 0克 —— 标题里最硬的那个数，也是被拆穿的落差本身。
  主线「名字里的棉不算数」—— 讲判断，不复读标题的「合规/违规」。
  副线「填充物三行都写聚酯纤维」—— 标题没给的吊牌细节。
  尾线「羽绒棉含绒不足1%」—— 一级源消费警示里的另一组数，封面三行未出现。
  胶囊三项均对应正文段落，且不与三行自复读。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover_neon as cn
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-11-08-cotton-padded"))
BG_SRC = os.path.join(
    BASE_DIR, "Wide_2_35_1_cinematic_cyberpun_2026-11-08T06-32-50.png")
BG = os.path.join(BASE_DIR, "bg_cover.png")
OUT = os.path.join(BASE_DIR, "cover_news.png")

# 左上 3D 主数字
NUM = [dict(scale=1.00, segs=[("0", cn.WARM, 1.00), ("克", cn.WARM, 0.62)])]

# 左下三行：主线 1.00 / 副线 0.88 / 尾线 0.80，成阶梯；不复读标题
LINES = [
    dict(scale=1.00, segs=[("名字里的棉", cn.WHITE, 1.00), ("不算数", cn.WARM, 1.05)]),
    dict(scale=0.88, segs=[("填充物三行", cn.COOL, 1.06), ("都写聚酯纤维", cn.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("羽绒棉含绒不足1%", cn.WHITE, 1.00)]),
]

cn.PILL = ["品类与成分", "1—2秒回弹", "18批次虚标"]


def load_bg():
    im = Image.open(BG_SRC).convert("RGB")
    w, h = im.size
    im = im.crop((0, 0, w, h - 52))          # 去右下「AI生成」水印
    im = im.resize((cn.W * cn.S, cn.H * cn.S), Image.LANCZOS)
    im.save(BG, quality=95)
    print("bg: %dx%d -> 下裁52px -> %dx%d" % (w, h, im.width, im.height))
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
        print("  %s 字号 %2d 基线 %3d 右端 %3d %s"
              % (name, int(max_px), int(y), int(x),
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
    im = cn.render_text(im, LINES, 36, 175, 40, "hei")
    im = cn.render_pill(im, cn.PILL)
    out = im.convert("RGB").resize((cn.W, cn.H), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("→ %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))
    selfcheck("数字", NUM, 34, 112, 96)
    selfcheck("标题", LINES, 36, 175, 40)


if __name__ == "__main__":
    main()
