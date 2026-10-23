"""抓取能力连通性测试（纯标准库，不依赖第三方包）。

只做一件事：把一批目标站点跑一遍，如实报告
  能否连上 / 拿到多少字节 / 有没有 og:image / 正文能否抽出。
不落盘缓存、不做批量、不绕反爬。
"""
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

TARGETS = [
    ("GitHub Blog",   "https://github.blog/news-insights/"),
    ("OpenAI News",   "https://openai.com/news/"),
    ("IT之家",        "https://www.ithome.com/"),
    ("机器之心",      "https://www.jiqizhixin.com/"),
    ("MIT Tech Review", "https://www.technologyreview.com/"),
    ("arXiv API",     "http://export.arxiv.org/api/query?search_query=all:agent&max_results=1"),
]


def fetch(url, timeout=15):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        raw = r.read()
        return raw, r.headers.get("Content-Type", ""), r.status, time.time() - t0


def decode(raw, ctype):
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    for enc in ([m.group(1).lower()] if m else []) + ["utf-8", "gb18030"]:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="ignore")


def analyze(html):
    out = {}
    m = re.search(r"<title[^>]*>([^<]{1,200})", html, re.I)
    out["title"] = (m.group(1).strip() if m else "")[:50]

    og = re.search(r'property=["\']og:image(?::url)?["\'][^>]*content=["\']([^"\']+)', html, re.I)
    if not og:
        og = re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image', html, re.I)
    out["og_image"] = urllib.parse.urlparse(og.group(1)).netloc if og else ""

    out["og_type"] = bool(re.search(r'property=["\']og:type["\'][^>]*content=["\']article', html, re.I))
    out["schema"] = bool(re.search(r'"@type"\s*:\s*"(NewsArticle|Article|BlogPosting)"', html))
    out["imgs"] = len(re.findall(r"<img\b", html, re.I))

    body = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    body = re.sub(r"(?is)<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    out["text_len"] = len(body)
    out["sample"] = body[:80]
    return out


def main():
    print("%-16s %-6s %-9s %-7s %-8s %-6s %-6s %s"
          % ("站点", "状态", "字节", "耗时", "og图源", "og:art", "schema", "正文字数"))
    print("-" * 96)
    ok = 0
    for name, url in TARGETS:
        try:
            raw, ctype, status, cost = fetch(url)
            html = decode(raw, ctype)
            a = analyze(html)
            ok += 1
            print("%-16s %-6s %-9s %-7s %-8s %-6s %-6s %s"
                  % (name, status, "%dKB" % (len(raw) // 1024), "%.1fs" % cost,
                     a["og_image"][:12] or "-", "Y" if a["og_type"] else "n",
                     "Y" if a["schema"] else "n", a["text_len"]))
            print("   └ 标题: %s" % (a["title"] or "(未取到)"))
            print("   └ 正文样本: %s" % a["sample"])
        except Exception as e:
            print("%-16s %-6s %s" % (name, "FAIL", type(e).__name__ + ": " + str(e)[:70]))
    print("-" * 96)
    print("可连通 %d / %d" % (ok, len(TARGETS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
