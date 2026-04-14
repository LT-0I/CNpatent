# CNpatent — 中国发明专利技术交底书生成器

一个 [Claude Code Skill](https://docs.anthropic.com/en/docs/claude-code)，将学术论文、研发笔记、开源项目等参考素材转化为符合 CNIPA 规范的专利技术交底书（.docx）。

## 功能特点

- **模板驱动生成** — 加载内置专利模板，由模板样式（`Heading 1`/`Heading 2`/`Normal`/`Caption`/`公式`）承载字体格式
- **主旨四段式结构** — 整篇专利围绕"针对什么问题→采取什么方法→基于什么原理→带来什么提升"四要素展开，背景技术局限↔发明目的优势↔技术效果效果三方一一对应
- **领域驱动微创新** — 要求用户指定目标应用领域，用于场景迁移与专利查重规避
- **多 Agent 并行架构** — Planner 生成大纲 → 4 个 Writer Agent 并行写作 → Reviewer Agent 三重 rubric 审查（非 open critique），大纲确认后全程无需人工干预。所有角色（Planner / Writer-A/B/C/D / Reviewer）的角色简报和写作规则定义在 `agents/` 子目录下的角色文件里；orchestrator 调用时显式传 `model="opus"` 强制模型层级
- **三层去 AI 痕迹** — 写作预防 + 正则自动替换 + Reviewer 终审（调用 `CNpatent-humanizer` skill 做专利专用的人类化润色）
- **信息源锚定（防幻觉）** — 所有技术内容追溯到参考素材，无法确认的参数标记 `[待确认]`，杜绝内容编造
- **可编辑的最终态文本 + 断点重启** — 工作目录只保留 `01_outline.md`（大纲）和 `sections/*.md`（8 个章节文件，DOCX 写入前的最终文本），用户编辑任意章节后只需重跑 Phase 3 即可重新生成 DOCX，无需重跑 Writer/Reviewer
- **防幻觉附图提示词** — 静默生成空间锚定的 AI 生图提示词，附带严格文字排他警告
- **纯文本 LaTeX 公式** — 所有数学公式以纯文本 LaTeX 写入，使用模板的 `公式` 段落样式
- **bundled scripts** — `scripts/cnpatent_docx.py` 提供 docx 操作辅助函数（模板加载/锚点定位/公式写入/写后验证），`scripts/deai_cleanup.py` 提供写入前去 AI 兜底正则。所有 docx 操作单一真理源，避免每次调用时重复定义

## 前置依赖

### Python 环境

```bash
pip install python-docx
```

### 依赖的 Skill

| Skill 名称 | 用途 | 必需 |
|------------|------|:----:|
| **CNpatent-humanizer** | 专利专用的去 AI 写作痕迹 skill（3 级词汇检测 / 加权评分 / 9 步重写流水线） | 是 |
| **pdf** | 读取用户提供的 PDF 格式参考素材（论文、技术文档等） | 是 |
| **docx** | 读取用户提供的 .docx 格式参考素材或已有专利草稿 | 是 |

## 必需输入

| 输入项 | 必需 | 说明 | 示例 |
|--------|:----:|------|------|
| **参考素材** | 是 | 学术论文、技术文档、开源项目等 | PDF / .docx / 文本 / 链接 |
| **目标应用领域** | 是 | 专利要落地的具体工程场景 | 肛瘘术后创口三维重建 / 工业焊缝检测 |
| 现有专利参考 | 可选 | 同领域已有专利，用于差异化设计 | 专利号 / 标题 / 摘要 |
| 输出目录 | 可选 | 工作目录，保留全部中间文件，默认 `outputs/[专利名称]/` | `outputs/uav_recon/` |

## 安装方式

### 方式一：项目级安装（推荐）

将 `CNpatent/` 目录放到项目的 `.claude/skills/` 下：

```
your-project/
└── .claude/
    └── skills/
        └── CNpatent/
            ├── SKILL.md
            ├── README.md
            ├── LICENSE
            ├── assets/
            │   └── 交底书模板.docx
            ├── agents/                    # 角色提示词模板（非原生子 agent，由 orchestrator 读入拼接）
            │   ├── README.md              # 架构说明 + orchestrator 调用约定（伪代码）
            │   ├── cnpatent-planner.md    # Phase 0 大纲生成
            │   ├── cnpatent-writer-a.md   # Writer-A（一/二/三节）
            │   ├── cnpatent-writer-b.md   # Writer-B（四节，对应三角守护者）
            │   ├── cnpatent-writer-c.md   # Writer-C（五 + 六前半）
            │   ├── cnpatent-writer-d.md   # Writer-D（六后半 + 固定结尾）
            │   └── cnpatent-reviewer.md   # Phase 2 三重 rubric 审查
            ├── references/
            │   ├── docx-patterns.md      # python-docx 用法示例 + Common Issues
            │   └── writing-rules.md      # 禁用词表 + 写作规范 + 句式检测
            └── scripts/
                ├── cnpatent_docx.py      # docx 辅助函数（load_template / clear_placeholders / verify_docx 等）
                └── deai_cleanup.py       # 写入前去 AI 痕迹兜底正则
```

### 方式二：全局安装

将 `CNpatent/` 目录复制到用户级 Claude 配置目录：

```
~/.claude/skills/CNpatent/
```

## 使用方法

在 Claude Code 中提供参考素材和目标领域：

```
帮我写一份专利技术交底书，参考这篇论文，目标领域是工业焊缝检测
```

```
把这篇论文转成专利交底书，应用场景是自动驾驶障碍物识别
```

如未指定目标领域，Skill 会主动询问。

## 执行流程

```
Phase 0  输入确认 → 工作目录初始化 → 场景迁移 → 结构化大纲生成（含主旨四段式）
           ↓
         用户确认大纲（唯一确认点） → 写入 01_outline.md
           ↓
Phase 1  自动任务拆分 → 4 个 Writer Agent 并行写入 sections/*.md（8 个章节文件）
           ↓
Phase 2  Reviewer Agent 三重审查（一致性 + 防幻觉 + 去AI味）→ 直接修改 sections/*.md
           ↓
Phase 3  对 sections/*.md 调用 final_deai_cleanup() in-place → 按序读入并写入 DOCX
           ↓
Phase 4  DOCX 写入后自动验证（Heading 样式 + 附图编号连续性 + 公式区间 + 全角编号）
           ↓
Phase 5  静默生成 AI 附图提示词文档
           ↓
Phase 6  附图修正（按需触发）

修改场景：用户编辑 sections/*.md → 仅重跑 Phase 3 即可重新生成 DOCX
```

## 输出文件

工作目录 `outputs/[专利名称]/` 下保留两类文件：**最终态文本**（用于编辑回滚）和 **DOCX**（最终交付）。

| 文件 | 说明 | 阶段 |
|------|------|---|
| `01_outline.md` | 用户确认的大纲 | Phase 0 |
| `sections/1_name.md` | 一、发明名称 | Phase 1+2 |
| `sections/2_field.md` | 二、技术领域 | Phase 1+2 |
| `sections/3_background.md` | 三、背景技术 | Phase 1+2 |
| `sections/4a_purpose.md` | 四·发明目的 | Phase 1+2 |
| `sections/4b_solution.md` | 四·技术解决方案 | Phase 1+2 |
| `sections/4c_effect.md` | 四·技术效果 | Phase 1+2 |
| `sections/5_figures.md` | 五、附图说明 | Phase 1+2 |
| `sections/6_implementation.md` | 六、具体实施方式（Writer-C/D 拼接而成） | Phase 1+2 |
| `[专利名称]_专利技术交底书.docx` | 完整专利技术交底书 | Phase 3 |
| `[专利名称]_全套AI生图提示词.docx` | 防幻觉 AI 附图生成提示词 | Phase 5 |

> **设计原则**：审查报告、Writer 原始草稿、人类化润色前/后对比等过程产物**不落盘**。这些"修改痕迹"由 Reviewer 在聊天窗口的简要总结呈现；如需精确 diff，由用户在 `outputs/[专利名称]/` 做 `git init` 自行管理。
> **第四节拆三个文件的理由**：四·发明目的、四·技术解决方案、四·技术效果三者构成"对应三角"，用户最常对照修改这三段，分文件后可以并排打开校对。

## 文档结构（电学类交底书）

```
【正文六节】              [样式]
  一、发明/实用新型名称（≤25字）              [Heading 1]
  二、所属技术领域（1句双层定位）              [Heading 1]
  三、现有技术（背景技术）                    [Heading 1]
     现有技术概况 + 任务场景 + 编号局限（1）-（N） + 引出句
  四、发明内容                              [Heading 1]
     发明目的                              [Heading 2]
        总起 + 优势条目（1）-（N） + 综述
     技术解决方案                          [Heading 2]
        开场（图引用） + 编号步骤（1）-（N）
     技术效果                              [Heading 2]
        总起 + 效果条目（1）-（N，与优势同名异述） + 综述
  五、附图及附图的简单说明                    [Heading 1]
     图1 [描述]、图2 [描述]、...            [Caption]
  六、具体实施方式                          [Heading 1]
     开场（图引用） + 详细步骤 + 变量解释    [Normal]
     $$LaTeX 公式$$                          [公式]
```

注：权利要求书由专利代理人根据本交底书另行撰写。本格式不含说明书摘要。

## 核心技术特性

### 多 Agent 架构

| Agent | 职责 | 字数上限 | 角色文件 |
|-------|------|---------|---------|
| Planner | Phase 0 大纲生成（主旨四段式 / 三方对应 / 术语锁定） | — | `agents/cnpatent-planner.md` |
| Writer-A | 一、发明名称 + 二、技术领域 + 三、背景技术 | ~1200字 | `agents/cnpatent-writer-a.md` |
| Writer-B | 四、发明内容（发明目的 + 技术解决方案 + 技术效果） | ~3500字 | `agents/cnpatent-writer-b.md` |
| Writer-C | 五、附图说明 + 六、具体实施方式 · 前半 | ~3500字 | `agents/cnpatent-writer-c.md` |
| Writer-D | 六、具体实施方式 · 后半 + 固定结尾 | ~3500字 | `agents/cnpatent-writer-d.md` |
| Reviewer | Rubric-A 一致性 + Rubric-B 反幻觉 + Rubric-C 去 AI 味 | — | `agents/cnpatent-reviewer.md` |

**模型强制**：orchestrator 每次调用 Agent 工具时**显式传** `model="opus"`（从角色文件 frontmatter 读取），这是唯一的运行时强制点——`agents/` 下的文件**不是**原生 Claude Code 子 agent，frontmatter 不会被自动发现。详见 [`agents/README.md`](agents/README.md)。

### 三层去 AI 痕迹

| 层级 | 机制 | 说明 |
|------|------|------|
| 第一层 | 写作预防 | Writer prompt 注入禁用词表，写作时即避免 |
| 第二层 | 正则替换 | `final_deai_cleanup()` 硬编码替换，不依赖 AI 判断 |
| 第三层 | Reviewer 终审 | 禁用词残留扫描 + 句式结构检测 + `CNpatent-humanizer` skill |

### 真实专利行文经验

基于 5 份中国发明专利文档（3 份交底书 + 2 份公开专利）提取的写作模式：

- 背景技术"漏斗式"段落节奏（短→长→长→短问题句）
- 发明内容"问题-方案"交叉叙事
- "所述"回指分区策略（发明内容严格、具体实施方式放松）
- 步骤标题功能名词短语命名法
- 子算法引入句固定模板
- "一简一繁"描述策略（已有技术简写、创新步骤详写）
- 公式"夹叙夹议"穿插物理直觉解读
- "短标题+冒号"技术效果条目化格式

## 许可证

MIT
