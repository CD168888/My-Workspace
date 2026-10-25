"""Playwright 截首屏（营销页 / SPA 没有正文容器时，比抓 collection 靠谱）。

用法：
    python shot_first_screen.py --url "https://..." --out 素材/x/a.png [--full] [--wait 6000]
"""
import argparse
import os
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wait", type=int, default=6000)
    ap.add_argument("--full", action="store_true", help="截整页")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    a = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": a.width, "height": a.height},
                            user_agent=UA, device_scale_factor=1)
        pg = ctx.new_page()
        try:
            pg.goto(a.url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print("goto warn:", e)
        pg.wait_for_timeout(a.wait)
        try:
            pg.mouse.wheel(0, 400)
            pg.wait_for_timeout(800)
        except Exception:
            pass
        pg.screenshot(path=a.out, full_page=a.full)
        print("saved", a.out, "title:", pg.title()[:60])
        b.close()


if __name__ == "__main__":
    main()
