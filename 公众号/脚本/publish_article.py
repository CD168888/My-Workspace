"""本地排版 + 推草稿箱（SOP 方案 B）。

流程：Markdown -> 微信安全 HTML（全内联样式）-> 上传正文图 -> 上传封面 -> draft/add
不依赖任何第三方渲染服务，文章内容不出本机。

用法：
    python publish_article.py --md ../../稿件/反着看/反着看_2026-10-23.md \
        --cover ../../素材/2026-10-23-tesla-fly/cover.png \
        --title "标题" --digest "摘要"
"""
import argparse
import json
import os
import re
import struct
import sys
import urllib.parse
import urllib.request
import uuid

import markdown

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
# 凭据位置：skill 目录可能被迁移（最早在 .workbuddy/skills，现迁到 .codex/skills），
# 按顺序找第一个存在 .env 的位置，避免迁移后脚本直接挂掉。
SKILL_CANDIDATES = [os.path.join(ROOT, d, "skills", "md-to-wechat")
                    for d in (".workbuddy", ".codex")]
API = "https://api.weixin.qq.com/cgi-bin"


def find_env():
    for d in SKILL_CANDIDATES:
        p = os.path.join(d, ".env")
        if os.path.isfile(p):
            return p
    raise FileNotFoundError("找不到 md-to-wechat 的 .env，已尝试：%s" % SKILL_CANDIDATES)

# 版式 token —— 取值参考 doocs/md default(经典) 主题骨架 + 主流公众号实践
THEMES = {
    "signal": {"primary": "#0B6EFD", "accent": "#00B8D9", "fg": "#0F172A", "body": "#334155", "muted": "#64748B", "quote": "#F0F7FF", "line": "#D9E7F5"},
    "editorial": {"primary": "#111827", "accent": "#FF4D4F", "fg": "#111827", "body": "#27303F", "muted": "#6B7280", "quote": "#FFF5F5", "line": "#E5E7EB"},
    "swiss": {"primary": "#E11D48", "accent": "#F59E0B", "fg": "#111111", "body": "#262626", "muted": "#737373", "quote": "#FFF7ED", "line": "#E5E5E5"},
}
THEME = THEMES["signal"]
PRIMARY = THEME["primary"]
FG = "#1A1A1A"        # 标题/强调文字
BODY = "#333333"      # 正文
MUTED = "#8C8C8C"     # 图注/尾注
QUOTE_BG = "#F5F7FA"  # 引用底色
LINE = "#E8E8E8"      # 分隔线

# 版式节奏（短段落文章专用：段距压到 15px，行高 1.75）
FS = "15px"           # 正文字号
LH = "1.75"           # 行高
LS = "0.5px"          # 中文字距
GAP_P = "12px"        # 段间距
GAP_H2_TOP = "28px"   # 节标题上间距
GAP_H2_BOT = "14px"   # 节标题下间距


