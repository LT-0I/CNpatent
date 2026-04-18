# 决策记录

7 个决策 + 用户补充信息。每条带选项、选择、rationale、补充。

---

## 决策 1：learned-rules.md 的晋升触发

**Question**：consolidate 是手动还是自动？

**Options**：
- **A) 手动触发**：你跑 `/cnpatent-consolidate` 时才分析和提议 ← **选中**
- B) 自动触发：每 N 次 /cnpatent-write 后自动分析

**选择：A**

**Rationale**：
- 符合"人在回路"的期望
- 避免 AI 自动晋升坏规则
- 用户可掌握节奏，不被打断工作流
- 规则晋升是重要决策，值得专门时间审

**补充** (用户 2026-04-18)：
- 开发阶段，希望通过用户给的现成专利 PDF 文件，AI 提炼核心点后按 skill 流程书写，然后自行学习，类似强化学习原理

**影响**：
- PR #5：consolidate 完全手动触发
- PR #13：批量训练（阶段 B）跑完后用户手动触发一次大批量 consolidate

---

## 决策 2：老 3 skill 的退役时机

**Question**：老 cnpatent / humanizer / noveltycheck 什么时候下线？

**Options**：
- **A) 保留半年后移入 `_legacy/`** ← **选中**
- B) 新 skill 上线立刻移走

**选择：A**

**Rationale**：
- 给充分时间切换
- 任何怀疑"新 skill 不如老的"都能快速回滚对比
- 老 skill 有参考价值（即使未经核验）

**补充** (用户 2026-04-18)：
- 老 3 skill 存在很多问题，只有参考价值
- 重构时**不预设老机制正确**，需重新跑测试
- 对应 Finding 1 的 MVM 机制（机制核验清单）

**影响**：
- PR #12：归档到 `.claude/skills/_legacy/`，加 deprecation 注释
- 所有用到老机制的 PR 都要走 MVM 核验（PR #8 #9 #10）

---

## 决策 3：第一批训练 PDF 的规模

**Question**：批量训练用多少份？

**Options**：
- A) 10 份典型 PDF
- **B) 20 份（更广覆盖）** ← **选中**
- C) 5 份（快速验证）

**选择：B**

**Rationale**：
- 20 份能出更稳的规则集
- 跨技术领域覆盖更广
- 减少过拟合风险

**补充** (用户 2026-04-18)：
- 输入内容不一定是 PDF，也可能是 docx 等 → 多格式支持
- 用户目前手头没有 20 份专利训练资料
- **训练过程可往后放**，不阻塞主开发
- 阶段 B 延后执行

**影响**：
- PR #4：`/cnpatent-ref-extract` 必须多格式（PDF / docx 至少）
- PR #13：延后到用户攒够资料再跑
- 阶段 A 所有 PR 不依赖训练数据

---

## 决策 4：extracted_outline 是否必须人工审核

**Question**：从专利 PDF 抽 outline 要不要人审？

**Options**：
- A) 必须人审
- **B) 自动审核（多轮自校验）** ← **选中**
- C) 抽样审核

**选择：B**

**Rationale**（用户 2026-04-18）：
- 用户争取提供较清晰的 PDF 或 OCR 后的文件
- 自动审核即可
- **可多循环几轮，不怕浪费 tokens**

**影响**：
- PR #4：多轮自审流程（5 轮）
  - Round 1 初步抽取
  - Round 2 覆盖性自检
  - Round 3 忠实性自检
  - Round 4 针对性补抽取
  - Round 5 一致性 cross-check
- 上限 3 次补抽取，不收敛就 audit.md 记录并跳过该份

---

## 决策 5：模板识别失败的兜底

**Question**：`/cnpatent-template-setup` 识别失败时怎么办？

**Options**：
- **A) 停下让用户手动补 meta.json** ← **选中**
- B) 用默认值继续
- C) 尝试 3 次自动识别后再让用户介入

**选择：A**

**Rationale**：
- 与决策 4 相反，因为模板 meta 是结构级决策，错了全盘偏
- 必须人审

**补充** (用户 2026-04-18)：
- 希望流程：用户在一个 session 中使用 `/cnpatent-template-setup` 安装好模板
- 安装完 AI 生成一个样例，包括各种样式、段落
- 做好方便用户指出错误的**标记**
- 有错误再进行对话改正（循环）

**影响**：
- PR #2：设计为**对话式工作流**
  1. AI 分析 → 初版 meta + build_docx
  2. 生成 `verification_sample.docx`（各样式各一段，带标签/批注）
  3. 生成 `verification.md`（人类可读报告）
  4. 用户在同 session 指出错误
  5. AI 更新 meta + 重生成 sample
  6. 循环直到用户 ok
  7. finalize，config.json 设 active

