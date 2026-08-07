"""对每日新闻做确定性打分，输出 JSON 供自动化格式化写入创意分类目录。
- 情绪/热度：给每条高价值动态打 情绪(-2~2) 与 热度(1~3)
- 副业四维度：对蓝海/副业机会打 门槛/成本/变现速度/竞争度(1~5) 并排序
- 徽章：从今天向前回溯连续有归档文件的天数（连续观察天数）
用法：python 脚本/score.py --date 2026-08-07
"""
import sys, os, re, json, glob, datetime, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import parse_daily

POS = ["突破", "发布", "开源", "融资", "上涨", "加速", "领先", "首个", "斩获", "达成", "落地", "红利", "机遇", "估值"]
NEG = ["失败", "下滑", "质疑", "推迟", "裁员", "亏损", "风险", "套壳", "打脸", "泡沫", "泄露", "危机"]

BIG_NAMES = ["Meta", "OpenAI", "Anthropic", "Claude", "Google", "微软", "字节", "阿里", "腾讯", "X2", "面壁"]


def sentiment(text):
    s = 0
    for w in POS:
        if w in text:
            s += 1
    for w in NEG:
        if w in text:
            s -= 1
    return max(-2, min(2, s))


def heat(text):
    score = 1
    if any(k in text for k in ["融资", "IPO", "估值", "发布", "开源", "突破"]):
        score += 1
    if any(k in text for k in BIG_NAMES):
        score += 1
    return score


def side_score(blue):
    out = []
    for b in blue:
        txt = b.get("desc", "") + b.get("why", "")
        barrier = 4
        if any(k in txt for k in ["无需", "零代码", "信息差", "不懂", "新手", "一人"]):
            barrier = 5
        if any(k in txt for k in ["代码", "技术", "开发", "算法"]):
            barrier = 2
        cost = 3
        if any(k in txt for k in ["零成本", "0 成本", "低成本", "199", "599", "低价"]):
            cost = 5
        if any(k in txt for k in ["万元", "万级", "投资"]):
            cost = 2
        speed = 3
        if any(k in txt for k in ["复购", "月", "代运营", "运维", "收费"]):
            speed = 4
        if any(k in txt for k in ["长期", "积累", "壁垒"]):
            speed = 2
        comp = 3
        if any(k in txt for k in ["稀缺", "蓝海", "刚起", "信息差", "先入场"]):
            comp = 5
        if any(k in txt for k in ["红海", "众多", "普遍"]):
            comp = 2
        total = barrier + cost + speed + comp
        out.append({"title": b["title"], "门槛": barrier, "成本": cost,
                    "变现速度": speed, "竞争度": comp, "总分": total,
                    "source": b.get("source", "")})
    out.sort(key=lambda x: x["总分"], reverse=True)
    return out


def streak(base):
    arch = os.path.join(base, "归档")
    files = glob.glob(os.path.join(arch, "**", "????-??-??.md"), recursive=True)
    dates = set()
    for f in files:
        name = os.path.basename(f)[:-3]
        if re.match(r"^\d{4}-\d{2}-\d{2}$", name):
            dates.add(name)
    if not dates:
        return 0
    d = max(dates)
    cnt = 0
    while d in dates:
        cnt += 1
        d = (datetime.date.fromisoformat(d) - datetime.timedelta(days=1)).isoformat()
    return cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--base", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = ap.parse_args()

    month = args.date[:7]
    daily_path = os.path.join(args.base, "归档", month, args.date + ".md")
    if not os.path.exists(daily_path):
        print(json.dumps({"error": "no daily file", "path": daily_path}, ensure_ascii=False))
        sys.exit(1)

    with open(daily_path, encoding="utf-8") as f:
        md = f.read()
    parsed = parse_daily(md)

    items_out = []
    for it in parsed["items"]:
        txt = it.get("desc", "") + it.get("reason", "")
        items_out.append({
            "title": it["title"],
            "情绪": sentiment(txt),
            "热度": heat(txt),
            "source": it.get("source", ""),
        })

    blue_out = side_score(parsed["blue"])
    run = streak(args.base)

    result = {
        "date": args.date,
        "items": items_out,
        "blue": blue_out,
        "连续观察天数": run,
        "情绪均值": round(sum(i["情绪"] for i in items_out) / len(items_out), 2) if items_out else 0,
        "热度均值": round(sum(i["热度"] for i in items_out) / len(items_out), 2) if items_out else 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
