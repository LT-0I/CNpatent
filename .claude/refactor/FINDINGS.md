# 评审发现（Findings）

10 个 Finding，来自用户 5 轮质疑 + 工程评审方法论。每条带严重度、置信度、源头、修订方向、影响 PR。

严重度：P0（必改，影响正确性）/ P1（应改，影响质量或维护）

---

## Finding 1 — 重构过度革命化

**Severity: P1 · Confidence: 9/10**  
**源于**：用户质疑 1（3 个 skill 虽臃肿但不能过度删减）

### 诊断
初版方案"瘦身 / 简化"措辞危险。**结构重组**（移到 kit、拆长文件）和**机制删除**（去掉检测器、改 gate 逻辑）是两回事，不能混为一谈。

### 初版错误
- 提出 14 个 skill 大拆重写
- 对老 humanizer 说"瘦身"，没说具体保留哪些、丢弃哪些
- 没有区分可逆变动（移位置）与不可逆变动（删代码）

### 修订方向
- 用 **MVM（Mechanism Verification Manifest）** 替代隐性的"瘦身"
- 每个老机制先挂"未核验"状态，实验证明有效才采纳
- **Strangler Fig** 演进：新 skill 包装旧脚本/规则，老 skill 归档不删
- 决策 2A：老 skill 保留半年

### 影响 PR
- PR #1（MVM 清单）
- PR #9（humanize 机制核验）
- PR #12（老 skill 归档）

---

## Finding 2 — 查新缺精读层

**Severity: P0 · Confidence: 10/10**  
**源于**：用户质疑 2（高相关度命中必须精读才能判断是否破坏新颖性）

### 诊断
初版"全部卡片化（50 字摘要）"一刀切方案**在三步法判定阶段无法工作**：
- 三步法 ① 确定最接近现有技术 → 需全文
- 三步法 ② 确定区别技术特征 → 需逐特征对比
- 三步法 ③ 判断显而易见性 → 需实施例级精读

卡片是筛选工具，不是判定工具。

### 修订方向：三层阅读
```
L0  raw hits jsonl         50 条，落盘不进 context
L1  卡片（~200 字/条）     50 × 200 字 = 10KB（shortlist 用）
L2  精读卡（2-3KB/条）     top 3-5 × 2.5KB = 12KB（judge 用）
所有层级缓存到 state/<run-id>/refs/，ref_id 去重
```

### Token 复核
- shortlist：~10K
- judge（含精读）：~12K 新增
- 总查新：25-30K（对比现状 200K+）
- 仍然 6-8 倍节省，但不牺牲判定质量

### 影响 PR
- PR #10（新增 `/cnpatent-deepread`）

---

## Finding 3 — corrections.jsonl 不足以"永久学会" ⚠️ 最关键

**Severity: P0 · Confidence: 9/10**  
**源于**：用户质疑 3（手改 docx → AI 学习 → 不再手改 的意图）

### 诊断
初版 `corrections.jsonl` + few-shot 注入方案**达不到用户"永久学会、不再反复"的期望**：
- few-shot 是模式匹配，不是规则内化
- 积累到 200 条就装不下，必须 retrieval
- retrieval miss → 同类错误再犯
- 用户期望：改一次、永不再犯 → few-shot 无法保证

### 用户原做法的本质
- ✅ 正确意图：规则要固化、持久、显式
- ❌ 错误实现：让 AI 整块重写 skill md，导致补丁叠补丁

### 修订方向：两层学习 + 人审晋升
```
Layer 1: corrections.jsonl   (原始日志，append-only)
              ↓
         /cnpatent-learn
              ↓
         聚类条件触发
              ↓
         /cnpatent-consolidate (手动，决策 1A)
              ↓
         AI 提议新规则 + 证据
              ↓
         AskUserQuestion 人审晋升
              ↓
         跑 golden 回归验证
              ↓
Layer 2: learned-rules.md    (晋升规则，只追加)
```

**为什么能真正学会**：
- 规则每次都全量加载，不靠 retrieval
- 规则是显式文字约束，不是 example
- 一条规则永久覆盖一类错误
- 规则可读、可审、可单条回滚

### 影响 PR
- PR #5（learn + consolidate）
- PR #6（revise 输出 revision_plan 带 decision）
- PR #7+（write 加载 learned-rules.md 作为硬约束）

---

## Finding 4 — 测试策略：训练数据即黄金集

**Severity: P0 · Confidence: 9/10**  
**源于**：用户补充"用 PDF 做 ground truth 训练"

### 诊断
每跑一份 PDF 训练，天然产生三份对应文件：
- extracted_outline.md（抽的核心点）
- 原 PDF 正文各章节（ground truth）
- ai_draft.md（AI 写的）

