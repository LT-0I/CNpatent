# 数据库目录 —— CNpatent-noveltycheck

> 按"付费 / 免费专利 / 非专利"三层组织。每个条目给出 URL、覆盖范围、核心特色、检索语法、中文支持、2026 年可用性。

## 分层总览

| 层级 | 数据库 | 角色 | 当前用户可访问 |
|---|---|---|:---:|
| **T1 必查** | incoPat | CN 主力 + 语义检索 | ✓ (校园 IP) |
| **T2 强烈推荐** | PatSnap (智慧芽) | CN 备选 + 中文友好 | — |
| **T2 强烈推荐** | Derwent Innovation | DWPI 标准化摘要 + AI Search | — |
| **T2 强烈推荐** | Questel Orbit | Boolean + 近似运算符 | — |
| **免费兜底** | CNIPA pss-system | CN 官方权威 | ✓ |
| **免费兜底** | Google Patents | 全球 + Prior Art Finder | ✓ |
| **免费兜底** | WIPO PATENTSCOPE | PCT + CLIR 跨语言 | ✓ |
| **免费兜底** | The Lens | 全球结构化 + API | ✓ |
| **非专利必查** | Google Scholar | 英文论文 | ✓ |
| **非专利必查** | arXiv | 预印本 (CS / ML) | ✓ |
| **非专利必查** | CNKI 中国知网 | 中文学位 + 会议 | ✓ (校园 IP) |

---

## T1 付费：incoPat

| 字段 | 值 |
|---|---|
| **中文名** | 合享新创 / incoPat |
| **URL** | https://www.incopat.com/ |
| **运营方** | 合享智慧 (与"合享新创"是同一产品线) |
| **覆盖范围** | 170+ 国家和地区，1 亿 + 专利文献 |
| **访问方式** | 机构 IP 自动登录 / 个人账号 / 集团订阅 |
| **当前用户** | 校园 IP 登录，无需注册，无额度限制 |

### 核心特色

1. **10 种检索方式**
   - 智能检索（自然语言 + 关键词自动扩展）
   - 高级检索（字段组合 + Boolean）
   - 命令行检索（240+ 字段可用）
   - **语义检索**（粘贴段落做概念召回）← 本 skill 重点使用
   - 分类号检索（IPC / CPC / LocarNo）
   - 扩展检索（同族 / 引证 / 诉讼）
   - 法律状态检索
   - 批量检索（导入专利号列表）
   - 文献检索（非专利文献）
   - 图像检索（设计专利外观）

2. **240+ 检索字段** 含：
   - 标准字段：TI / AB / CL / IPC / CPC / AD / PD / PA
   - 家族字段：同族去重 / 扩展家族
   - 法律字段：授权 / 驳回 / 无效 / 诉讼状态
   - 价值字段：引证次数 / 剩余寿命 / 权项数
   - 申请人字段：母公司 / 所属集团 / 合作关系

3. **抵触申请检索**（本 skill 独特依赖）
   - 支持早期申请 / 未公开申请的检索
   - 公开状态筛选："早期申请"、"未公开"、"已公开"
   - 这是大多数免费库不具备的能力

4. **同族合并**
   - 默认按简单家族 (DOCDB simple family) 去重
   - 可切换为扩展家族 (INPADOC) 或 PatSnap 自建家族

### 检索语法速查

| 算子 | 含义 | 示例 |
|---|---|---|
| `AND` | 逻辑与 | `A AND B` |
| `OR` | 逻辑或 | `A OR B` |
| `NOT` | 逻辑非 | `A NOT B` |
| `()` | 分组 | `(A OR B) AND C` |
| `""` | 短语 | `"neural network"` |
| `*` | 多字符通配 | `neural*` → neural, neurally, ... |
| `?` | 单字符通配 | `colo?r` → color, colour |
| `NEAR/n` | 相距 ≤ n 词 | `A NEAR/5 B` |
| `WITH` | 同一字段内 | `A WITH B` |
| `SAME` | 同一段落内 | `A SAME B` |
| `=` | 字段赋值 | `TI=neural` |
| `<=` / `>=` | 数值比较（日期） | `AD<=2026-04-15` |

