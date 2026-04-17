# Phase B.2 结果合并与同族去重规则

> 用途：Phase B.2 所有 subagent（T1-T6）完成后，orchestrator 按本文件定义的算法合并 6 份 `queryN.json` 并写入 `4_manual_search_template.md` B.2 字段。
>
> 定位：下游实现规范。Judge 不读此文件，只看合并后的 template。

---

## 1. 同族合并 —— 走 incoPat 站内功能

**不自己写启发式同族判定**。incoPat 结果页自带完整的同族合并控件（简单同族合并 / 扩展同族合并 / DocDB同族合并）。Playwright subagent 在 inject → sort 之后、extract 之前调用 `scripts/playwright/incopat_merge_family.js`，让 incoPat 服务端自己做族内聚合。extract 脚本返回的每一行就是族代表，不需要 orchestrator 做二次分组。

**单通道查询流程**（incoPat T1/T3 命令检索、T2 语义检索）：

```
1. browser_tabs 切目标 tab
2. browser_navigate /advancedSearch/init (或 /semanticSearch/init)
3. browser_evaluate incopat_inject.js (或 incopat_semantic_inject.js)
4. browser_wait_for 3 秒
5. browser_evaluate incopat_sort.js (AD DESC 排序)
6. browser_wait_for 2 秒
7. browser_evaluate incopat_merge_family.js  ← 站内简单同族合并
8. browser_wait_for 3 秒                      ← 等 incoPat 重新渲染
9. browser_evaluate incopat_extract.js        ← 每行已是族代表
10. Write .omc/research/<channel>/queryN.json
```

`incopat_extract.js` 返回 `family_merged: true` + `total_text: "N个专利族"` 时，orchestrator 知道结果已站内合并。

**CNKI / Scholar / arXiv 不做同族**。非专利文献没有"族"概念，按 url / title 去重即可。

---

## 2. orchestrator 合并算法（剩余职责）

incoPat 站内合并解决了单通道内的族冗余。orchestrator 只负责**跨通道 + 跨来源**的简单去重：

### Step 1 — 跨通道同 PN 合并

同一 `pn` 在多个 incoPat 通道（T1/T2/T3）命中：
- 合并为一条
- 记录 `hit_channels: [T1-Q1, T3-Q1]`（多通道命中 = 强相关性信号）

### Step 2 — 跨通道同 AN 合并（兜底）

若某个 `pn` 只在一个通道出现，但另一条命中的 `an` 和它相同（同一申请的不同公开阶段，如 A 公开 / B 授权）：
- 合并为一条
- 保留 `pd` 最晚的 `pn` 作为代表
- 其余进入 `also_published_as: [...]`

这种情况在 incoPat 内已通过同族合并基本消除，但跨通道（T1 简单同族 vs T2 语义结果）仍可能出现。

### Step 3 — Phase A 去重标记

读 `1_auto_novelty_report.md` 的 Top 命中 PN 列表：
- B.2 某条的 `pn` 已在 Phase A → `phase_a_duplicate: true`
- **不从 B.2 移除**，保留作为跨阶段一致性证据
- template 里加 "（Phase A 已命中）" 标记

### Step 4 — 非专利去重

Scholar / arXiv / CNKI 的命中：
- 优先按 `url` 去重
- `url` 缺失时按 `title` 精确匹配去重

---

## 3. 相关性评分

对每条合并后的命中，针对 `candidate_outline` 的每个区别特征（F1…Fn）打分：

| 分值 | 含义 | 判定 |
|---|---|---|
| 0 | 无关 | 标题/摘要未涉及该特征 |
| 1 | 弱相关 | 提到相关领域但方法不同 |
| 2 | 中等 | 方法相似但参数/场景不同 |
| 3 | 强相关 | 方法实质相同，参数接近 |
| 4 | 直接命中 | 明确披露该特征 |

**评分只基于检索返回字段**（pn / title / ipc）。全文推断由 Phase B.1 精读卡承担，不在此阶段做。

```
relevance_total = Σ(Fi_score)
```

**跨通道加权**：同一 `pn` 在多个通道命中 → `relevance_total × 1.2`（上限 `4 × n`）。

按 `relevance_total` 降序写入 template。

---

## 4. 输出格式

`4_manual_search_template.md` 的 `## 二、B.2 付费库检索结果`，每条合并后命中：

```markdown
### 命中 #N

- **pn**: CN118570217B
- **an**: CN202410012345.6
- **also_published_as**: [CN118570217A]（同申请不同公开阶段，按 AN 合并时列出）
- **hit_channels**: [T1-Q1, T3-Q1]
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

- **incoPat subagent 必须在 extract 前调 merge_family**，否则族冗余会污染结果
- **不要做启发式族判定**（相似 title + 近 AD + 同申请人）—— 会把不同发明错并成一族，incoPat 服务端的合并规则已久经验证，信任即可
- **验证族代表**：extract 返回的 `family_merged: true` + `total_text: "N个专利族"` 是 merge 生效的标志；若 `family_merged: false`，说明 merge 脚本失败（如 `window.mergeCongeners` 不可用），orchestrator 应记录警告但仍可继续（按 v1.2 行为回退到未合并结果）
- **evidence anchor 必保留**：每条命中的 `raw_json_ref` 指向具体 queryN.json 的 index，Phase C Judge 要能回溯原始数据

---

## 6. 反模式

| 反模式 | 后果 |
|---|---|
| 把同族判定塞给 subagent | 单通道 subagent 看不到跨通道全局，且不该重新实现 incoPat 已做的事 |
| 启发式族判定（title + applicant + AD） | 会误并不同发明；incoPat 服务端的官方合并规则更可靠 |
| 跨通道评分取平均 | 取最高值——高分说明至少一个通道确认强相关 |
| 覆盖 Phase A 去重 | 不从 B.2 移除 Phase A 已有命中，只打标 |
| 合并后丢掉 raw_json_ref | Phase C Judge 必须能回溯到原始 queryN.json |
| merge_family 失败后继续当作已合并 | 必须检查 `family_merged` 标志，假阴性会导致族内冗余污染 template |
