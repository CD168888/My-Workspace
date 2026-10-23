# Skill 清单与分工

> 安装位置：**项目级** `.workbuddy/skills/`（仅本工作区可用，不影响全局）
> 安装时间：2026-10-23 ｜ 来源：skillhub.cn ｜ 迁移记录：先装用户级 → 当日迁至项目级 `.workbuddy/skills/` → 当日又被迁到 `.codex/skills/`
>
> ⚠️ **2026-10-23 现状：两份并存**。`.codex/skills/` 是当前生效的那份，已复制一份回 `.workbuddy/skills/`（两边各 213 个文件，内容一致）。
> `publish_article.py` 用 `SKILL_CANDIDATES` 按序查找（`.workbuddy` 优先 → `.codex`），两份都在时读 `.workbuddy`。
> **改动 skill 要两边同步**，否则会出现"改了没生效"。

> ⚠️ **版本库注意**：`.gitignore` 第 71 行忽略整个 `.workbuddy/`、第 74 行忽略整个 `.codex/`，因此这些 skill（含 `.env` 凭据）**不会进入 git**。
> 若希望随仓库备份/共享，需在 `.gitignore` 追加例外规则：
> ```
> !.workbuddy/skills/
> !.workbuddy/skills/**
> ```
> 但 `.env` 必须继续排除（里面将是你的真实 AppSecret）：
> ```
> .workbuddy/skills/md-to-wechat/.env
> ```

## 一、已安装清单

| Skill（目录名） | 对外 name | 实际能力 | 对应环节 | 含代码 | 外部依赖 |
|---|---|---|---|---|---|
| `self-dev-web-scraper` | `web-scraper` | 多策略级联抓取正文（HTTP → HTML 解析 → Playwright 渲染），自带新闻检测、样板文本移除、结构化元数据 | 素材采集 | 否（纯 prompt） | Playwright（仅 JS 渲染档位需要，**未安装**） |
| `wechatarticle` | `wechat-article-writer` | 1500-3000 字深度长文，强制含"读者反驳"、金句、案例、对话式结尾；双交付 MD + 内联样式 HTML | 写作 | 否（2 份 references） | 无 |
| `wechat-cover-maker` | `wechat-cover-maker` | AI 封面生成/改图/精修，支持标题入图或预留安全区 | 封面 | 是（授权 + MCP 客户端 + 自动更新） | **Beatra MCP 服务，需授权**（mcp.beatra.cn） |
| `md-to-wechat` | `md-to-wechat` | Markdown → 公众号内联样式 HTML → 推草稿箱，一步完成 | 排版 + 推送 | 是（`publish.cjs`） | Node 18+（本机 22 ✅）；渲染服务需账号 |
| `wechat-article-pro-plus` | `wechat-article-pro-plus` | 全流程 prompt 库：选题 / 扩写 / 洗稿 / 去 AI 味 / 排版 / 配图 / 封面 | 全流程参考 | 否（8 份 prompt + 模板） | 无 |
| `unclecheng-reduce-ai-perception-v2` | `humanizer` | 去 AI 味：AI 高频词、过度结构化、虚假客观、机械化连接、公式化结尾等 | 降重 / 去味 | 否（3 份 references） | 无 |

## 二、权威分工（重要：三处功能重叠，必须指定主用）
`wechatarticle`、`md-to-wechat`、`wechat-article-pro-plus` 都能出公众号 HTML。不定规则会打架，导致同一篇文章出现两套样式。

**定死这一条：**

| 环节 | 唯一权威 | 说明 |
|---|---|---|
| 素材采集 | `self-dev-web-scraper` | 只负责拿正文和元数据，不做评判 |
| 选题 / 结构 | `wechat-article-pro-plus` 的 `prompt/topic.md`、`prompt/outline.md` | 只借 prompt，不借它的排版 |
| 写作 | `wechatarticle` | **只产出 Markdown**，不用它自带的 HTML |
| 去 AI 味 | `unclecheng-reduce-ai-perception-v2` | 唯一权威，其他两个的自带去味 prompt 不用 |
| 封面 | `wechat-cover-maker` | 需先完成 Beatra 授权 |
| **排版 + 推草稿箱** | **`脚本/publish_article.py`** | 2026-10-23 起改为自家脚本。`md-to-wechat` 的渲染走第三方 `feishu2weixin`，文章内容会出本机；且样式不可控。**不再使用** |
| 配图抓取 | `extract-images` + `脚本/fetch_via_browser.py` | 自制数据图、官方棚拍图（用户明确否决） |

> 原则：**Markdown 出处唯一，样式出口唯一。** 中间任何一环自带样式都不要用。
>
> 版式 token 集中在 `publish_article.py`（三套主题 signal / editorial / swiss），
> 详见 `内容生产SOP.md` 阶段 ③。改样式只改脚本，不要改 Markdown。

## 三、安全处置记录（2026-10-23）

安装时发现并处理了三处风险：

