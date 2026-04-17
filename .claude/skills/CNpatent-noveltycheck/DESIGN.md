# CNpatent-noveltycheck 设计文档 v1.0 (DRAFT)

## 0. 元信息

| 字段 | 值 |
|---|---|
| 版本 | 1.0 DRAFT |
| 日期 | 2026-04-14 |
| 状态 | 待用户评审 |
| skill 路径 | `.claude/skills/CNpatent-noveltycheck/` |
| 依赖 skill | CNpatent, pdf, docx |
| 下游 skill | CNpatent (Planner 输入) |

---

## 1. 背景与动机

CNpatent skill 假设输入的技术方案"值得写专利"。但：

- AI 可能基于参考文献编造"创新点"
- 参考文献里的想法可能早已被他人申请
- 用户自己也难判断方案是否具备新颖性和创造性
- 写完整篇专利后才发现撞车，成本远大于前置筛查

本 skill 在 CNpatent 之前插入一道筛查关卡，对方案做：

- 一轮自动免费库查重（查全优先）
- 一轮指导用户在付费库人工核查（查准优先）
- 基于中国专利法标准做新颖性和创造性判断
- 输出三色灯决策：进入 CNpatent / 调整方案 / 放弃

---

## 2. 目标与非目标

### 目标

- 在 CNpatent 工作流之前识别明显缺乏新颖性的方案
- 按中国专利法新颖性和创造性标准做初步判断
- 给出可直接喂给 CNpatent Planner 的经查新大纲
- 为用户提供付费库人工核查的具体指南

### 非目标

- 不提供正式的专利可专利性意见
- 不替代专利代理人的完整检索分析
- 不做 FTO 或无效宣告级的检索深度
- 不承担最终法律判断责任
- 不处理权利要求书撰写

---

## 3. 架构总览

```
[用户输入] 参考文献 + 领域 + 付费库清单 (默认 incoPat)
       │
       ▼
┌─────────────────────────────────────┐
│  Phase A: 自动筛查 + 大纲生成        │
│  Agent: screener (opus)             │
│  ─ 读素材 → 提创新点 → 领域迁移      │
│  ─ 免费库自动检索 × 5 库             │
│  ─ 特征对比 + 三步法预判             │
│  ─ 输出大纲草稿                      │
└─────────────────────────────────────┘
       │
       ▼ 0_input_summary.md
         1_auto_novelty_report.md
         2_candidate_outline.md
       │
       ▼
┌─────────────────────────────────────┐
│  Phase B: 人工核查指南生成           │
│  Agent: guide (opus)                │
│  ─ 读 1_auto_novelty_report         │
│  ─ 按 user_profile 生成操作卡片      │
│  ─ 输出回填模板                      │
└─────────────────────────────────────┘
       │
       ▼ 3_manual_search_guide.md
         4_manual_search_template.md
       │
       │   [人类工作: 60-90 分钟]
       │   用户在 incoPat / Scholar / arXiv / CNKI
       │   按指南检索，填写 4_manual_search_template.md
       │
       ▼
┌─────────────────────────────────────┐
│  Phase C: 决策                       │
│  Agent: judge (opus)                │
│  ─ 读回填后的 template              │
│  ─ 单篇新颖性 + 三步法创造性判断     │
│  ─ 输出三色灯 + 下一步               │
└─────────────────────────────────────┘
       │
       ▼ 5_verified_outline.md       (绿灯)
         5_adjustment_suggestions.md (黄灯)
         5_rejection_report.md       (红灯)
       │
       ▼
   绿灯 ─→ CNpatent Planner 直接读入
   黄灯 ─→ 用户确认调整方向 → 回到 Phase A
   红灯 ─→ 方案重构或放弃
```

---

## 4. 输入输出契约

### 4.1 输入

| 字段 | 必需 | 形式 | 用途 |
|---|---|---|---|
| 参考文献 | 是 | PDF / DOCX / URL / 文本 | 技术内容来源 |
| 目标领域 | 是 | 自由文本 | 领域迁移 + IPC 预估 |
| 已知相关专利 | 否 | 专利号 / 标题 | 检索起点扩展 |
| 已知相关论文 | 否 | DOI / arXiv ID | 检索起点扩展 |
| 方案是否公开过 | 否 | 日期 + 形式 | 宽限期判断 |

### 4.2 输出

| 文件 | 阶段 | 性质 | 用途 |
|---|---|---|---|
| `0_input_summary.md` | A | 最终态 | 素材要点 + 领域迁移 |
| `1_auto_novelty_report.md` | A | 最终态 | 免费库检索报告 |
| `2_candidate_outline.md` | A | 最终态 | 带查新标注的大纲 |
| `3_manual_search_guide.md` | B | 最终态 | 付费库操作卡片 |
| `4_manual_search_template.md` | B | 半空 | 用户回填 |
| `5_verified_outline.md` | C 绿 | 最终态 | 喂 CNpatent Planner |
| `5_adjustment_suggestions.md` | C 黄 | 最终态 | 调整方向 |
| `5_rejection_report.md` | C 红 | 最终态 | 放弃说明 |

所有文件存于 `outputs/[方案名]/` 目录。

---

## 5. Agent 规格

沿用 CNpatent 的"角色模板文件"模式——不是原生子 agent，orchestrator 调用时 Read 角色文件 + 显式传 `model="opus"`。

### 5.1 Screener (Phase A)

- **name**: `cnpatent-noveltycheck-screener`
- **model**: opus
- **tools**: Read, Write, Edit, Bash, WebSearch, Agent（用于调 pdf/docx skill）
- **输出**: `0_input_summary.md` + `1_auto_novelty_report.md` + `2_candidate_outline.md`

**职责**:

1. 读参考文献，抽取技术要点（方法论 + 关键参数 + 效果数据）
2. 提取潜在创新点（delta，不是整个方案）
3. 映射到目标领域，识别哪些通用哪些领域特定
4. 构建中英双语关键词块
5. 预估 2-4 个核心 IPC 分类号
6. 并行调用 WebSearch 查 5 个免费库
7. 读 Top 20-50 摘要，筛出 Top 5-10 精读
8. 做特征对比表（目标 vs 命中 per feature）
9. 做三步法预判（最接近现有技术 + 区别特征 + 实际技术问题 + 显而易见性）
10. 输出大纲草稿，对齐 CNpatent Planner 的大纲 schema

**约束**:

- 免费库结果只能做提示性判断，不能说"一定新颖"
- 特征对比必须有可追溯的原文依据
- 每个风险判断必须标注依据的命中文件号
- 不得基于单一库的结果下结论，至少两库交叉

