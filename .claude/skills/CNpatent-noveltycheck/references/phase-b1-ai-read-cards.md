# Phase B.1 —— AI 自动精读卡片模板

本文件是 `agents/cnpatent-noveltycheck-guide.md` 的下沉模板库。v1.1 把 Phase B 拆成 B.1（AI 执行）+ B.2（用户执行）两个子阶段；Guide agent 在生成 Phase B.2 用户卡片的同时，为 Phase A 的 Top 5-10 命中生成 Phase B.1 的 AI 精读卡片。本文件提供三种卡片的模板和执行规范。

## 为什么要 Phase B.1

2026-04-15 端到端测试（见 `TEST_REPORT_2026-04-15.md` Issue 6 / Issue 7）暴露了两个结构性问题：

1. **Phase A WebSearch 摘要存在 hallucination 风险**：测试中 Phase A 的搜索摘要曾把 VoxelMap 论文的 "anisotropic Gaussian" 列为命中事实，而原论文里根本没有这个术语。只靠摘要做创造性预判会被这类幻觉污染。
2. **AI 有能力自主全文精读公开资源**：同一次测试里，AI 对 VoxelMap / D²-LIO / LiLi-OM / Surfel-LIO 做了全文精读，并对 LIO-Livox 做了 git clone 源码精读，这次精读把创造性风险从"中-高"下调到"低"，是 Round 2 走绿灯的关键转折。v1.0 把这类工作假设成"用户必做的付费库人工检索"是严重低估了 AI 的实际能力。

Phase B.1 把能自动化的部分从人类工作时段搬到 AI 执行时段，只留下真正只能由用户登录付费库才能完成的工作（incoPat 抵触申请 / CNKI 中文学位论文）给 Phase B.2。

## 卡片类型一览

| 卡片 | 适用命中 | 目的 |
|---|---|---|
| **摘要-全文交叉核实卡** | 所有 Top 5-10 命中（必做，Issue 6） | 防止 Phase A WebSearch 摘要 hallucination 污染后续判断 |
| **arXiv 全文精读卡** | 命中是 arXiv / openaccess 论文 | 全文定位区别特征的原文依据 |
| **GitHub 源码精读卡** | 命中是 GitHub 开源项目 | git clone + grep 源码锚定特征实现 |

执行者在三种卡片里都是 AI 子 agent（不是用户）。Guide 不执行卡片，只生成卡片文本；orchestrator 在 B.1 阶段负责派发子 agent。

## 卡片模板

### 1. 摘要-全文交叉核实卡

对每个 Phase A Top 5-10 命中**必做**一张。核心任务：核实 Phase A 报告里对该命中的关键声称在原文中是否真正存在。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【B.1 必查】摘要-全文交叉核实：命中 #N
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
命中类型:   论文 / 专利 / 源码
来源:       <arXiv ID / 专利号 / GitHub URL>
标题:       <从 1_auto_novelty_report.md 命中 #N 读>

Phase A 关键声称（逐条抄自 1_auto_novelty_report.md 命中 #N 的摘要）:
  1. <声称 1，如 "VoxelMap 使用各向异性高斯对 voxel 进行建模"> 
  2. <声称 2>
  3. ...

核实任务：对每条声称给出判定（支持 / 部分支持 / 不支持）。

执行步骤：
  1. 根据命中类型获取全文：
     - arXiv → WebFetch arXiv HTML 版 (arxiv.org/html/<id>) 或 abs 页
     - 专利 → WebFetch Google Patents 详情页
     - GitHub → Bash: git clone --depth 1 + Grep/Read
  2. 对每条关键声称：
     a. 提取该声称里的名词或术语（如 "anisotropic Gaussian"）
     b. 在全文或源码里搜索该术语
     c. 判定：
        - 找到原文证据 → "支持"，记录段落号或文件:行号
        - 找到相似但不一致的证据 → "部分支持"，记录差异
        - 完全找不到 → "不支持"，明确说明 Phase A 摘要是 hallucination
  3. 在 4_manual_search_template.md 的"命中 #N · B.1 全文核实"字段里填：
     - 声称 1: 支持/部分支持/不支持 + 原文证据
     - 声称 2: 同上
     - ...
  4. 如任意声称判为"不支持"，在该命中旁加 🚨 标记，并在命中记录的"全文核实结论"里写明："该命中的 Phase A 摘要存在幻觉，<说明>，建议在 Phase C Judge 判断时不采信此命中的 Phase A 描述"

