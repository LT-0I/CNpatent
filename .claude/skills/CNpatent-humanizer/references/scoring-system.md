# 加权评分系统（专利校准版）

> 本文档定义 CNpatent-humanizer 的加权评分系统，由 Phase 2 调用。综合
> 自 [Humanize Chinese v2.0](https://github.com/openclaw/skills/blob/main/skills/0xspeter/humanize-chinese-2-0-0/SKILL.md)
> 的 4 级加权（致命/高/中/风格）和 [avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing)
> 的改写决策阈值，并针对中文专利场景重新校准。

---

## 总体评分公式

```
总分 = min(100, Σ(category_count × category_weight))
```

其中 `category_count` 是某类问题的命中次数，`category_weight` 是该类的权重。

---

## 五大类权重

### 致命级 (Critical)，权重 = 8

任何一处命中，单独贡献 8 分。出现 2 处即可超过"低"等级（24 分以下）。

**专利场景中的致命级**：

| 模式 | 检测方法 | 示例 |
|---|---|---|
| 三段式连接词 | 段首/句首正则 `首先|其次|然后|最后`（连续 2+ 段） | `首先...其次...最后...` |
| "其一其二其三" | 正则 `其一|其二|其三` | `其一...其二...` |
| 综上所述类 | 正则 `综上所述|总而言之|总之|综合来看` | `综上所述，本发明...` |
| 第一人称 | 正则 `\b(我|我们|笔者|作者)\b`（排除法律声明段） | `我们提出` / `本文` |
| **术语漂移** | 同概念 ≥2 个术语在文中并存 | `稀疏点云` 与 `初始点云` 混用 |
| **公式出现在发明内容** | 在"四、发明内容"节内匹配 `\$.+\$` | 任何 LaTeX 公式 |
| 偷换的"所述"规则 | 发明内容章节首次提及加了"所述"，或后续未加 | `通过所述运动恢复结构...`（首次） |
| 商业宣传语 | 正则 `颠覆性|革命性|突破性|划时代|开创性` | `本发明颠覆性地提出` |
| **附图说明含"所述"** | 在"五、附图说明"节内匹配 `所述` | `所述图1...` |

### 高信号 (High)，权重 = 4

**专利场景中的高信号**：

| 模式 | 检测方法 |
|---|---|
| 推销形容词 | 正则 `(显著|大幅|极大|卓越|优异|出色)的?(提升|提高|改善)?` |
| AI 高频虚词 | 正则 `(旨在|致力于|得益于|有鉴于此|鉴于此)` |
| 平衡式句型 | 正则 `虽然.{1,30}但.{1,30}同时|不仅.{1,30}而且|既.{1,30}又` |
| 模板套句 | 正则 `(随着.{1,15}的不断发展|在.{1,15}的背景下|众所周知)` |
| "值得注意的是"类 | 正则 `值得注意的是|需要(?:指出|强调|说明)的是|值得一提` |
| 学术引文格式 | 正则 `\[\d+\]|参见(?:文献|论文)|实验结果表明` |
| 推销动词 | 正则 `(创新性地|开创性地|巧妙地|精妙地|完美地)` |
| 段尾总结句 | 正则 `(为后续.{1,15}(?:奠定|提供|打下)|为.{1,15}提供.{1,5}支撑)` |

### 中信号 (Medium)，权重 = 2

**专利场景中的中信号**：

| 模式 | 检测方法 |
|---|---|
| 过度对冲 | `(可能|也许|或许|大概|大约|约)` 在文中出现 ≥5 次（排除合理参数范围用法） |
| 列表过多 | 一段内 `（\d+）|（\d+）` 出现 ≥6 次 |
| 标点过用 | 破折号 `——` 在文中出现 ≥3 次（专利极少用破折号） |
| 修辞滥用 | 段中含设问/反问 `?$` |
| 动词名词化 | 正则 `进行(?:[\u4e00-\u9fa5]{1,3})` 全文出现 ≥10 次 |
| 比较级模糊 | 正则 `更(?:好|高|快|强|准)` 出现 ≥3 次且无具体对照 |
| 段中括号注释 | 正则 `（.{20,}）` 长括号注释 ≥3 处 |

### 风格信号 (Style)，权重 = 1.5

**专利场景中的风格信号**：

| 模式 | 检测方法 |
|---|---|
| 段落均匀 | 连续 4+ 段字数差异 < 15% |
| 句长突发度低 | 滑动窗口（4 句）字数标准差/均值 < 0.15 |
| 段首聚集 | 连续 3+ 段以同关联词开头（"因此/同时/此外/另外"） |
| 信息密度均匀 | 段落间技术名词密度方差 < 全文均值 × 0.2 |
| 句式骨架同质 | 连续 3+ 段以"主语+通过+宾语+实现+宾语"骨架 |

由 `scripts/burstiness.py` 自动计算。

### 专利专属 (Patent-only)，权重 = 6

通用 humanizer 不会检测的项，但在专利中是严重问题：

| 模式 | 检测方法 |
|---|---|
| 发明目的-技术效果字面镜像 | 余弦相似度 > 0.85 |
| 步骤数为完美偶数（4/6/8） | 计步骤数 |
| 子步骤格式不是 a）b）c） | 检测 `\(a\)|A\.|1\.` 子步骤 |
| 公式编号不连续 | 提取 `（\d+）` 检查序列 |
| 图引用不连续 | 提取 `图\s*\d+` 检查序列 |
| 步骤标题用动宾短语 | 步骤标题以动词开头（"采集"/"获取"等）而非名词短语 |

---

## 严重程度分级

来自 Humanize Chinese v2.0 的 4 级，专利场景沿用：

| 总分 | 等级 | 处理 |
|---|---|---|
| **0-24** | LOW | 基本无 AI 痕迹，可直接交付 |
| **25-49** | MEDIUM | 少量 AI 信号，需局部修改 |
| **50-74** | HIGH | 明显 AI 生成，需大幅改写 |
| **75-100** | VERY HIGH | 几乎全文重写 |

---

## 改写决策阈值

来自 avoid-ai-writing 的 "rewrite-from-scratch threshold"，专利场景调整：

```python
def decide_rewrite_or_patch(audit_report):
    """决定是局部修补还是整体重写"""
    tier1_hits = audit_report['tier1_hits_count']
    structural_categories = audit_report['structural_categories_triggered']
    rhythm_uniform = audit_report['rhythm']['burstiness'] < 0.15
    term_drift_count = audit_report['term_lock_violations_count']

    # 专利专属：术语漂移单独足以触发整体重写
    if term_drift_count >= 3:
        return 'rewrite', '术语漂移 ≥3 处，必须整体重写以恢复术语锁定'

    # 通用阈值：5+ 词级 + 3+ 句式 + 节奏均匀
    if tier1_hits >= 5 and structural_categories >= 3 and rhythm_uniform:
        return 'rewrite', '满足"5+ Tier1 + 3+ 句式 + 节奏均匀"整体重写阈值'

    # 总分 ≥ 75 也触发整体重写
    if audit_report['score'] >= 75:
        return 'rewrite', f'总分 {audit_report["score"]} ≥ 75，整体重写'

    return 'patch', '局部修补即可'
```

---

## 评分代码示意

```python
def compute_score(issues):
    """
    issues 是 Phase 1 检测输出的字典，结构如：
    {
        'critical': [{'pattern': '三段式', 'count': 2}, ...],
        'high': [{'pattern': '推销形容词', 'count': 5}, ...],
        'medium': [{'pattern': '过度对冲', 'count': 6}, ...],
        'style': [{'pattern': '段落均匀', 'count': 1}, ...],
        'patent': [{'pattern': '镜像', 'count': 1}, ...],
    }
    """
    weights = {
        'critical': 8,
        'high': 4,
        'medium': 2,
        'style': 1.5,
        'patent': 6,
    }

    total = 0
    breakdown = {}
    for category, items in issues.items():
        category_score = sum(item['count'] * weights[category] for item in items)
        breakdown[category] = category_score
        total += category_score

    total = min(100, total)

    # 等级判定
    if total < 25:
        level = 'low'
    elif total < 50:
        level = 'medium'
    elif total < 75:
        level = 'high'
    else:
        level = 'very_high'

    return {
        'score': total,
        'level': level,
        'breakdown': breakdown,
    }
```

---

## 评分校准（专利场景）

通用 humanizer 对"严格语气"扣分，但专利**应当**严格。校准方式：

1. **降低对"长复合句"的惩罚**：通用 humanizer 把 50+ 字的句子算作问题，
   专利场景中 50-80 字是正常的（描述复杂技术流程）。本 skill 把"超长句"
   阈值提高到 80 字。

2. **降低对"被动语态"的惩罚**：专利中"X 被 Y 处理"是合理的，不算 AI 味。

3. **降低对"高频次术语"的惩罚**：专利要求术语锁定，重复使用同一术语是
   **正确**的，不算 elegant variation 缺失。本 skill 对术语词反向加分。

4. **提高对"形容词修饰技术名词"的惩罚**：通用文本可以接受"出色的算法"，
   专利中不可以。本 skill 把"形容词+技术名词"的命中权重从 1.5 调到 4。

5. **提高对"同义词轮换"的惩罚**：通用文本鼓励 elegant variation，专利
   完全相反。本 skill 对术语漂移的权重从 4（avoid-ai-writing 默认）调到 8。

---

## 输出报告示例

```json
{
  "score": 67,
  "level": "high",
  "breakdown": {
    "critical": 16,
    "high": 24,
    "medium": 12,
    "style": 6,
    "patent": 9
  },
  "recommendation": {
    "action": "rewrite",
    "reason": "总分 67 ≥ 50，需大幅改写"
  },
  "issues": {
    "critical": [
      {"pattern": "三段式连接词", "count": 1, "locations": ["§3 P2"]},
      {"pattern": "综上所述", "count": 1, "locations": ["§4.3 P5"]}
    ],
    "high": [
      {"pattern": "推销形容词", "count": 4, "locations": ["§3 P1", "§4.1 P3", ...]},
      {"pattern": "AI 高频虚词", "count": 2, "locations": [...]}
    ],
    "medium": [
      {"pattern": "动词名词化", "count": 6, "locations": [...]}
    ],
    "style": [
      {"pattern": "句长突发度低", "count": 1, "locations": ["§6 P10-13"]}
    ],
    "patent": [
      {"pattern": "镜像段落", "count": 1, "locations": ["§4.1 ↔ §4.3"]},
      {"pattern": "公式出现在发明内容", "count": 1, "locations": ["§4.2 P3"]}
    ]
  }
}
```