### 5.2 Guide (Phase B)

- **name**: `cnpatent-noveltycheck-guide`
- **model**: opus
- **tools**: Read, Write, Edit
- **输出**: `3_manual_search_guide.md` + `4_manual_search_template.md`

**职责**:

1. 读 `1_auto_novelty_report.md` 提取关键词块 + IPC
2. 读用户 `user_profile`（默认 incoPat）
3. 生成对应库的操作卡片：登录方式 / 检索入口 / 字段代码 / 3 条检索式 / 步骤编号 / 预计耗时 / 停止准则
4. 生成非专利库操作卡片（Google Scholar, arXiv, CNKI）
5. 生成回填模板

**约束**:

- 不得伪造检索式，必须基于 Phase A 的关键词块 + IPC 构造
- 时间总预算控制在 60-90 分钟
- 每个卡片必须给出停止准则
- 模板字段必须对齐 Phase C judge 的解析格式

### 5.3 Judge (Phase C)

- **name**: `cnpatent-noveltycheck-judge`
- **model**: opus
- **tools**: Read, Write, Edit
- **输出**: `5_verified_outline.md` 或 `5_adjustment_suggestions.md` 或 `5_rejection_report.md`

**职责**:

1. 读用户填好的 `4_manual_search_template.md`
2. 对每个"是 / 存疑"的命中做单篇新颖性分析
3. 从所有命中选最接近现有技术
4. 做三步法创造性判断（按 2023 审查指南）
5. 扫描常见陷阱（上下位 / 等同 / 参数 / 公知组合）
6. 给出新颖性 + 创造性风险等级
7. 按三色灯模型决定下一步
8. 输出对应的 5_*.md 文件

**约束**:

- 三步法每一步必须给出显式推理
- 实际解决的技术问题必须按 2023 指南更新：基于区别特征的实际效果，不是说明书声称的
- 陷阱检测必须给出具体的判断依据
- 绿灯必须有明确的新颖性证据 + 无明显创造性陷阱
- 黄灯必须给出具体的调整方向
- 红灯必须明确指出哪篇文件破坏了新颖性
- **不得输出替代大纲或大段重写**（借鉴 CNpatent Reviewer 约束）

---

## 6. 数据库策略

### 6.1 用户画像 (当前默认)

```yaml
user: default

paid_access:
  incopat:
    available: true
    auth: campus_ip      # 无需注册，校园网 IP 登录
    quota: unlimited     # IP 登录无次数限制
  patsnap: false
  derwent: false
  orbit: false

free_access:
  cnipa_pss: true
  google_patents: true
  patentscope: true
  lens: true

non_patent:
  google_scholar: true
  arxiv: true
  cnki:
    available: true
    auth: campus_ip
```

**配置位置**: `.claude/skills/CNpatent-noveltycheck/user_profile.yml`（初次运行时 skill 生成，用户可编辑）

### 6.2 Phase A 自动查询 (skill 直接调 WebSearch)

| 库 | 角色 | 查询次数 |
|---|---|---|
| Google Patents | 排序 + 语义 + Prior Art Finder | 2-3 |
| CNIPA pss-system | CN 权威 | 2 |
| WIPO PATENTSCOPE CLIR | 跨语言 | 1 |
| The Lens | 全球结构化 | 1 |
| Google Scholar + arXiv | 非专利现有技术 | 2-3 |

### 6.3 Phase B 人工查询 (用户自己做)

**必查层**:

| 库 | 访问 | 角色 | 耗时 |
|---|---|---|---|
| **incoPat 命令行/高级** | 校园 IP | Boolean + IPC 精确检索 | 20-30 分 |
| **incoPat 语义检索** | 校园 IP | 粘贴方案描述做概念召回 | 10-15 分 |

**非专利必查层**:

| 库 | 访问 | 角色 | 耗时 |
|---|---|---|---|
| **Google Scholar** | 免费 | 英文论文 + 跨领域 | 10-15 分 |
| **arXiv** | 免费 | 预印本，算法类必查 | 5-10 分 |
| **CNKI** | 校园 IP | 中文学位 + 会议 | 10-15 分 |

**可选交叉层** (时间允许):

| 库 | 访问 | 角色 | 耗时 |
|---|---|---|---|
| Google Patents Prior Art Finder | 免费 | 粘贴方案段落 | 5 分 |
| PATENTSCOPE CLIR | 免费 | 跨语言验证 | 5-10 分 |

**总时间预算**: 60-90 分钟

### 6.4 为什么砍掉 T2 和 T3

**T2 (Derwent / Orbit)**:

- 用户无订阅
- 主要价值是 DWPI 标准化摘要
- 可由 incoPat 语义检索替代
- 强推只会产生"跳过"提示噪音

**T3 (innojoy / Patentics / Baiten)**:

- 需要独立注册账号
- 个人免费额度不明或较低
- 与 incoPat 覆盖重叠度高
- 边际收益 < 注册摩擦成本

**核心补偿**: 失去 Derwent DWPI 的"概念级标准化摘要"作用，由 **incoPat 语义检索** 弥补。incoPat 支持粘贴一段自然语言描述做语义检索，是 10 种检索方式之一。

**扩展性**: 用户未来获得 PatSnap / Derwent / Orbit 访问时，改 `user_profile.yml`，Phase B 会自动加入相应操作卡片。

### 6.5 抵触申请的手动查法

抵触申请是 Phase B 的单独一节，因为它需要用户在 incoPat 里做一次特殊检索：

```
检索目标：申请日在近 18 个月内、尚未公开的专利
操作：incoPat 高级检索 → 申请日字段设为 [今天 - 18 个月, 今天] 
      → 公开状态设为"未公开"或"早期申请"
      → 按本方案关键词检索
备注：这类文件量少，读 Top 20 即可
```

未公开申请无法通过 Google Patents / CNIPA pss 等免费库查到，这是 incoPat 的独特价值之一。

---

## 7. Phase A 详细规格

### 7.1 关键词块构建

每个核心特征建立一个"块"。块内用 OR 扩展，块间用 AND 连接。

扩展维度：

- 中英双语
- 同义词和近义词
- 上下位概念
- 全称和缩写
- 异名和别称

示例（假设 UAV 集群专利）：

```
块 1 主体: (无人机 OR UAV OR drone OR "unmanned aerial" OR 多旋翼 OR quadrotor)
块 2 集合: (集群 OR swarm OR formation OR "multi-UAV" OR 编队)
块 3 行为: (覆盖 OR coverage OR 侦察 OR surveillance OR reconnaissance)
```

### 7.2 IPC 预估策略

