"""每日 AI 新闻 md 解析（与前端 app.js 的 parseDaily 保持同一口径）。
仅用标准库，供自动化脚本在 Bash 中调用。
"""
import re


def parse_daily(md_text):
    lines = md_text.splitlines()
    items, blue, notes = [], [], []
    cur = None
    cur_section = "other"
    section = "other"

    def flush():
        if not cur:
            return
        if cur_section == "items" and (cur.get("desc") or cur.get("reason") or cur.get("source")):
            items.append(cur)
        elif cur_section == "blue" and (cur.get("desc") or cur.get("why") or cur.get("source")):
            blue.append(cur)

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        h1 = re.match(r"^#\s+(.*)$", line)
        h2 = re.match(r"^##\s+(.*)$", line)
        h3 = re.match(r"^###\s+(.*)$", line)
        field = re.match(r"^\s*[-*]?\s*\*\*(.+?)\*\*\s*[：:]\s*(.*)$", line)
        if h1:
            continue
        if h2:
            flush()
            cur = None
            cur_section = "other"
            t = h2.group(1)
            if "今日高价值" in t or "新闻条目" in t:
                section = "items"
            elif "蓝海" in t or "副业" in t:
                section = "blue"
            elif "备注" in t:
                section = "notes"
            else:
                section = "other"
            continue
        if h3:
            flush()
            if section == "items":
                cur = {"title": re.sub(r"^\d+[.、]\s*", "", h3.group(1)).strip(),
                       "desc": "", "reason": "", "source": ""}
                cur_section = "items"
            elif section == "blue":
                cur = {"title": h3.group(1).strip(), "desc": "", "why": "", "source": ""}
                cur_section = "blue"
            else:
                cur = None
                cur_section = "other"
            continue
        if field:
            key = field.group(1).strip()
            val = field.group(2).strip()
            if cur is not None:
                if "事件内容简述" in key or "机会描述" in key:
                    cur["desc"] = val
                elif "值得关注的原因" in key or "为什么值得关注" in key:
                    cur["why" if cur_section == "blue" else "reason"] = val
                elif "来源" in key:
                    cur["source"] = val
            continue
        if section == "notes" and cur is None:
            notes.append(line.strip("- ").strip())
    flush()
    return {"items": items, "blue": blue, "notes": notes}