---

## 决策 6：代理人范本作为 section 要求的严格程度

**Question**：范本里每段要求是硬约束还是软约束？

**Options**：
- **A) 软约束（writer 参考，允许合理偏离）** ← **选中**
- B) 硬约束（必须严格遵守）
- C) 混合（结构硬、内容软）

**选择：A**

**Rationale**：
- 范本只是一份样例
- 不同技术领域应有差异
- 硬约束会在写化学专利时崩

**补充** (用户 2026-04-18)：
- 代理人范本并非一直存在，有时候没有
- `/cnpatent-template-study` 作为**可选项**即可

**影响**：
- PR #3：skill 设计为可选；不跑也能正常写
- PR #7：writer 检测 `section-requirements.md` 存在才加载
- pipeline 不强制 study 前置

---

## 决策 7：`/cnpatent-revise` 默认解析哪几路

**Question**：revise 支持 chat、tracked、批注，默认解析哪些？

**Options**：
- **A) 三路全解析** ← **选中**
- B) 按配置开关
- C) 只支持一种

**选择：A**

**Rationale**：
- 每路发现了就处理
- 缺了就忽略
- 不强制用户用哪种

**补充** (用户 2026-04-18)：
- 用户可决定此次修改内容**是否要被 AI 学习**
- AI 内部**也要做判断**，看是否需要学习这个东西
- 这是**双把关机制**，见 Finding 10

**影响**：
- PR #6：revision_plan.json 每条带 `user_learn` + `ai_learn_propose` + `decision`
- PR #5：learn 消费 revision_plan 时 respect `decision` 字段

---

## 未编号的关键补充

### 补充 A：跨 session 续跑 + 并行专利（2026-04-18）

**用户提问**：
1. 一个文件夹可以跑多个专利？还是一个？
2. 工作流长，Session 1 做查新，Session 2 能续跑么？
3. 并行写多个专利 AI 能分辨么？

**回答**：
- 一个安装跑无限多 run，kit 共享，state/<run-id>/ 按专利隔离
- 可跨 session 续跑，但需补 Run 生命周期机制（Finding 9）
- 并行需要显式 active_run + AI 声明契约

**影响**：
- 新增 Finding 9
- 新增 skill `/cnpatent-runs` + `/cnpatent-resume`（PR #6b）
- 所有 skill 首动作前打印 "当前 run:"
- 文件锁保护共享写

### 补充 B：开发阶段特性（2026-04-18）

**用户补充**：现有 3 个 skill 仍处开发阶段，所有内容只有参考价值，重构时还需重新跑测试，原有机制不一定正确。

**影响**：
- Finding 1 的 MVM 是核心机制（先核验再采纳）
- 每个引用老机制的 PR 都要先跑实验（PR #8 #9 #10 尤其）

### 补充 C：docx 模板学习是架构级需求（2026-04-18）

**用户补充**：
- 每个人都有自己的 docx 模板
- 项目安装时先需要学习模板
- 主要是 docx 文件的排版
- **最好可以固化为和模板 .docx 文件一一对应的 build_docx 文件脚本**
- "这个机制还是比较重要的"

**影响**：
- 新增 Finding 5
- PR #2 提至第二位，与模板相关的 PR #11 依赖 #2

### 补充 D：第一份资料是代理人范本（2026-04-18）

**用户补充**：第一份学习资料是代理人给的交底书范本，**没有实质内容**，只是指导 + 举例说明每部分填什么。

**影响**：
- 新增 Finding 6（两类参考资料分开处理）
- PR #3（template-study）设计为指令型文档处理

### 补充 E：修订模式 + 双把关学习（2026-04-18）

**用户提问 + 补充**：
- 修订模式支持什么形式？直接发意见 / tracked / 批注？
- 用户可决定是否学习，AI 也要判断

**回答**：三路合一 + 双 flag 把关（Finding 7 + Finding 10）

---

## 决策检查清单（开任何 PR 前过一遍）

每开一个 PR 前，问自己：

- [ ] 是否违反决策 1（consolidate 自动化）？
- [ ] 是否违反决策 2（删老 skill）？
- [ ] 是否依赖决策 3 的训练数据（不应该，阶段 A 独立）？
- [ ] 是否违反决策 4（extract 加人审）？
- [ ] 是否违反决策 5（模板识别自动猜默认）？
- [ ] 是否违反决策 6（study 必须前置）？
- [ ] 是否违反决策 7（revise 单路）？
- [ ] 是否违反补充 A（无视 active_run）？
- [ ] 是否违反补充 B（假设老机制正确）？
- [ ] 是否违反补充 C（模板硬编码）？

任何 ✗ 都应停下重新设计。
