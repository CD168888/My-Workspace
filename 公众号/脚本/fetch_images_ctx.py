"""取图时带上「图片周围的文字」，用于没有肉眼核图能力时做机器验证。

在正文容器里按「innerText 长度 + p 数量×50」打分取最厚的容器作为 scope，
对每张 img 记录：地址、尺寸、alt、以及它最近的可读文字上下文（前一段 / 父节点文本）。
"""
import argparse
import hashlib
import json
import os
import re
import time

from playwright.sync_api import sync_playwright
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

SKIP = re.compile(r"(icon|logo|avatar|qrcode|share_?icon|loading|placeholder|blank|"
                  r"spacer|1x1|pixel|\.svg(\?|$)|/t\.png|advert|adv/|ads?[_-])", re.I)

CONTAINER_JS = r"""() => {
  const sels = ['#js_content', '.rich_media_content', 'article', '.article-content',
                '.syl-article-base', '.article_content', '.post_content', '.content',
                '.main-content', '.news_info', '.content_box', 'main'];
  let best = null, bestScore = 0;
  for (const s of sels) {
    for (const el of document.querySelectorAll(s)) {
      const text = (el.innerText || '').length;
      if (text < 400) continue;
      const score = text + el.querySelectorAll('p').length * 50;
      if (score > bestScore) { bestScore = score; best = el; }
    }
  }
  const scope = best || document.body;

  function ctxOf(img) {
    // 往上找第一个有可读文字的祖先，再取其首句
    let p = img.parentElement, depth = 0;
    while (p && p !== scope && depth < 4) {
      const t = (p.innerText || '').trim();
      if (t.length > 30) return t.replace(/\s+/g, ' ').slice(0, 80);
      p = p.parentElement; depth++;
    }
    // 退而求其次：前一个兄弟节点的文字
    let prev = img.previousElementSibling, k = 0;
    while (prev && k < 3) {
      const t = (prev.innerText || '').trim();
      if (t.length > 10) return t.replace(/\s+/g, ' ').slice(0, 80);
      prev = prev.previousElementSibling; k++;
    }
    const cap = img.closest('figcaption');
    if (cap) return 'FIGCAPTION ' + (cap.innerText || '').trim().slice(0, 80);
    return '';
  }

  const imgs = Array.from(scope.querySelectorAll('img')).map(i => ({
    src: i.currentSrc || i.src || '',
    w: i.naturalWidth || 0,
    h: i.naturalHeight || 0,
    alt: (i.alt || i.title || '').trim(),
    dataSrc: i.getAttribute('data-src') || i.getAttribute('data-original') || '',
    ctx: ctxOf(i)
  }));
  const head = (scope.innerText || '').replace(/\s+/g, ' ');
  return {
    found: !!best,
    selectorText: best ? (best.className || best.id || best.tagName).toString().slice(0, 40) : 'body(fallback)',
    paragraphs: scope.querySelectorAll('p').length,
    textLen: head.length,
    head80: head.slice(0, 80),
    imgs
  };
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-width", type=int, default=600)
    ap.add_argument("--min-bytes", type=int, default=20 * 1024)
    ap.add_argument("--max", type=int, default=12)
    a = ap.parse_args()

    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True, channel="chromium")
        except Exception:
            browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900},
                                  locale="zh-CN")
        page = ctx.new_page()
        page.goto(a.url, timeout=45000, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        for _ in range(6):
            page.mouse.wheel(0, 1400)
            page.wait_for_timeout(500)
        page.wait_for_timeout(1200)
        res = page.evaluate(CONTAINER_JS)
        title = page.title()
        browser.close()

    print("页面：%s" % title[:70])
    print("容器：%s ｜ 段落 %d ｜ 文字 %d ｜ 图 %d"
          % (res.get("selectorText"), res.get("paragraphs", 0),
             res.get("textLen", 0), len(res.get("imgs", []))))
    print("容器首句：%s" % res.get("head80", "")[:90])
    if not res.get("found"):
        print("⚠ 未锁到正文容器")

    kept, seen, items = 0, set(), []
    for it in res.get("imgs", []):
        if kept >= a.max:
            break
        u = it["src"] or it["dataSrc"]
        if not u.startswith("http") or SKIP.search(u):
            continue
        if it["w"] and it["w"] < a.min_width:
            continue
        try:
            r = requests.get(u, headers={"User-Agent": UA, "Referer": a.url}, timeout=30)
        except Exception as e:
            items.append({**it, "skip": str(e)[:40]}); continue
        ct = r.headers.get("Content-Type", "")
        if r.status_code != 200 or not ct.startswith("image/"):
            items.append({**it, "skip": "http%s" % r.status_code}); continue
        buf = r.content
        if len(buf) < a.min_bytes:
            items.append({**it, "skip": "small:%dKB" % (len(buf) // 1024)}); continue
        dg = hashlib.sha256(buf).hexdigest()[:12]
        if dg in seen:
            items.append({**it, "skip": "dup"}); continue
        seen.add(dg)
        ext = ".png" if "png" in ct else ".jpg"
        name = "%03d_%s%s" % (kept + 1, dg, ext)
        open(os.path.join(out, name), "wb").write(buf)
        kept += 1
        rec = {k: it[k] for k in ("src", "w", "h", "alt", "ctx")}
        rec.update({"ok": True, "file": name, "kb": len(buf) // 1024})
        items.append(rec)
        print("✓ %-22s %4dx%-4d %4dKB alt=%s ctx=%s"
              % (name, it["w"], it["h"], len(buf) // 1024, it["alt"][:24], it["ctx"][:55]))

    json.dump({"page": a.url, "title": title, "at": time.strftime("%Y-%m-%d %H:%M:%S"),
               "items": items},
              open(os.path.join(out, "manifest_ctx.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("保留 %d 张 → %s" % (kept, out))


if __name__ == "__main__":
    main()
