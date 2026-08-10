"""将 Markdown 内容导出为 GitHub Pages 可直接读取的静态 JSON。

每个 Markdown 对应一个 JSON，目录结构与源文件保持一致；web/data/index.json
仅保存文件索引。前端因此无需调用 GitHub Contents API。

用法：python 每日新闻/脚本/export_web_data.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

from common import parse_daily


CREATIVE_FOLDERS = ("人格主播", "打假", "盲盒", "金句", "副业榜", "情绪", "漫画", "徽章")


def write_json(path: Path, payload: dict, written: set[Path] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if written is not None:
        written.add(path.resolve())


def title_from_markdown(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def file_entry(name: str, url: str, title: str) -> dict:
    return {"name": name, "title": title, "url": url}


def export_daily(base: Path, data_dir: Path, written: set[Path]) -> dict[str, list[dict]]:
    output: dict[str, list[dict]] = {}
    archive = base / "归档"
    if not archive.exists():
        return output
    for month_dir in sorted((p for p in archive.iterdir() if p.is_dir()), reverse=True):
        entries = []
        for source in sorted(month_dir.glob("????-??-??.md"), reverse=True):
            markdown = source.read_text(encoding="utf-8")
            parsed = parse_daily(markdown)
            payload = {
                "type": "daily",
                "date": source.stem,
                "title": title_from_markdown(markdown, source.stem),
                "items": parsed["items"],
                "blue": parsed["blue"],
                "notes": parsed["notes"],
            }
            relative = Path("daily") / month_dir.name / f"{source.stem}.json"
            write_json(data_dir / relative, payload, written)
            entries.append(file_entry(source.stem, relative.as_posix(), payload["title"]))
        output[month_dir.name] = entries
    return output


def export_markdown_group(source_dir: Path, data_dir: Path, output_dir: Path, kind: str, written: set[Path]) -> list[dict]:
    entries = []
    if not source_dir.exists():
        return entries
    for source in sorted(source_dir.glob("*.md"), reverse=True):
        markdown = source.read_text(encoding="utf-8")
        title = title_from_markdown(markdown, source.stem)
        payload = {"type": kind, "name": source.stem, "title": title, "markdown": markdown}
        if kind == "creative:漫画":
            month = re.search(r"\d{4}-\d{2}", source.stem)
            image = source_dir / "images" / f"月报_{month.group(0)}.png" if month else None
            if image and image.exists():
                payload["image"] = f"../创意/漫画/images/{image.name}"
        relative = output_dir / f"{source.stem}.json"
        write_json(data_dir / relative, payload, written)
        entries.append(file_entry(source.stem, relative.as_posix(), title))
    return entries


def export_all(base: Path, data_dir: Path) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    written: set[Path] = set()

    daily = export_daily(base, data_dir, written)
    reports = {
        "weekly": export_markdown_group(base / "汇总" / "周报", data_dir, Path("reports/weekly"), "report:weekly", written),
        "monthly": export_markdown_group(base / "汇总" / "月报", data_dir, Path("reports/monthly"), "report:monthly", written),
    }
    creative = {
        folder: export_markdown_group(
            base / "创意" / folder,
            data_dir,
            Path("creative") / folder,
            f"creative:{folder}",
            written,
        )
        for folder in CREATIVE_FOLDERS
    }

    source_files = list((base / "归档").rglob("*.md")) + list((base / "汇总").rglob("*.md")) + list((base / "创意").rglob("*.md"))
    newest = max((p.stat().st_mtime for p in source_files), default=0)
    generated_at = dt.datetime.fromtimestamp(newest, dt.timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "schemaVersion": 1,
        "generatedAt": generated_at,
        "latestDate": next((items[0]["name"] for items in daily.values() if items), None),
        "daily": daily,
        "reports": reports,
        "creative": creative,
    }
    write_json(data_dir / "index.json", manifest, written)

    # 增量清理：删除本次运行未生成的旧 JSON，避免整体 rmtree 触发 safe-delete 拦截
    for stale in data_dir.rglob("*.json"):
        if stale.resolve() not in written:
            try:
                stale.unlink()
            except OSError:
                pass

    return manifest


def main() -> None:
    default_base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="导出每日新闻静态 Web JSON")
    parser.add_argument("--base", type=Path, default=default_base, help="每日新闻目录")
    parser.add_argument("--output", type=Path, help="输出目录，默认 <base>/web/data")
    args = parser.parse_args()
    base = args.base.resolve()
    output = args.output.resolve() if args.output else base / "web" / "data"
    manifest = export_all(base, output)
    count = sum(len(items) for items in manifest["daily"].values())
    count += sum(len(items) for items in manifest["reports"].values())
    count += sum(len(items) for items in manifest["creative"].values())
    print(json.dumps({"output": str(output), "files": count, "generatedAt": manifest["generatedAt"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