def load_env():
    env = {}
    p = find_env()
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def api(path, token, payload=None):
    url = "%s%s?access_token=%s" % (API, path, token)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def upload(path, token, kind):
    """kind: 'material' 永久素材（封面，返回 media_id）/ 'url' 正文图（返回 url）"""
    boundary = "----wb" + uuid.uuid4().hex
    fn = os.path.basename(path)
    ctype = "image/png" if fn.lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        blob = f.read()
    body = ("--%s\r\nContent-Disposition: form-data; name=\"media\"; filename=\"%s\"\r\n"
            "Content-Type: %s\r\n\r\n" % (boundary, fn, ctype)).encode() + blob
    body += ("\r\n--%s--\r\n" % boundary).encode()
    if kind == "material":
        url = "%s/material/add_material?access_token=%s&type=image" % (API, token)
    else:
        url = "%s/media/uploadimg?access_token=%s" % (API, token)
    req = urllib.request.Request(url, data=body, method="POST",
                                headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def styles():
    """按当前 THEME 生成四类段落样式。

    必须做成函数而不是模块级常量：主题由 main() 的 --theme 才确定，
    常量会在 import 时就固化成默认主题的颜色，切主题后正文/图注/尾注不跟着变。
    """
    return {
        "p": ("font-size:%s;line-height:%s;color:%s;letter-spacing:%s;margin:0 0 %s;"
              % (FS, LH, BODY, LS, GAP_P)),
        "lead": ("font-size:16px;line-height:%s;color:%s;letter-spacing:%s;margin:0 0 18px;"
                 % (LH, FG, LS)),
        "cap": ("font-size:13px;line-height:1.6;color:%s;text-align:center;"
                "letter-spacing:0.2px;margin:8px 0 %s;" % (MUTED, GAP_P)),
        "note": ("font-size:13px;line-height:1.7;color:%s;letter-spacing:0.2px;margin:0 0 10px;"
                 % (MUTED,)),
    }


def inline(html):
    """Markdown HTML -> 微信安全的内联样式 HTML。

    版式骨架取自 doocs/md 经典(default)主题，再按公众号主流做法调整：
      - h2  深色标题 + 3px 强调色下划线（杂志的 editorial 走法，不用大色块标签）
      - 正文 15px / 行高 1.75 / 字距 0.5px，段距按短段落文章收紧到 12px
      - 引用 浅底 + 4px 强调色左描边 + 6px 圆角
      - 图片 8px 圆角 + 轻投影 + 居中灰字图注
    全部内联 style，不用 class / 外部 CSS / flex / grid（微信会剥）。
    """
    S = styles()
    P_STYLE, LEAD_STYLE = S["p"], S["lead"]
    CAP_STYLE, NOTE_STYLE = S["cap"], S["note"]

    # 列表 -> 段落
    html = re.sub(r"<li>\s*<p>(.*?)</p>\s*</li>", r"<p>• \1</p>", html, flags=re.S)
    html = re.sub(r"<li>(.*?)</li>", r"<p>• \1</p>", html, flags=re.S)
    html = html.replace("<ul>", "").replace("</ul>", "").replace("<ol>", "").replace("</ol>", "")

    # ---- 节标题：主色标签，居中 ----
    def h2_block(m):
        inner = m.group(1).strip()
        return ('<section style="margin:%s 0 %s;">'
                '<span style="display:inline-block;color:%s;font-size:18px;font-weight:bold;'
                'letter-spacing:0.5px;padding:0 0 7px;border-bottom:3px solid %s;line-height:1.4;">%s</span></section>'
                % (GAP_H2_TOP, GAP_H2_BOT, THEME["fg"], THEME["accent"], inner))
    html = re.sub(r"<h2[^>]*>(.*?)</h2>", h2_block, html, flags=re.S)

    def h3_block(m):
        inner = m.group(1).strip()
        return ('<p style="font-size:16px;font-weight:bold;color:%s;margin:26px 0 %s;'
                'padding-left:10px;border-left:4px solid %s;line-height:1.5;">%s</p>'
                % (THEME["primary"], GAP_P, THEME["accent"], inner))
    html = re.sub(r"<h3[^>]*>(.*?)</h3>", h3_block, html, flags=re.S)

    # ---- 正文段落 ----
    html = html.replace("<p>", '<p style="%s">' % P_STYLE)

    # ---- 引用 ----
    html = html.replace("<blockquote>",
                        '<blockquote style="margin:%s 0;padding:14px 16px;background:%s;'
                        'border-left:4px solid %s;border-radius:6px;'
                        'font-size:14px;line-height:1.75;color:#4A4A4A;">'
                        % (GAP_P, THEME["quote"], THEME["accent"]))
    html = html.replace("<blockquote>\n<p style=\"%s\">" % P_STYLE,
                        '<blockquote>\n<p style="margin:0;font-size:14px;line-height:1.75;">')

    # ---- 强调 ----
    html = html.replace("<strong>", '<strong style="color:%s;font-weight:bold;">' % (PRIMARY,))
    html = html.replace("<em>", '<em style="color:%s;font-style:normal;">' % (MUTED,))

    # ---- 图片 + 图注（alt 当图注）----
    def img_block(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        out = ('<section style="margin:22px 0 0;">'
               '<img src="%s" style="width:100%%;display:block;border-radius:8px;box-shadow:0 6px 18px rgba(15,23,42,0.12);" />'
               '</section>' % (src.group(1) if src else ""))
        if alt and alt.group(1).strip():
            out += '<p style="%s">%s</p>' % (CAP_STYLE, alt.group(1).strip())
        else:
            out += '<p style="%s">&nbsp;</p>' % CAP_STYLE.replace("margin:8px", "margin:4px")
        return out
    html = re.sub(r"<img[^>]*?/?>", img_block, html)

    # ---- 分隔线：细灰线（grace/simple 主题的渐变线，退化为纯色以保证微信兼容）----
    html = re.sub(r"<hr\s*/?>",
                  '<section style="margin:28px 0;height:1px;background:%s;'
                  'font-size:0;line-height:0;overflow:hidden;">&nbsp;</section>' % (LINE,),
                  html)

    # ---- 尾注：分隔线之后的段落降为小字灰 ----
    marker = '<section style="margin:28px 0;height:1px;'
    if marker in html:
        head, tail = html.split(marker, 1)
        tail = marker + tail
        tail = tail.replace('<p style="%s">' % P_STYLE, '<p style="%s">' % NOTE_STYLE)
        html = head + tail

    # ---- 首段 lead ----
    html = re.sub(r'^<p style="%s">' % re.escape(P_STYLE),
                  '<p style="%s">' % LEAD_STYLE, html, count=1)

    html = re.sub(r"</?(div|article)[^>]*>", "", html)
    # 外层容器：统一基线，微信正文自带左右留白，这里只兜底
    html = ('<section style="font-size:%s;line-height:%s;color:%s;'
            'letter-spacing:%s;">%s</section>' % (FS, LH, BODY, LS, html))
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--cover", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--digest", default="")
    ap.add_argument("--author", default="小P")
    ap.add_argument("--theme", choices=sorted(THEMES), default="signal")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    global THEME, PRIMARY, FG, BODY, MUTED, QUOTE_BG, LINE
    THEME = THEMES[a.theme]
    PRIMARY, FG, BODY, MUTED, QUOTE_BG, LINE = (THEME[k] for k in ("primary", "fg", "body", "muted", "quote", "line"))
    md_path = os.path.abspath(a.md)
    base = os.path.dirname(md_path)
    text = open(md_path, encoding="utf-8").read()

    # 标题去掉一级标题（正文里不需要重复）
    text = re.sub(r"^#\s+.*?\n", "", text, count=1)

    html = inline(markdown.markdown(text, extensions=["extra", "nl2br"]))
    imgs = re.findall(r'src="([^"]+)"', html)
    local_imgs = [i for i in imgs if not i.startswith("http")]

    print("标题：%s  (%d 字)" % (a.title, len(a.title)))
    print("摘要：%s  (%d 字)" % (a.digest, len(a.digest)))
    print("正文：%d 字符  | 图片 %d 张：%s" % (len(html), len(local_imgs), local_imgs))

    if a.dry_run:
        out = md_path.replace(".md", ".html")
        open(out, "w", encoding="utf-8").write(html)
        print("dry-run：HTML 已写到 %s" % out)
        return 0

    env = load_env()
    tok_url = "%s/token?grant_type=client_credential&appid=%s&secret=%s" % (
        API, env["WECHAT_APP_ID"], urllib.parse.quote(env["WECHAT_APP_SECRET"], safe=""))
    with urllib.request.urlopen(urllib.request.Request(tok_url), timeout=30) as r:
        tok = json.loads(r.read().decode("utf-8"))
    if "access_token" not in tok:
        print("token 失败:", tok)
        return 1
    token = tok["access_token"]

    # 正文图 -> 微信图床
    for name in local_imgs:
        p = os.path.join(base, name)
        r = upload(p, token, "url")
        if "url" not in r:
            print("正文图上传失败 %s: %s" % (name, r))
            return 1
        html = html.replace('src="%s"' % name, 'src="%s"' % r["url"])
        print("  正文图 OK  %-16s -> %s" % (name, urllib.parse.urlparse(r["url"]).netloc))

    # 封面
    cov = upload(os.path.abspath(a.cover), token, "material")
    if "media_id" not in cov:
        print("封面上传失败:", cov)
        return 1
    print("  封面 OK  media_id=%s..." % cov["media_id"][:12])

    payload = {"articles": [{
        "title": a.title,
        "author": a.author,
        "digest": a.digest,
        "content": html,
        "thumb_media_id": cov["media_id"],
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }]}
    r = api("/draft/add", token, payload)
    if "media_id" not in r:
        print("建草稿失败:", r)
        return 1
    print("\n草稿已创建  media_id = %s" % r["media_id"])
    print("ad_count = %s（0 表示无敏感词提示）" % r.get("ad_count", "?"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
