# -*- coding: utf-8 -*-
"""2026-11-18《反着看》封面：129万降到28.86万，能报的只有三种淋巴瘤

底图 ImageGen 一次直出（请求 1536x653，实得 1536x640），深蓝电路
+ 右侧 3D 输液袋 / 注射器 / 淋巴细胞球 / 空白全息卡片 / 日历沙漏图标，
左侧大片暗部留白；右下「AI生成」水印下裁 52px 后重采样 1536x653 存 cover_bg.png。

文字全部由本脚本叠：左上 3D 主数字 + 左下三行混色标题 + 右下信息胶囊。
不修改共享 cover_neon.py 的 LINES / PILL，只在本 wrapper 里覆盖。

文案口径（封面不复读标题「129万降到28.86万，能报的只有三种淋巴瘤」）：
  主数字 28.86万 —— 标题里最硬的官方数，经济参考报 11-17 的谈判支付标准，
                    药明巨诺 11-15 投资者交流会公布 288600 元，同一个数。
  主线「降下来的不是自付」—— 标题只给降价，没说降的是什么，直接回答。
  副线「10万出自专家估算」—— 标题没给的第二个数，李洪超估算且带「可能」。
  尾线「297号 三项都限二线及以上」—— 目录条目的真限制，标题只说三种淋巴瘤。
  胶囊三项对应正文：一、三个数三套口径 / 二、目录297号 / 五、几道关三句话。

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
    os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-11-18-cart"))
BG_SRC = os.path.join(BASE_DIR, "cover_bg.png")
OUT = os.path.join(BASE_DIR, "cover_news.png")

# 左上 3D 主数字：28.86 万元，医保谈判支付标准（官方数，非自付金额）
NUM = [dict(scale=1.00, segs=[("28.86", cn.WARM, 1.00), ("万", cn.WHITE, 0.86)])]

# 左下三行：主线 1.00 / 副线 0.88 / 尾线 0.80，成阶梯
LINES = [
    dict(scale=1.00, segs=[("降下来的", cn.WHITE, 1.00), ("不是自付", cn.WARM, 1.00)]),
    dict(scale=0.88, segs=[("10万", cn.COOL, 1.00), ("出自专家估算", cn.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("297号", cn.COOL, 1.00), ("三项都限二线及以上", cn.WHITE, 1.00)]),
]

cn.PILL = ["先分三个数", "再看297号", "末了问医院"]


def prepare_bg():
    """生图右下自带「AI生成」水印：下裁 52px 再重采样回 1536x653。"""
    raw = sorted(glob.glob(os.path.join(BASE_DIR, "Ultra_wide_2_35_1_cyberpunk_te*.png")))[-1]
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
    im = cn.render_text(bg, NUM, 34, 112, 62, "hei")
    im = cn.render_text(im, LINES, 36, 168, 40, "hei")
    im = cn.render_pill(im, cn.PILL)
    out = im.convert("RGB").resize((cn.W, cn.H), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("-> %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))
    selfcheck("数字", NUM, 34, 112, 62)
    selfcheck("标题", LINES, 36, 168, 40)


if __name__ == "__main__":
    main()
