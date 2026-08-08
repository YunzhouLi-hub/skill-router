---
name: skill-router
description: >
  Central skill index and router for Cursor / Claude / Codex. Use when deciding
  which installed skills to apply, when many skills are installed, or when the
  user asks which skill to use. Match the task to 1-3 skills, then load them.
  Skip for trivial chit-chat. Prefer precise matches over loading everything.
version: 1.1.0-optimized
---

# Skill Router (Optimized)

> **Directive**: For substantive tasks (code, design, research, deploy, docs),
> consult this index **before** deep work. Pick **1-3** best-fit skills, load them,
> then answer. Do **not** load every weak match. Skip this skill for greetings
> and one-line clarifications.

---

## 1. Skill Index

<!-- SKILL_INDEX_START -->
> Auto-generated 2026-08-08 03:21 UTC — **0** unique skills


<!-- SKILL_INDEX_END -->

---

## 2. How to load a skill (Cursor / Claude)

1. Find matching skill names in the index below.
2. **Cursor**: `Read` the skill file at the path under `~/.agents/skills/<name>/SKILL.md`
   (or the path shown in your environment’s skill list), then follow it.
3. **Claude Code**: use the Skill tool / open `~/.claude/skills/<name>/SKILL.md`.
4. If two design skills conflict (e.g. Hallmark vs impeccable vs taste-*), ask the
   user which aesthetic to follow, or pick one and state why.

---

## 3. Routing Rules

### Rule 1 - Precision over volume
- Load **at most 3** skills per turn unless the user explicitly asks for more.
- Prefer the **most specific** skill (language/framework/domain) over generic ones.
- If confidence is low, load **one** skill or ask a short clarifying question.

### Rule 2 - Useful combos (examples)
| Task | Suggested combo |
|---|---|
| New marketing/landing UI | `hallmark` **or** `impeccable` **or** `design-taste-frontend` (pick one) |
| Frontend polish / a11y | `impeccable` + optionally `frontend-design` |
| API design | `api-design` + language backend skill |
| Git / PR | `git-workflow` or Cursor git rules; don’t over-load |
| Research | `deep-research` / `exa-search` (if installed) |
| Security-sensitive code | relevant language reviewer + `security-review` / `security-scan` |

### Rule 3 - Design-skill conflict policy
You may have several anti-slop / taste skills installed. **Do not stack them all.**
Priority when user does not specify:
1. Explicit name mention (`hallmark`, `impeccable`, `taste-skill`, …)
2. Else one primary design skill for greenfield UI
3. Mention alternatives briefly if relevant

### Rule 4 - When NOT to route
- Pure chit-chat, thanks, or "ok"
- User already named the exact skill to use
- Task is fully covered by repo rules / user rules already in context

---

## 4. Usage Report (compact)

After substantive answers where routing mattered, append a **short** report:

```
---
**Skills:** `skill-a` (loaded) · `skill-b` (skipped - overlapping)
```

- One line is enough. Omit the report for trivial turns.
- If no skill matched: `**Skills:** none (general answer)`

---

## 5. Refresh index

```bash
# Cursor-first (default multi-root scan)
python scripts/generate.py

# Custom roots
python scripts/generate.py --skills-dir "%USERPROFILE%\.agents\skills" --skills-dir "%USERPROFILE%\.claude\skills"

# Install into Cursor agents skills
python scripts/generate.py --install
```

Also writes `skills-catalog.json` for tooling / search.
