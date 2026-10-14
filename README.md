# 灵感插图 · Muse Illustration

> 把**诗词、意象，甚至一句灵感**，变成**插画或海报**。

[![Release](https://img.shields.io/github/v/release/Stayfoool/muse-illustration)](https://github.com/Stayfoool/muse-illustration/releases) [![License](https://img.shields.io/github/license/Stayfoool/muse-illustration)](LICENSE)

**内置 3 种可复用风格任你挑；不想挑，就让它按意象与情绪替你选。**

- 🎨 **多种风格任选** —— 水印木刻 / risograph 版画 / 色块彩墨。每条都是**完整配方**（正向提示词 + 负向约束 + 参考图 + 参数），不是随口形容 —— 所以风格能稳定复现，也能一条条持续新增。
- ✨ **自动匹配风格** —— 不指定风格照样能用：技能解析出意象后，按**景物与情绪**替你裁定一条，**并说明为什么选它**；两条难分高下时，会把两条都摆出来让你点。
- 🧠 **意象解析** —— 诗词 / 意象词 / 单句灵感 → 六维意象清单（主体 · 景物 · 动作 · 色彩 · 情绪 · 时空），再由内置词典翻成可执行的画面元素。
- 🖼 **形态与张数自选** —— 竖版立轴 2:3 / 小红书 3:4 / 方图 1:1 / 横版 3:2 / 带标题字海报；1 / 2 / 4 张变体择优。
- 🌱 **越用越准** —— 采纳的成图连同经验一起归档进风格库；风格库与意象词典都随使用增长。

遵循开放的 Agent Skill 格式（`SKILL.md`），Claude Code / Codex / Cursor / Gemini CLI / Copilot 等 20+ 工具通用。

一句话就能开始：

> 用江南春那个风格，把《忆江南》画成画 —— 或者干脆说「你替我挑个风格」。

![muse-illustration 成品示例：江南春·水印木刻 / 忆江南·水印木刻 / 江南春·risograph / 江南春·色块彩墨](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/hero.jpg)

## 效果示例

> 以下**均为本技能实际产出**，对应风格配方见 `skills/muse-illustration/assets/styles/`。

| 杜牧《江南春》· 水印木刻 | 白居易《忆江南》· 水印木刻 |
|---|---|
| ![江南春·水印木刻](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/01-jiangnanchun-muke.jpg) | ![忆江南·水印木刻](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/02-yijiangnan-muke.jpg) |

| 杜牧《江南春》· risograph 版画 | 杜牧《江南春》· 色块彩墨 |
|---|---|
| ![江南春·risograph](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/03-jiangnanchun-riso.jpg) | ![江南春·色块彩墨](https://raw.githubusercontent.com/Stayfoool/muse-illustration/main/showcase/04-jiangnanchun-chunkcolor.jpg) |

## 风格库

三条风格现成可用，各带一份参考图与提示词配方：

| 风格 | 画面语言 | 适配情绪 | 适合题材 |
|---|---|---|---|
| **江南春 · 水印木刻** | 米白纸底、平涂色块、短刻痕，套色 / 水印木刻的平面语言 | 清雅 / 静谧 / 悠远 | 古典诗词、山水、江南、田园、建筑群 |
| **江南春 · risograph 版画** | 3-4 色有限调色板、颗粒噪点、油墨不均、套色错位 | 怀旧 / 清新 / 安静 | 古典诗词、山水、江南、田园 |
| **色块彩墨** | 下三分之二沉静单色面 + 上沿细墨线 + 大留白，展览海报式 | 清雅 / 静谧 / 克制 / 隐逸 | 古典诗词、山水、水乡、田园 |

**不指定风格时会弹出选择框**：第一项固定是「**自动匹配风格**」，其后逐条列出库内每一个风格，并带上它的适配情绪，方便你一眼判断。选择框的清单**不写死在技能里** —— 每次现读风格目录，风格库新增一条，它就自动多一项。

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
├── .claude-plugin/               # 插件市场清单（Claude Code 等）
├── skills/
│   └── muse-illustration/        # ← 技能本体（整个目录可独立拷贝使用）
│       ├── SKILL.md
│       ├── references/           # 组装规则 / 风格与案例模板
│       └── assets/
│           ├── styles/           # 风格库（每条：正向 + 负向 + 参考图）
│           ├── lexicon/          # 意象 → 视觉元素 词典
│           └── cases/            # 已采纳案例 + 成图
├── showcase/                     # README 成品图
├── scripts/                      # 打包 / 发布 / 发版门禁 / 同步
└── .github/workflows/release.yml # 自动升版、打 Release 并推市场
```

## 怎么用

对 agent 说一句就够了，技能会自动走完：**解析意象 → 选择风格 → 组装提示词 → 生成 → 询问是否采纳**。采纳后，成图与经验一并归档进风格库。

风格没指定时，它会**弹出选择框把决定权交给你**（第一项是「自动匹配风格」）；你说了「随便 / 你定」，它就按意象与情绪替你挑，并给出理由。

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

**Muse Illustration** turns poems, imagery, or a single line of inspiration into illustrations or posters. It is an Agent Skill with a *growing built-in style library* — **pick any of the bundled styles, or let the skill pick for you**: when you don't name one, it shows a picker whose first entry is **auto-match**, and if you take it, the skill chooses by imagery and mood and *tells you why*. Each style bundles a positive prompt, negative constraints, a reference image and parameters, so results are reproducible rather than one-off. You also choose the number of variants and the output format (vertical scroll, 3:4, 1:1, 3:2, or a titled poster).

```
/plugin marketplace add Stayfoool/muse-illustration
/plugin install muse-illustration@muse-illustration
```

Or `npx skills add Stayfoool/muse-illustration`.

MIT © 2026 Stayfoool