**字段代码**：

| 代码 | 含义 |
|---|---|
| `TI` | 标题 |
| `AB` | 摘要 |
| `CL` | 权利要求 |
| `TIABC` | 标题+摘要+权要合并 |
| `DSC` | 说明书 |
| `IPC` | IPC 分类 |
| `CPC` | CPC 分类 |
| `AD` | 申请日 |
| `PD` | 公开日 |
| `PA` | 申请人 |
| `IN` | 发明人 |
| `APN` | 申请号 |
| `PN` | 公开号 |

### 典型检索式示例

```
# 示例 1: 无人机集群 + 强化学习 + G06N
TIABC=(无人机 OR UAV OR drone OR "unmanned aerial") 
AND TIABC=(集群 OR swarm OR formation OR 编队) 
AND TIABC=(强化学习 OR "reinforcement learning" OR Q-learning) 
AND IPC=(G06N OR G05D) 
AND AD<=2026-04-15

# 示例 2: 抵触申请检索 (近 18 个月)
TIABC=(肛瘘 OR "anal fistula") 
AND TIABC=("三维重建" OR "3D reconstruction" OR NeRF) 
AND AD>=2024-10-15 
AND AD<=2026-04-15
# + UI 筛选: 公开状态 = 早期申请 / 未公开
```

### 2026 年状态

运营中，校园 IP 登录稳定。界面为中文，命令行检索语法稳定。

---

## T2 付费：PatSnap (智慧芽)

| 字段 | 值 |
|---|---|
| **中文名** | 智慧芽 |
| **URL** | https://www.patsnap.com/ |
| **覆盖范围** | 116 国 / 地区，1.3 亿 + 专利 |
| **访问方式** | 机构订阅为主，部分高校 IP 登录 |

### 核心特色

- **智能检索**：自然语言 + AI 理解
- **价值评分**：按专利价值（剩余寿命 / 引证 / 权项数）排序
- **全球覆盖**：116 国，覆盖比 incoPat 略广
- **10 种检索方式**（和 incoPat 类似）
- **中文界面 + 中文检索全球**

### 与 incoPat 对比

| 维度 | incoPat | PatSnap |
|---|:---:|:---:|
| CN 专利覆盖 | 更全 | 稍弱 |
| 非 CN 全球覆盖 | 强 | 更强 |
| 语义检索 | 有 | 有 |
| 智能检索 | 有 | 更成熟 |
| 价值评分 | 无 | 有 |
| 命令行检索 | 240+ 字段 | 字段数更少 |
| 中文界面 | 有 | 有 |

**本 skill 的决策**：用户有 incoPat，PatSnap 作为 T1 的可选替代。如果用户同时有两者，优先 incoPat（CN 更全 + 命令行更强）。

---

## T2 付费：Derwent Innovation

| 字段 | 值 |
|---|---|
| **英文名** | Derwent Innovation (Clarivate) |
| **中文名** | 德温特创新 |
| **URL** | https://derwentinnovation.clarivate.com.cn/ |
| **覆盖范围** | 全球 130M+ 专利，约 67M 同族 |
| **访问方式** | 付费订阅，机构为主 |

### 核心特色

1. **DWPI 摘要**：Derwent World Patents Index
   - 900+ 编辑团队每周手工处理 9 万篇新专利
   - 用**标准化技术术语**重写摘要，去除营销语言
   - 分三节：Novelty / Use / Advantage / Description of Drawing
   - **核心价值**：关键词检索会漏掉的"换皮"专利，DWPI 标准化摘要能命中

2. **2024 年 Q4 上线 AI Search**
   - 基于 transformer 的自然语言搜索
   - 相当于全库的向量检索
   - 比传统 Boolean 召回率高

3. **多语言翻译**
   - 中日韩原文自动翻译为英文
   - 检索时可同时查全球多语言专利

### 与 incoPat 语义检索对比

Derwent 的 DWPI 摘要由人工标引，精度最高但有延迟（1-2 个月）。incoPat 语义检索是算法召回，实时但精度略低。

