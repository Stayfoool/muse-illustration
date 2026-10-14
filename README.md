# 灵感插图 · Muse Illustration

> 把**诗词、意象，甚至一句灵感**，变成**插画或海报**。

一个**可成长的 Agent Skill**：内置「风格库」，自动把文学性输入解析成意象、匹配风格、组装提示词并生成插画。支持自选**风格**、**出图张数**与**成品形态**。

遵循开放的 Agent Skill 格式（`SKILL.md`），Claude Code / Codex / Cursor / Gemini CLI / Copilot 等 20+ 工具通用。

![muse-illustration 成品示例：江南春·水印木刻 / 忆江南·水印木刻 / 江南春·risograph / 江南春·色块彩墨](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/hero.jpg)

## 效果示例

> 以下**均为本技能实际产出**，对应风格配方见 `skills/muse-illustration/assets/styles/`。

| 杜牧《江南春》· 水印木刻 | 白居易《忆江南》· 水印木刻 |
|---|---|
| ![江南春·水印木刻](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/01-jiangnanchun-muke.jpg) | ![忆江南·水印木刻](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/02-yijiangnan-muke.jpg) |

| 杜牧《江南春》· risograph 版画 | 杜牧《江南春》· 色块彩墨 |
|---|---|
| ![江南春·risograph](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/03-jiangnanchun-riso.jpg) | ![江南春·色块彩墨](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/04-jiangnanchun-chunkcolor.jpg) |

## 特性

- 🌱 **可成长的风格库** —— 每条风格 = 正向提示词 + 负向约束 + 参考图 + 参数。用得越多越准。
- 🧠 **意象解析** —— 诗词 / 意象词 / 单句灵感 → 六维意象清单（主体 · 景物 · 动作 · 色彩 · 情绪 · 时空）。
- 🎨 **自选风格** —— 内置「江南春 · 水印木刻」「risograph 版画」「色块彩墨」，可持续新增。**选择框里始终带一项「自动匹配风格」**：不想自己挑时，交给技能按意象与情绪裁定。
- 🖼 **自选成品形态** —— 竖版立轴 2:3 / 小红书 3:4 / 方图 1:1 / 横版 3:2 / 带标题字海报。
- 🔢 **自选张数** —— 1 / 2 / 4 张变体择优。
- 📦 **案例沉淀** —— 采纳的成图连同经验一起归档，风格越用越稳。

## 安装

### 方式一 · Claude Code 插件市场（推荐，可自动更新）

```
/plugin marketplace add Stayfoool/muse-illustration
/plugin install muse-illustration@muse-illustration
```

在插件设置里开启 `autoUpdate` 后，**本仓库发新版即自动同步**，无需重装。

### 方式二 · npx skills

```
npx skills add Stayfoool/muse-illustration
```

### 方式三 · 手动

把 `skills/muse-illustration/` 整个目录复制到你的 skills 目录，例如：

- Claude Code：`~/.claude/skills/`
- WorkBuddy：`~/.workbuddy/skills/`

然后重启 / 重载会话。

## 目录结构

```
.
├── .claude-plugin/
│   ├── marketplace.json          # 插件市场清单
│   └── plugin.json               # 插件清单
├── skills/
│   └── muse-illustration/        # ← 技能本体
│       ├── SKILL.md
│       ├── references/           # 组装规则 / 模板
│       └── assets/
│           ├── styles/           # 风格库（每条：正向 + 负向 + 参考图）
│           ├── lexicon/          # 意象 → 视觉元素 词典
│           └── cases/            # 已采纳案例 + 成图
├── scripts/
│   └── sync-skill.sh             # 本地技能 → 仓库 同步脚本
└── .github/workflows/release.yml # 自动打版
```

## 怎么用

对 agent 说一句，比如：

> 用江南春那个风格，把《忆江南》画成画

技能会自动走完：**解析意象 → 选择风格 → 组装提示词 → 生成 → 询问是否采纳**。采纳后，成图与经验一并归档进风格库。

没指定风格时会**弹出选择框，把决定权交给你**，选项 = 「**自动匹配风格**」（让技能按意象与情绪挑）+ 库内每一个风格。风格库新增一条，选择框就自动多一项。

## 新增风格

在 `skills/muse-illustration/assets/styles/` 下按 `references/style-spec-template.md` 建目录，放入 `meta.yaml`、`prompt.positive.txt`、`prompt.negative.txt`、`ref.jpg`。

**两条关键方法论**（写在 `SKILL.md` 里）：

1. **部件级指令 > 抽象形容词** —— 说「屋顶收成深色轮廓、墙用纸色留白、水只几笔横线」，比说「简洁高级」有效得多。
2. **负向约束与正向同等重要** —— 必须显式写出要避免的东西。

## 版本与发布

提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)：`feat:` 升次版本、`fix:` 升修订版。GitHub Actions 会自动升版本号、同步插件清单版本并打 Release。

## 许可证

[MIT](LICENSE) © 2026 Stayfoool

---

## English

**Muse Illustration** turns poems, imagery, or a single line of inspiration into illustrations or posters. It is an Agent Skill with a *growing built-in style library* — each style bundles a positive prompt, negative constraints, a reference image and parameters. When you don't name a style, it shows a picker whose first entry is **auto-match** (it picks by imagery and mood for you), followed by every style in the library. You also choose the number of variants and the output format (vertical scroll, 3:4, 1:1, 3:2, or a titled poster).

```
/plugin marketplace add Stayfoool/muse-illustration
/plugin install muse-illustration@muse-illustration
```

Or `npx skills add Stayfoool/muse-illustration`.

MIT © 2026 Stayfoool