电学 / 软件 / 算法类常用 IPC：

| IPC | 含义 |
|---|---|
| G06N | AI / 神经网络 / 遗传算法 |
| G06F | 电数字数据处理 |
| G06T | 图像处理 |
| G06V / G06K | 计算机视觉 / 数据识别 |
| G06Q | 商业方法 |
| H04L | 数字信息传输 |
| H04W | 无线通信网络 |
| B64C / B64U | 无人机结构 |
| G05D | 自动控制 |

**策略**：先按关键词粗检，从 Top 20 命中统计高频 IPC 小组，用这些 IPC 做定向检索。

### 7.3 特征对比表 schema

```markdown
| 本方案特征 (权要拆分) | 对比文件 | 段落 | 是否公开 | 差异 |
|---|---|---|---|---|
| 特征 A: ... | CN1234567A | 0023 | 是 | 完全相同 |
| 特征 B: ... | CN1234567A | — | 否 | 区别特征 |
| 特征 C: ... | CN1234567A | 0045 | 部分 | X vs Y，等同需分析 |
```

### 7.4 三步法预判 (2023 审查指南)

**Step 1 — 确定最接近的现有技术**

- 与本申请技术领域最相关
- 解决的技术问题最关联
- 公开的技术特征最多

**Step 2 — 确定区别特征与实际技术问题**

- 列本申请 vs 最接近对比文件的区别技术特征
- **基于区别特征在本申请中的实际技术效果** 重新确定技术问题
- 2023 指南强调：不是说明书声称的问题

**Step 3 — 判断显而易见性**

- 现有技术中是否存在"技术启示"
- 启示来源：同一文件其他部分 / 另一文件 / 公知常识 / 惯用手段
- 2023 新增：技术词典、技术手册列为公知常识证据

---

## 8. Phase B 详细规格

### 8.1 时间预算细分

| 项 | 耗时 |
|---|---|
| incoPat 命令行 + IPC × 3 条检索式 | 20-30 分 |
| incoPat 语义检索 × 1 轮 | 10-15 分 |
| 抵触申请检索（18 个月窗口） | 5-10 分 |
| Google Scholar × 2-3 条 | 10-15 分 |
| arXiv × 2 条 | 5-10 分 |
| CNKI × 2 条（中文学位论文） | 5-10 分 |
| Google Patents Prior Art Finder（可选） | 5 分 |
| **合计** | **60-95 分** |

### 8.2 incoPat 操作卡片模板

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【T1 必查】incoPat
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL:     https://www.incopat.com/
登录:    校园 IP 自动登录
入口:    首页 → 高级检索 或 命令行检索

字段代码:
  TIABC  - 标题+摘要+权要合并
  TI     - 标题
  AB     - 摘要
  CL     - 权利要求
  IPC    - IPC 分类
  AD     - 申请日
  PD     - 公开日
  PA     - 申请人

检索式 1 (按特征 A):
  TIABC=(<关键词块1>) AND TIABC=(<关键词块2>) 
  AND IPC=(G06N OR G06F) 
  AND AD<=2026-04-14

检索式 2 (按特征 B):
  TIABC=(<关键词块3>) AND IPC=(<次分类>)
  AND AD<=2026-04-14

检索式 3 (语义检索):
  切到"语义检索"标签 → 粘贴以下段落:
  "<skill 生成的 2-3 句方案摘要>"

操作步骤:
  1. 运行检索式 1 → 同族合并 → 按相关度排序
  2. 读 Top 50 标题，筛 Top 15 候选
  3. Top 15 读摘要 + 权要 1，填入记录表
  4. 重复检索式 2 和 3
  5. 合并三次结果，去重
  6. 对合并 Top 10 精读全文

预计耗时: 30-45 分钟
停止准则: 最后 20 篇命中无新的高相关文献

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【特殊】抵触申请检索
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
同一平台 incoPat:
  设申请日范围 = [2024-10-14, 2026-04-14]
  关键词 = 核心特征块（简化版）
  读 Top 20，重点看未公开/早期申请

耗时: 5-10 分钟
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

卡片里的检索式是 Phase A 关键词块和 IPC 的直接产物，用户只需复制粘贴。

### 8.3 非专利库操作卡片（简版）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【非专利必查】Google Scholar + arXiv + CNKI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Google Scholar:
  URL: https://scholar.google.com/
  检索式: "<英文关键词组合>"
  时间过滤: 自定义范围到 2026-04-14
  读 Top 30 标题
  耗时: 10-15 分

arXiv:
  URL: https://arxiv.org/
  Advanced Search: Category (cs.CV / cs.LG / cs.RO ...)
  + Keywords (英文)
  读 Top 20 摘要
  耗时: 5-10 分

CNKI:
  URL: https://www.cnki.net/ (校园 IP)
  主题检索: "<中文关键词>"
  文献类型: 学位论文 + 会议
  读 Top 20 摘要
  耗时: 10-15 分

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 8.4 回填模板 schema

```markdown
# 人工核查记录 [方案名]

## 检索元信息
- 检索日期: 2026-04-__
- 检索人: __
- 使用数据库: [x] incoPat  [x] Scholar  [x] arXiv  [x] CNKI
- 检索式列表:
  - incoPat 式 1: ...
  - incoPat 式 2: ...
  - incoPat 语义: ...
  - Scholar: ...
  - arXiv: ...
  - CNKI: ...
- 命中总数（去同族）: __
- 详读篇数: __
- 总耗时: __

## 发现的命中

### 命中 1
- 专利号 / 论文 ID: 
- 公开日 / 发表日:
- 申请日 / 投稿日 / 优先权日:
- 申请人 / 作者:
- IPC (专利) / 类别 (论文):
- 标题:
- 摘要要点 (30-80 字):
- 关键技术特征:
  1. 
  2. 
  3. 
- 与本方案的特征对照:
  | 本方案特征 | 该文件是否公开 | 差异 |
  |---|---|---|
  | 特征 A: ... | 是/否/部分 | |
  | 特征 B: ... | | |
- 相关度 (X/5):
- 是否可能破坏新颖性: 是 / 否 / 存疑
- 备注:

### 命中 2
...

## 初步结论（留空，由 skill judge 填写）
- 新颖性风险: __
- 创造性风险: __
- 最接近现有技术: 命中 #__
- 区别技术特征: 
- 三步法判断: 
- 建议: __ (绿 / 黄 / 红)
```

---

## 9. Phase C 详细规格

### 9.1 新颖性判断算法

对每个标记为"是 / 存疑"的命中：