这就是一个 **golden test case**。不充分利用是浪费。

### 修订方向
```
cnpatent-kit/tests/golden/
├── training-corpus/<patent_id>/    每份 PDF 训练都保留
│   ├── source.pdf
│   ├── extracted_outline.md
│   ├── ground_truth_sections/
│   └── corrections_generated.jsonl
├── regression/                     老 correction 回归
├── rule-application/               新规则适用 case
├── no-overreach/                   不误伤正常文本
└── template-roundtrip/             canonical ↔ template 双向验证
```

每次改规则/prompt/检测器，跑 training-corpus 重新评分。

### 影响 PR
- PR #1（tests/ 骨架）
- PR #5（consolidate 晋升前跑 golden）
- PR #13（训练产物自动归档）

---

## Finding 5 — docx 模板耦合

**Severity: P0 · Confidence: 10/10**  
**源于**：用户补充 "每个人都有自己的 docx 模板"

### 诊断
当前 cnpatent_docx.py 对一个固定模板硬编码（段落锚点、样式名、公式占位符）。换模板就崩。用户说"每个人都有自己的模板"，这是硬需求。

### 修订方向
模板学习做成安装期一次性"编译"步骤，**产出模板专属 build 脚本**：
```
用户 template.docx
     ↓
/cnpatent-template-setup（对话式）
     ↓
cnpatent-kit/templates/<fingerprint>/
  ├── template.docx
  ├── template.meta.json     结构 + canonical 映射
  ├── build_docx.py          1:1 生成
  ├── verification.md
  └── verification_sample.docx
```

### 关键性质
- 一个模板 = 一个 fingerprint = 一个 build_docx.py
- 换模板 = 重跑 setup，不改任何 skill 代码
- 支持多模板并存，按 active_template 切换

### 影响 PR
- PR #2（template-setup 核心）
- PR #11（build 调用对应脚本）

---

## Finding 6 — 两类参考资料必须分开处理

**Severity: P1 · Confidence: 9/10**  
**源于**：用户补充"第一份资料是代理人范本（指令型文档）"

### 诊断
代理人范本**不是** ground truth 专利，而是指令型文档（"此处写技术领域"）。如果当 ground truth 处理，AI 会写出"此处写..."的指令腔。

### 修订方向：明确两类

| 类型 | 性质 | 学什么 | 处理 | 消费方 |
|------|------|-------|------|--------|
| A 真实专利 | ground truth | 书写风格 | diff → correction | learned-rules.md |
| B 代理人范本 | 指令型 | 内容要求 | 抽取 section requirements | writer prompt 参考 |

类型 B 用 `/cnpatent-template-study` 处理，产物 `section-requirements.md` 作为 writer 参考（决策 6A 软约束）。

### 影响 PR
- PR #3（template-study 作为可选 skill）
- PR #7（writer 可选加载 section-requirements）

---

## Finding 7 — 修订模式三路合一

**Severity: P1 · Confidence: 9/10**  
**源于**：用户补充问题 1（修订模式用什么形式）

### 诊断
单一修订方式支持不了所有场景：
- chat 适合高层指令，局部精改表达不了
- tracked changes 适合精确替换，大段重写麻烦
- 批注适合"指出问题不给答案"，模糊需对话

### 修订方向：三路合一
```
/cnpatent-revise 解析：
  a. diff(原稿, signed) → tracked changes + 直接编辑
  b. 读 signed.docx 的批注 → issue 列表
  c. 读 chat 指令 → global directive
  → 合并为 revision_plan.json
  → 展示给用户过目
  → 应用 → v2.docx
  → 循环
```

决策 7A：三路全解析，缺了忽略不强制。

### 分类规则（影响 correction.type）
- tracked 直接替换 → phrasing
- 整段删改 → structure
- 批注+AI 重写 → content_improvement
- chat 全局指令 → global_style

### 影响 PR
- PR #6（revise skill）
- PR #5（learn 消费 revision_plan）

---

## Finding 8 — 多模板 canonical 内核

**Severity: P1 · Confidence: 9/10**  
**源于**：用户补充问题 2（多模板 + 中间产物差异）

### 诊断
不同模板可能有不同 section 结构、公式编号、图片惯例。若中间产物 `06_sections/` 跟着变，下游 review/humanize 都要适配 → 复杂度炸。

### 修订方向：canonical 内核 + 边界吸收

