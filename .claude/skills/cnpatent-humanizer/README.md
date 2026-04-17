# cnpatent-humanizer

中文专利文本去 AI 味器。专为专利文体（术语锁死、句式固定、法律严谨性）设计，不同于通用 humanizer。

## 定位

cnpatent skill 家族的第三个成员。在 cnpatent Phase 2 (Reviewer 审查) 中被自动调用，对 Writer 输出做去 AI 痕迹润色。也可独立使用。

```
cnpatent-noveltycheck (入口) --> cnpatent (写作) --> cnpatent-humanizer (润色)
                                     Phase 2 自动调用 ───────────┘
```

## 核心能力

- 3 级词汇检测：always-replace / cluster-flag / density-flag
- 4 维加权评分（0-100）
- 9 步改写流水线
- "不要过度矫正" 保护机制：专利的正式语气本身不是 AI 味
- 中文专利特有 AI 痕迹检测：成语堆砌、动词名词化、标点混用、低 burstiness

## 文件结构

```
cnpatent-humanizer/
├── SKILL.md                 # 主指令 (303 行)
├── README.md                # 本文件
├── references/              # 7 份下沉文档
│   ├── three-tier-vocabulary.md    # 3 级词汇表
│   ├── scoring-system.md           # 评分系统
│   ├── section-rules.md            # 按章节的改写规则
│   ├── patent-anti-patterns.md     # AI 反模式库
│   ├── chinese-specific-tells.md   # 中文特有 AI 痕迹
│   ├── do-not-overcorrect.md       # 过度矫正防护
│   └── protected-regions.md        # 受保护区域
└── scripts/
    ├── audit.py             # 自动审计脚本
    ├── burstiness.py        # burstiness 计算
    └── regex_clean.py       # 正则清理
```

## 使用方式

通常由 cnpatent Phase 2 Reviewer 自动调用，不需要手动触发。

独立使用时，对已有的专利文本 .md 文件调用：

```
请用 cnpatent-humanizer 润色 sections/6_implementation.md
```

## 注意

不要用通用 humanizer skill 处理专利文本。通用 humanizer 会引入第一人称、口语化、观点性表达，严重破坏专利文书的法律严谨性。