**在缺失 Derwent 的情况下**，本 skill 用 incoPat 语义检索作为替代。失去的主要是 DWPI 的"人工标引精度"，但换皮专利的召回能力还在。

### 2026 年状态

运营中，AI Search 稳定上线。界面为英文，提供中文翻译。

---

## T2 付费：Questel Orbit Intelligence

| 字段 | 值 |
|---|---|
| **URL** | https://www.questel.com/patent/ip-intelligence-software/orbit-intelligence/ |
| **覆盖范围** | CN / US / JP / KR / EP 五大局 85% + |
| **访问方式** | 付费订阅 |

### 核心特色

- **同时使用 Boolean + 近似运算符**（其他库通常二选一）
- **语义 + 引证 + 分类三重相似检索**
- **Designer 模块**：设计专利图像检索
- **FTO 模块**：freedom-to-operate 分析

### 典型使用场景

Orbit 在 FTO 和无效检索场景下优于 incoPat，但对中文原文的处理弱于 incoPat。本 skill 的初筛场景不依赖 FTO 能力，所以 Orbit 不是必需的。

---

## 免费兜底：CNIPA 专利检索及分析系统

| 字段 | 值 |
|---|---|
| **中文名** | 专利检索及分析系统（官方名） |
| **URL** | https://pss-system.cponline.cnipa.gov.cn/ |
| **运营方** | 国家知识产权局 |
| **覆盖范围** | 105 国 / 地区，CN 数据最权威 |
| **访问方式** | 免费，需注册账号 |

### 核心特色

- **完全免费**，CNIPA 官方数据源
- 常规检索 / 高级检索 / 命令行检索 / 导航 / 专题库 5 种入口
- 9 种语言界面（中 / 英 / 日 / 德 / 法 / 俄 / 韩 / 西 / 葡）
- 同族、引证、法律状态
- PDF 全文下载

### 限制

- UI 加载慢，查询响应一般 3-10 秒
- 海外专利检全率不如 PatSnap / incoPat
- **无抵触申请检索**（这是商业库的独有能力）
- 命令行检索算子和 incoPat 略有差异

### Phase A 使用方式

Phase A 自动查询时调用 WebSearch（`site:pss-system.cponline.cnipa.gov.cn` + 关键词）。Phase B 让用户人工登录做命令行检索（如果用户有账号）。

---

## 免费兜底：Google Patents

| 字段 | 值 |
|---|---|
| **URL** | https://patents.google.com/ |
| **覆盖范围** | 100+ 局，120M+ 文献 + Google Scholar 非专利文献 |
| **访问方式** | 免费 |

### 核心特色

- **Prior Art Finder**：粘贴方案段落做现有技术检索
  - 自然语言输入
  - Google 语义排序
  - 含非专利文献（论文 / 期刊）
- CPC 分类浏览
- 完整全文 + PDF 下载
- 支持中文检索（但中文原文索引精度略弱）

### 本 skill 使用方式

- Phase A 自动查询的主力之一
- Phase B 可选交叉验证（Prior Art Finder 粘贴式）
- 不适合做深度检索（排序不够精准）

---

## 免费兜底：WIPO PATENTSCOPE

| 字段 | 值 |
|---|---|
| **URL** | https://patentscope.wipo.int/ |
| **运营方** | 世界知识产权组织 |
| **覆盖范围** | PCT 全文 + 几十个国家局 |
| **访问方式** | 免费 |

### 核心特色

- **CLIR 跨语言检索**
  - URL: https://patentscope.wipo.int/search/en/clir/clir.jsf
  - 支持 13 语言（中 / 英 / 日 / 韩 / 德 / 法 / 西 / 葡 / 俄 / 阿 / 印尼 / 泰 / 越）
  - 自动同义词扩展
  - 对日德俄专利覆盖强

### 本 skill 使用方式

- Phase A 自动查询（跨语言补强）
- Phase B 可选交叉（查日德韩专利）

---

## 免费兜底：The Lens

