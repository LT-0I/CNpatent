# Patent Writing Rules (去AI痕迹 & 专利语言规范)

## Anti-AI Vocabulary Replacement Table

| Forbidden (AI味)         | Replacement (专利味)       |
|--------------------------|---------------------------|
| 显著提升/大幅提升          | 改善 / 提高               |
| 卓越的/优异的             | 较高的 / 可靠的            |
| 颠覆性的                 | — (delete entirely)       |
| 有力保障                 | 确保 / 保证               |
| 完美解决                 | 解决 / 缓解               |
| 创新性地提出              | 提供 / 采用               |
| 巧妙地                   | — (delete entirely)       |
| 充分利用                 | 利用 / 基于               |
| 值得注意的是              | — (delete entirely)       |
| 至关重要                 | — (delete, or 关键)       |
| 首先...其次...最后        | 自然段落递进，不用排比      |
| 其一...其二...其三        | 自然段落递进，不用排比      |

## Formatting Rules

1. **No bold/italic in body text** — Only section titles (技术领域, 背景技术, etc.) use bold via 黑体 font
2. **No bullet lists** in 背景技术 and 发明内容 — Convert to flowing paragraphs with logical transitions
3. **No step titles** — Write "步骤S1：" inline, not as standalone heading
4. **所述 back-references** — Every element mentioned the second time must use "所述xxx"
   - First mention: "通过运动恢复结构算法获取初始稀疏点云"
   - Second mention: "将所述初始稀疏点云输入..."
5. **Semicolons between steps** in claims: S1...；S2...；S3...。(last step ends with period)
6. **No quotation marks** around technical terms — Use them as plain text

## Patent Term Conversion Examples

| Academic Term              | Patent Term                    |
|---------------------------|-------------------------------|
| Cube-based sampling        | 基于空间体素剖分的采样          |
| Neural Radiance Field      | 神经辐射场网络                 |
| 3D Gaussian Splatting      | 三维高斯泼溅                   |
| Structure from Motion      | 运动恢复结构算法               |
| COLMAP                    | 运动恢复结构算法（不写软件名）   |
| alpha compositing          | 透明度加权混合                 |
| differentiable rasterizer  | 可微分光栅化器                 |
| loss function             | 损失函数                      |
| learning rate             | 学习率                        |
| ground truth              | 真实图像 / 真实值              |
| dataset                   | 图像序列 / 样本集              |
| ablation study            | — (删除，专利不写消融实验)      |
| SOTA / state-of-the-art   | 现有技术                      |
| pipeline                  | 处理流程 / 技术方案            |
| feature descriptor        | 特征描述子                     |
| point cloud completion    | 点云补全                      |
| voxel grid                | 体素网格 / 体素单元网格        |

## Section-Specific Guidelines

### 技术领域
- 1-2 sentences only
- Pattern: "本发明属于[大领域]技术领域，具体涉及一种[具体方法]。"

### 背景技术
- Max 3 paragraphs
- Paragraph 1: Clinical/engineering need (why the problem matters)
- Paragraph 2: Existing approaches and their objective limitations
- Paragraph 3: Why current neural rendering methods fall short for this specific scenario
- NO academic citations, NO "[1]" references

### 发明内容
- Pure text, NO formulas
- First paragraph: "针对现有技术的不足，本发明提供一种..."
- Middle: Summarize S1-Sn in one flowing paragraph
- Last paragraph: "本发明的有益效果包括：..." (compress each effect to 1 sentence)

### 附图说明
- One line per figure: "图X为[name]。"
- No verbose scene descriptions

### 具体实施方式
- Engineering "how-to" style, not academic "why" explanations
- Every step must reference at least one figure
- All core computations expressed as LaTeX formulas
- Explain each variable's physical meaning after formulas
- Include concrete parameter values (e.g., N=128, K=256, λ=0.2)

## "一简一繁"描述策略

专利中同时包含已有技术（现有技术的组合使用）和本发明的创新点。二者的描述力度必须形成鲜明对比：

### 已有算法 → 弱化（一笔带过）

对 SfM、NeRF、3DGS 等已被广泛公开的通用算法，**只说"用了什么"，不展开"怎么做"**：
- 压缩为 1-2 句功能性描述，点明输入和输出即可
- 不展开其内部原理、网络结构、训练流程
- 不堆砌教科书推导，避免喧宾夺主
- 措辞："{算法名}为本领域公知技术，此处不再赘述"

