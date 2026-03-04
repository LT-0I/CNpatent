# Claims Drafting Guide (权利要求书撰写指南)

## Independent Method Claim (独立方法权利要求)

Pattern:
```
权利要求1：
一种[技术名称]方法，其特征在于，包括以下步骤：
S1：[第一步骤描述]；
S2：[第二步骤描述]；
...
Sn：[最后步骤描述]。
```

Rules:
- Use "其特征在于" after the preamble
- Steps separated by Chinese semicolons "；"
- Last step ends with Chinese period "。"
- Keep each step as one sentence covering what is done, not how
- Use "所述" for back-references within steps

## Dependent Claims (从属权利要求)

Pattern:
```
权利要求X：
根据权利要求Y所述的方法，其特征在于，步骤SZ中，[具体细化描述]。
```

Strategies for dependent claims:
1. **Preprocessing details** — Expand preprocessing sub-steps (e.g., specular suppression, CLAHE)
2. **Formula claims** — Add the mathematical formulation for a core computation
3. **Architecture details** — Specify network structure, encoding dimensions
4. **Parameter decomposition** — Detail how a matrix/parameter is represented
5. **Loss function** — Define the specific loss formulation
6. **Density control** — Describe clone/split/prune operations
7. **Fallback mechanism** — Define adaptive refinement triggers and limits

## Storage Medium Claim (存储介质权利要求)

Pattern:
```
权利要求N：
一种计算机可读存储介质，其上存储有计算机程序，其特征在于，
所述计算机程序被处理器执行时实现如权利要求1至M中任意一项所述的方法。
```

## System Claim (系统权利要求)

Pattern:
```
权利要求N：
一种[应用场景]系统，其特征在于，包括：
[采集模块名称]，用于[采集功能]；
存储器，用于存储计算机程序及[数据类型]；
处理器，与所述存储器和所述[采集模块]通信连接，
所述处理器被配置为执行所述计算机程序时实现如权利要求1至M中任意一项所述方法的步骤S1至Sn；
[输出模块名称]，用于[输出功能]。
```

## Claim Dependency Tree Example

```
权利要求1 (独立): 方法总步骤 S1-S5
├── 权利要求2: S1 预处理细节
├── 权利要求3: S2 核心公式
├── 权利要求4: S3 网络结构
├── 权利要求5: S4 参数分解
├── 权利要求6: S5 损失函数
├── 权利要求7: S5 密度控制
└── 权利要求8: S5 回溯机制
权利要求9: 存储介质
权利要求10: 系统
```

## Common Mistakes to Avoid

- Putting formulas in 发明内容 (only allowed in claims and 具体实施方式)
- Using "本发明" in claims (use "所述" instead)
- Missing "其特征在于" in any claim
- Referencing a claim number that doesn't exist
- Using academic language ("we propose", "experiments show")
