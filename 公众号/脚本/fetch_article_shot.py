"""锁正文容器取新闻配图：优先抠干净 DOM 图，失败则截正文容器顶部区域兜底。

用法：
    python fetch_article_shot.py --url <来源页> --out <输出目录> --name <文件名前缀>
    # 输出 <out>/<name>.png 或 <name>.jpg（抠到图时为原格式），最多 1 张
"""
import argparse
import json
import os
import re
import urllib.parse

import requests
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

SKIP = re.compile(
    r"(icon|logo|avatar|qrcode|share_?icon|loading|placeholder|blank|spacer|"
    r"1x1|pixel|\.svg(\?|$)|/t\.png|sprite|banner|ad[-_])", re.I)

SELECTORS = ['#js_content', '.rich_media_content', 'article', '.article-content',
             '.syl-article-base', '.article_content', '.post_content', '.content',
             '.main-content', '.content-body', '.formatted-text', 'main']

PICK_JS = """() => {
  const sels = %s;
  let best = null, bs = 0;
  for (const s of sels) {
    for (const el of document.querySelectorAll(s)) {
      const t = (el.innerText || '').length;
      if (t < 200) continue;
      const sc = t + el.querySelectorAll('p').length * 50;
      if (sc > bs) { bs = sc; best = el; }
    }
  }
  const scope = best || document.body;
  const getSrc = (i) => {
    let s = i.currentSrc || i.getAttribute('data-src') ||
            i.getAttribute('data-lazy-src') || i.getAttribute('data-original') ||
            i.getAttribute('data-lazy') || i.src || '';
    if (!s && i.srcset) s = i.srcset.split(',')[0].trim().split(' ')[0];
    return s;
  };
  const imgs = Array.from(scope.querySelectorAll('img')).map(i => ({
    src: getSrc(i), w: i.naturalWidth || 0, h: i.naturalHeight || 0, alt: i.alt || ''
  }));
  const r = scope.getBoundingClientRect();
  return { found: !!best,
           sel: best ? (best.className || best.id || best.tagName).toString().slice(0, 40) : 'body',
           textLen: (scope.innerText || '').length,
           imgs, top: r.top + window.scrollY, h: r.height, w: r.width };
}""" % json.dumps(SELECTORS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="shot")
    ap.add_argument("--max-h", type=int, default=720)
    ap.add_argument("--timeout", type=int, default=50)
    a = ap.parse_args()

    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True, channel="chromium")
        except Exception:
            browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 900},
                                  locale="zh-CN")
        page = ctx.new_page()
        print("[1/3] 打开 %s" % a.url)
        page.goto(a.url, timeout=a.timeout * 1000, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        # 强制懒加载占位图转正
        try:
            page.evaluate("""() => {
              const sel = 'img[data-src],img[data-lazy-src],img[data-original],img[data-lazy]';
              document.querySelectorAll(sel).forEach(i => {
                const s = i.getAttribute('data-src') || i.getAttribute('data-lazy-src') ||
                          i.getAttribute('data-original') || i.getAttribute('data-lazy');
                if (s) i.src = s;
              });
            }""")
        except Exception:
            pass
        print("[2/3] 滚动触发懒加载…")
        for _ in range(6):
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(500)
        page.wait_for_timeout(1500)

        info = page.evaluate(PICK_JS)
        print("    正文容器：%s ｜ 文字 %d ｜ 候选图 %d"
              % (info.get("sel"), info.get("textLen", 0), len(info.get("imgs", []))))

        # —— 优先抠干净 DOM 图 ——
        chosen = None
        for it in info.get("imgs", []):
            u = it.get("src") or ""
            if not u:
                continue
            if u.startswith("//"):
                u = "https:" + u
            elif u.startswith("/"):
                u = urllib.parse.urljoin(a.url, u)
            if not u.startswith("http"):
                continue
            if SKIP.search(u) or SKIP.search(it.get("alt", "")):
                continue
            if it.get("w") and it["w"] < 480:
                continue
            chosen = u
            break

        if chosen:
            try:
                r = requests.get(chosen, headers={"User-Agent": UA, "Referer": a.url}, timeout=30)
                ct = r.headers.get("Content-Type", "")
                if r.status_code == 200 and ct.startswith("image/") and len(r.content) >= 20 * 1024:
                    ext = ".png" if "png" in ct else ".jpg"
                    p = os.path.join(out, a.name + ext)
                    open(p, "wb").write(r.content)
                    print("[3/3] 抠图成功 -> %s (%dKB)" % (p, len(r.content) // 1024))
                    browser.close()
                    return 0
                else:
                    print("    抠图失败 http%s %s，转截图兜底" % (r.status_code, ct))
            except Exception as e:
                print("    抠图异常 %s，转截图兜底" % str(e)[:60])

        # —— 兜底：截正文容器顶部区域 ——
        try:
            top = max(0, int(info.get("top", 0)))
            h = min(int(info.get("h", 0) or 0), a.max_h)
            w = min(int(info.get("w", 0) or 1280), 1280)
            if h < 80:  # 容器太矮，退而截首屏
                top, h, w = 0, 720, 1280
            page.evaluate("window.scrollTo(0, %d)" % top)
            page.wait_for_timeout(400)
            clip = {"x": 0, "y": top, "width": w, "height": h}
            p = os.path.join(out, a.name + ".png")
            page.screenshot(path=p, clip=clip)
            print("[3/3] 截图兜底 -> %s (%dx%d)" % (p, w, h))
            browser.close()
            return 0
        except Exception as e:
            print("截图失败: %s" % str(e)[:80])
            browser.close()
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
