# Skill Router (Optimized Fork)

**English** | [简体中文](README_CN.md)

> Auto-route Cursor / Claude / Codex to the right installed skills — without dumping every skill into context or loading ten overlapping design skills.

This is an **optimized fork** of [YunzhouLi-hub/skill-router](https://github.com/YunzhouLi-hub/skill-router), tuned for machines with **hundreds** of skills and for **Cursor** (`~/.agents/skills`) as well as Claude Code.

---

## What changed vs upstream

| Area | Upstream | This fork |
|---|---|---|
| Scan roots | `~/.claude/skills` only | Multi-root: `.agents` → `.claude` → `.cursor/skills-cursor` → `.codex` |
| Dedup | None | By skill `name`, prefer Cursor agents path |
| Index size | Full sentences | Compact triggers (~56 chars) |
| Routing | Load all matches | Cap **1–3** skills; precision first |
| Design conflicts | Not handled | Hallmark / impeccable / taste-* pick one |
| Reports | Mandatory long block every turn | Compact one-liner; skip trivial turns |
| Tooling | Markdown only | Also emits `skills-catalog.json` |
| Install | Manual copy | `python scripts/generate.py --install` |
| YAML desc | Single-line only | Supports `>`, `\|`, quoted descriptions |

---

## Quick start

```bash
cd skill-router
python scripts/generate.py --install
```

This will:

1. Scan your local skill directories  
2. Write `SKILL.md` + `skills-catalog.json` in this repo  
3. Install into:
   - `%USERPROFILE%\.agents\skills\skill-router\`
   - `%USERPROFILE%\.claude\skills\skill-router\`

Re-run after installing new skills.

### Custom roots

```bash
python scripts/generate.py --skills-dir "%USERPROFILE%\.agents\skills" --install
```

### Longer blurbs (less compact)

```bash
python scripts/generate.py --no-compact --install
```

---

## How it works

```
~/.agents/skills     ┐
~/.claude/skills     ├─► generate.py ─► SKILL.md index + skills-catalog.json
~/.cursor/skills-*   ┘         │
                               ▼
                     skill-router skill (installed)
                               │
              user task → match 1–3 skills → Read/load → answer → short report
```

---

## Usage in chat

You don’t need to call it by name for every message. For substantive work, the skill’s description should surface it.

Examples:

- 「做一个落地页」→ router → pick `hallmark` *or* `impeccable` *or* `design-taste-frontend`
- 「审一下这段 Go」→ language + review skill
- 「skill-router 我有哪些设计技能？」→ answers from the index

Expected report (when relevant):

```
---
**Skills:** `hallmark` (loaded) · `impeccable` (skipped — overlapping)
```

---

## Design philosophy

| You own | Router owns |
|---|---|
| Which skills to install | Discover + index what’s installed |
| Taste preference when several design skills exist | Default conflict policy + ask if unclear |
| Whether to force a named skill | Soft routing for unnamed tasks |

---

## License

MIT (same as upstream). Optimized changes live in this local fork.
