"""抓取能力测试 第二轮：真实文章页 + 图片能否下载。

流程：首页 -> 提取一篇真实文章链接 -> 抓文章正文 -> 提取 og:image/正文首图
     -> 尝试下载图片（带/不带 Referer 各一次）。
"""
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def ctx():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def get(url, referer=None, timeout=15):
    h = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx()) as r:
        return r.read(), r.headers.get("Content-Type", ""), r.status


def decode(raw, ctype):
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    for enc in ([m.group(1).lower()] if m else []) + ["utf-8", "gb18030"]:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="ignore")


def text_of(html):
    b = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    b = re.sub(r"(?is)<[^>]+>", " ", b)
    return re.sub(r"\s+", " ", b).strip()


def first_article(html, base):
    """从首页找一条看起来像文章的链接。"""
    pats = [r'href="(https?://[^"]*?/\d{8}/[^"]+\.htm)"',
            r'href="(https?://[^"]*?/0/\d+/\d+\.htm)"',
            r'href="(https?://[^"]*?/\d{4}/\d{2}/[^"]{6,})"']
    for p in pats:
        m = re.search(p, html)
        if m:
            return urllib.parse.urljoin(base, m.group(1))
    return None


def main():
    targets = [
        ("IT之家", "https://www.ithome.com/"),
        ("MIT Tech Review", "https://www.technologyreview.com/"),
    ]
    for name, home in targets:
        print("=" * 78)
        print("【%s】首页 %s" % (name, home))
        try:
            raw, ctype, _ = get(home)
            html = decode(raw, ctype)
            art = first_article(html, home)
            print("  提取到文章链接: %s" % (art or "未找到"))
            if not art:
                continue
            raw2, ctype2, st2 = get(art, referer=home)
            html2 = decode(raw2, ctype2)
            txt = text_of(html2)
            print("  文章页状态 %s  %dKB  正文 %d 字" % (st2, len(raw2) // 1024, len(txt)))
            m = re.search(r"<title[^>]*>([^<]{1,120})", html2, re.I)
            print("  标题: %s" % (m.group(1).strip() if m else "-"))
            print("  正文样本: %s" % txt[:100])

            # 图片：先 og:image，再正文首图
            img = None
            og = re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)', html2, re.I)
            if og:
                img = ("og:image", urllib.parse.urljoin(art, og.group(1)))
            else:
                for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)', html2, re.I):
                    u = urllib.parse.urljoin(art, m.group(1))
                    if re.search(r"\.(jpe?g|png|webp)", u, re.I) and "icon" not in u.lower():
                        img = ("正文首图", u)
                        break
            if not img:
                print("  图片: 未找到")
                continue
            kind, iu = img
            print("  图片(%s): %s" % (kind, iu[:90]))

            # 下载测试：不带 Referer / 带 Referer
            for label, ref in (("裸请求", None), ("带Referer", art)):
                try:
                    blob, ict, ist = get(iu, referer=ref, timeout=20)
                    print("    下载[%s] %s  %dKB  %s" % (label, ist, len(blob) // 1024, ict.split(";")[0]))
                    break
                except Exception as e:
                    print("    下载[%s] FAIL %s" % (label, str(e)[:60]))
        except Exception as e:
            print("  FAIL %s" % (type(e).__name__ + ": " + str(e)[:70]))

    print("=" * 78)
    print("【arXiv 换 https】")
    try:
        raw, ctype, st = get("https://export.arxiv.org/api/query?search_query=all:agent&max_results=1")
        print("  状态 %s  %dKB  %s" % (st, len(raw) // 1024, ctype.split(";")[0]))
        print("  样本: %s" % raw.decode("utf-8", "ignore")[:120].replace("\n", " "))
    except Exception as e:
        print("  FAIL %s" % (str(e)[:80]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