1. 读该命中记录的特征对照表
2. 检查是否所有特征都对应为"是"
3. 若全部对应 → 破坏新颖性（红灯）
4. 若有部分对应 → 判断是否"等同"（注意：等同不是抵触新颖性的条件，等同是创造性层面的）
5. 若存在明确的"否"（区别特征）→ 具备新颖性，进入 9.2

**抵触申请特殊处理**：标记为"抵触申请检索"来源的命中，即使全部特征对应，也只破坏新颖性不进创造性流程。

### 9.2 创造性判断算法（三步法）

**Step 1 — 选最接近现有技术**：

- 在所有具备新颖性的命中中
- 选择领域最接近、技术问题最关联、公开特征最多的那篇
- 通常是 Top 3 中的一篇

**Step 2 — 确定区别特征和实际技术问题**：

- 对照命中记录的特征对照表，列出所有"否"和"部分"
- 综合这些区别特征在本方案中的实际技术效果
- 重新确定实际解决的技术问题（**不是**用户说明书声称的问题）

**Step 3 — 判断显而易见性**：

对区别特征逐条分析：

- 本领域技术人员是否有动机将其引入最接近现有技术？
- 其他命中文件中是否存在该区别特征的启示？
- 是否属于公知常识、惯用手段、常规替换？

### 9.3 常见陷阱扫描

对区别特征列表，逐条扫以下陷阱：

| 陷阱类型 | 判据 | 示例 |
|---|---|---|
| 简单数值替换 | 参数微调且无新效果 | 温度 80 → 82 |
| 上下位概念替换 | 窄到宽或宽到窄 | 神经网络 → CNN |
| 等同手段替换 | 功能相同的已知手段互换 | 电机 → 液压缸 |
| 公知常识组合 | 已知模块简单拼接，无协同 | A 模块 + B 模块 |
| 惯用手段 | 领域内常见实现 | "本领域公知" |
| 参数优化 | 常规实验可达到 | 超参数网格搜索 |

命中任一陷阱 → 创造性风险 +1 档

### 9.4 三色灯决策

| 灯 | 新颖性 | 创造性 | 下一步 |
|---|:---:|:---:|---|
| 🟢 绿 | 低 | 低-中 | 生成 `5_verified_outline.md` → CNpatent |
| 🟡 黄 | 低 | 中-高 | 生成 `5_adjustment_suggestions.md` → 用户手动重跑 A |
| 🔴 红 | 中-高 | 任意 | 生成 `5_rejection_report.md` → 放弃或大改 |

### 9.5 黄灯调整建议格式

```markdown
# 调整建议 [方案名]

## 创造性风险分析
- 最接近现有技术: 命中 #__
- 识别的区别特征: [列表]
- 疑似陷阱: [列表]

## 可行调整方向

### 方向 1: 增加区别特征
- 在现有方案基础上引入 [具体特征描述]
- 预期效果: [解决新的技术问题]
- 风险: [需重新验证该特征是否已被公开]

### 方向 2: 强化技术效果
- [具体效果维度] 的量化指标
- 需要补充实验/对比数据

### 方向 3: 缩小保护范围
- 从通用 [领域 X] 收窄到 [特定子领域]
- 牺牲一定保护范围换取更强的创造性证据

## 下一步
请用户选择调整方向，更新输入后**手动重跑 Phase A**。
```

### 9.6 绿灯输出 (`5_verified_outline.md`)

格式对齐 CNpatent Planner 的输入 schema（详见第 12 节集成点）。至少包含：

- 发明名称候选
- 技术领域一句定位
- 背景技术要点（引用的现有技术命中文件号）
- 发明目的条目
- 技术解决方案步骤列表
- 技术效果条目
- 附图清单（建议）
- 验证状态标记：`novelty_verified: true, date: ..., judge_model: opus`

---

## 10. 法律标准参考 (简明)

### 10.1 新颖性（专利法 22.2）

**定义**：不属于现有技术；没有抵触申请

**破坏条件**：单一对比文件完整披露全部技术特征

**判断方式**：单篇对比，不允许组合

### 10.2 抵触申请

**定义**：他人在先申请 + 在后公开（含申请日当天或之后）

**效果**：单独破坏新颖性，**不破坏创造性**

**检测难点**：在检索时可能尚未公开，依赖 incoPat 的未公开申请检索功能

### 10.3 创造性（专利法 22.3）

**定义**：与现有技术相比有突出的实质性特点和显著的进步

**判断方法**：三步法（见 7.4）

**2023 指南关键更新**：

- 强调"技术问题的关联性"作为 Step 1 标准
- 实际技术问题需基于区别特征的效果重新确定
- 技术词典和技术手册列为公知常识证据

### 10.4 新颖性宽限期（专利法 24 条）

申请日前 6 个月内下列情形不丧失新颖性：

1. 国家紧急状态下为公共利益首次公开
2. 中国政府主办或承认的国际展览会首次展出
3. 规定的学术或技术会议首次发表（需国务院有关主管部门或全国性学术团体组织）
4. 他人未经申请人同意泄露

**关键注意**：

- 申请人自己在论文、博客、产品发布会上的公开**不包含**（与美日欧不同）
- 程序要求：申请时声明 + 2 个月内提交证明
- 2023 新增：紧急状态或未经同意泄露后，第三人再次公开不重复计算宽限期

---

## 11. 与 CNpatent skill 的集成

### 11.1 接口点

`5_verified_outline.md` 的格式必须与 CNpatent Planner 的输入 schema 对齐。

**待确认**：两个 schema 的具体字段映射（见第 15 节开放问题）。

### 11.2 CNpatent Planner 的行为修改

在 Phase 0 输入确认阶段，Planner 检查：

```python
if exists("outputs/[方案名]/5_verified_outline.md"):
    # 直接读入作为大纲基础
    # 跳过自动大纲生成
    # 保留用户确认环节（用户可微调）
    # 在大纲中标记 "novelty_verified: true"
else:
    # 提示用户: "建议先过 CNpatent-noveltycheck 筛查"
    # 但不强制阻塞，允许用户 override 继续
    # 在大纲中标记 "novelty_verified: false"
```

### 11.3 不影响的部分

CNpatent Phase 1-6 保持不变。本 skill 仅在 Phase 0 入口插入一次检查。

---

## 12. 实施计划

