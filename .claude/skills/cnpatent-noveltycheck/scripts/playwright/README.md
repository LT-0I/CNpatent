# Phase B.2 Playwright 自动化脚本

本目录包含 cnpatent-noveltycheck Phase B.2 使用的 Playwright 浏览器自动化脚本。
每个脚本在浏览器上下文中执行，由后台 subagent 通过 Playwright MCP 的 `browser_evaluate` 工具调用。

## 环境搭建（一次性）

```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest
```

依赖：Node.js + Google Chrome。

## 脚本调用方式

subagent 执行步骤：
1. `Read` 脚本文件内容
2. 替换占位符：`.replace('__QUERY__', actualQuery)`
3. `browser_evaluate({ function: scriptContent })`
4. 解析返回的 JSON 结果

## 脚本清单

| 脚本 | 平台 | 功能 | 占位符 |
|---|---|---|---|
| `incopat_check_login.js` | incoPat | 登录态检测 (v1.2.1) | 无 |
| `incopat_inject.js` | incoPat | 命令检索注入 + 点击搜索 | `__QUERY__` |
| `incopat_sort.js` | incoPat | 排序切换为申请日倒序 | 无 |
| `incopat_merge_family.js` | incoPat | 站内简单同族合并 (v1.2.1) | 无 |
| `incopat_extract.js` | incoPat | 选择性 DOM 结果提取 + 申请号 + 同族标志 | `__TOP_N__` |
| `incopat_semantic_inject.js` | incoPat | 语义检索注入 + 点击搜索 | `__SEMANTIC_TEXT__` |
| `cnki_check_login.js` | CNKI | 登录态检测 (v1.2.1) | 无 |
| `cnki_inject.js` | CNKI | 高级检索注入 (SU= 语法) + 点击搜索 | `__QUERY__` |
| `cnki_extract.js` | CNKI | 结果提取 (含 fallback) | `__TOP_N__` |
| `cnki_dismiss_overlay.js` | CNKI | Cookie/遮罩关闭 + CAPTCHA 检测 | 无 |

## IP 登录机制 (v1.2.1)

### 原理

incoPat 和 CNKI 对校园/机构 IP 段做自动认证：访问的客户端 IP 在白名单里时，站点直接派发登录态 cookie，**无需表单、无需密码、无需点按**。Phase B.2 的"AI 自主登录"就是让 Playwright 走这个机制。

### 生效前提

Claude Code 本身必须运行在校园 / 机构认可的 IP 段内。Playwright MCP 是本地子进程，出口 IP 等于 Claude Code 所在主机的 IP。若 Claude Code 不在认可段，IP 登录必然失败，orchestrator 退回用户手工登录模式。

### 验证流程

orchestrator 用"目标页工作元素能否加载"作为 IP 登录是否生效的验证信号：

```
1. browser_tabs new × 4 → 按 user_profile.yml tabs 映射开 4 个标签页
2. browser_navigate 到 4 个目标 URL (不是登录页, 直接目标检索页)
3. 每 tab browser_evaluate *_check_login.js
4. 若 verify_tabs=all 且 4/4 返回 logged_in=true → IP 登录生效, 跳过用户提示
5. 任一 false → 按 on_failure 策略: manual_prompt 退回手工 / abort 终止
```

### 各平台验证判据

- **incoPat**: `navigate('/advancedSearch/init')` 后 `#textarea` (或 `#querytext` for semantic) 存在且 URL 未重定向到 `/` → IP 登录生效
- **CNKI**: 检索 textarea 就绪 + CAPTCHA 不可见 + (`退出`/`个人中心` 链接可见 或 无 `登录` 链接) → IP 登录生效

## 单次查询标准流程

### incoPat 命令检索 (T1)

```
1. browser_tabs → select tab 0
2. browser_navigate → /advancedSearch/init (每次查询前重置)
3. browser_evaluate → incopat_inject.js (替换 __QUERY__)
4. browser_wait_for → 等待 3 秒
5. browser_evaluate → incopat_sort.js (AD DESC)
6. browser_wait_for → 等待 2 秒
7. browser_evaluate → incopat_merge_family.js (站内简单同族合并, v1.2.1)
8. browser_wait_for → 等待 3 秒 (incoPat 服务端重算分页)
9. browser_evaluate → incopat_extract.js (替换 __TOP_N__, 每行已是族代表)
10. Write → .omc/research/incopat_command/queryN.json
```

### incoPat 语义检索 (T2)

```
1. browser_tabs → select tab 1
2. browser_navigate → /semanticSearch/init
3. browser_evaluate → incopat_semantic_inject.js (替换 __SEMANTIC_TEXT__)
4. browser_wait_for → 等待 5 秒 (语义检索较慢)
5. browser_evaluate → incopat_merge_family.js
6. browser_wait_for → 等待 3 秒
7. browser_evaluate → incopat_extract.js (替换 __TOP_N__)
8. Write → .omc/research/incopat_semantic/query1.json
```

