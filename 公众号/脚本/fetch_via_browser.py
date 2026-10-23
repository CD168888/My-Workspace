"""用真实浏览器渲染后取图（解决 JS 站 / 反爬站抓不到图的问题）。

extract-images 走 requests，拿不到 JS 渲染的页面。本脚本用 Playwright 打开页面、
滚动触发懒加载、等网络空闲，再从 DOM 里取所有已加载图片的真实地址。

用法：
    python fetch_via_browser.py --url "https://..." --out ../素材/xxx --min-width 700
    python fetch_via_browser.py --url "https://..." --headful   # 需要人工过验证时
"""
import argparse
import hashlib
import json
import os
import re
import time
import urllib.parse

from playwright.sync_api import sync_playwright
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

SKIP = re.compile(r"(icon|logo|avatar|qrcode|share_?icon|loading|placeholder|blank|"
                  r"spacer|1x1|pixel|\.svg(\?|$)|/t\.png)", re.I)


CONTAINER_JS = """() => {
  // 在候选容器里挑「正文最厚」的那个，避免抓到推荐流/侧栏的无关图
  const sels = ['#js_content', '.rich_media_content', 'article', '.article-content',
                '.syl-article-base', '.article_content', '.post_content', '.content',
                '.main-content', 'main'];
  let best = null, bestScore = 0;
  for (const s of sels) {
    for (const el of document.querySelectorAll(s)) {
      const text = (el.innerText || '').length;
      if (text < 200) continue;
      const score = text + el.querySelectorAll('p').length * 50;
      if (score > bestScore) { bestScore = score; best = el; }
    }
  }
  const scope = best || document.body;
  const imgs = Array.from(scope.querySelectorAll('img')).map(i => ({
    src: i.currentSrc || i.src || '',
    w: i.naturalWidth || 0,
    h: i.naturalHeight || 0,
    alt: i.alt || i.title || ''
  }));
  return {
    found: !!best,
    selectorText: best ? (best.className || best.id || best.tagName).toString().slice(0, 40) : 'body(fallback)',
    paragraphs: scope.querySelectorAll('p').length,
    textLen: (scope.innerText || '').length,
    imgs
  };
}"""


def collect(page):
    # 滚动触发懒加载
    for _ in range(6):
        page.mouse.wheel(0, 1400)
        page.wait_for_timeout(600)
    page.wait_for_timeout(1200)
    return page.evaluate(CONTAINER_JS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-width", type=int, default=700)
    ap.add_argument("--min-bytes", type=int, default=25 * 1024)
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--headful", action="store_true")
    ap.add_argument("--timeout", type=int, default=45)
    a = ap.parse_args()

    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)

    with sync_playwright() as pw:
        # headless=True 在 1.6x 会用 chromium_headless_shell（需单独下载）。
        # 若只装了完整版 chromium，用 channel="chromium" 走完整版，避免多下一个内核。
        try:
            browser = pw.chromium.launch(headless=not a.headful, channel="chromium")
        except Exception:
            browser = pw.chromium.launch(headless=not a.headful)
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900},
                                  locale="zh-CN")
        page = ctx.new_page()
        print("[1/3] 打开 %s" % a.url)
        page.goto(a.url, timeout=a.timeout * 1000, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        print("[2/3] 滚动触发懒加载…")
        res = collect(page)
        title = page.title()
        browser.close()

    imgs = res.get("imgs", [])
    print("    页面标题：%s" % title[:60])
    print("    正文容器：%s ｜ 段落 %d ｜ 文字 %d 字 ｜ 图 %d 张"
          % (res.get("selectorText"), res.get("paragraphs", 0),
             res.get("textLen", 0), len(imgs)))
    if not res.get("found"):
        print("    ⚠ 未识别到正文容器，已退化到全页取图，结果可能混入推荐位图片")

    seen, kept, manifest = set(), 0, []
    for it in imgs:
        if kept >= a.max:
            break
        u, w = it["src"], it["w"]
        if not u.startswith("http") or SKIP.search(u):
            continue
        if w and w < a.min_width:
            continue
        rec = {"image_url": u, "dom_width": w, "alt": it["alt"][:60]}
        try:
            r = requests.get(u, headers={"User-Agent": UA, "Referer": a.url}, timeout=30)
            buf = r.content
        except Exception as e:
            rec["skip"] = str(e)[:40]; manifest.append(rec); continue
        if r.status_code != 200 or not r.headers.get("Content-Type", "").startswith("image/"):
            rec["skip"] = "http%s" % r.status_code; manifest.append(rec); continue
        if len(buf) < a.min_bytes:
            rec["skip"] = "small:%dKB" % (len(buf) // 1024); manifest.append(rec); continue
        dg = hashlib.sha256(buf).hexdigest()[:12]
        if dg in seen:
            rec["skip"] = "dup"; manifest.append(rec); continue
        seen.add(dg)
        ext = ".png" if "png" in r.headers["Content-Type"] else ".gif" if "gif" in r.headers["Content-Type"] else ".jpg"
        name = "%03d_%s%s" % (kept + 1, dg, ext)
        open(os.path.join(out, name), "wb").write(buf)
        rec.update({"ok": True, "file": name, "bytes": len(buf), "dom_width": w})
        kept += 1
        print("    ✓ %-16s %4dpx  %4dKB" % (name, w, len(buf) // 1024))
        manifest.append(rec)

    json.dump({"page": a.url, "title": title,
               "at": time.strftime("%Y-%m-%d %H:%M:%S"), "items": manifest},
              open(os.path.join(out, "manifest_browser.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("[3/3] 完成，保留 %d 张 → %s" % (kept, out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
