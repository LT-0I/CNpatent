---
name: cnpatent-humanizer
description: >
  Patent-specific Chinese humanizer for removing AI writing traces from Chinese
  patent technical disclosure documents (技术交底书) and patent specifications.
  Unlike generic humanizers that add personality, opinions, first-person voice,
  idioms, and casual variation, this skill preserves the formal
  terminology-locked patent voice and removes ONLY the AI-specific tells
  layered on top of it. Implements: (a) 3-tier vocabulary detection
  (always-replace / cluster-flag / density-flag), (b) weighted 4-level scoring
  0-100, (c) 9-step rewrite pipeline, (d) "don't over-correct" protection of
  legitimate patent stiffness, (e) Chinese-specific tells including idiom
  stacking, verb nominalization, mixed punctuation, and low burstiness. Use
  this skill whenever you need to remove AI traces from Chinese patent text —
  never use the generic `humanizer` skill on patent text, it will break
  terminology lock, introduce hedging, add inappropriate first-person voice,
  and corrupt the legal register. Triggers on: 去AI味, 去AI痕迹, 专利去AI,
  人类化润色, humanize patent, de-AI patent, 专利润色, 交底书润色,
  remove AI traces from patent.
---

# cnpatent-humanizer — 中文专利文本去 AI 味器

> 中文专利专用的 humanizer，针对专利文体的"形式严格、术语锁死、句式固定"
> 的特殊性做适配。

---

## 核心原则

专利的 AI 味不在于"太正式"，而在于"正式得**机械**"——形容词堆砌、三段式凑数、信息密度均匀、过渡填充词泛滥、动词名词化、比较级模糊化。要去除的是这些机械痕迹，而**不是**正式语气本身。

这与通用 humanizer "注入灵魂、加入观点、用第一人称"的方向相反：专利文体严禁第一人称（会被审查员质疑）、严禁同义词轮换（致命：术语漂移导致权利要求范围不清）、严禁不确定语气（"可能/也许"会导致权利要求被驳回）。

---

## 输入与输出

**必需输入**：
1. **待处理文本**（完整交底书或某节文本）
2. **章节上下文**（一/二/三/四/五/六/法律声明），不同节用不同规则。
   详见 [section-rules.md](references/section-rules.md)

**可选输入**：
3. **术语锁定表**（从 cnpatent Phase 0 大纲产出），用于检测术语漂移
4. **参考素材摘要**，用于校验技术内容是否被改写得偏离原意
5. **严格度档位**：`strict` / `normal` / `relaxed`（默认 normal）

**输出**：
1. **修改后的文本**（保持原结构、原段落数）
2. **加权评分报告**（0-100 分，4 个等级，按维度拆解）
3. **审查报告**（修改了什么、为什么修改、剩余疑似问题）
4. **保护清单**（哪些段落被识别为受保护区域而未做修改）

---

## 核心架构：四维 × 五阶段

去 AI 味问题被拆解成**四个互相正交的维度**（词级 / 句式 / 篇章 / 章节规则）和**五个执行阶段**。每个阶段专注一类问题，避免单遍处理时不同维度互相干扰。

### 四个维度的参考文档
- [three-tier-vocabulary.md](references/three-tier-vocabulary.md) — 3 级词汇模型
- [scoring-system.md](references/scoring-system.md) — 加权评分
- [chinese-specific-tells.md](references/chinese-specific-tells.md) — 中文独有痕迹
- [do-not-overcorrect.md](references/do-not-overcorrect.md) — 不过度矫正清单
- [protected-regions.md](references/protected-regions.md) — 保护区域识别
- [section-rules.md](references/section-rules.md) — 各节差异化规则
- [patent-anti-patterns.md](references/patent-anti-patterns.md) — 专利专属反模式

### 五阶段

```
Phase 0 ── Phase 1 ── Phase 2 ── Phase 3 ── Phase 4
(Protect)  (Detect)   (Score)    (Rewrite)  (Verify)
```

下面逐阶段说明。

---

## Phase 0：保护区域映射 (Protection Mapping)

在做任何修改前，识别**绝对不能改动**的区域。详见
[protected-regions.md](references/protected-regions.md)。

需要保护的 8 类区域：
1. 法律声明段（附图前 2 段、具体实施方式前 5 段、末尾 1 段）
2. 公式段（含 `$...$` 或 `$$...$$`）
3. 章节标题段（一、~六、+ 三个子标题）
4. 附图描述段（"图X 为本发明实施例..."）
5. 封面信息表
6. 注意事项段
7. 具体参数数值（K=20、N=128 等）
8. 专利号引用（CN... 格式）
9. 术语锁定表中的所有术语字符串

