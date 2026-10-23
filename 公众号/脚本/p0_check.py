"""P0 连通性验证：token -> 封面素材 -> 正文图 -> 建草稿 -> 确认 -> 清理。
仅用标准库，不依赖 Pillow。不打印任何凭据。
"""
import json
import os
import struct
import sys
import urllib.parse
import urllib.request
import zlib

SKILL = r"C:/Users/Administrator/Desktop/My-Workspace/.workbuddy/skills/md-to-wechat"
TMP = os.path.join(os.environ.get("TEMP", "/tmp"), "wx_p0")
os.makedirs(TMP, exist_ok=True)
API = "https://api.weixin.qq.com/cgi-bin"


def load_env():
    env = {}
    with open(os.path.join(SKILL, ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def png(w, h, fn):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(fn(x, y))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))


PURPLE = (124, 58, 237)
PINK = (236, 72, 153)
WHITE = (250, 245, 255)


def cover_px(x, y):
    if x < 300:
        return PURPLE
    if x < 340:
        return PINK
    return WHITE


def body_px(x, y):
    return PINK if (y // 40) % 2 == 0 else WHITE


def http_json(url, payload=None, raw_body=None, ctype="application/json; charset=utf-8"):
    data = None
    if raw_body is not None:
        data = raw_body
    elif payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    if data is not None:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def upload_material(token, path, name):
    boundary = "----wbP0Boundary"
    with open(path, "rb") as f:
        blob = f.read()
    body = (
        "--%s\r\nContent-Disposition: form-data; name=\"media\"; filename=\"%s\"\r\n"
        "Content-Type: image/png\r\n\r\n" % (boundary, name)
    ).encode() + blob + ("\r\n--%s--\r\n" % boundary).encode()
    return http_json("%s/material/add_material?access_token=%s&type=image" % (API, token),
                     raw_body=body,
                     ctype="multipart/form-data; boundary=%s" % boundary)


def upload_body_img(token, path, name):
    boundary = "----wbP0Boundary2"
    with open(path, "rb") as f:
        blob = f.read()
    body = (
        "--%s\r\nContent-Disposition: form-data; name=\"media\"; filename=\"%s\"\r\n"
        "Content-Type: image/png\r\n\r\n" % (boundary, name)
    ).encode() + blob + ("\r\n--%s--\r\n" % boundary).encode()
    return http_json("%s/media/uploadimg?access_token=%s" % (API, token),
                     raw_body=body,
                     ctype="multipart/form-data; boundary=%s" % boundary)


def main():
    env = load_env()
    aid, sec = env.get("WECHAT_APP_ID"), env.get("WECHAT_APP_SECRET")
    step = {}

    # 1) token
    r = http_json("%s/token?grant_type=client_credential&appid=%s&secret=%s"
                  % (API, aid, urllib.parse.quote(sec)))
    if "access_token" not in r:
        print("STEP1 token: FAIL", r.get("errcode"), r.get("errmsg"))
        return 1
    token = r["access_token"]
    print("STEP1 token      : OK (expires_in=%s)" % r.get("expires_in"))

    # 2) 封面素材
    cover = os.path.join(TMP, "cover_900x383.png")
    open(cover, "wb").write(png(900, 383, cover_px))
    r = upload_material(token, cover, "cover.png")
    if "media_id" not in r:
        print("STEP2 cover      : FAIL", r)
        return 1
    thumb = r["media_id"]
    print("STEP2 cover      : OK media_id=%s... (%d bytes src)" % (thumb[:12], os.path.getsize(cover)))

    # 3) 正文图
    body_img = os.path.join(TMP, "body_600x300.png")
    open(body_img, "wb").write(png(600, 300, body_px))
    r = upload_body_img(token, body_img, "body.png")
    body_url = r.get("url", "")
    if not body_url:
        print("STEP3 body_img   : FAIL", r)
        return 1
    print("STEP3 body_img   : OK host=%s" % urllib.parse.urlparse(body_url).netloc)

    # 4) 建草稿（中文 + 内联样式 + 正文图）
    content = (
        '<section style="font-size:16px;line-height:1.75;color:#3F3F3F;">'
        '<p style="margin:0 0 16px;">这是一条接口连通性验证草稿，用于确认中文编码、'
        '内联样式与正文图片是否正常。看到这段文字没有变成乱码，说明链路已通。</p>'
        '<p style="margin:0 0 16px;text-align:center;">'
        '<img src="%s" style="width:100%%;display:block;border-radius:8px;" /></p>'
        '<p style="margin:0 0 16px;color:#7C3AED;font-weight:bold;">'
        '验证项：token / 封面素材 / 正文图 / 建草稿</p>'
        '</section>' % body_url
    )
    payload = {"articles": [{
        "title": "【测试】链路验证",
        "author": "小P",
        "digest": "接口连通性验证草稿，验证完自动删除。",
        "content": content,
        "thumb_media_id": thumb,
        "need_open_comment": 0,
        "only_fans_can_comment": 0,
    }]}
    r = http_json("%s/draft/add?access_token=%s" % (API, token), payload=payload)
    if "media_id" not in r:
        print("STEP4 draft/add  : FAIL", r)
        return 1
    draft_id = r["media_id"]
    print("STEP4 draft/add  : OK media_id=%s" % draft_id)

    # 5) 确认草稿存在
    r = http_json("%s/draft/batchget?access_token=%s" % (API, token),
                  payload={"offset": 0, "count": 5, "no_content": 1})
    total = r.get("total_count", 0)
    titles = [i.get("content", {}).get("news_item", [{}])[0].get("title", "")
              for i in r.get("item", [])]
    hit = any("链路验证" in t for t in titles)
    print("STEP5 batchget   : OK total=%s 命中测试草稿=%s" % (total, hit))

    # 6) 清理
    r = http_json("%s/draft/delete?access_token=%s" % (API, token), payload={"media_id": draft_id})
    print("STEP6 cleanup    : %s" % ("OK 已删除" if r.get("errcode") == 0 else "FAIL %s" % r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
