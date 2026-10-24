# -*- coding: utf-8 -*-
"""幂等：删除标题完全相同的旧草稿，避免重跑堆重复。"""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from publish_article import API, load_env  # noqa: E402

TITLE = sys.argv[1] if len(sys.argv) > 1 else None


def token():
    env = load_env()
    url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential"
           "&appid=%s&secret=%s" % (env["WECHAT_APP_ID"], urllib.parse.quote(env["WECHAT_APP_SECRET"], safe="")))
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))["access_token"]


def post(path, tk, payload):
    req = urllib.request.Request(
        "%s/%s?access_token=%s" % (API, path, tk),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


tk = token()
res = post("draft/batchget", tk, {"offset": 0, "count": 20, "no_content": 1})
print("batchget:", res.get("errcode", 0), "共 %d 条" % res.get("total_count", 0))
hit = 0
for it in res.get("item", []):
    news = (it.get("content") or {}).get("news_item") or []
    t = news[0].get("title", "") if news else ""
    mid = it.get("media_id")
    print("  -", t[:36], mid[:12])
    if TITLE and t == TITLE:
        d = post("draft/delete", tk, {"media_id": mid})
        print("    deleted:", d.get("errcode", 0))
        hit += 1
print("deleted_count=%d" % hit)