| 步骤 | 动作 | 估计 |
|---|---|---|
| 1 | DESIGN.md 评审 + 修订 | 当前 |
| 2 | 定义 verified_outline schema，对齐 CNpatent Planner | 小 |
| 3 | 创建 skill 目录结构 + SKILL.md + README.md | 中 |
| 4 | 创建 agents/ 下三角色文件（screener / guide / judge） | 中 |
| 5 | 创建 references/ 下四知识文件 | 中 |
| 6 | 单元测试：用一篇真实论文跑完整流程 | 中 |
| 7 | CNpatent Planner 的 Phase 0 修改 | 小 |
| 8 | 文档更新（CNpatent README 提及前置 skill） | 小 |
| 9 | commit + PR | 小 |

---

## 13. 已知局限

1. **免费库检全率有限** — Phase A 只能做提示性判断，绿灯前必须走 Phase B
2. **AI 幻觉风险** — 特征对比可能读错原文，用户必须人工复核 Top 命中
3. **抵触申请覆盖不全** — 依赖 incoPat 的未公开申请检索，其他库无此功能
4. **新颖性宽限期的自我公开** — 中国不包括申请人自己的公开。如果方案来源于用户自己的论文且超过 6 个月，无法补救，需用户在输入阶段主动告知
5. **非英文非中文文献覆盖弱** — 日文、德文、俄文专利或论文漏检率较高
6. **不构成法律意见** — 最终判断须由专利代理人做正式检索 + CNIPA 审查员实质审查

---

## 14. 风险与缓解

| 风险 | 缓解 |
|---|---|
| AI 判断过于乐观（false green） | Judge 必须为绿灯引用原文段落；无引用不绿 |
| AI 判断过于悲观（false red） | 红灯必须明确指出破坏新颖性的文件号和段落，用户可申诉复议 |
| 用户不完成 Phase B | Phase C 拒绝执行，要求 Phase B 填写必需字段 |
| 检索式过窄导致漏检 | Phase A 强制至少 3 组不同的关键词块组合 |
| 语义检索幻觉 | Phase B 明确告知：incoPat 语义检索后要读完整命中列表，不是只看前 5 |

---

## 15. 开放问题

以下问题需在实施前确认：

1. **`verified_outline` schema** — 和 CNpatent Planner 现有大纲 schema 的字段如何对齐？是否需要修改 Planner 的输入格式？
2. **`user_profile.yml` 位置** — 放在 skill 目录内还是 `~/.claude/` 全局？初次运行时如何创建？
3. **测试夹具** — 是否准备 sample 论文 + 期望输出用于自测？由谁提供论文？
4. **黄灯回路版本追溯** — 用户多次调整 idea 后如何追踪版本？简单用 git，还是 skill 自己管理版本号？
5. **是否需要 Reviewer 终审** — 类似 CNpatent Phase 2 的 rubric 审查，本 skill 是否需要一个独立的 Reviewer 角色复核 judge 的决策？
6. **结构化 JSON 输出** — 是否输出结构化 JSON 供其他 skill 消费，还是只输出 Markdown？
7. **CNKI 访问是否确认** — 用户校园 IP 是否覆盖 CNKI？如果没有需降级

---

## 16. 附录：关键术语表

| 术语 | 解释 |
|---|---|
| 现有技术 | 申请日前国内外公开过的技术 |
| 新颖性 | 不属于现有技术 + 无抵触申请 |
| 创造性 | 有突出的实质性特点和显著的进步 |
| 抵触申请 | 他人在先申请后公开的文件 |
| 三步法 | 创造性判断的官方方法 |
| 最接近现有技术 | 三步法 Step 1 选出的对比文件 |
| 区别技术特征 | 本申请相对对比文件独有的特征 |
| 技术启示 | 促使本领域技术人员做某改动的提示 |
| 公知常识 | 本领域技术人员普遍知晓的知识 |
| 新颖性宽限期 | 6 个月内特定公开不破坏新颖性 |
| DWPI | Derwent 世界专利索引，人工标引的标准化摘要 |
| CLIR | PATENTSCOPE 的跨语言检索功能 |
| Prior Art Finder | Google Patents 的粘贴式现有技术检索 |

---

## 17. v1.1 架构升级（基于 2026-04-15 端到端测试反馈）

本节是 v1.0 之后的增量。上面 §1-16 保留为 v1.0 历史快照（2026-04-14 起草，以下改动来自 2026-04-15 的 real dog-food 测试）。agent 文件和 SKILL.md 已按本节的说明实装，读者如发现 §1-16 与 agent 行为有冲突，**以本节为准**。

### 17.1 动机

Round 2 真实测试（`TEST_REPORT_2026-04-15.md`）揭示了两个关键事实：

1. **Phase A 的 WebSearch 摘要存在 hallucination 风险**。VoxelMap 原论文完全没有 "anisotropic Gaussian" 字样，但 Phase A 的搜索结果摘要曾把它列为命中事实，误导了创造性预判。靠单轮 WebSearch 摘要做判断会被这类幻觉污染。
2. **AI 有能力自主全文精读公开资源**。Round 2 的关键转折是 AI 对 VoxelMap / D²-LIO / LiLi-OM / Surfel-LIO 做了全文精读，同时对 LIO-Livox 做了 git clone 源码精读。这些工作在 v1.0 被假设成"用户必须亲自做的付费库人工检索工作"——实际上 AI 在 Phase B 阶段完全可以独立执行。

v1.0 的 Phase B 定位是"用户在付费库的作业指导书"，隐含假设所有信息检索和精读都只能由用户完成。这个假设对公开资源（arXiv 全文 / GitHub 源码）是严重低估 AI 的实际能力；对真正的付费资源（incoPat 抵触申请 / CNKI 中文学位论文）则依然成立。

### 17.2 Phase B 两阶段改造

把 Phase B 拆成两个子阶段：

**Phase B.1 —— AI 自动精读公开资源（必做，AI 执行，无需用户在场）**

Guide agent 为 Phase A 的 Top 5-10 命中分别生成一张"AI 精读卡片"，卡片内容是对该命中的具体精读任务：
- 摘要-全文交叉核实卡（**所有 Top 命中必做**，修复 Issue 6 的 WebSearch hallucination 风险）
- arXiv 全文精读卡（命中是论文时）
- GitHub 源码精读卡（命中是开源项目时）

卡片由 orchestrator 在 B.1 阶段派发给 `subagent_type="general-purpose"` 的子 agent 执行（模型 sonnet，不需要 opus）。执行结果直接写入 `4_manual_search_template.md` 的"命中 #N · B.1 全文核实"字段。

**产物预期**：Phase A 的疑似命中被升级为"原文锚定 / 源码锚定"或"Phase A 摘要 hallucination，不采信"。两种结论都比单轮 WebSearch 摘要可信。

**Phase B.2 —— 用户人工付费库（必做，用户执行）**

