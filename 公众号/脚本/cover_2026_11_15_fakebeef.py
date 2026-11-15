# -*- coding: utf-8 -*-
"""2026-11-15《反着看》封面：10元猪肉冒充30多元牛肉，买前先算三个价

底图 ImageGen 一次直出（请求 1536x653，实得 1536x640），深蓝电路
+ 右侧 3D 玻璃肉块切片 + DNA 双螺旋 + 空白价签 + 放大镜，左侧大块暗色留白；
右下「AI生成」水印已下裁 52px 再重采样 1536x653 存 cover_bg.png。

文字全部由本脚本叠：左上 3D 主数字 + 左下三行混色标题 + 右下信息胶囊。
不修改共享 cover_neon.py 的 LINES / PILL，只在本 wrapper 里覆盖。

文案口径（封面不复读标题「10元猪肉冒充30多元牛肉，买前先算三个价」，
也不复读摘要的 36.755元 / DNA / 七年 / 柠檬黄禁用）：
  主数字 36.755 —— 一手核验出的真牛肉每斤批发均价，本期最硬的那个数。
  主线「售价低于批发价」—— 标题只说「算三个价」，封面给判断。
  副线「颜色气味纹理都能造」—— 标题没讲的那句，三重伪装为什么能骗过肉眼。
  尾线「差价每斤16到25元」—— 自算硬数，标题与摘要都没给，与胶囊首项呼应。
  胶囊三项对应正文第五节判断标准：换算单价 / 要两证 / 留票据。

等价命令（共享脚本口径）：
  python 公众号/脚本/cover_neon.py --bg cover_bg.png --out cover_news.png \
      --base 40 --baseline0 168 --left 36
本 wrapper 额外多叠一层左上主数字，并覆盖本期 LINES / PILL。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cover_neon as cn
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "素材", "2026-11-15-fakebeef"))
BG_SRC = os.path.join(BASE_DIR, "cover_bg.png")
OUT = os.path.join(BASE_DIR, "cover_news.png")

# 左上 3D 主数字：农业农村部第45周牛肉批发均价 73.51 元/公斤 ÷ 2 = 36.755 元/斤
NUM = [dict(scale=1.00, segs=[("36.755", cn.WARM, 1.00)])]

# 左下三行：主线 1.00 / 副线 0.88 / 尾线 0.80，成阶梯
LINES = [
    dict(scale=1.00, segs=[("售价", cn.WHITE, 1.00), ("低于批发价", cn.WARM, 1.00)]),
    dict(scale=0.88, segs=[("颜色气味纹理", cn.WHITE, 1.00), ("都能造", cn.COOL, 1.00)]),
    dict(scale=0.80, segs=[("差价每斤", cn.WHITE, 1.00), ("16到25元", cn.COOL, 1.00)]),
]

cn.PILL = ["先换算单价", "当场要两证", "留票据样品"]


def load_bg():
    im = Image.open(BG_SRC).convert("RGB")
    w, h = im.size
    im = im.resize((cn.W * cn.S, cn.H * cn.S), Image.LANCZOS)
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
    im = cn.render_text(bg, NUM, 34, 112, 84, "hei")
    im = cn.render_text(im, LINES, 36, 168, 40, "hei")
    im = cn.render_pill(im, cn.PILL)
    out = im.convert("RGB").resize((cn.W, cn.H), Image.LANCZOS)
    out.save(OUT, quality=95)
    print("-> %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))
    selfcheck("数字", NUM, 34, 112, 84)
    selfcheck("标题", LINES, 36, 168, 40)


if __name__ == "__main__":
    main()
