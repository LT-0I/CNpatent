# cnpatent — Agent 角色文件架构约定

本文件说明 `agents/` 子目录下 `cnpatent-*.md` 角色文件的使用约定。由 SKILL.md 在 Phase 0–2 各阶段引用。

## 这些文件不是 Claude Code 原生子 agent

Claude Code 的子 agent 发现机制只扫 `.claude/agents/`（项目级）和 `~/.claude/agents/`（用户级）。本 skill `agents/` 目录下的文件 **不会** 被 `subagent_type: cnpatent-writer-a` 这种调用发现和加载。

这些文件的定位是 **结构化角色简报 + 任务模板**：orchestrator（执行 cnpatent skill 的主 Claude）在 Phase 0–2 的各阶段显式 `Read` 这些文件，把 body 拼接到 Agent 工具调用的 `prompt` 参数中，再附上本次任务的具体上下文（大纲片段、参考素材、目标章节、字数上限等）。

## Frontmatter 约定

每个文件的 frontmatter 采用 Claude Code 子 agent 的字段名，便于将来迁移到 `.claude/agents/` 时改动最小：

| 字段 | 含义 | 运行时效果 |
|---|---|---|
| `name` | 角色 ID，如 `cnpatent-writer-a` | 文档性 |
| `description` | 角色职责一句话描述 | 文档性 |
| `model` | 强制模型层级，统一为 `opus` | **orchestrator 读取后显式传给 Agent 工具的 `model` 参数** |
| `tools` | 该角色需要的工具列表 | 纯文档（Agent 工具不接受工具限制参数） |
| `outputs` | 该角色写入的文件路径清单 | 给 orchestrator 参考，避免 Writer 越界 |
| `word_budget` | 字数软上限 | 写入 Writer body，Writer 自行遵守 |

## Orchestrator 调用约定（伪代码）

```python
# Phase 1 并行派发 Writer（orchestrator 视角）
for writer_id in ['writer-a', 'writer-b', 'writer-c', 'writer-d']:
    # 1. Read 角色文件
    role_content = Read(f'.claude/skills/cnpatent/agents/cnpatent-{writer_id}.md')

    # 2. 解析 frontmatter 取 model（统一是 opus）
    frontmatter, body = split_frontmatter(role_content)

    # 3. body 拼接任务上下文
    task_prompt = f"""
{body}

---

# 本次任务的上下文

## 大纲片段
{outline_section_for_this_writer}

## 参考素材
{reference_material_for_this_writer}

## 术语锁定表
{terminology_dict}

## 写入路径
{frontmatter['outputs']}
"""

    # 4. Agent 工具调用（显式传 model=opus）
    Agent(
        subagent_type='general-purpose',
        model=frontmatter['model'],   # 'opus'
        prompt=task_prompt,
        run_in_background=True,        # 4 个 Writer 并行
    )
```

## 能硬强制 vs 只能软影响

| 约束 | 强制方式 | 效果 |
|---|---|---|
| 模型 opus 层级 | orchestrator 调用 Agent 工具时显式传 `model="opus"` | 硬 |
| 具体模型版本（opus-4-6 vs opus-4-5） | 依赖运行时默认 | 无法 |
| 扩展思考强度 | body 里写 "Reason before drafting" 等自然语言触发 | 软 |
| 工具限制 | 仅文档，Agent 工具不支持 | 无法 |
| 字数上限 | body 里要求 + Reviewer 抽查 | 软 |

> **关于扩展思考**：2026 年 1 月 Claude Code 一度废除了 `ultrathink` 魔法词，3 月 v2.1.68 回归但默认降为 medium effort。`ultrathink` / `think harder` 这类魔法词的行为在不同版本间不稳定，本 skill 的 agent 文件一律**不**依赖魔法词，而是用自然语言引导（"先推理这 6 个问题再动笔"），让模型默认打开的思考自然展开。

## 设计原则（research-backed）

研究结论来自 MAST 多 agent 失败分析框架、LLM4Review、MARG 等论文：

1. **Role separation**：Writer 之间、Writer 和 Reviewer 之间不共享 system prompt。防止 Writer 反向 game Reviewer 的规则，也防止 Reviewer 对 Writer 的 system prompt 产生 agreement bias。
2. **Outline as contract**：所有 Writer 都看同一份大纲（`01_outline.md`）作为唯一合约；Reviewer 也对照大纲检查，而不是"这段写得好不好"。
3. **No replacement drafts from Reviewer**：Reviewer 原则上只发结构化问题清单 + 就地做机械性修补；涉及语义 / 结构的改动必须退回对应 Writer。允许 Reviewer 重写会触发 "over-correction stripping voice" 失败模式。
4. **Closed rubric, not open critique**：Reviewer 有一份明确的 Rubric-A/B/C 清单，逐项 pass/fail。开放式 "请审查这段" 会触发 sycophancy。
5. **Hard revision cap**：最多 2 轮审查往返。超出 2 轮就保留 `[待确认]` 标记由用户决定。这是多 agent 写作管线的 top failure mode（infinite revision loop）。
6. **术语锁定表**：research 中被明确列为"最高 ROI 的一致性干预"。由 Planner 建立后传给每个 Writer 和 Reviewer。

## 迁移到原生子 agent 的路径

如果将来 Claude Code 支持 skill 子目录下的 agent 自动发现，或者 cnpatent 要让用户通过 slash command 直接调用 Writer-A：

1. 把这些文件复制到项目的 `.claude/agents/` 下（文件名和 frontmatter 不变）
2. SKILL.md 的 orchestrator 部分改为使用 `subagent_type='cnpatent-writer-a'` 代替 Read + 拼接

frontmatter 字段已按 Claude Code 的约定命名，迁移成本接近零。

## 文件清单

| 文件 | 触发阶段 | 职责 |
|---|---|---|
| [`cnpatent-planner.md`](../agents/cnpatent-planner.md) | Phase 0 | 大纲生成，建立主旨四段式 / 三方对应 / 术语锁定 |
| [`cnpatent-writer-a.md`](../agents/cnpatent-writer-a.md) | Phase 1 | 写 一、发明名称 + 二、技术领域 + 三、背景技术 |
| [`cnpatent-writer-b.md`](../agents/cnpatent-writer-b.md) | Phase 1 | 写 四·发明目的 + 四·技术解决方案 + 四·技术效果 |
| [`cnpatent-writer-c.md`](../agents/cnpatent-writer-c.md) | Phase 1 | 写 五、附图说明 + 六、具体实施方式前半 |
| [`cnpatent-writer-d.md`](../agents/cnpatent-writer-d.md) | Phase 1 | 写 六、具体实施方式后半 + 固定结尾段 |
| [`cnpatent-reviewer.md`](../agents/cnpatent-reviewer.md) | Phase 2 | 三重审查：一致性 / 反幻觉 / 去 AI 味 |