v1.0 原有的 incoPat + 抵触申请 + CNKI 工作流**不变**。这是 AI 无法做的工作：
- incoPat 的 Boolean / IPC 精确检索和语义检索需要登录态
- incoPat 的抵触申请（未公开申请）检索是本 skill v1.0 的独特价值
- CNKI 的中文学位论文 + 会议论文覆盖是 Scholar / arXiv 替代不了的

**Phase B.3 —— 合并进 Phase C**

两个子阶段的产物都落到同一个 `4_manual_search_template.md`，Phase C Judge 读 template 时不需要区分来源，按命中类型（专利 / 论文 / 源码）做新颖性和创造性判断。v1.0 的 Judge 判断逻辑（§9）完全不需要改。

### 17.3 Issue 4 — 发明名称英文品牌词硬规则

测试中 "一种 LIO-Livox..." 的 Livox 是 DJI 旗下的品牌，4 个 Writer 全部原样沿用，Phase 0 也没拦截。品牌词在权利要求书阶段会破坏保护范围（专利保护技术方案本身，不能依赖特定品牌），且易引起商标争议。

**两层防御**：

- `agents/cnpatent-noveltycheck-screener.md` 步骤 10 的硬约束列表加一条：发明名称不得含英文品牌词。正则: 连续 3 个以上 ASCII 字母视为英文词，通用术语缩写（SLAM / LIDAR / GPS / UAV / CPU / GPU / ARM 等）在白名单内。
- `agents/cnpatent-noveltycheck-judge.md` 在写入 `5_verified_outline.md` 前对发明名称做复校验，发现品牌词 → 用功能性描述替换（如 "Livox 激光雷达" → "非重复扫描固态激光雷达"），并在绿灯触发提示里告知用户。

### 17.4 对文件的影响

| 文件 | 改动 |
|---|---|
| `SKILL.md` Phase B 节 | 描述改成两阶段（B.1 AI + B.2 用户），添加 Phase B.1 的执行协议 |
| `agents/cnpatent-noveltycheck-guide.md` | 插入一步"生成 Phase B.1 AI 精读卡片"；现有 incoPat / CNKI 卡片步骤归入 Phase B.2 大节；时间预算表增加"执行者"列区分 AI 和用户；详细卡片模板下沉到 `references/phase-b1-ai-read-cards.md` |
| `agents/cnpatent-noveltycheck-screener.md` | 步骤 10 硬约束列表加发明名称品牌词禁令 + Anti-pattern 新增一条 |
| `agents/cnpatent-noveltycheck-judge.md` | 插入新步骤 8 "发明名称复校验"，原步骤 8 顺延为步骤 9 |
| `references/phase-b1-ai-read-cards.md` | 新增。三种 B.1 卡片模板 + 回填字段 schema + 派发协议 + Anti-patterns |

### 17.5 向后兼容

v1.1 的改动没有破坏性：

- `user_profile.yml` schema **不变**
- `5_verified_outline.md` schema **不变**（九、查新验证元信息的字段集合一致）
- `4_manual_search_template.md` **追加**"B.1 全文核实"字段，原有的 B.2 用户填写字段位置不动，用户仍可在同一张表里填写
- CNpatent skill 不需要任何改动（v1.1 仅影响 noveltycheck skill，不影响下游写作 skill）

Phase C Judge 的判断逻辑完全兼容：B.1 产物只是让命中的"是/否/部分"判定多了一层原文锚定依据，不改变判据本身。

### 17.6 未覆盖

v1.1 仍未解决的已知问题（继续延后）：

- **红灯路径没测**：mock 一份 Judge 判定"区别特征在最接近现有技术里全命中"的数据做红灯 smoke test
- **Phase 0 校验失败路径没测**：删除 `5_verified_outline.md` 里的"九、查新验证元信息"字段，验证 CNpatent 拒绝执行的分支
- **Writer 额度降级**（Issue 2）：4 Writer 并行用 opus 时撞限额的降级策略暂不处理

下一次 round 3 端到端测试建议用**不同领域的论文**（非 SLAM/UAV），验证 v1.1 的 B.1 + 品牌词拦截不会在新领域回归。

---

---

## 18. v1.2 Phase B.2 Playwright 自动化（2026-04-17）

本节是 v1.1 之后的增量。v1.1 的 Phase B.2 仍要求用户在 incoPat / CNKI 里手动检索 70-110 分钟；v1.2 把这部分改为 AI 驱动的 Playwright 浏览器自动化，用户仅需登录（~5 分钟）。

### 18.1 动机

2026-04-16 端到端测试用 Playwright MCP 驱动 Chromium 完成了整个 B.2 流程：

| 通道 | 查询数 | 总命中 | 入选 |
|---|---|---|---|
| incoPat T1 命令检索 | 4 | 2871 | 21 |
| incoPat T2 语义检索 | 1 | — | 3 |
| incoPat T3 抵触申请 | 1 | 22799 | 1 (CN121860589A) |
| CNKI T6 | 3 | 236 | 7 |
| Scholar T4 | 3 | — | 5 |
| arXiv T5 | 2 | — | 5 |

全程用户仅需在 Playwright 浏览器窗口中登录。核心发现：incoPat 的 `#textarea` 是 contentEditable div，需用 InputEvent 注入；选择性 DOM 提取（`#graphicTable .patent_information`）把 20 行结果压缩到 ~3k token（全页 HTML ~50k，压缩率 94%）。

### 18.2 架构变更

v1.1 → v1.2 的关键变化：**所有 6 个检索通道都改为后台 subagent 执行**，主 session 只做派发 + 合并。

```
Phase B (v1.2)
│
├── B.1 AI 自动精读（不变）
│
├── B.2 用户登录（~5 分钟）
│   Playwright 启动浏览器 → 用户开 4 标签页 + 登录 → 确认
│
├── B.2 AI 后台 subagent 自动检索（6 通道并行）
│   ┌─ Playwright subagent ──────────────────────────┐
│   │  T1-agent: incoPat 命令检索 × 3-4 条 (tab 0)   │
│   │  T2-agent: incoPat 语义检索 × 1 条  (tab 1)    │
│   │  T3-agent: incoPat 抵触申请 × 1 条  (tab 2)    │
│   │  T6-agent: CNKI 高级检索 × 2-3 条   (tab 3)    │
│   └────────────────────────────────────────────────┘
│   ┌─ WebSearch subagent ───────────────────────────┐
│   │  T4-agent: Google Scholar × 2-3 条             │
│   │  T5-agent: arXiv × 2 条                       │
│   └────────────────────────────────────────────────┘
│   每个 subagent 独占一个 tab/通道，写 JSON 后返回摘要
│
├── B.2 合并
│   orchestrator 读 JSON → 评分 → 去重 → 写 template
│
└── → Phase C（Judge 逻辑不变）
```