执行方式：扫描全文，给每段打标签 `{protected: bool, reason: str}`，并
对每个术语字符串用占位符 `__TERM_NNNN__` 屏蔽。后续 Phase 1-4 只在
`protected=False` 的段落上操作。

---

## Phase 1：多维度检测 (Multi-dimensional Detection)

并行执行四个子检测，输出问题清单。

### 1A. 词级检测（Tier 1/2/3 模型）

**Tier 1（必替词）**：单次出现即标记，必须替换或删除。约 **80 个中文条目**。
完整列表见 [three-tier-vocabulary.md](references/three-tier-vocabulary.md)
的 Tier 1 节。

**Tier 2（聚集标记词）**：单次出现不标记，**同一段落内 ≥2 次**或
**500 字范围内 ≥3 次**才标记。约 **40 个中文条目**。

**Tier 3（密度标记词）**：常见词，但全文密度 ≥ 3% 时标记。约
**15 个中文条目**。

**重要**：3 级模型大幅减少误报。比如"基于"是技术中性词，不应每次
都触发，但若全文超过 50 处使用"基于"则可能是 AI 套话。

### 1B. 句式检测（Structural Patterns）

- 三段式凑数（首先...其次...最后；其一...其二...其三）
- 平行结构过密（连续 3+ 段相同句首）
- 段落镜像（发明目的与技术效果字面对应）
- 比较级泛化（"更...更..."无具体对照）
- 整齐因果链（每段都"因此/由此"）
- 偶数步骤（步骤数为 4/6/8）

详见 [patent-anti-patterns.md](references/patent-anti-patterns.md)。

### 1C. 篇章检测（Discoursal Rhythm）

- **句长突发度**：连续 N 句字数标准差/均值 < 0.15 → 告警
- **段落均匀度**：连续 4+ 段字数差异 < 15% → 告警
- **技术名词密度均匀**：段落间技术名词密度方差 < 全文均值 × 0.2 → 告警
- **段首词聚集**：连续 3+ 段以相同关联词开头 → 告警

由 `scripts/burstiness.py` 自动执行。

### 1D. 中文独有检测（Chinese-Specific）

- **成语堆叠**：连续两个以上四字成语 → 删除
- **动词名词化**："进行 X" → "X" / "对 X 进行 Y" → "对 X Y"
- **中英标点混用**：` , ` vs `，` 不一致 → 统一
- **括号注释滥用**：括号中放整句话 → 拆出独立句

详见 [chinese-specific-tells.md](references/chinese-specific-tells.md)。

### 1E. 术语锁定违反（Term Lock Violation）

对每个核心术语扫描是否存在同义改写。若术语锁定表中"稀疏点云"映射多个
近义词（"初始点云"/"原始点云"），全部统一为首次出现的术语。这是**专利
humanizer 区别于通用 humanizer 最关键的检测项**。

---

## Phase 2：加权评分 (Weighted Scoring)

将 Phase 1 的问题清单按权重加权求和，得到 0-100 分总分。
详见 [scoring-system.md](references/scoring-system.md)。

权重设计（专利场景重新校准）：

| 类别 | 权重 | 示例 |
|---|---|---|
| **致命级 (Critical)** | 8 | 三段式（首先/其次/最后）、综上所述、术语漂移、第一人称"我们" |
| **高信号 (High)** | 4 | 推销词（显著/卓越）、AI 高频词（旨在/致力于）、平衡式句型 |
| **中信号 (Medium)** | 2 | 过度对冲（>5 处）、列表过多、动词名词化（>10 处） |
| **风格信号 (Style)** | 1.5 | 段落均匀、句长突发度低、段首聚集 |
| **专利专属 (Patent)** | 6 | 公式出现在发明内容、所述使用错误、附图描述用所述 |

**严重程度分级**：
- **0-24（低）**：基本无 AI 痕迹，可直接交付
- **25-49（中）**：少量 AI 信号，需局部修改
- **50-74（高）**：明显 AI 生成，需大幅改写
- **75-100（极高）**：几乎全文重写

**改写决策阈值**：
- 若 `Tier 1 命中 ≥5 处` AND `句式问题 ≥3 类` AND `节奏均匀` →
  推荐**整体重写**（rewrite from scratch）而非局部修补
- 否则 → 局部修补

---

## Phase 3：九步重写流水线 (Nine-Step Rewrite)