示例（弱化）：
```
利用运动恢复结构算法对所述预处理后的图像序列进行特征匹配与三角化，
获得稀疏点云及各帧图像对应的相机位姿参数。
```

### 创新算法 → 强化（充分展开）

对本发明独创的改进点，必须**详尽到本领域技术人员可以复现**：
- 构建"场景痛点 → 技术选择 → 具体操作 → 公式推导 → 参数取值"的完整逻辑链
- 每一步的动机（"为什么这么做"）和操作（"怎么做"）都要写清
- 公式完整保留，变量逐一解释
- 给出具体的实施参数和取值范围

示例（强化）：
```
步骤S4中，由于肛瘘术后创口表面为柔软非刚性粘膜组织，
传统各向同性球形高斯难以贴合弯曲壁面，导致渲染边界模糊。
为此，本发明对每个高斯分布施加基于表面法向量的各向异性约束：

(a) 对补全后的致密点云中每个点 p_i，取其 K 近邻点集（K=20），
构建局部协方差矩阵并进行特征值分解...

(b) 取最小特征值对应的特征向量作为表面法向量 n_i...

(c) 通过 Gram-Schmidt 正交化，由 n_i 构建局部坐标系的旋转矩阵...
```

### 判断标准

| 描述对象 | 篇幅 | 公式 | 参数 |
|----------|------|------|------|
| 已有算法（SfM、基础NeRF、基础3DGS等） | 1-2 句 | 无或极简 | 无 |
| 创新算法（本发明的核心贡献） | 多段 + 子步骤 | 完整推导 | 具体取值 |

**核心原则**：已有算法是"工具"，一句话交代即可；创新算法是"发明点"，必须充分公开到可复现。篇幅分配上，创新部分应占具体实施方式总篇幅的 70% 以上。

---

## 公式分层管理策略

专利中的公式分为两类，应区别对待：

### 教科书公式（可精简）
通用算法的标准推导（如 NeRF 的位置编码、体渲染积分、3DGS 的高斯概率密度函数、alpha 混合公式等），这些公式在教科书或通用论文中已被充分公开。

处理方式：
- **不要整段删除**，而是压缩为一句概括 + 关键公式
- **领域化"蒙皮"**：将通用变量重新释义为目标领域的物理含义
- 例：NeRF 的 σ_i → "组织空间占据概率"，α_i → "次表面散射衰减因子"，c_i → "隐蔽组织颜色"

### 创新公式（必须保护）
体现本发明核心贡献的公式（如 PCA 法向量约束、Gram-Schmidt 正交化构建旋转矩阵、尺度约束、混合损失函数等）。

处理方式：
- **完整保留**，一个变量都不能省
- 公式后紧跟**每个变量的物理含义**解释
- 给出具体的参数取值范围

### 领域化"蒙皮"示例

| 通用变量 | 领域化释义（医学三维重建） | 领域化释义（工业检测） |
|----------|--------------------------|----------------------|
| σ (density) | 组织空间占据概率 | 缺陷区域占据概率 |
| α (opacity) | 次表面散射衰减因子 | 表面反射衰减因子 |
| c (color) | 隐蔽组织颜色 | 缺陷区域色彩响应 |
| T (transmittance) | 光线穿透组织的累积透射率 | 光线穿透材料的累积透射率 |

## 具体实施方式的段落结构

### 子步骤拆分 (a/b/c/d/e)

当一个步骤包含多个操作时，避免写成一整段，应拆分为：
- **1-2 句简短引言**（说明本步骤目的）
- **带编号的子步骤** (a)、(b)、(c)...（每个子步骤 1-3 句）

示例：
```
步骤S3：对所述稀疏点云进行基于立方体的神经辐射场点云补全，
获得致密化的补全点云。如图4所示，具体包括：

(a) 以所述稀疏点云的空间范围构建三维包围盒，
将其均匀剖分为 N×N×N 个体素单元；

(b) 在每个体素单元中，利用分层采样策略
沿每条穿入光线均匀选取 M 个查询点；

(c) 将查询点的三维坐标经位置编码后，
连同其所在立方体的局部特征向量，输入多层感知机...
```

好处：
- 审查员快速定位每个操作的技术细节
- 避免整段大块文本导致关键操作被淹没
- 从属权利要求可直接引用子步骤编号（如"步骤S3的(b)中..."）