### incoPat 抵触申请 (T3)

```
1. browser_tabs → select tab 2
2. browser_navigate → /advancedSearch/init
3. browser_evaluate → incopat_inject.js
   查询含 AD 日期范围: TIABC=(...) AND AD="<18月前>,<今天>"
4. browser_wait_for → 等待 3 秒
5. browser_evaluate → incopat_sort.js
6. browser_wait_for → 等待 2 秒
7. browser_evaluate → incopat_merge_family.js
8. browser_wait_for → 等待 3 秒
9. browser_evaluate → incopat_extract.js
10. Write → .omc/research/incopat_conflict/query1.json
```

### CNKI 高级检索 (T6)

```
1. browser_tabs → select tab 3
2. browser_evaluate → cnki_dismiss_overlay.js (先关闭遮罩)
3. browser_evaluate → cnki_inject.js (替换 __QUERY__, SU= 语法)
4. browser_wait_for → 等待 5 秒
5. browser_evaluate → cnki_extract.js (替换 __TOP_N__)
6. Write → .omc/research/cnki/queryN.json
```

## incoPat 字段代码速查

| 代码 | 含义 |
|---|---|
| TIABC | 标题 + 摘要 + 权利要求 |
| TI | 标题 |
| AB | 摘要 |
| IPC | IPC 分类号 |
| AD | 申请日 (范围语法: `AD="YYYYMMDD,YYYYMMDD"`) |
| PD | 公开(公告)日 |
| AN | 申请号 |
| AP | 申请人 |

## 同族合并 (v1.2.1)

**直接调用 incoPat 站内的合并功能**, 不做客户端启发式族判定。

实测 2026-04-17: 隧道衬砌相关查询 **512 条专利 → 364 个专利族**, 合并率 ~29%。

### 关键 API

incoPat 结果页暴露全局函数 `window.mergeCongeners(mode, liElement)`:

| mode | 效果 |
|---|---|
| 0 | 不合并 (默认) |
| 1 | 简单同族合并 (默认启用) |
| 2 | 扩展同族合并 |
| 3 | DocDB 同族合并 |

`incopat_merge_family.js` 默认走 mode=1 (简单同族合并), 这是 incoPat 推荐、覆盖面最好的选项。

### 字段

合并后 `incopat_extract.js` 返回:

| 字段 | 说明 | 示例 |
|---|---|---|
| `pn` | 族代表公开号 | `CN118570217B` |
| `an` | 申请号 (跨通道去重用) | `CN202410012345.6` |
| `family_merged` | 布尔: incoPat 站内已合并 | `true` |
| `total_text` | 计数原文 | `"364个专利族"` 或 `"共512条"` |

orchestrator 只做跨通道同 `pn` / 同 `an` 合并 + Phase A 去重标记, 不做族内分组。详见 `references/phase-b2-merge-rules.md`。

## 踩坑记录

1. **incoPat AD 日期范围**: 正确语法是 `AD="YYYYMMDD,YYYYMMDD"`（带双引号，逗号分隔）。`AD<=YYYYMMDD` 和 `AD=[date,date]` 会触发字符位置解析错误。
2. **incoPat 结果页按钮数量变化**: init 页有 2 个可见 `input.retrieval`，结果页只有 1 个。脚本已处理两种情况。
3. **incoPat 每次查询前必须重置**: 结果页 URL 不变（仍是 /advancedSearch/init），但 DOM 状态变了。新查询前 `browser_navigate` 回到 `/advancedSearch/init` 重置。
4. **CNKI SU= 分词问题**: 长词组（如 `SU='路面病害'`）命中率低，应拆成 `(SU='路面' OR SU='隧道') AND (SU='病害' OR SU='裂缝')`。
5. **CNKI Cookie 遮罩**: 首次访问可能弹出 Cookie 同意遮罩拦截点击。先调用 `cnki_dismiss_overlay.js`。
6. **CNKI 滑块验证码**: 无法自动化，用户必须手动完成。subagent 检测到验证码时应提示用户处理。
7. **CNKI DOM 版本差异**: cnki_extract.js 包含 fallback 逻辑。如果提取为空，subagent 应使用 `browser_snapshot` 从 accessibility tree 解析。

## Token 预算

| 操作 | 预估 Token |
|---|---|
| 单次注入 + 提取 20 行 | ~3-4k |
| 全页 HTML (未优化) | ~50k |
| **压缩率** | **~94%** |
| 6 通道 × 平均 2 查询 | **~30-40k 总计** |

## DOM 验证日期

所有选择器最后验证于 **2026-04-17**（incoPat 通过实操验证，CNKI 基于已知 DOM 结构）。
如果 incoPat 或 CNKI 更新了页面结构，只需修改对应的脚本文件。
