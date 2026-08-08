#!/usr/bin/env python3
"""
Skill Router — optimized index generator

Improvements over upstream:
- Scan multiple skill roots (Cursor / Claude / Codex)
- Deduplicate by skill name (prefer .agents > .claude > .cursor)
- Compact index (short triggers) so large inventories fit in context
- Richer auto-categorization + optional JSON catalog
- Skip self (skill-router) from the index
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()

# Preferred scan order: earlier = higher priority when deduping
DEFAULT_SKILL_DIRS = [
    HOME / ".agents" / "skills",
    HOME / ".claude" / "skills",
    HOME / ".cursor" / "skills-cursor",
    HOME / ".codex" / "skills",
]

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "SKILL.md"
DEFAULT_JSON = Path(__file__).resolve().parent.parent / "skills-catalog.json"

# Category rules: first match wins. Order matters — more specific first.
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Skill Meta / 技能管理", [
        "skill-router", "skill router", "skills add", "manage skills",
        "migrate-to-skills", "create-skill", "create-rule", "create-hook",
        "hookify", "rules-distill",
    ]),
    ("Design Systems / 设计系统", [
        "hallmark", "impeccable", "taste", "design taste", "frontend-design",
        "visual design", "brandkit", "typography", "ui design", "anti-ai-slop",
        "minimalist-ui", "brutalist", "stitch-design", "high-end-visual",
        "design-system", "design system", "figma", "image-to-code",
        "imagegen-frontend", "canvas-design", "brand-guidelines",
    ]),
    ("Architecture / 规划与架构", [
        "architect", "blueprint", "hexagonal", "adr", "architecture decision",
        "system design", "code-architect", "planner", "define-goal",
    ]),
    ("Code Quality / 代码质量", [
        "code review", "coding standard", "clean code", "code tour",
        "onboarding", "codebase", "refactor", "simplifier", "silent-failure",
        "repo-scan", "click-path",
    ]),
    ("Git & Version Control", [
        "git workflow", "github", "version control", "commit", "pull request",
        "release", "babysit",
    ]),
    ("API & Backend / API & 后端", [
        "api-design", "rest api", "backend", "middleware", "endpoint",
        "nestjs", "springboot", "django", "laravel", "api connector",
    ]),
    ("Database / 数据库", [
        "database", "sql", "migration", "schema", "orm", "postgres", "jpa",
    ]),
    ("DevOps & Deploy", [
        "docker", "kubernetes", "deploy", "ci/cd", "pipeline", "container",
        "infrastructure", "harness", "migrate-to-builds", "render-deploy",
    ]),
    ("Testing / 测试", [
        "test", "e2e", "playwright", "unit test", "benchmark", "qa",
        "regression", "tdd",
    ]),
    ("Frontend / 前端", [
        "frontend", "react", "vue", "nextjs", "nuxt", "css", "component",
        "accessibility", "wcag", "canvas", "statusline",
    ]),
    ("Mobile / 移动端", [
        "android", "ios", "flutter", "mobile", "swiftui", "kotlin", "compose",
    ]),
    ("Language-specific / 语言专项", [
        "golang", "java ", "python", "cpp", "c++", "c#", "dotnet", "rust",
        "typescript", "javascript", "perl", "pytorch", "jupyter",
    ]),
    ("AI / Agent", [
        "agent", "llm", "prompt", "rag", "retrieval", "eval", "mcp",
        "autonomous", "subagent", "continuous-learning", "council",
        "nanoclaw", "openclaw", "loop",
    ]),
    ("Ops & Business / 业务运维", [
        "billing", "ops", "email", "logistics", "inventory", "investor",
        "procurement", "scheduling", "carrier", "finance", "customer",
        "returns", "messaging", "workspace", "notion", "linear",
        "healthcare", "product-capability", "production-scheduling",
    ]),
    ("Content / 内容创作", [
        "writing", "blog", "article", "content", "brand-voice", "copy",
        "documentation", "docx", "pptx", "pdf", "manim", "video",
        "persona",
    ]),
    ("Research / 研究", [
        "research", "scraper", "crawl", "data extraction", "investigation",
        "deep-research", "exa-search",
    ]),
    ("Security / 安全", [
        "security", "hipaa", "compliance", "phi", "vulnerability", "bounty",
    ]),
    ("System Tools / 系统工具", [
        "context", "token", "budget", "optimization", "monitoring",
        "cursor-settings", "automate", "rename-chat", "configure-ecc",
        "cli-creator", "onboard", "connections-optimizer",
    ]),
]

SKIP_NAMES = {"skill-router"}


def parse_frontmatter(content: str) -> dict[str, str] | None:
    """Parse YAML-ish frontmatter; supports quoted and folded/block scalars."""
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return None

    fm = fm_match.group(1)
    data: dict[str, str] = {}

    name_m = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
    if not name_m:
        return None
    data["name"] = _strip_scalar(name_m.group(1))
    data["description"] = _parse_description(fm)
    return data


def _parse_description(fm: str) -> str:
    """Extract description from frontmatter, including >, |, and quoted forms."""
    lines = fm.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        rest = line[len("description:") :].strip()

        # Folded / literal block: description: >  or description: |
        if rest in {">", ">-", "|", "|-", "|+"} or rest.startswith(">") or rest.startswith("|"):
            block: list[str] = []
            for next_line in lines[i + 1 :]:
                if not next_line.strip():
                    block.append("")
                    continue
                if next_line.startswith(" ") or next_line.startswith("\t"):
                    block.append(next_line.strip())
                    continue
                # next top-level key
                if re.match(r"^[A-Za-z0-9_-]+:", next_line):
                    break
                block.append(next_line.strip())
            return re.sub(r"\s+", " ", " ".join(block)).strip()

        return _strip_scalar(rest)
    return ""


def _strip_scalar(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1]
    return re.sub(r"\s+", " ", value.replace("\\n", " ")).strip()


def categorize_skill(name: str, description: str) -> str:
    text = f"{name} {description}".lower()
    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in text:
                return category
    return "Other / 其他"


def short_trigger(description: str, limit: int = 64) -> str:
    if not description:
        return "(no description)"
    # Prefer first sentence / clause
    for sep in (". ", "。", "; ", "；", " — ", " - "):
        if sep in description:
            description = description.split(sep, 1)[0].strip()
            break
    description = re.sub(r"\s+", " ", description).strip()
    if len(description) > limit:
        return description[: limit - 1].rstrip() + "…"
    return description


def scan_dirs(skills_dirs: list[Path]) -> list[dict]:
    """Scan dirs, dedupe by name, keep highest-priority source."""
    by_name: dict[str, dict] = {}

    for root in skills_dirs:
        if not root.exists():
            print(f"[Skip] missing: {root}")
            continue
        print(f"[Scan] {root}")

        for skill_dir in sorted(root.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            try:
                content = skill_file.read_text(encoding="utf-8")
            except OSError as exc:
                print(f"[Warn] cannot read {skill_file}: {exc}")
                continue

            meta = parse_frontmatter(content)
            if not meta:
                continue

            name = meta["name"]
            if name in SKIP_NAMES:
                continue

            # Prefer first-seen (higher priority root)
            if name in by_name:
                continue

            by_name[name] = {
                "name": name,
                "description": meta.get("description", ""),
                "path": str(skill_dir),
                "source": str(root),
                "category": categorize_skill(name, meta.get("description", "")),
            }

    return sorted(by_name.values(), key=lambda s: (s["category"], s["name"]))


def generate_index_markdown(skills: list[dict], compact: bool = True) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for s in skills:
        grouped[s["category"]].append(s)

    order = [c for c, _ in CATEGORY_RULES] + ["Other / 其他"]
    lines: list[str] = []
    limit = 56 if compact else 80

    for cat in order:
        items = grouped.get(cat)
        if not items:
            continue
        lines.append(f"### {cat} ({len(items)})")
        lines.append("| Skill | Trigger |")
        lines.append("|---|---|")
        for s in items:
            trigger = short_trigger(s["description"], limit=limit)
            # Escape pipes in markdown tables
            trigger = trigger.replace("|", "\\|")
            lines.append(f"| `{s['name']}` | {trigger} |")
        lines.append("")

    return "\n".join(lines)


def generate_template_sections() -> str:
    """Return the static routing + report sections (English primary for model)."""
    return '''---
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
> Run `python scripts/generate.py` to refresh this index from local installs.
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
python scripts/generate.py --skills-dir "%USERPROFILE%\\.agents\\skills" --skills-dir "%USERPROFILE%\\.claude\\skills"

# Install into Cursor agents skills
python scripts/generate.py --install
```

Also writes `skills-catalog.json` for tooling / search.
'''


def write_skill_md(skills: list[dict], output: Path, compact: bool) -> None:
    index = generate_index_markdown(skills, compact=compact)
    template = generate_template_sections()
    start, end = "<!-- SKILL_INDEX_START -->", "<!-- SKILL_INDEX_END -->"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    replacement = (
        f"{start}\n"
        f"> Auto-generated {stamp} — **{len(skills)}** unique skills\n\n"
        f"{index}\n"
        f"{end}"
    )
    result = re.sub(
        f"{re.escape(start)}.*?{re.escape(end)}",
        replacement,
        template,
        count=1,
        flags=re.DOTALL,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")
    print(f"[Done] Wrote {output} ({len(skills)} skills)")


def write_catalog_json(skills: list[dict], path: Path) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(skills),
        "skills": skills,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Done] Wrote {path}")


def install_to_agents(skill_md: Path) -> None:
    targets = [
        HOME / ".agents" / "skills" / "skill-router" / "SKILL.md",
        HOME / ".claude" / "skills" / "skill-router" / "SKILL.md",
    ]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(skill_md.read_text(encoding="utf-8"), encoding="utf-8")
        # Copy generator for local refresh
        scripts_dst = target.parent / "scripts"
        scripts_dst.mkdir(exist_ok=True)
        src_gen = Path(__file__).resolve()
        (scripts_dst / "generate.py").write_text(
            src_gen.read_text(encoding="utf-8"), encoding="utf-8"
        )
        print(f"[Install] {target}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate optimized Skill Router index")
    p.add_argument(
        "--skills-dir",
        action="append",
        dest="skills_dirs",
        default=None,
        help="Skill root to scan (repeatable). Default: multi-root Cursor/Claude/Codex paths.",
    )
    p.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output SKILL.md path")
    p.add_argument("--json", default=str(DEFAULT_JSON), help="Output skills-catalog.json path")
    p.add_argument(
        "--no-compact",
        action="store_true",
        help="Use longer trigger blurbs in the markdown table",
    )
    p.add_argument(
        "--install",
        action="store_true",
        help="Copy generated SKILL.md into ~/.agents/skills and ~/.claude/skills",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.skills_dirs:
        roots = [Path(os.path.expanduser(d)) for d in args.skills_dirs]
    else:
        roots = DEFAULT_SKILL_DIRS

    skills = scan_dirs(roots)
    by_cat: dict[str, int] = defaultdict(int)
    for s in skills:
        by_cat[s["category"]] += 1
    print(f"[Summary] {len(skills)} unique skills")
    for cat, n in sorted(by_cat.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {n:3d}  {cat}")

    out = Path(args.output)
    write_skill_md(skills, out, compact=not args.no_compact)
    write_catalog_json(skills, Path(args.json))

    if args.install:
        install_to_agents(out)


if __name__ == "__main__":
    main()
