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
