# Phase B.2 结果合并与同族去重规则

> 用途：Phase B.2 所有 subagent（T1-T6）完成后，orchestrator 按本文件定义的算法合并 6 份 `queryN.json`，做同族去重、跨通道合并、相关性评分，最终写入 `4_manual_search_template.md` B.2 字段。
>
> 定位：下游实现规范。Judge 不读此文件，只看合并后的 template。

---

## 1. 输入

```
.omc/research/
├── incopat_command/queryN.json
├── incopat_semantic/query1.json
├── incopat_conflict/query1.json
├── cnki/queryN.json
├── scholar/queryN.json
└── arxiv/queryN.json
```

每条记录（incoPat 通道）典型字段：
```json
{
  "pn": "CN118570217B",
  "an": "CN202410012345.6",
  "family_key": "CN20241001",
  "family_tag": "中国同族 3",
  "family_count": 3,
  "title_cn": "...",
  "ad": "2024-01-05",
  "pd": "2025-01-14",
  "applicant": "...",
  "ipc": "G06T7/00"
}
```

---

## 2. 合并算法（按此顺序执行）

### Step 1 — 通道内同 PN 去重

同一通道（如 T1）内，若多条查询命中了相同 `pn`，合并为一条。保留首次出现的位置索引（用于后续排序）。

### Step 2 — 跨通道同 PN 合并

不同通道命中同一 `pn`：
- 合并为一条
- 记录 `hit_channels: [T1, T3]` 用于多通道交叉验证信号
- 相关性评分取 **最高值**（非平均）

### Step 3 — 同族合并（核心）

**同族判定（两层）**：

1. **强同族**（确定）：
   - `family_key` 相同（申请号前 10 位一致）→ 同族
   - 或 `an` 完全相同 → 同专利不同公开号（如 CN...A 和 CN...B，实际是同一申请的公开→授权两次公开）

2. **弱同族**（启发式，需同时满足）：
   - `applicant` 完全一致（去除标点空格后）
   - `ad` 日期差 ≤ 7 天
   - `title_cn` 相似度 ≥ 80%（简单字符重合率即可，不需要 embedding）

**合并时保留谁**：
- 公开日（`pd`）**最晚**的那条作为代表（最接近当前授权状态）
- 若 `pd` 相同，保留 `pn` 字母后缀较晚的（B > A，C > B，授权 > 公开）
- 被合并的条目列入 `family_members: ["CN118570217A", ...]`

**不做同族合并的情况**：
- `family_tag` 为空（孤立专利）
- 非 incoPat 通道（Scholar / arXiv / CNKI 无同族概念，按 `url` 或 `title` 去重）

### Step 4 — 与 Phase A 命中去重

读 `1_auto_novelty_report.md` 的 Top 命中列表。若 B.2 某条的 `pn` 或 `family_key` 已出现在 Phase A，标记 `phase_a_duplicate: true`：
- **不从 B.2 移除**（保留作为跨阶段一致性证据）
- 在 template 中加标记 "（Phase A 已命中）"

### Step 5 — 非专利去重

Scholar / arXiv / CNKI 的命中：
- 按 `url` 去重（首选）
- 若 url 缺失，按 `title` 精确匹配去重

---

## 3. 相关性评分

### 评分维度

对每条合并后的命中，针对 `candidate_outline` 的每个区别特征（F1…Fn）打分：

| 分值 | 含义 | 判定 |
|---|---|---|
| 0 | 无关 | 标题/摘要未涉及该特征 |
| 1 | 弱相关 | 提到相关领域但方法不同 |
| 2 | 中等 | 方法相似但参数/场景不同 |
| 3 | 强相关 | 方法实质相同，参数接近 |
| 4 | 直接命中 | 明确披露该特征 |

**评分只基于检索返回字段**（pn / title / abstract / ipc），**不做全文推断**。全文推断是 Phase B.1 精读卡的职责。

### 综合相关性

```
relevance_total = Σ(Fi_score for i in 1..n)
```

按 `relevance_total` 降序排列。

### 跨通道加权

同一 `pn` 在多个通道命中 → relevance_total × 1.2（上限 4×n）。

---

## 4. 输出格式

写入 `4_manual_search_template.md` 的 `## 二、B.2 付费库检索结果` 段落。每条合并后的命中：

```markdown
### 命中 #N

- **pn**: CN118570217B（授权公告号，代表本族）
- **family_members**: CN118570217A（公开）
- **hit_channels**: [T1-Q1, T3-Q1]（命令检索 + 抵触申请）
- **phase_a_duplicate**: true / false
- **title**: ...
- **ad / pd**: ...
- **applicant**: ...
- **ipc**: ...
- **relevance_scores**: F1=3, F2=2, F3=0, F4=1 → total=6
- **_flag**: "key_candidate" / "interfering_candidate" / ""
- **raw_json_ref**: .omc/research/incopat_command/query1.json#result_3
```

---

## 5. orchestrator 实现要点

- **不要让 subagent 做合并**。subagent 只负责单通道内的查询 + 提取 + 原始 JSON 落盘。合并是 orchestrator 的主职责，保持逻辑集中。
- **合并前打印每个通道的命中数** → 合并后总数，便于用户 sanity check（用户会看到"T1 原始 80 → 合并后 62"这样的日志）。
- **同族合并务必输出日志**："合并同族：CN118570217A + CN118570217B → 保留 CN118570217B，另 1 条归入 family_members"。
- **evidence anchor 必保留**：每条命中的 `raw_json_ref` 必须指向具体 queryN.json 的某条记录（orchestrator 可用 0-based index）。Phase C Judge 需要回溯。

---

## 6. 反模式

| 反模式 | 说明 |
|---|---|
| 跨通道评分取平均 | 错。取最高值——因为高分说明至少一个通道确认强相关 |
| 同族合并用 IPC | 错。同发明可能多 IPC，不同发明可能同 IPC。必须用 AN 或 family_key |
| 启发式合并阈值过宽 | 错。title 相似度 < 80% 或 ad 差 > 7 天不合并，否则会误并 |
| 覆盖 Phase A 去重 | 错。不从 B.2 移除 Phase A 已有命中，只打标 |
| 让 subagent 判定 family_key | 错。subagent 只抓原始字段，family_key 在 orchestrator 合并阶段计算（subagent 返回的 family_key 仅供参考） |
| 合并后丢掉 raw_json_ref | 错。Phase C Judge 必须能回溯到原始 queryN.json，否则无锚点 |