| 项 | 问题 | 处置 |
|---|---|---|
| `md-to-wechat/.env` | 作者把自己的**真实 AppID + AppSecret**（`wx1f6b3d7b…`）和手机号打包进公开 Zip | 已清空为占位符，原文件备份为 `.env.orig.bak` |
| `md-to-wechat/.cache.json` | 含作者账号下的素材 `media_id` 与图片映射 | 已清空为 `{"covers":{},"bodyImages":{}}`，备份为 `.cache.json.orig.bak` |
| `md-to-wechat` API_URL | 留空时回退到作者架设的 `feishu2weixin.maolai.cc`，**文章内容会先发到第三方服务器渲染** | 已设为 `http://localhost:3000`；如在意隐私，需本地自建渲染服务 |

> 那份 AppSecret 已随公开包泄露，属该作者的失效凭证，**任何情况下都不要使用**。要填必须填自己的。

另：`wechat-cover-maker` 自带 `auto_update.py`，会从 `cdn.beatra.cn` 下载并替换自身代码。这是厂商 SDK 的常见做法，非恶意，但意味着**该 skill 的代码会变**，后续若报错先查版本一致性。

## 四、运行依赖现状

**Python 环境：** `~/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（Windows 上必须用 `Scripts\` 下的解释器）

| 依赖 | 版本 | 状态 |
|---|---|---|
| Node.js | 22.22.2 | ✅ `publish.cjs` 语法自检通过 |
| Python | 3.13.12 | ✅ venv 已建 |
| requests | 2.34.2 | ✅ 2026-10-23 安装 |
| beautifulsoup4 | 4.15.0 | ✅ 2026-10-23 安装 |
| lxml | 6.1.3 | ✅ 2026-10-23 安装 |
| **trafilatura** | 2.3.1 | ✅ 2026-10-23 安装 —— 正文抽取主力 |
| markdown | 3.11.2 | ✅ 2026-10-23 安装 |
| Playwright | 1.64.1 | ✅ 2026-10-23 安装，内核 `chromium-1248`。**必须走国内镜像**，官方 CDN 只有 33KB/s：
`export PLAYWRIGHT_DOWNLOAD_HOST="https://cdn.npmmirror.com/binaries/playwright"`（约 4 分钟，版本必须匹配 chromium-1248） |

### 抓取实测结论（2026-10-23）

| 站点 | 结果 |
|---|---|
| MIT Technology Review | ✅ 完整可用。正文 4744 字，元数据全（作者/日期/站点），og:image 裸请求可下（JPEG 61KB，无防盗链） |
| IT之家 | ✅ 可用。trafilatura 把 1289 字压到 307 字（真实正文），自动剔掉导航/推荐位 |
| GitHub Blog | ✅ 可抓（列表页会只抽摘要，正常） |
| arXiv API | ✅ 必须用 **https**，http 版返回 502；`application/atom+xml` 可枚举 |
| OpenAI News | ❌ 403，Cloudflare 反爬，需 Playwright |
| 机器之心 | ❌ 纯 JS 站，HTML 只有 3KB 壳页 |

**两个必须处理的坑：**

1. **懒加载**。IT之家正文图 `src` 是占位符 `//img.ithome.com/images/v2/t.png`，真图在 `data-original`。顺序应为 `data-original` → `data-src` → `src`，并过滤 `t.png` 类占位符，否则下到的全是同一张 1 像素图。
2. **正文长度 ≠ 正文质量**。首页/列表页的"正文字数"多是导航堆出来的。必须用 trafilatura 或锁定容器（IT之家是 `id="paragraph"`），不要用朴素去标签。

**trafilatura 的额外价值：** 能自动给出 `author` / `date` / `sitename`，这对"反着看"栏目的溯源是刚需（谁写的、什么时候写的，直接影响可信度判定）。

## 五、这套 skill 还没覆盖的缺口

对照流水线，以下环节目前**没有**现成 skill 承担，需要自建或在 prompt 里补：

1. **RSS / API 线索池与事件去重** —— 现在只有"单页抓取"，没有"今天有哪些事"的枚举能力。
2. ~~配图批量下载 + 转存微信图床~~ —— ✅ 2026-10-23 已解决：`fetch_via_browser.py` 按正文容器取图，`build_assets.py` 加工，`publish_article.py` 自动转存图床。
3. **引用校验闸门** —— 链接可达性 + 标题比对，防 AI 编造引文。
4. **草稿箱幂等与状态管理** —— 半解决：`draft/batchget` 查重 + `manifest.json` 记 `draft_media_id` 已是约定，但没做成脚本自动执行。
5. **发布后数据复盘** —— 阅读/完读/关注转化回填。

> 这五项正好对应 `docs/公众号自动化流水线可行性评估.md` 的 P2、P4、P5 阶段。

## 六、生效与排错

- **迁移到项目级后需重启 WorkBuddy**，skill 列表才会按新路径重新加载。判断是否生效：看会话可用 skill 列表里是否出现 `web-scraper`、`wechat-article-writer`、`humanizer` 等 name（注意 name 与目录名不一定相同）。
- 若某个 skill 未加载，先确认 `.workbuddy/skills/<目录>/SKILL.md` 存在且首行是 `---`。
- `wechat-cover-maker` 首次使用会触发 Beatra 授权（`scripts/authorize.py`），需要联网与账号；未授权时它调不动 `beatra.images.*` 工具。
- `md-to-wechat` 未填 `.env` 时会直接失败，这是预期行为（宁可失败，也不要用包里带的那份泄露凭证）。
