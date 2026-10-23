"""把生成的正文 HTML 渲染成手机宽度长图，用来人工核对版式。

用法：
    python preview_wechat.py --html ../稿件/反着看/反着看_2026-10-23.html \
        --out ../素材/2026-10-23-tesla-fly/preview.png --width 414
"""
import argparse
import os
import sys

SHELL = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=%(w)d,initial-scale=1">
<style>
  html,body{margin:0;padding:0;background:#EDEDED;}
  body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",
       "Hiragino Sans GB","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased;}
  .phone{width:%(w)dpx;margin:0 auto;background:#fff;padding:16px 14px 40px;
         box-sizing:border-box;}
  .bar{height:44px;background:#EDEDED;}
</style></head><body>
<div class="phone">%(body)s</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=414)
    a = ap.parse_args()

    html = open(a.html, encoding="utf-8").read()
    page = SHELL % {"w": a.width, "body": html}

    tmp = os.path.abspath(a.html).replace(".html", ".preview.html")
    open(tmp, "w", encoding="utf-8").write(page)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": a.width, "height": 900},
                        device_scale_factor=2)
        pg.goto("file:///" + tmp.replace("\\", "/"))
        pg.wait_for_timeout(1200)
        pg.screenshot(path=os.path.abspath(a.out), full_page=True)
        b.close()
    os.remove(tmp)
    print("预览图：%s" % os.path.abspath(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
