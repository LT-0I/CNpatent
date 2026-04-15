# CNpatent-noveltycheck — 中国发明专利新颖性 + 创造性初筛

一个 [Claude Code Skill](https://docs.anthropic.com/en/docs/claude-code)，在编写中国发明专利之前做一轮自动 + 人工的新颖性和创造性筛查。

> 本 skill 是 CNpatent 工作流的**唯一入口**。CNpatent 已经被改造为只接受本 skill 产出的 `5_verified_outline.md` 作为输入。用户要写中国发明专利，必须从本 skill 开始。

## 核心价值

**防止写出已被他人申请的专利**。

AI 工具（包括 CNpatent）容易基于参考文献编造"创新点"，但这些"创新点"可能早已在别人的专利里。写完整篇专利（几千字 + 多个 Writer Agent + Reviewer 审查 + DOCX 生成）后才发现撞车，成本远大于前置筛查。

本 skill 通过两轮筛查识别这类问题：

1. **自动筛查**（Phase A）：5 个免费库（Google Patents + CNIPA pss + PATENTSCOPE + Lens + Scholar/arXiv）并行检索，做第一道提示性判断
2. **人工核查**（Phase B）：为用户生成付费库（incoPat）的操作卡片，用户按指南做详细检索，填写结构化记录
3. **决策**（Phase C）：按中国专利法 22 条和 2023 审查指南的三步法做结构化判决，输出绿 / 黄 / 红灯

## 功能特点

- **三阶段流程** — 自动初筛 + 人工核查 + 决策，通过状态检测支持断点续跑
- **2023 审查指南对齐** — 三步法按最新版本执行，含 Step 2 的"实际技术问题重新确定"和 Step 3 的新公知常识证据类型（技术词典、技术手册）
- **抵触申请检索** — 独立利用 incoPat 的未公开申请字段，查免费库查不到的"别人先申请后公开"的专利
- **非专利文献必查** — Google Scholar + arXiv + CNKI 对算法 / 软件 / 电学类专利是硬性要求，本 skill 强制纳入
- **大纲 schema 对齐 CNpatent** — Phase C 绿灯输出的 `5_verified_outline.md` 直接使用 CNpatent Planner 的大纲 schema（主旨四段式 + 三方对应 + 术语锁定），无缝交接
- **三色灯决策 + 硬 cap** — 黄灯不允许自动重跑 Phase A，必须用户手动触发，防止 AI 过度修改方案和 infinite revision loop
- **可配置的数据库清单** — `user_profile.yml` 记录用户对各库的访问权限，Phase B 根据配置动态生成操作卡片
- **陷阱扫描** — 创造性判断内置 6 类常见陷阱（简单数值替换 / 上下位 / 等同 / 公知组合 / 惯用手段 / 参数优化），审查员常用驳回理由预先覆盖

## 前置依赖

### Python 环境

```bash
pip install python-docx
```

（WebSearch 由 Claude Code 原生提供，无需安装）

### 依赖的 Skill

| Skill 名称 | 用途 | 必需 |
|---|---|:---:|
| **pdf** | Phase A 读取用户提供的 PDF 格式参考文献 | 是 |
| **docx** | Phase A 读取用户提供的 DOCX 格式参考文献 | 是 |
| **CNpatent** | Phase C 绿灯后自动触发，完成大纲到 docx 的写作 | 是（下游） |

### 外部数据库访问

| 数据库 | 必需 | 访问方式 |
|---|:---:|---|
| **incoPat** | 是 | 校园 IP / 机构账号 |
| Google Patents | 是 | 免费 |
| CNIPA 专利检索及分析系统 | 是 | 免费 |
| WIPO PATENTSCOPE | 是 | 免费 |
| The Lens | 是 | 免费注册 |
| Google Scholar | 是 | 免费 |
| arXiv | 是 | 免费 |
| **CNKI 中国知网** | 是 | 校园 IP / 机构订阅 |

## 必需输入

| 输入项 | 必需 | 形式 | 用途 |
|--------|:----:|------|------|
| **参考文献** | 是 | PDF / DOCX / URL / 文本 | 技术内容来源 |
| **目标应用领域** | 是 | 自由文本 | 领域迁移 + IPC 预估 + 微创新 |
| 已知相关专利 | 可选 | 专利号 / 标题 | 检索起点扩展 |
| 已知相关论文 | 可选 | DOI / arXiv ID | 检索起点扩展 |
| 方案是否已公开过 | 可选 | 日期 + 形式 | 宽限期判断（专利法 24 条） |

## 安装方式

### 项目级安装（推荐）

把 `CNpatent-noveltycheck/` 目录放到项目的 `.claude/skills/` 下：

```
your-project/
└── .claude/
    └── skills/
        ├── CNpatent/
        ├── CNpatent-humanizer/
        └── CNpatent-noveltycheck/
            ├── SKILL.md
            ├── README.md
            ├── DESIGN.md
            ├── user_profile.yml
            ├── agents/
            │   ├── README.md
            │   ├── cnpatent-noveltycheck-screener.md   # Phase A
            │   ├── cnpatent-noveltycheck-guide.md      # Phase B
            │   └── cnpatent-noveltycheck-judge.md      # Phase C
            └── references/
                ├── database-catalog.md    # 数据库分层 + 详细信息
                ├── search-methodology.md  # 关键词块 / IPC / Boolean / 特征拆解
                ├── cn-patent-law.md       # 新颖性 + 创造性 + 宽限期 + 抵触申请
                └── templates.md           # 全部模板集合
```

### 全局安装

```
~/.claude/skills/CNpatent-noveltycheck/
```

## 使用方法

在 Claude Code 中像调用 CNpatent 一样直接说：

```
帮我写一份专利技术交底书，参考这篇论文，目标领域是工业焊缝检测
```

Claude 会识别这是专利写作请求，自动启动 **CNpatent-noveltycheck**（不是直接 CNpatent）。完整流程：

```
用户: "帮我写专利, 参考 XYZ.pdf, 领域是 ABC"
  ↓
Phase A (自动, ~10 分钟)
  读参考文献 → 提创新点 → 领域迁移 → 免费库并行检索 → 大纲草稿
  ↓
Phase B (指南生成, ~1 分钟)
  读 user_profile.yml → 生成 incoPat 操作卡片 + 回填模板
  ↓
⏸ 用户手动查新 (~60-90 分钟)
  打开 outputs/[方案名]/3_manual_search_guide.md
  按卡片在 incoPat / Scholar / arXiv / CNKI 里查
  填写 outputs/[方案名]/4_manual_search_template.md
  ↓
用户: "查新完成"
  ↓
Phase C (自动, ~5 分钟)
  读回填表 → 单篇新颖性判断 → 三步法创造性判断 → 陷阱扫描 → 三色灯
  ↓
  ├── 🟢 绿灯 → 自动触发 CNpatent → Phase 1-5 → 专利交底书 .docx
  ├── 🟡 黄灯 → 输出调整建议, 等用户手动重跑 Phase A
  └── 🔴 红灯 → 输出拒绝报告, 建议放弃或大改
```

### 状态检测与断点续跑

每次调用本 skill 时先做状态检测：

```
outputs/[方案名]/
  └─ 5_verified_outline.md 存在 ────────→ 直接触发 CNpatent
  └─ 4_manual_search_template.md 已填 ──→ 跳到 Phase C
  └─ 3_manual_search_guide.md 存在 ─────→ 提醒用户完成人工核查
  └─ 以上都不存在 ──────────────────────→ 从 Phase A 开始
```

用户在 Phase B 后可以离开会话，人工核查完毕再回来继续。

## 输出文件

工作目录 `outputs/[方案名]/` 下按阶段顺序产出：

| 文件 | 说明 | 阶段 |
|---|---|---|
| `0_input_summary.md` | 素材要点 + 领域迁移推演 | A |
| `1_auto_novelty_report.md` | 免费库检索报告 + 三步法预判 | A |
| `2_candidate_outline.md` | CNpatent 格式的大纲草稿 | A |
| `3_manual_search_guide.md` | 付费库操作卡片 | B |
| `4_manual_search_template.md` | 回填模板（用户填） | B |
| `5_verified_outline.md` | 绿灯输出（喂 CNpatent） | C |
| `5_adjustment_suggestions.md` | 黄灯输出 | C |
| `5_rejection_report.md` | 红灯输出 | C |

绿灯后 CNpatent 写入同目录：

```
outputs/[方案名]/
├── 01_outline.md                      # CNpatent 从 5_verified_outline.md 复制
├── sections/                          # 8 章节文件
│   └── ...
├── [专利名称]_专利技术交底书.docx       # 最终交付
└── [专利名称]_全套AI生图提示词.docx     # 附图提示词
```

## 文档结构（本 skill 的角色文件）

```
agents/
├── README.md                              # 角色模板文件约定
├── cnpatent-noveltycheck-screener.md     # Phase A (opus)
├── cnpatent-noveltycheck-guide.md        # Phase B (opus)
└── cnpatent-noveltycheck-judge.md        # Phase C (opus)
```

所有角色统一用 opus。**模型层级通过 orchestrator 调用 Agent 工具时显式传 `model="opus"` 强制**。详见 `agents/README.md`。

## 核心技术特性

### 数据库分层

| 层级 | 数据库 | 默认 |
|---|---|:---:|
| **T1 必查** | incoPat（命令行 + 语义 + 抵触申请） | ✓ |
| **T2 可选** | PatSnap / Derwent / Orbit | 当前未启用 |
| **免费兜底** | Google Patents / CNIPA pss / PATENTSCOPE / The Lens | ✓ |
| **非专利必查** | Google Scholar / arXiv / CNKI | ✓ |

详细数据库信息见 [references/database-catalog.md](references/database-catalog.md)。

### 三步法（2023 审查指南）

本 skill 的 Phase C Judge 严格按 2023 版审查指南执行：

- **Step 1** — 确定最接近现有技术，优先考虑技术问题关联性
- **Step 2** — 确定区别特征，**基于区别特征的实际技术效果重新确定技术问题**（不是说明书声称的）
- **Step 3** — 判断显而易见性，技术启示来源包括教科书、技术词典、技术手册（2023 新增证据类型）

详细法律标准见 [references/cn-patent-law.md](references/cn-patent-law.md)。

### 陷阱扫描（6 类）

Judge 自动扫描以下创造性陷阱：

1. 简单数值替换
2. 上下位概念替换
3. 等同手段替换
4. 公知常识组合
5. 惯用手段
6. 参数优化

任一陷阱命中 → 创造性风险 +1 档。

### 时间预算

| 阶段 | 模式 | 耗时 |
|---|---|---|
| Phase A | 自动 | ~10 分 |
| Phase B | 自动（指南生成） | ~1 分 |
| 人工核查 | 用户 | **60-90 分** |
| Phase C | 自动 | ~5 分 |
| CNpatent 触发 | 自动 | CNpatent 内部 15-30 分 |

总计**约 90-140 分钟**从参考文献到专利技术交底书 .docx。

## 限制与免责声明

1. **免费库检全率有限** — Phase A 只做提示性判断，绿灯前必须走 Phase B
2. **AI 幻觉风险** — 特征对比可能读错原文，用户必须人工复核 Top 命中
3. **抵触申请覆盖不全** — 仅依赖 incoPat 的未公开申请字段，其他库无此数据
4. **宽限期自我公开不豁免** — 中国专利法 24 条不包括申请人自己的公开（与美日欧不同）
5. **非中英文献覆盖弱** — 日文 / 德文 / 俄文专利或论文漏检率较高
6. **不构成法律意见** — 仅为 AI 辅助初筛，最终判断须由专利代理人和 CNIPA 审查员做出

## 完整文档

- [DESIGN.md](DESIGN.md) 完整架构设计（16 节，~800 行）
- [SKILL.md](SKILL.md) 主流程文件
- [references/database-catalog.md](references/database-catalog.md) 数据库目录
- [references/search-methodology.md](references/search-methodology.md) 检索方法论
- [references/cn-patent-law.md](references/cn-patent-law.md) 新颖性 + 创造性 + 宽限期
- [references/templates.md](references/templates.md) 模板汇总
- [agents/README.md](agents/README.md) 角色文件架构说明
- [agents/cnpatent-noveltycheck-screener.md](agents/cnpatent-noveltycheck-screener.md) Phase A 角色
- [agents/cnpatent-noveltycheck-guide.md](agents/cnpatent-noveltycheck-guide.md) Phase B 角色
- [agents/cnpatent-noveltycheck-judge.md](agents/cnpatent-noveltycheck-judge.md) Phase C 角色

## 下游 skill

- **CNpatent** — 绿灯后自动触发，完成专利技术交底书的 .docx 生成

## 许可证

MIT
