# Skill Router（优化版）

[English](README.md) | **简体中文**

> 自动把 Cursor / Claude / Codex 路由到合适的已安装技能——不把几百个 skill 全文塞进上下文，也不一次加载十个互相打架的设计技能。

本仓库是对 [YunzhouLi-hub/skill-router](https://github.com/YunzhouLi-hub/skill-router) 的**本地优化版**，针对「技能特别多」和 **Cursor**（`~/.agents/skills`）场景做了加强。

---

## 相对原版改了什么

| 方面 | 原版 | 本优化版 |
|---|---|---|
| 扫描目录 | 仅 `~/.claude/skills` | 多目录：`.agents` → `.claude` → `.cursor/skills-cursor` → `.codex` |
| 去重 | 无 | 按 `name` 去重，优先 Cursor agents 路径 |
| 索引体积 | 整句描述 | 压缩触发摘要（约 56 字） |
| 路由策略 | 能匹配就全加载 | 每轮最多 **1–3** 个，宁精勿滥 |
| 设计技能冲突 | 未处理 | Hallmark / impeccable / taste-* 只选一个 |
| 使用报告 | 每条强制长报告 | 一行摘要；闲聊可省略 |
| 附带产物 | 仅 Markdown | 额外生成 `skills-catalog.json` |
| 安装 | 手动复制 | `python scripts/generate.py --install` |
| YAML 描述 | 仅单行 | 支持 `>`、`\|`、引号描述 |

---

## 快速开始

```bash
cd skill-router
python scripts/generate.py --install
```

会做三件事：

1. 扫描本机技能目录  
2. 在本仓库生成 `SKILL.md` 与 `skills-catalog.json`  
3. 安装到：
   - `%USERPROFILE%\.agents\skills\skill-router\`
   - `%USERPROFILE%\.claude\skills\skill-router\`

以后每装一批新技能，再跑一次即可。

### 指定目录

```bash
python scripts/generate.py --skills-dir "%USERPROFILE%\.agents\skills" --install
```

### 使用更长的触发描述

```bash
python scripts/generate.py --no-compact --install
```

---

## 工作原理

```
~/.agents/skills     ┐
~/.claude/skills     ├─► generate.py ─► SKILL.md 索引 + skills-catalog.json
~/.cursor/skills-*   ┘         │
                               ▼
                     安装后的 skill-router
                               │
         用户任务 → 匹配 1–3 个技能 → Read/加载 → 回答 → 短报告
```

---

## 对话里怎么用

不必每句话点名。做实质工作时，靠 skill 的 description 触发即可。

示例：

- 「做一个落地页」→ 路由 → 在 `hallmark` / `impeccable` / `design-taste-frontend` 里选一个  
- 「审一下这段 Go」→ 语言 + review 类技能  
- 「skill-router 我有哪些设计技能？」→ 直接查索引回答  

相关任务结束后的短报告示例：

```
---
**Skills:** `hallmark` (loaded) · `impeccable` (skipped — overlapping)
```

---

## 设计理念

| 你负责 | Router 负责 |
|---|---|
| 决定装哪些技能 | 发现并索引已安装技能 |
| 多个设计技能时的口味偏好 | 冲突策略 + 必要时反问 |
| 是否强制点名某个技能 | 未点名时的软路由 |

---

## License

MIT（与上游一致）。优化改动在本本地 fork 中维护。
