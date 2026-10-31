# -*- coding: utf-8 -*-
"""2026-10-31 反着看封面 · 霓虹拼贴（SOP 1.4）。
文案三层：主数字 64% 绑定主文案，副标给标题没说的「标称500→实际318」，尾行硬信息呼应胶囊。
底图：ImageGen 出 2.35:1 深色科技底（无文字），文字 100% 由 cover_neon 叠。
"""
import sys
sys.path.insert(0, r"C:\Users\Administrator\Desktop\My-Workspace\公众号\脚本")
import cover_neon as cn

cn.LINES = [
    # 主线：主数字 64% + 核心事件（标题没把「打六四折」说出来）
    dict(scale=1.00, segs=[("冬天续航", cn.WHITE, 0.95),
                           ("64%", cn.WARM, 1.28),
                           ("打六四折", cn.WARM, 0.92)]),
    # 副线：标题没说的那句——标称和实际的对账（信息差型）
    dict(scale=0.86, segs=[("标称500", cn.COOL, 1.05),
                           ("实际只有", cn.WHITE, 0.95),
                           ("318", cn.COOL, 1.12),
                           ("公里", cn.WHITE, 0.9)]),
    # 尾线：硬信息，呼应底部胶囊
    dict(scale=0.80, segs=[("零下7度实测", cn.WHITE, 1.0),
                           ("官方盖了章", cn.WARM, 0.95)]),
]
cn.PILL = ["官方指南", "三档对照", "怎么算 >"]

# 2.35:1 扁画幅：字号比 16:9 小一号，基线往下压
cn.BASE_SIZE = 38
cn.BASELINE0 = 226
cn.LEFT = 36
cn.TRACK = 0.10

BG = r"C:\Users\Administrator\Desktop\My-Workspace\公众号\素材\2026-10-31-cltc-range\bg\cyberpunk_tech_background__dar_2026-10-31T06-14-13.png"
OUT = r"C:\Users\Administrator\Desktop\My-Workspace\公众号\素材\2026-10-31-cltc-range\cover_news.png"

im = cn.Image.open(BG).convert("RGB")
W0, H0 = im.size
im = im.crop((0, 0, W0, H0 - 52))                       # 去掉底部疑似「AI生成」水印带
im = im.resize((cn.W * cn.S, cn.H * cn.S), cn.Image.LANCZOS)

out = cn.render_text(im, cn.LINES, cn.LEFT, cn.BASELINE0, cn.BASE_SIZE,
                     "hei", line_h=cn.LINE_H, track=cn.TRACK)
out = cn.render_pill(out, cn.PILL)
out.convert("RGB").resize((cn.W, cn.H), cn.Image.LANCZOS).save(OUT, quality=95)
print("→", OUT)

# ---- 排版自检（与 cover_neon.main 同逻辑）----
gap = cn.TRACK * cn.BASE_SIZE
baselines, prev_max = [], None
for i, line in enumerate(cn.LINES):
    max_px = max(cn.BASE_SIZE * line["scale"] * s[2] for s in line["segs"])
    y = cn.BASELINE0 if prev_max is None else baselines[-1] + (prev_max + max_px) / 2 * cn.LINE_H
    baselines.append(y)
    prev_max = max_px
    x = cn.LEFT
    prev_text = ""
    for seg in line["segs"]:
        key = seg[3] if len(seg) > 3 else "hei"
        x += cn.gap_after(prev_text, seg[0], gap)
        x += cn.ImageFont.truetype(cn.FONTS[key], int(cn.BASE_SIZE * line["scale"] * seg[2])).getlength(seg[0])
        prev_text = seg[0]
    print("  行%d 字号 %2d 基线 %3d 右端 %3d %s"
          % (i + 1, int(max_px), int(y), int(x), "右侧出界" if x > 878 else "ok"))
print("  末行基线 %d，胶囊上沿约 %d %s"
      % (int(baselines[-1]), cn.H - 22 - 37,
         "压到胶囊!" if baselines[-1] > cn.H - 22 - 37 else "不冲突"))
