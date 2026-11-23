# -*- coding: utf-8 -*-
"""2026-11-23《反着看》封面：网传糟蹋一千多斤苹果，11月23日通报只称出181斤。

底图 ImageGen 一次直出（请求 1536x653，实得 1536x640），深蓝电路底
+ 右侧 3D 玻璃切开的苹果/电子秤/空白全息读数卡 + 左侧大片暗部留白；
右下「AI生成 WORKBUDDY」水印下裁 52px 后重采样 1536x653 存 cover_bg.png。

文字全部由本脚本叠：左上 3D 主数字 + 左下三行混色标题 + 右下信息胶囊。
不修改共享 cover_neon.py 的 LINES / PILL，只在本 wrapper 里覆盖。

文案口径（封面不复读标题「网传糟蹋一千多斤苹果，11月23日通报只称出181斤」）：
  主数字「181斤」—— 通报现场称量的那个数，标题里最硬的锚点。
  主线「双方见证下过秤」—— 通报原话里的方式限定，标题没讲。
  副线「主播受邀找错果园」—— 标题没讲的那句（应常某某邀请、找错地点误入）。
  尾线「11月22日已道歉赔偿」—— 通报结论，硬信息。
  胶囊三项对应正文：二节分估算与称量 / 三节核单价与倍数 / 五节等通报再转发。

等价命令（共享脚本口径）：
  python 公众号/脚本/cover_neon.py --bg cover_bg.png --out cover_news.png \
      --base 40 --baseline0 168 --left 36
本 wrapper 额外多叠一层左上主数字，并覆盖本期 LINES / PILL。
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover_neon as cn
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-11-23-apple181"))
BG_SRC = os.path.join(BASE_DIR, "cover_bg.png")
OUT = os.path.join(BASE_DIR, "cover_news.png")

# 左上 3D 主数字：政府通报「经现场称量，损毁苹果共计181斤」
NUM = [dict(scale=1.00, segs=[("181", cn.WARM, 1.00), ("斤", cn.WHITE, 0.80)])]

# 左下三行：主线 1.00 / 副线 0.88 / 尾线 0.80，成阶梯；三层都不复读标题
LINES = [
    dict(scale=1.00, segs=[("双方见证下", cn.WHITE, 1.00), ("过秤", cn.WARM, 1.00)]),
    dict(scale=0.88, segs=[("主播受邀找错果园", cn.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("11月22日", cn.WHITE, 1.00), ("已道歉赔偿", cn.COOL, 1.00)]),
]

cn.PILL = ["估算与称量分开看", "单价和倍数自己核", "等通报再转发"]


def prepare_bg():
    """生图右下自带「AI生成」水印：下裁 52px 再重采样回 1536x653。"""
    raw = sorted(glob.glob(os.path.join(
        BASE_DIR, "Ultra_wide_2_35_1_cyberpunk_te_*.png")))[-1]
    im = Image.open(raw).convert("RGB")
    w, h = im.size
    crop = im.crop((0, 0, w, h - 52))
    out = crop.resize((1536, 653), Image.LANCZOS)
    out.save(BG_SRC, quality=95)
    print("bg raw %dx%d -> crop %dx%d -> %s %dx%d"
          % (w, h, crop.width, crop.height, os.path.basename(BG_SRC), out.width, out.height))
    return raw


def load_bg():
    im = Image.open(BG_SRC).convert("RGB")
    w, h = im.size
    im = im.resize((cn.W * cn.S, cn.H * cn.S), Image.LANCZOS)
    print("bg: %dx%d -> %dx%d（水印已裁除）" % (w, h, im.width, im.height))
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
    prepare_bg()
    bg = load_bg()
    im = cn.render_text(bg, NUM, 34, 112, 78, "hei")
    im = cn.render_text(im, LINES, 36, 168, 40, "hei")
    im = cn.render_pill(im, cn.PILL)
    out = im.convert("RGB").resize((cn.W, cn.H), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("-> %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))
    selfcheck("数字", NUM, 34, 112, 78)
    selfcheck("标题", LINES, 36, 168, 40)


if __name__ == "__main__":
    main()