停止准则：所有 Phase A 关键声称都有"支持 / 部分支持 / 不支持"判定
预计耗时：5-10 分钟/命中
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. arXiv 全文精读卡

命中是 arXiv 论文或 openaccess 论文时生成。重点从 Phase A 的"摘要级印象"升级到"Method 节原文级锚定"。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【B.1 必查】arXiv 全文精读：命中 #N
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
论文 ID:    arXiv:XXXX.YYYYY
HTML URL:   https://arxiv.org/html/XXXX.YYYYY
标题:       <从 Phase A 报告读>

精读重点（从 2_candidate_outline.md 的区别技术特征列表抽）:
  - 区别特征 A: <从候选大纲读>
  - 区别特征 B: <从候选大纲读>
  - 区别特征 C: <从候选大纲读>
  - ...

执行步骤：
  1. WebFetch arXiv abs 页，读 Abstract + Introduction，判断是否值得继续
     （若 Abstract 里完全无相关术语 → 标为"相关度低"，跳过全文精读，直接填 template）
  2. WebFetch arXiv HTML 版，重点读 Method / Approach 节和 Experiments / Results 节
  3. 对每个区别特征，在 Method 节里搜索对应术语（中英双语都试）：
     - 找到原文实现 → 判"是"，引用 Section 号 + 段落文字
     - 找到相关但不等同的实现 → 判"部分"，说明差异
     - 完全找不到 → 判"否"，该特征具备区别性
  4. 填 4_manual_search_template.md 的"命中 #N · 特征对照"表：
     | 本方案特征 | 该文件是否公开 | 原文依据 |
     |---|---|---|
     | 区别特征 A | 是/否/部分 | Section X, page Y, "<原文引用>" |
     ...

停止准则：所有区别特征都给出"是 / 否 / 部分"判定，并附原文引用（"部分"和"是"必须带引用，"否"可不带）
预计耗时：10-15 分钟/命中
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. GitHub 源码精读卡

命中是 GitHub 开源项目时生成。直接 git clone 源码，用 grep 搜关键字，Read 命中文件定位实现位置。

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【B.1 必查】GitHub 源码精读：命中 #N
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
仓库:       github.com/<owner>/<repo>
分支/tag:   main (或 Phase A 指定的版本)
本地路径:   /tmp/b1_<repo_name>

精读重点（从 2_candidate_outline.md 的区别技术特征列表抽）:
  - 区别特征 A: <从候选大纲读>
  - 区别特征 B: <从候选大纲读>
  - ...

执行步骤：
  1. Bash: git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/b1_<repo_name>
     （--depth 1 是硬性要求，避免拖全部 history 占磁盘和带宽）
  2. 对每个区别特征，用中英双语关键词在源码里 grep：
     - 例：本方案"各向异性体素" → Grep "anisotropic|asymmetric|non[_\-]uniform" --type=cpp,c,h,py
     - 例：本方案"分层退化判据" → Grep "degener|layered|hierarch" --type=cpp,c,h,py
     - 例：本方案"类级动态权重" → Grep "class.*weight|per_class|category.*weight" --type=cpp,c,h,py
  3. 对每个 grep 命中，Read 源码文件，定位到实现位置，判断是否等同于本方案的该区别特征：
     - 完全等同 → 本方案该特征被公开（"是"）
     - 部分实现或形似而神不似 → "部分"，记录差异
     - 零命中 → 本方案该特征未公开（"否"），是有效区别特征
  4. 填 4_manual_search_template.md 的"命中 #N · 源码对照"表：
     | 本方案特征 | 源码状态 | 源码锚点 | 实现差异 |
     |---|---|---|---|
     | 区别特征 A | 是/否/部分 | <file:line> 或 "零命中" | <简要描述> |
     ...
  5. 清理：Bash: rm -rf /tmp/b1_<repo_name> （避免长期占磁盘）

停止准则：所有区别特征都有源码锚点或"零命中"结论
预计耗时：15-25 分钟/命中（取决于仓库大小和特征数量）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 回填模板字段（加入 4_manual_search_template.md）

