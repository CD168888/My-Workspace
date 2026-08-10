# My-Workspace · 每日 AI 新闻统一管理仓库

自动收集、整理与归档每日 AI 领域重要动态，并叠加创意扩展产物（人格主播、金句、打假、副业榜、情绪、漫画、盲盒、徽章），最终通过 GitHub Pages 看板可视化展示。

> **目录与命名规范**：详见 [`docs/目录规范.md`](docs/目录规范.md)。所有新增文件、目录、自动化脚本都应遵循该约定。

---

## 一、顶层结构

```
My-Workspace/
├── docs/           全仓说明与规范（README_创意.md、目录规范.md）
├── 每日新闻/       项目根（自动化与网页的基准路径）
│   ├── sources/   归档/   每日原始采集（年-月/日期.md）
│   ├── reports/   汇总/   周报/、月报/
│   ├── creative/  创意/   人格主播/金句/打假/副业榜/情绪/漫画/盲盒/徽章
│   ├── scripts/   脚本/   common.py、score.py
│   ├── web/                  看板（index.html + assets/）
│   └── templates/ 模板/   每日新闻模板.md
├── index.html     重定向到 每日新闻/web/（Pages 兼容）
└── README.md      本文件
```

> 中文语义目录名（`归档`、`汇总`、`创意`、`脚本`、`模板`）予以保留，因为它们已被自动化任务 prompt 硬编码引用。

---

## 二、自动化任务

由 WorkBuddy 自动化驱动，共 4 个定时任务：

| 任务 | 执行时间 | 主要输出 |
|------|----------|----------|
| 每日 AI 新闻采集 | 每天 08:30 | `sources/归档/YYYY-MM/YYYY-MM-DD.md` + 创意产物 |
| 每周 AI 新闻汇总 | 每周五 18:00 | `reports/汇总/周报/周报_YYYY-Www.md` + 副业榜/情绪 |
| 每月 AI 新闻汇总 | 每月最后一天 18:00 | `reports/汇总/月报/月报_YYYY-MM.md` + 四格漫画 |
| 冷知识盲盒 | 每天 12:30 | `creative/盲盒/YYYY-MM-DD.md` |

自动化在生成内容后会自动发送纯文本邮件（邮箱 2364728886@qq.com）并提交代码。

---

## 三、看板（GitHub Pages）

看板页面位于 `每日新闻/web/`，通过同目录下的静态 JSON 数据渲染，不调用 GitHub REST API。
仓库根 `index.html` 仅作重定向，访问仓库 Pages 地址会自动跳转到看板。

每个 Markdown 对应一个独立 JSON，目录索引位于 `每日新闻/web/data/index.json`。内容或创意产物更新后、提交代码前必须执行：

```bash
python 每日新闻/脚本/export_web_data.py
```

WorkBuddy 的每日、每周、每月和盲盒自动化均应在 `git add` 前执行该命令，使 Pages 数据与 Markdown 保持同步。

---

## 四、文件格式与手动补充

- 每日归档：`sources/归档/YYYY-MM/YYYY-MM-DD.md`，含 3–5 条高价值动态（事件简述 + 关注原因）+ 可选「蓝海/副业」小节。
- 格式模板见 `templates/模板/每日新闻模板.md`。
- 手动补充新闻：直接在对应日期 md 末尾追加，保持结构统一即可。