| 字段 | 值 |
|---|---|
| **URL** | https://www.lens.org/ |
| **运营方** | 开源非盈利 |
| **覆盖范围** | 全球专利 + 学术文献联动 |
| **访问方式** | 免费，登录后可导出 5 万条 |

### 核心特色

- 结构化查询 / 集合管理 / 警报
- 专利 + 学术文献联动检索（独家特色）
- 提供免费 API
- 可用于批量自动化

### 本 skill 使用方式

- Phase A 自动查询（结构化检索）
- 未来可接入 API 做自动化批量检索

---

## 非专利必查：Google Scholar

| 字段 | 值 |
|---|---|
| **URL** | https://scholar.google.com/ |
| **覆盖范围** | 英文论文 + 学位论文 + 会议 + 专利链接 |

### 重要性

**算法 / 软件 / 电学类专利必查**。学术论文构成现有技术，可破坏新颖性。许多发明人忽略这一点，导致专利申请被驳回。

### 使用方式

- Phase A 自动查询（通过 WebSearch）
- Phase B 人工核查必选

### 检索技巧

- 时间过滤（自定义范围到今天）
- 排序方式（相关度 / 日期）
- 引用扩展（点击"Cited by"追溯）
- 相关文章（点击"Related articles"）

---

## 非专利必查：arXiv

| 字段 | 值 |
|---|---|
| **URL** | https://arxiv.org/ |
| **覆盖范围** | 预印本 (CS / Math / Physics / ...) |

### 重要性

**AI / ML / CS 必查**。arXiv 是这些领域的首发地，很多技术在正式发表前已经出现在 arXiv，构成现有技术。

### 常用 category（电学 / 软件类）

| Category | 含义 |
|---|---|
| `cs.AI` | 人工智能 |
| `cs.LG` | 机器学习 |
| `cs.CV` | 计算机视觉 |
| `cs.NE` | 神经网络 |
| `cs.RO` | 机器人 |
| `cs.CL` | 计算语言学 / NLP |
| `cs.CR` | 密码学 / 安全 |
| `cs.DC` | 分布式 / 并行 / 集群 |
| `cs.DS` | 数据结构 / 算法 |
| `eess.IV` | 图像 / 视频处理 |
| `eess.SP` | 信号处理 |

### 使用方式

- Advanced Search 指定 category + keywords
- 时间过滤到今天
- 读 Top 20 摘要

---

## 非专利必查：CNKI 中国知网

| 字段 | 值 |
|---|---|
| **URL** | https://www.cnki.net/ |
| **覆盖范围** | 中文期刊 / 学位论文 / 会议 / 报纸 |
| **访问方式** | 校园 IP 登录 (机构订阅) |

### 重要性

**中文学位论文和会议论文是中文现有技术的主库**。Google Scholar 对中文学位论文覆盖有限，CNKI 是这类文献的唯一全面入口。

如果你的发明和国内学位论文撞车，**只有 CNKI 能查到**。

### 使用方式

- 主题检索 / 篇名检索 / 关键词检索
- 文献类型筛选（学位论文 + 会议论文为主）
- 时间筛选
- 学科分类筛选

---

## 其他可考虑的库（2026 年状态待核实）

| 名称 | 状态 | 备注 |
|---|---|---|
| 大为 innojoy | 需核实 | 国内付费，AI 助手 |
| Patentics (索意互动) | 需核实 | 国内付费，机器标引 |
| 佰腾 Baiten | 运营中 | 免费 + 付费，功能弱于 incoPat |
| LexisNexis PatentAdvisor | 运营中 | 美国市场为主 |

---

## 数据库选择的决策树（本 skill 当前用户）

```
Phase A (自动):
  Google Patents + CNIPA pss + PATENTSCOPE + The Lens + Scholar + arXiv

Phase B (人工):
  incoPat 命令行 + 语义 (必)
  incoPat 抵触申请检索 (必)
  Google Scholar + arXiv + CNKI (必)
  Google Patents Prior Art Finder (可选)
  PATENTSCOPE CLIR (可选)
```

用户未来获得新库访问时，改 `user_profile.yml`，Phase B 的 Guide agent 会自动加入对应卡片。