B.1 产物写入命中记录的以下新增字段。B.2 用户填写的字段保持不变。

```markdown
### 命中 #N · B.1 全文核实（由 AI 子 agent 填写）

**Phase A 声称核实**：
- 声称 1 <引原文>: 支持 / 部分支持 / 不支持（原文证据: <段落号 / 文件:行号 / "零命中">）
- 声称 2 <引原文>: 同上
- ...

**区别特征全文对照**（arXiv/论文类命中）：

| 本方案特征 | 是否公开 | 原文依据 |
|---|---|---|
| 区别特征 A | 是/否/部分 | Section N, "<引文>" |
| ... | | |

**区别特征源码对照**（GitHub 类命中）：

| 本方案特征 | 源码状态 | 源码锚点 | 实现差异 |
|---|---|---|---|
| 区别特征 A | 是/否/部分 | `<file:line>` 或 "零命中" | <描述> |
| ... | | | |

**全文核实结论**：
- [ ] Phase A 摘要全部支持，命中有效
- [ ] Phase A 摘要部分不支持，命中需重新评估：<说明>
- [ ] Phase A 摘要 hallucination，命中不采信：<说明>

**执行元信息**：
- 执行 agent: <sub-agent-id>
- 执行时间: <YYYY-MM-DD HH:MM>
- 命中类型: 论文 / 专利 / 源码
```

## Guide agent 生成卡片的规则

1. **Top 5-10 命中每个都必须生成一张交叉核实卡**。这是 Issue 6 的修复点。
2. **命中类型识别**：
   - 来源字段含 `arxiv.org` / DOI / 论文 ID → arXiv 全文精读卡
   - 来源字段是 `github.com/...` → GitHub 源码精读卡
   - 来源字段是 Google Patents / CNIPA / PatentScope 专利号 → **只生成交叉核实卡**，不生成专利全文精读卡（专利全文的结构化解析交给 Phase B.2 的 incoPat 人工检索更可靠）
3. **卡片内容必须具体到命中号**：不要生成"对所有命中做精读"的通用卡片，每张卡片都显式写出命中号 / 来源 URL / 精读重点字段。
4. **精读重点**必须抄自 `2_candidate_outline.md` 的区别技术特征列表，不得自编。

## orchestrator 派发协议

Guide agent 把生成的卡片写入 `3_manual_search_guide.md` 的第一大节（标题 `# Phase B.1 AI 自动精读卡片 (必做)`）。orchestrator 在 Guide 返回后：

1. 读 `3_manual_search_guide.md` 第一大节，逐张卡片提取
2. 对每张卡片，`Agent` 工具派发一个子 agent：
   - `subagent_type="general-purpose"`
   - `prompt` = 卡片全文 + "执行完后直接写入 `4_manual_search_template.md`"
   - `model="sonnet"`（精读不需要 opus，sonnet 对全文提取够用；交叉核实任务也只是关键词搜索）
3. 所有子 agent 在同一条消息里并行派发（最多 10 个）
4. 所有子 agent 完成后，orchestrator 继续进入"人类工作时段"提示 Phase B.2

## Anti-patterns

1. **跳过摘要-全文交叉核实卡** —— 错。每个 Top 命中都必须有一张，否则 Phase A hallucination 会继续污染 Phase C 判断。
2. **Guide agent 自己执行精读** —— 错。Guide 只生成卡片，不执行。执行在 orchestrator 派发的子 agent 里完成，这是为了让 Guide 的输出保持"可查验的卡片集合"而不是一个黑盒的预读结果。
3. **卡片模板化不够具体** —— 错。每张卡片必须显式写命中号、来源、精读重点，用户打开 `3_manual_search_guide.md` 时一眼能看到"卡片 3 要精读 arXiv:2501.13876"。
4. **git clone 不加 --depth 1** —— 错。完整 history 对源码精读是冗余数据，会严重占用磁盘和带宽。
5. **用 opus 跑 B.1 子 agent** —— 错。B.1 是结构化的信息提取任务，sonnet 足够，opus 浪费配额。
6. **把 Phase B.1 结果写到 `3_manual_search_guide.md` 而不是 template** —— 错。guide 是"任务卡片集合"，template 是"结果记录表"。Phase C Judge 读的是 template。
