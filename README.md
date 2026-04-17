# cnpatent — 中国发明专利技术交底书自动生成器

基于 Claude Code 的中国发明专利技术交底书（.docx）自动生成工具。提供参考素材和目标应用领域，经新颖性 + 创造性初筛后，自动生成符合 CNIPA 规范的完整交底书。

## Skill 家族

本仓库包含 3 个协作的 Claude Code Skill，形成一条完整的专利生成流水线：

```
cnpatent-noveltycheck (唯一入口)
  Phase A  自动免费库筛查 + 大纲生成
  Phase B  B.1 AI 自动精读 + B.2 AI Playwright 自动化检索 (用户仅登录 5 分钟)
  Phase C  三步法创造性判断 + 三色灯决策
      |
      | 绿灯 → 5_verified_outline.md
      v
cnpatent (下游写作)
  Phase 0  接收 verified_outline
  Phase 1  4 Writer 并行生成 (opus)
  Phase 2  Reviewer 审查 + cnpatent-humanizer 润色
  Phase 3  兜底清理 + 公式重编号 + DOCX 写入
  Phase 4  DOCX 验证
  Phase 5  防幻觉 AI 附图提示词
      |
      v
输出: [专利名称]_专利技术交底书.docx
      [专利名称]_全套AI生图提示词.md
```

| Skill | 定位 | 路径 |
|---|---|---|
| **cnpatent-noveltycheck** | 唯一入口，新颖性 + 创造性初筛 | `.claude/skills/cnpatent-noveltycheck/` |
| **cnpatent** | 下游写作，verified_outline 到 .docx | `.claude/skills/cnpatent/` |
| **cnpatent-humanizer** | 去 AI 痕迹润色，Phase 2 自动调用 | `.claude/skills/cnpatent-humanizer/` |

## 快速开始

### 1. 环境准备

确保已安装 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)（CLI），并安装 Python 依赖：

```bash
pip install python-docx
```

### 2. 使用

在本目录下启动 Claude Code，直接对话即可：

```bash
claude
```

```
帮我写一份专利技术交底书，参考这篇论文，目标领域是工业焊缝检测
```

Claude 会自动触发 cnpatent-noveltycheck skill，引导你完成新颖性初筛 + 写作全流程。

**用户需要手动操作的环节**：
1. Phase B.2 — 在 Playwright 浏览器中登录 incoPat 和 CNKI（约 5 分钟），AI 自动完成检索
   - 若未安装 Playwright MCP，降级为手动模式（约 60-90 分钟）
2. 确认绿灯后自动进入写作，无需额外交互

### 3. 依赖 Skill

| Skill | 用途 | 来源 |
|---|---|---|
| **pdf** | 读取 PDF 参考素材 | 内置或 anthropic-skills |
| **docx** | 读取 .docx 参考素材 | 内置或 anthropic-skills |

## 输出文件

| 文件 | 内容 |
|------|------|
| `[专利名称]_专利技术交底书.docx` | 完整的电学类专利技术交底书（一到六节） |
| `[专利名称]_全套AI生图提示词.md` | 每张附图的防幻觉 AI 生图提示词 |

生成的交底书包含以下章节（不含权利要求书）：

```
一、发明名称
二、技术领域
三、背景技术
四、发明内容（发明目的 / 技术解决方案 / 技术效果）
五、附图说明
六、具体实施方式
```

权利要求书由专利代理人根据交底书另行撰写。

## 核心能力

- **前置新颖性筛查** — 写专利前先查重，防止写完才发现撞车
- **场景迁移与微创新** — 从论文场景迁移到目标领域，推导差异化创新点
- **4 Writer 并行架构** — Writer-A/B/C/D 分工并行，opus 模型驱动
- **三层去 AI 痕迹** — 写作预防 + 正则替换 + cnpatent-humanizer 深度润色
- **信息源锚定** — 所有参数标注来源 `[源:论文X节]`，无法确认标 `[待确认]`
- **公式全局重编号** — Phase 3 自动修复 Writer 并行产生的公式编号冲突
- **品牌词自动拦截** — 发明名称里的英文品牌词被功能性描述替换

## 目录结构

```
.claude/skills/
├── cnpatent-noveltycheck/       # 入口 skill
│   ├── SKILL.md
│   ├── DESIGN.md                # 架构设计 (v1.0 + v1.1 补丁)
│   ├── agents/                  # screener / guide / judge 角色文件
│   ├── references/              # 法律标准 / 检索方法 / 模板 / AI精读卡片
│   └── user_profile.yml         # 用户付费库访问配置
├── cnpatent/                    # 下游写作 skill
│   ├── SKILL.md
│   ├── agents/                  # planner / writer-a~d / reviewer 角色文件
│   ├── assets/                  # DOCX 模板
│   ├── references/              # 写作规范 / docx代码模板 / 质量检查清单
│   └── scripts/                 # cnpatent_docx.py / deai_cleanup.py / formula_renumber.py
└── cnpatent-humanizer/          # 去 AI 味 skill
    ├── SKILL.md
    ├── references/              # 7 份检测与改写规范
    └── scripts/                 # audit.py / burstiness.py / regex_clean.py
```

## 常见问题

**Q: 可以跳过新颖性筛查直接写交底书吗？**

不可以。cnpatent 已改造为只接受 cnpatent-noveltycheck 的 `5_verified_outline.md` 作为输入。直接调用 cnpatent 会被拒绝。

**Q: 为什么不生成权利要求书？**

权利要求书是法律文件，涉及保护范围界定。建议交由专业专利代理人根据交底书撰写。

**Q: 支持哪些参考素材格式？**

PDF 论文、.docx 技术文档、纯文本描述、网页链接均可。

**Q: Phase B.2 的人工核查可以省略吗？**

不可以。免费库检索只能做提示性判断，必须走完 Phase B.2 + Phase C 才能出绿灯。

## 许可证

MIT
