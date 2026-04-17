# cnpatent-noveltycheck Agents — 角色模板文件

> 本目录遵循与 cnpatent 相同的"角色模板文件"约定。**不是**原生 Claude Code 子 agent。

## 架构说明

Claude Code 的原生 subagent 发现机制只扫描 `.claude/agents/` 和 `~/.claude/agents/`，**不会**递归进 `.claude/skills/<skill>/agents/`。因此本目录下的文件 **frontmatter 中的 `model` 字段不会被自动读取**，不能当作原生子 agent 调用。

它们是 **角色提示词模板**。orchestrator（主 Claude 会话）的调用流程：

```python
# 伪代码
role_file = Read("agents/cnpatent-noveltycheck-screener.md")
frontmatter = parse_frontmatter(role_file)  # 提取 model, description, tools, outputs
body = extract_body(role_file)              # 角色职责主体

task_context = compose_task_context(...)     # 本次任务的具体数据

full_prompt = body + "\n\n" + task_context

Agent(
    subagent_type="general-purpose",
    model=frontmatter["model"],               # ← 这里显式传
    prompt=full_prompt,
    run_in_background=True                    # Phase A 并行 / Phase B-C 串行
)
```

**唯一的运行时强制点** 是 orchestrator 在调用 Agent 工具时的 `model=` 参数。orchestrator 从角色文件 frontmatter 读出 model 字段，然后显式传给 Agent 工具。如果 orchestrator 忘了传，frontmatter 里写多少都没用。

## 角色文件清单

| 文件 | 阶段 | 模型 | 输出 |
|---|---|---|---|
| `cnpatent-noveltycheck-screener.md` | Phase A | opus | 0_input_summary / 1_auto_novelty_report / 2_candidate_outline |
| `cnpatent-noveltycheck-guide.md` | Phase B | opus | 3_manual_search_guide / 4_manual_search_template |
| `cnpatent-noveltycheck-judge.md` | Phase C | opus | 5_verified_outline / 5_adjustment_suggestions / 5_rejection_report |

## 调用约定

### 1. Phase A (串行启动, 内部并行检索)

Phase A 需要串行启动（等用户输入 → screener 处理）。screener 内部通过并发 WebSearch 调用实现检索并行。

```python
role_file = Read("agents/cnpatent-noveltycheck-screener.md")
body = extract_body(role_file)

task_context = f"""
# 本次任务

参考文献: {reference_path}
目标应用领域: {target_domain}
已知相关专利: {known_patents or "无"}
工作目录: {work_dir}
"""

Agent(
    subagent_type="general-purpose",
    model="opus",   # ← 显式传, 不能省
    prompt=body + "\n\n" + task_context,
    description="Phase A novelty screener"
)
```

### 2. Phase B (串行启动)

Phase B 完全串行，依赖 Phase A 的输出。

```python
role_file = Read("agents/cnpatent-noveltycheck-guide.md")
body = extract_body(role_file)
profile = Read("user_profile.yml")

task_context = f"""
# 本次任务

Phase A 报告: {work_dir}/1_auto_novelty_report.md
用户配置: {profile_content}
工作目录: {work_dir}
"""

Agent(
    subagent_type="general-purpose",
    model="opus",
    prompt=body + "\n\n" + task_context,
    description="Phase B manual search guide generator"
)
```

### 3. Phase C (串行启动, 依赖用户回填)

Phase C 触发条件是 `4_manual_search_template.md` 已被用户填写。orchestrator 应先读取并验证该文件非空。

```python
template = Read(f"{work_dir}/4_manual_search_template.md")
if not has_filled_hits(template):
    # 提示用户先完成 Phase B
    return

role_file = Read("agents/cnpatent-noveltycheck-judge.md")
body = extract_body(role_file)

task_context = f"""
# 本次任务

候选大纲: {work_dir}/2_candidate_outline.md
用户填写的人工核查表: {work_dir}/4_manual_search_template.md
工作目录: {work_dir}
"""

Agent(
    subagent_type="general-purpose",
    model="opus",
    prompt=body + "\n\n" + task_context,
    description="Phase C novelty judge"
)
```

## 设计原则

### 1. 角色文件 body 是常驻指令

禁用词表、三步法细则、特征对比格式、禁用句式等规则写在角色文件 body 里，作为 agent 的"长期记忆"。orchestrator 每次调用时**不要在 task_context 里重复注入**这些规则，避免 prompt 膨胀和规则漂移。

### 2. task_context 只注入本次特有信息

每次调用时 task_context 只含：
- 本次要处理的文件路径
- 本次要查询的关键词 / IPC
- 用户对本次任务的特殊要求（如果有）

### 3. Rubric-based Judge (非 open critique)

Judge 角色使用 closed rubric 做结构化判断，不做开放式评论。这是吸取 cnpatent Reviewer 的设计经验：
- open critique 会触发 sycophancy（Judge 附和 Screener）
- 允许 Judge 输出替代大纲会触发 over-correction（改变用户意图）
- 硬 cap 黄灯回路为"用户手动重跑"防止 infinite revision loop

### 4. 模型层级强制

所有 agent 都必须用 opus。Phase C 的 Judge 尤其吃推理深度（三步法需要多步因果链），不能降级到 sonnet。

**orchestrator 调用时务必显式传 `model="opus"`**。

## 迁移路径

如果未来 Claude Code 支持 `.claude/skills/<skill>/agents/` 下的 subagent 自动发现，本目录可以直接迁移到 `.claude/agents/`（把 `cnpatent-noveltycheck-*` 作为前缀区分归属）。届时 orchestrator 的 `Read + 显式 model 传参` 协议可以简化为直接 `Agent(subagent_type="cnpatent-noveltycheck-screener", ...)`。

在此之前，本目录的文件只是**角色模板**，由 orchestrator 手动加载和执行。
