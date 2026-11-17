# -*- coding: utf-8 -*-
"""11-17 期配图整理：筛选同期现场图/一级源截图，统一 1080 宽 JPEG q88。"""
import os
from PIL import Image, ImageEnhance, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
os.makedirs(ASSETS, exist_ok=True)


def load(p):
    return Image.open(os.path.join(BASE, p)).convert("RGB")


def save(img, name, width=1080, q=88):
    if img.width > width:
        h = round(img.height * width / img.width)
        img = img.resize((width, h), Image.LANCZOS)
    out = os.path.join(ASSETS, name)
    img.save(out, "JPEG", quality=q, optimize=True)
    print(name, img.size, "%dKB" % (os.path.getsize(out) // 1024))
    return out


# 1) 上金所官网行情数据（大象新闻 11-17 09:28:59，Au99.99 828.3）——一级源硬证据
save(load("raw_daxiang/001_28ef501144a4.jpg"), "01_sge_828.jpg")

# 2) 新浪 11-17 原文「三个柜台价」段：裁顶部品牌条+黑块，提亮去灰罩
im = load("raw_shot/02_three_prices.png")  # 1800x1280 (2x DPR)
im = im.crop((90, 310, 1710, 940))
im = ImageEnhance.Brightness(im).enhance(1.42)
im = ImageEnhance.Contrast(im).enhance(1.06)
save(im, "02_three_prices.jpg")

# 3) 新浪 11-17 原文「回收规则」段
im = load("raw_shot/01_recycle_rule.png")
im = im.crop((90, 410, 1710, 1120))
im = ImageEnhance.Brightness(im).enhance(1.42)
im = ImageEnhance.Contrast(im).enhance(1.06)
save(im, "03_recycle_rule.jpg")

# 4) 北京日报 11-13 走访：中国黄金柜台「金价160以旧换新 / 定价类黄金8折 / 高价回收」
save(load("raw_bj/002_68a98350a573.jpg"), "04_chinagold_160.jpg")

# 5) 北京日报 11-13 走访：金店柜台顾客挑金
save(load("raw_bj/001_8642bbe44927.jpg"), "05_counter_customers.jpg")

# 6) 北京日报 11-13 走访：珠宝城顾客询价
save(load("raw_bj/003_5bc366c7cc56.jpg"), "06_mall_inquiry.jpg")

# 7) 大象新闻 11-17 黄金连续2702 日K（连跌、829.50 -0.75%）
save(load("raw_daxiang/002_88e16c0d9825.jpg"), "07_futures_drop.jpg")

# 8) 金饰本体特写（龙凤镯，腾讯 11-10 报道配图，无明显年代标志）
save(load("raw_qq2/002_6b83609aa813.jpg"), "08_bangles.jpg")

# ---- 联系表：8 张并排缩略图，人眼复核用 ----
names = sorted(f for f in os.listdir(ASSETS) if f.lower().endswith(".jpg"))
cell_w, cell_h, cols = 400, 300, 2
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell_w, rows * (cell_h + 26)), (245, 245, 245))
d = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    im = Image.open(os.path.join(ASSETS, n)).convert("RGB")
    im.thumbnail((cell_w - 12, cell_h - 12), Image.LANCZOS)
    x = (i % cols) * cell_w + (cell_w - im.width) // 2
    y = (i // cols) * (cell_h + 26) + 6
    sheet.paste(im, (x, y))
    d.text(((i % cols) * cell_w + 10, (i // cols) * (cell_h + 26) + cell_h + 2),
           n, fill=(20, 20, 20))
sheet.save(os.path.join(BASE, "assets_sheet.png"))
print("联系表 assets_sheet.png", sheet.size)