```
Step 1: 结构清理     ── 删除三段式连接词、镜像段落、段尾总结句
Step 2: 词级替换     ── 应用 Tier 1 词表，进行确定性替换
Step 3: 句子合并     ── 连续短句（<15字）合并为一句，避免 AI 节奏
Step 4: 句子拆分     ── 超长句（>80字）在自然连接词处拆分
Step 5: 标点规范化   ── 去破折号过用、中英标点统一、分号语义化
Step 6: 术语锁定执行 ── 用术语锁定表统一术语，禁止同义词轮换
Step 7: 段落节奏调整 ── 调整段落长度方差，制造漏斗式分布
Step 8: 章节规则细化 ── 应用 section-rules 的差异化规则
Step 9: 最终正则兜底 ── 执行 final_deai_cleanup() 硬编码替换
```

整个流水线被 [do-not-overcorrect.md](references/do-not-overcorrect.md)
约束，避免破坏合法的专利刻板表达。

每步的详细操作和代码见 `scripts/audit.py` 和 `scripts/regex_clean.py`。

---

## Phase 4：自检与验证 (Self-Audit & Verification)

重写完成后，执行二次审查：

1. **零修改保护检查**：所有 Phase 0 标记的保护段落是否一字不变
2. **术语锁定检查**：占位符 `__TERM_NNNN__` 是否全部还原
3. **二次评分**：对重写后的文本再跑一次 Phase 1+2，期望分数 ≤ 24（低）
4. **字数变化检查**：与原文字数差异应在 ±20% 以内
5. **结构完整性检查**：章节顺序、标题、编号是否保留

如果二次评分仍 > 24 分，进入二次重写循环（最多 2 轮，避免死循环）。

---

## "不过度矫正"清单 (Don't Over-correct)

**保护合法的专利刻板表达**，不要把它们当作 AI 痕迹去除。完整的"应保留刻板表达"清单（法定开篇、所述回指、问题-方案叙事、附图引用规范、变量释义、权利要求标志句式等）见 [do-not-overcorrect.md](references/do-not-overcorrect.md)。

**判定原则**：对任何疑似 AI 痕迹，先问"这个表达在真实代理人撰写的专利中是否常见？"。如果答案是"是"，**保留**；如果答案是"否"，**删除/重写**。

---

## 自动化辅助脚本

### scripts/audit.py
执行 Phase 1 多维度检测 + Phase 2 加权评分。

```bash
PYTHONUTF8=1 python -X utf8 .claude/skills/cnpatent-humanizer/scripts/audit.py \
  --input draft.txt \
  --section all \
  --term-lock terms.json \
  --output audit_report.json
```

输出 JSON 结构：
```json
{
  "score": 67,
  "level": "high",
  "recommendation": "rewrite",
  "issues": {
    "tier1_hits": [...],
    "structural_patterns": [...],
    "burstiness": {...},
    "chinese_specific": [...],
    "term_lock_violations": [...]
  },
  "protected_paragraphs": [...]
}
```

### scripts/regex_clean.py
执行 Step 9 的硬编码兜底替换。与 cnpatent 的 `final_deai_cleanup()` 兼容
但增加了专利专属补丁词。

```bash
PYTHONUTF8=1 python -X utf8 .claude/skills/cnpatent-humanizer/scripts/regex_clean.py \
  --input draft.txt \
  --output cleaned.txt
```

### scripts/burstiness.py
计算文本的句长突发度（burstiness）和段落均匀度，用于 Phase 1C。

```bash
PYTHONUTF8=1 python -X utf8 .claude/skills/cnpatent-humanizer/scripts/burstiness.py \
  --input draft.txt
```

输出每个滑动窗口的标准差/均值比，低于 0.15 的窗口告警。

**重要**：脚本只做确定性替换和检测，**不做语义级重写**。语义级重写必须
由 LLM 完成。脚本是 LLM 重写之前的预处理和事后的校验工具。

---

## 参考文档清单

| 文件 | 用途 |
|---|---|
| [scoring-system.md](references/scoring-system.md) | 加权评分表（专利校准） |
| [three-tier-vocabulary.md](references/three-tier-vocabulary.md) | 中文 3 级词表 |
| [chinese-specific-tells.md](references/chinese-specific-tells.md) | 中文独有 AI 痕迹 |
| [do-not-overcorrect.md](references/do-not-overcorrect.md) | 不过度矫正清单 |
| [protected-regions.md](references/protected-regions.md) | 受保护区域识别 |
| [section-rules.md](references/section-rules.md) | 各节差异化规则 |
| [patent-anti-patterns.md](references/patent-anti-patterns.md) | 专利专属反模式 |
| [../cnpatent/references/writing-rules.md](../cnpatent/references/writing-rules.md) | cnpatent 主词表（共享） |

---

## 平台注意事项

Windows 环境下执行 Python 脚本必须使用 UTF-8 模式：
```bash
PYTHONUTF8=1 python -X utf8 script.py
```
