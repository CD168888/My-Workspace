"""按关键词取图（Bing 图片接口）+ 下载 + 溯源清单。

为什么不用"抓新闻页找图"：
  新闻页的图多走 JS 渲染/懒加载，或整站 403（极客公园、Tesla 官网），
  拿页面 HTML 常常一张图都取不到。改用图片搜索接口，按关键词直接拿
  原图 URL，并保留 purl（来源页）用于溯源与判断授权。

用法：
    python fetch_images.py --q "特斯拉 飞行汽车" --n 6 --min-width 800
    python fetch_images.py --q "..." --dry-run
"""
import argparse
import hashlib
import html
import json
import os
import re
import struct
import time
import urllib.parse

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
H = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}

# 图源分级：决定能不能直接用
OFFICIAL = ("tesla.com", "spacex.com", "nvidia.com", "openai.com", "anthropic.com",
            "blog.google", "deepmind.google", "microsoft.com", "github.blog",
            "huggingface.co", "arxiv.org")
FREE = ("unsplash.com", "pexels.com", "pixabay.com", "wikimedia.org")
MEDIA = ("autohome.com.cn", "yiche.com", "36kr.com", "ithome.com", "sina.com.cn",
         "163.com", "qq.com", "thepaper.cn", "geekpark.net", "ifeng.com", "cnbeta.com")


def tier(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    for d in OFFICIAL:
        if host == d or host.endswith("." + d):
            return "official"
    for d in FREE:
        if host == d or host.endswith("." + d):
            return "free"
    for d in MEDIA:
        if host.endswith(d):
            return "media"
    return "unknown"


def search(q, first=1):
    u = "https://cn.bing.com/images/search?q=%s&first=%d" % (urllib.parse.quote(q), first)
    r = requests.get(u, headers=H, timeout=25)
    out = []
    for raw in re.findall(r'class="iusc"[^>]*?m="([^"]+)"', r.text):
        try:
            d = json.loads(html.unescape(raw))
        except Exception:
            continue
        if d.get("murl"):
            out.append({"murl": d["murl"], "purl": d.get("purl", ""),
                        "title": d.get("t", "")[:60]})
    return out


def size_of(buf):
    if buf[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", buf[16:24]); return w, h
    if buf[:3] == b"GIF":
        w, h = struct.unpack("<HH", buf[6:10]); return w, h
    if buf[:2] == b"\xff\xd8":
        i = 2
        while i < len(buf) - 9:
            if buf[i] != 0xFF:
                i += 1; continue
            mk = buf[i + 1]
            if mk in (0xC0, 0xC1, 0xC2, 0xC3):
                h, w = struct.unpack(">HH", buf[i + 5:i + 9]); return w, h
            if mk in (0xD8, 0xD9) or 0xD0 <= mk <= 0xD7:
                i += 2
            else:
                i += 2 + struct.unpack(">H", buf[i + 2:i + 4])[0]
        return None
    return None


def download(url, referer=None):
    hh = dict(H)
    if referer:
        hh["Referer"] = referer
    r = requests.get(url, headers=hh, timeout=30, stream=True)
    buf = r.content
    return r.status_code, r.headers.get("Content-Type", ""), buf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True)
    ap.add_argument("--n", type=int, default=6, help="最多下载几张")
    ap.add_argument("--min-width", type=int, default=800)
    ap.add_argument("--min-bytes", type=int, default=30 * 1024)
    ap.add_argument("--out", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    out = os.path.abspath(a.out) if a.out else os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "素材",
                     "img-" + time.strftime("%Y%m%d")))
    items = search(a.q)
    print("搜索『%s』拿到 %d 条结果\n" % (a.q, len(items)))

    if not a.dry_run:
        os.makedirs(out, exist_ok=True)

    seen, kept, manifest = set(), 0, []
    for it in items:
        if kept >= a.n:
            break
        u = it["murl"]
        rec = {"image_url": u, "source_page": it["purl"], "tier": tier(u)}
        try:
            code, ctype, buf = download(u, referer=it["purl"])
        except Exception as e:
            rec["skip"] = "download:%s" % str(e)[:40]
            manifest.append(rec); print("  ✗ %s" % rec["skip"]); continue

        if code != 200 or not ctype.startswith("image/"):
            rec["skip"] = "http%s/%s" % (code, ctype.split(";")[0])
        elif len(buf) < a.min_bytes:
            rec["skip"] = "too_small:%dKB" % (len(buf) // 1024)
        else:
            sz = size_of(buf)
            if not sz:
                rec["skip"] = "unknown_format"
            elif sz[0] < a.min_width:
                rec["skip"] = "narrow:%dpx" % sz[0]
            else:
                digest = hashlib.sha256(buf).hexdigest()[:12]
                if digest in seen:
                    rec["skip"] = "dup"
                else:
                    seen.add(digest)
                    ext = ".png" if "png" in ctype else ".gif" if "gif" in ctype else ".jpg"
                    name = "%s_%s%s" % (tier(u), digest, ext)
                    if not a.dry_run:
                        p = os.path.join(out, name)
                        open(p, "wb").write(buf)
                        rec["file"] = p
                    rec.update({"ok": True, "width": sz[0], "height": sz[1],
                                "bytes": len(buf), "name": name})
                    kept += 1
                    print("  ✓ %-8s %4dx%-4d %4dKB  %s" % (rec["tier"], sz[0], sz[1],
                                                          len(buf) // 1024, it["purl"][:52] or u[:52]))
                    manifest.append(rec); continue

        manifest.append(rec)
        print("  ✗ %-22s %s" % (rec["skip"], u[:60]))

    if not a.dry_run:
        mp = os.path.join(out, "manifest.json")
        json.dump({"query": a.q, "at": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "items": manifest}, open(mp, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("\n保留 %d 张 | 目录 %s" % (kept, out))
        print("清单 %s" % mp)
    else:
        print("\ndry-run：命中 %d 条，未下载" % len(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
