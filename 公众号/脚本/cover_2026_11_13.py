# -*- coding: utf-8 -*-
"""本期封面驱动（2026-11-13 今日可领）· 复用 cover_neon 渲染逻辑。
底图：ImageGen 1536x640（带右下水印）→ 裁掉底部 76px 去水印 → 缩到 900x383(2.35:1)。
文案：主数字「0元」暖色放大 + 三行混色标题（③ 紧迫提醒型）+ 底部胶囊。
栏目定调：本期最大羊毛是混元 Hy4 在 WorkBuddy/CodeBuddy 的 0 元限免，11-15 23:59 关窗。
封面副文案刻意与文章标题（「混元 Hy4 免费额度剩 3 天，11-15 关窗」）错开，避免封面=标题。
"""
import os
from PIL import Image, ImageFont
import cover_neon as C

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "素材", "2026-11-13-ai-福利")
BG_RAW = os.path.join(HERE, "..", "..", "generated-images",
                       "cyberpunk_tech_background__dar_2026-11-13T00-27-51.png")
BG_CLEAN = os.path.join(SRC, "cover_bg.png")
OUT = os.path.join(SRC, "cover.png")

# 1) 去水印：裁掉底部 76px，再缩到 2.35:1
im = Image.open(BG_RAW).convert("RGB")
w, h = im.size
top = max(0, h - 76)
im = im.crop((0, 0, w, top))
im = im.resize((900, 383), Image.LANCZOS)
im.save(BG_CLEAN, quality=95)
print("bg clean:", BG_CLEAN, im.size)

# 2) 本期文案（三行，成阶梯；主数字「0元」暖色放大，紧迫提醒型）
C.LINES = [
    dict(scale=1.00, segs=[("0元", C.WARM, 1.30, "hei"), (" 混元 Hy4 限时", C.WHITE, 1.00)]),
    dict(scale=0.88, segs=[("免费窗口剩 3 天", C.WHITE, 1.00)]),
    dict(scale=0.80, segs=[("11-15 23:59 关窗", C.WHITE, 1.00)]),
]
C.PILL = ["截止时间整理", "领取方式", "避坑提醒"]

# 3) 调 render（直接拼装，不走 argparse）
bg = Image.open(BG_CLEAN).convert("RGB")
bg = bg.resize((C.W * C.S, C.H * C.S), Image.LANCZOS)
im = C.render_text(bg, C.LINES, C.LEFT, C.BASELINE0, C.BASE_SIZE, "hei",
                   line_h=C.LINE_H, track=C.TRACK)
im = C.render_pill(im, C.PILL)
out = im.convert("RGB").resize((C.W, C.H), Image.LANCZOS)
out.save(OUT, quality=95)
print("→ %s  %dx%d  %dKB" % (OUT, out.width, out.height, os.path.getsize(OUT) // 1024))

# 排版自检
gap = C.TRACK * C.BASE_SIZE
baselines, prev_max = [], None
for i, line in enumerate(C.LINES):
    max_px = max(C.BASE_SIZE * line["scale"] * s[2] for s in line["segs"])
    y = C.BASELINE0 if prev_max is None else baselines[-1] + (prev_max + max_px) / 2 * C.LINE_H
    baselines.append(y); prev_max = max_px
    x = C.LEFT; prev_text = ""
    for seg in line["segs"]:
        key = seg[3] if len(seg) > 3 else "hei"
        x += C.gap_after(prev_text, seg[0], gap)
        x += ImageFont.truetype(C.FONTS[key], int(C.BASE_SIZE * line["scale"] * seg[2])).getlength(seg[0])
        prev_text = seg[0]
    print("  行%d 字号 %2d 基线 %3d 右端 %3d %s" % (i+1, int(max_px), int(y), int(x),
          "右侧出界" if x > 878 else "ok"))
print("  末行基线 %d，胶囊上沿约 %d %s" % (int(baselines[-1]), C.H-22-37,
      "压到胶囊!" if baselines[-1] > C.H-22-37 else "不冲突"))
