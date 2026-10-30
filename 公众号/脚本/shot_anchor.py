"""按锚点文字定位截图（活动页 / 文档页取证据段用）。

用法：
    python shot_anchor.py --url "<URL>" --anchor "领取期限与使用期限" --out 素材/x/a.png \
        [--w 1100] [--h 760] [--pad 60] [--wait 3000]

行为：滚动到锚点（预留 150px 避开吸顶导航），从锚点上方 pad 像素起截 w×h 区域。
锚点找不到时直接报错，不退回截首屏——避免拿错图当证据。
"""
import argparse
import os
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--anchor", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--w", type=int, default=1100)
    ap.add_argument("--h", type=int, default=760)
    ap.add_argument("--pad", type=int, default=60)
    ap.add_argument("--wait", type=int, default=3000)
    ap.add_argument("--hide", default="", help="含该文字的浮层/Cookie 条，截图前移除")
    a = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": a.w, "height": a.h},
                            user_agent=UA, device_scale_factor=2)
        pg = ctx.new_page()
        pg.goto(a.url, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(a.wait)
        if a.hide:
            pg.evaluate(
                """(kw) => {
                    [...document.querySelectorAll('div,section,aside')].forEach(e => {
                        if (e.innerText && e.innerText.includes(kw) && e.getBoundingClientRect().height < 420) {
                            e.style.display = 'none';
                        }
                    });
                }""", a.hide)
            pg.wait_for_timeout(400)
        y = pg.evaluate(
            """(anchor) => {
                const all = [...document.querySelectorAll('h1,h2,h3,h4,td,th,p,li,div,span')];
                const hits = all.filter(e => {
                    if (!e.innerText || !e.innerText.trim().includes(anchor)) return false;
                    const r = e.getBoundingClientRect();
                    if (r.height === 0 || r.height > 220) return false;
                    const st = getComputedStyle(e);
                    return st.visibility !== 'hidden' && st.display !== 'none';
                });
                if (!hits.length) return null;
                // 取文档坐标最大且仍在正文里的那个（避开页头/吸顶导航里的同文副本）
                const pick = hits
                    .map(e => ({ e, top: e.getBoundingClientRect().top + window.scrollY }))
                    .sort((a, b) => b.top - a.top)[0];
                window.scrollTo(0, pick.top - 150);
                return pick.top;
            }""", a.anchor)
        if y is None:
            raise SystemExit("anchor not found: " + a.anchor)
        pg.wait_for_timeout(900)
        top = max(0, y - 150 - a.pad)
        doc_h = pg.evaluate("() => document.documentElement.scrollHeight")
        h = min(a.h, max(200, doc_h - top))
        pg.screenshot(path=a.out, full_page=True,
                      clip={"x": 0, "y": top, "width": a.w, "height": h})
        print("saved", a.out, "anchor_y", int(y), "clip_top", int(top))
        b.close()


if __name__ == "__main__":
    main()