```
模板差异 → 在 boundary 吸收:
  入口 /cnpatent-template-setup 建立 canonical 映射
  出口 /cnpatent-build 调模板专属 build_docx.py

中间所有 skill → 永远用 canonical:
  06_sections/01_name.md ~ 06_impl.md
  review / humanize / learn 零感知模板差异
```

### 多模板选择时机
```
/cnpatent-pipeline 启动:
  IF 只 1 个 fingerprint: 静默用
  ELIF >1: AskUserQuestion 选 active，写 state/<run-id>/config.json
```

### 影响 PR
- PR #2（template-setup 建 canonical 映射）
- PR #11（build 做反向映射）
- PR #12（pipeline 检测多模板）

---

## Finding 9 — Run 生命周期管理

**Severity: P0 · Confidence: 10/10**  
**源于**：用户补充问题 2（跨 session / 并行专利）

### 诊断
当前"隐式 run-id"机制在三种场景全崩：
- 跨 session 恢复：AI 猜不到从哪 run 继续
- 并行多 session：AI 串 run，状态污染
- 单 session 跨天跨周：context 清空后断了

### 修订方向：三层补丁

**a) Run 注册表 `.cnpatent/runs.jsonl`**  
append-only，记录所有 run（id、title、phase、template、status、时间戳）

**b) 活跃指针 `.cnpatent/active_run`**  
单行文件，当前 active run-id

**c) 显式声明契约**  
每 skill 首动作前打印："当前 run: ..., 上次 phase: ..., 下一步: ..."

**d) 新 skill**：`/cnpatent-runs` + `/cnpatent-resume`

### 并发安全
- corrections.jsonl 写入带 flock
- learned-rules.md 同样
- 模板/规则等共享文件只读
- state/<run-id>/ 按 run 隔离天然无冲突

### 影响 PR
- PR #1（契约定义）
- PR #6b（新 skill）
- PR #12（pipeline 启动检测）

---

## Finding 10 — 学习决定权双向把关

**Severity: P1 · Confidence: 9/10**  
**源于**：用户补充"用户可决定是否学习 + AI 也判断"

### 诊断
初版"所有修订都灌 corrections.jsonl"会学到不该学的：
- 一次性术语
- 特定技术细节
- typo 修正

这些学了会污染 rule 空间，甚至过拟合。

### 修订方向：双 flag 合取

```json
{
  "id": "rev-042",
  "user_learn": null | true | false,  // 用户决定
  "ai_learn_propose": true,            // AI 判断
  "ai_learn_reason": "法定开篇风格，跨专利通用",
  "decision": true                     // 合取
}

合取规则:
  user_learn = true  → 学（AI 可反对但不能否决）
  user_learn = false → 硬否决
  user_learn = null  → 看 AI
```

### AI 该判断不学的情形
- 纯 typo
- 专利特有术语
- 局部技术细节
- AI 自己 low confidence

### AI 该判断学的情形
- 句式/语气/开篇
- 违反 patent-voice
- 反复同类问题（本次 ≥2 次）

### 影响 PR
- PR #5（learn respect decision）
- PR #6（revise 产出 revision_plan 带双 flag）

---

## Findings 汇总

| # | 级别 | 主题 | 关键修订 | 影响 PR |
|---|-----|------|---------|---------|
| 1 | P1 | 重构过度革命化 | MVM 核验 + Strangler Fig | #1, #9, #12 |
| 2 | P0 | 查新缺精读 | L1/L2 分层 | #10 |
| 3 | P0 | 学习持久化 | 两层 + 人审晋升 | #5, #6, #7+ |
| 4 | P0 | 测试策略 | training-corpus 即 golden | #1, #5, #13 |
| 5 | P0 | 模板耦合 | fingerprint + 一对一 build | #2, #11 |
| 6 | P1 | 两类资料 | A 真实学风格 / B 指令学结构 | #3, #7 |
| 7 | P1 | 修订模式 | 三路合一 | #5, #6 |
| 8 | P1 | 多模板中间产物 | canonical 内核 + 边界吸收 | #2, #11, #12 |
| 9 | P0 | Run 生命周期 | active_run + runs.jsonl + 新 skill | #1, #6b, #12 |
| 10 | P1 | 学习双把关 | user_learn + ai_learn_propose | #5, #6 |

P0：5 条 · P1：5 条 · 无 P2

---

## 未转化为 Finding 但值得记录的用户关键补充

1. **开发阶段特性**：老 3 skill 仅参考价值，可自由重写
2. **Token 预算宽松**：多轮自审 OK，不怕浪费
3. **训练数据未到位**：阶段 B 延后，阶段 A 不阻塞
4. **多格式输入**：不仅 PDF，docx 等也要支持
5. **模板识别失败优先人审**：不猜默认值（决策 5A）