### 18.3 三层分离架构

| 层 | 职责 | 产物 |
|---|---|---|
| Guide agent | 读 Phase A → 构造检索表达式 | 执行计划（query expressions） |
| scripts/playwright/*.js | 固化 DOM 注入/提取模式 | 可复用的 JS 脚本 |
| 后台 subagent | 读执行计划 + 读脚本 → 驱动 Playwright | JSON 结果文件 |
| orchestrator（主 session） | 派发 subagent + 读 JSON + 合并评分 | 填好的 template |

DOM 操作固化为 7 个独立 JS 脚本（`scripts/playwright/`）。subagent 通过 Read 读取脚本 → 替换占位符 → `browser_evaluate(scriptContent)` 执行。脚本使用 `() => { ... }` 格式（Playwright MCP 要求的箭头函数格式）。

### 18.4 Playwright DOM 模式（关键发现）

**incoPat**：
- 命令检索输入：`#textarea`（contentEditable div），需 InputEvent 注入
- 搜索按钮：`input.retrieval`，init 页 2 个可见（btns[1] = 命令检索），结果页 1 个可见
- 结果提取：`#graphicTable .patent_information`，字段从 innerText 正则提取
- 总数：`#totalCount`（文本 "共N条"）
- 排序：`#sortText` → `#AD_DESC` → `input.retrieval[value*="确定"]` 可见按钮
- 语义检索：`#querytext`（标准 textarea），`#semanticButton`
- AD 日期范围：正确语法 `AD="YYYYMMDD,YYYYMMDD"`

**CNKI**：
- 输入：`textarea.textarea-major`
- 搜索：`input.btn-search`
- SU= 语法需拆短词（长词组分词差）
- 可能出现滑块验证码（用户手动处理）

### 18.5 降级策略

| 触发条件 | 行为 |
|---|---|
| `playwright.mcp_available: false` | 直接走 v1.1 用户手动路径 |
| `mcp_available: true` 但运行时不可用 | 自动检测 → 降级 + 警告 |
| 某个通道执行失败 | 该通道降级为用户手动 + 其他通道继续 |

降级由 `user_profile.yml` 的 `playwright:` 配置段控制。

### 18.6 token 预算

| 操作 | 预估 token |
|---|---|
| 单次注入 + 提取 20 行 | ~3-4k |
| 全页 HTML（未优化） | ~50k |
| 压缩率 | ~94% |
| 6 通道 × 平均 2 查询 | ~30-40k 总计 |

### 18.7 对文件的影响

| 文件 | 改动 |
|---|---|
| `SKILL.md` | Phase B.2 节重写 + 暂停点重写 + 新前置依赖 |
| `agents/cnpatent-noveltycheck-guide.md` | Steps 4-8 改为双模输出（Playwright 执行指令 / v1.1 用户卡片） |
| `scripts/playwright/*.js`（新增） | 7 个 DOM 操作脚本 + README |
| `user_profile.yml` | 新增 `playwright:` 配置段 |
| `agents/cnpatent-noveltycheck-judge.md` | 步骤 1 验证微调 |
| `references/templates.md` | B.2 自动填写标记 |

### 18.8 向后兼容

- `5_verified_outline.md` schema **不变** — CNpatent 下游完全不受影响
- `4_manual_search_template.md` schema **不变** — 字段相同，仅填写者从用户变为 AI
- Phase C Judge 判断逻辑 **不变**
- `user_profile.yml` **追加** playwright 段 — 老配置无此段时自动降级

### 18.9 踩坑记录

1. incoPat `AD<=YYYYMMDD` 和 `AD=[date,date]` 触发字符位置解析错误 → 正确语法 `AD="YYYYMMDD,YYYYMMDD"`
2. incoPat 结果页 `input.retrieval` 只 1 个可见（init 页有 2 个）→ 脚本已处理两种情况
3. incoPat 每次新查询前必须 `browser_navigate` 回 `/advancedSearch/init` 重置
4. CNKI `SU='路面病害'` 返回 0 条 → 拆成 `(SU='路面' OR SU='隧道') AND (SU='病害' OR SU='裂缝')`
5. CNKI Cookie 同意遮罩拦截点击 → `cnki_dismiss_overlay.js` 先关闭
6. CNKI 滑块验证码无法自动化 → 用户手动处理
7. Playwright MCP `browser_evaluate` 要求 `() => { ... }` 箭头函数格式（非 IIFE）

---

以上为 DESIGN.md v1.0 + v1.1 补丁 + v1.2 补丁。v1.0 章节（§1-16）为历史快照；v1.1（§17）、v1.2（§18）和 v1.2.1（§19）是当前实装版本的权威说明。

---

## 19. v1.2.1 Phase B.2 自主登录 + 同族合并落地（2026-04-17）

本节是 v1.2 的增量补丁。v1.2 首次上线时有两个遗留问题：(a) 登录完全由用户手动完成，AI 没做任何尝试；(b) 文档反复声明"同族合并必做"，但代码里没实现，orchestrator 的"→ 合并 → 去重"只是一行口头约束。v1.2.1 把这两件事落地。

### 19.1 AI 自主登录：IP 登录机制

**设计原则**：incoPat 和 CNKI 两大付费库都支持基于 IP 段的自动认证——机构/校园 IP 访问时站点后端直接派发登录态 cookie，无需表单、无需密码、无需点按。Phase B.2 的"AI 自主登录"就是让 Playwright 直接利用这个机制。**不做基于账号密码的表单登录**（凭据管理、验证码、风控规则都是坑，得不偿失）。

**三种 IP 场景**：

| 场景 | Playwright 出口 IP | 配置 |
|---|---|---|
| Claude Code 跑在校园网内 | 天然是校园 IP | `proxy_server: null`，什么都不用配 |
| Claude Code 在校外 + 有校园 VPN/代理 | 校园 VPN 出口 | `proxy_server: http://proxy.univ.edu:8080`；启动 MCP 时加 `--proxy-server` 参数 |
| Claude Code 在校外 + 无代理 | 任意公网 IP | IP 登录必然失败，退回用户手工登录（可让用户通过浏览器开发者工具复制 cookie 继续，但当前版本不支持） |

**启动 MCP 带代理的命令**：

```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest \
  --proxy-server=http://proxy.university.edu:8080
```

Playwright MCP 的代理是 **browser-launch-level** 配置，由 MCP server 启动参数决定，运行时无法切换。skill 只负责在 `user_profile.yml` 里记录这个参数（供用户参考 + orchestrator 提示），不会自动重启 MCP。

**验证层 —— check_login 脚本**：

IP 登录是否真正生效，通过"目标页的工作元素能否加载"验证：

| 脚本 | 判定逻辑 |
|---|---|
| `incopat_check_login.js` | navigate 到 `/advancedSearch/init` 后 `#textarea` 存在 + URL 未重定向到首页 → IP 登录成功 |
| `cnki_check_login.js` | navigate 到 CNKI 高级检索后检索 textarea 就绪 + CAPTCHA 未出现 → IP 登录成功 |

**为什么用工作元素做判据而不是找 `.user-info` 选择器**：
1. incoPat/CNKI 改 class 命名的频率远高于改"登录后能看到什么页面"
2. "能不能用"是终极业务信号，比"是否显示用户头像"更稳
3. 未登录时 incoPat 直接硬重定向到首页——`#textarea` 不存在是确定性信号

**orchestrator 协议**（SKILL.md Phase B.2 步骤 3 插入）：

```
3. IP 登录 + 验证 (v1.2.1):
   a. 读 user_profile.yml auto_login 段
      - enabled=false → 跳到步骤 4 (用户手工登录)
      - proxy_server 非空 → 打印 "依赖代理 ${proxy_server}, 请确认 MCP 启动时已加 --proxy-server"
   b. orchestrator browser_tabs new × 4 + browser_navigate (4 个 URL)
   c. 每 tab browser_evaluate *_check_login.js
   d. verify_tabs=all → 4/4 logged_in=true 才算成功
   e. 成功 → 跳过用户提示, 步骤 5
   f. 失败 → on_failure=manual_prompt 时退回步骤 4, abort 时终止
```

**降级路径**：任一 tab IP 登录失败 → 退回 v1.2 的用户手动模式，用户体验不退化。成功时省掉 5 分钟等待。

**不做的事**：
- 不写表单登录脚本（`*_account_login.js`）——账号密码链路风险远大于收益
- 不实现 cookie 导入（从用户浏览器拷 cookie）——v1.2.1 先保持简单
- 不自动切换代理——这是 MCP server 启动级配置，skill 改不动

### 19.2 同族合并落地

**问题**：v1.2 的 `incopat_extract.js` 只把 "中国同族" 当 tag token 过滤掉，根本没抓申请号（AN），也没记录同族数量。orchestrator 的 "→ 合并 → 去重" 步骤没有具体算法，实际执行时只能按 pn 做粗去重，真正的同族合并从未发生。

**v1.2.1 修复**：

1. **extract 层**：`incopat_extract.js` 新增三字段
   - `an`: 完整申请号（如 `CN202410012345.6`）
   - `family_key`: 申请号去标点后前 10 位（如 `CN20241001`）——作为同族分组键
   - `family_tag` / `family_count`: 解析 "中国同族 N" 或 "全球同族 N" 标签

2. **orchestrator 层**：新文件 `references/phase-b2-merge-rules.md` 定义完整合并算法
   - Step 1: 通道内同 pn 去重
   - Step 2: 跨通道同 pn 合并（取最高评分）
   - Step 3: 同族合并
     - 强同族：`family_key` 相同 或 `an` 相同
     - 弱同族（启发式）：`applicant` 一致 + `ad` ≤ 7 天 + `title` 相似度 ≥ 80%
     - 保留 `pd` 最晚的条目作为代表
   - Step 4: Phase A 去重（只打标，不移除）
   - Step 5: 非专利按 url / title 去重

3. **文档侧**：SKILL.md 的 orchestrator 协议步骤 7 直接引用 `phase-b2-merge-rules.md`，不再是一行"合并→去重"。

**为什么同族用 family_key 前 10 位**：CN 专利申请号格式为 `CN YYYYNN NNNNNNN.X`（年份 + 顺序号 + 校验位）。前 10 字符 `CN + 年 + 6 位顺序号` 足以锁定一个申请。族内不同公开号（A → B → C 对应公开→授权→再授权）共享同一 AN，自然共享同一 family_key。这个启发式比让 LLM 自己判断"是否同族"稳定得多，也不需要调外部 family 数据库。

**为什么不做 UI 侧合并同族**：incoPat 有 "合并同族" 按钮，但点了之后每行只显示一个代表，丢掉了对其他族成员的可见性——后续 Phase C Judge 如果想看某个族的最早优先权日就拿不到。保留原始结果 + orchestrator 侧计算代价很低（O(n)），拿到的信息最全。

### 19.3 反模式（v1.2.1）

| 反模式 | 后果 |
|---|---|
| check_login 用 `.user-info` 类选择器 | incoPat 改 class 命名就失效 |
| 把同族判定塞给 subagent | 同族是跨通道问题，单通道 subagent 看不到全局，必须 orchestrator 做 |
| 同族用 IPC 分组 | 同发明多 IPC，不同发明也可能共享 IPC，彻底错 |
| 弱同族阈值过宽 | title 相似度 < 80% 或 ad 差 > 7 天就合并，会把不同发明错并成一族 |
| 自主登录失败时阻塞 | 任一 tab 失败立刻退回手动模式，不重试不卡住 |
| 跨通道评分取平均 | 取最高值——高分说明至少一个通道确认强相关，平均会稀释这个信号 |

### 19.4 文件影响

| 文件 | 变更 |
|---|---|
| `scripts/playwright/incopat_check_login.js` | **新建** |
| `scripts/playwright/cnki_check_login.js` | **新建** |
| `scripts/playwright/incopat_extract.js` | 增加 an / family_key / family_tag / family_count 字段 |
| `references/phase-b2-merge-rules.md` | **新建** 合并算法 |
| `user_profile.yml` | playwright 段新增 auto_login 子段 |
| `SKILL.md` | Phase B.2 orchestrator 协议插入步骤 3（自主登录） + 人类工作时段改为双路径 |

### 19.5 向后兼容

- `4_manual_search_template.md` schema 不变（B.2 字段多了 `family_members` / `hit_channels`，但 Phase C Judge 不读这些字段也不报错）
- `5_verified_outline.md` 不变
- v1.2 的 7 个脚本全部保留，仅 `incopat_extract.js` 向后兼容扩展字段
- `auto_login.enabled: false` 时行为与 v1.2 完全一致

---

以上为 DESIGN.md v1.0 + v1.1 + v1.2 + v1.2.1 补丁。v1.0 章节（§1-16）为历史快照；v1.1（§17）、v1.2（§18）、v1.2.1（§19）是当前实装版本的权威说明。
