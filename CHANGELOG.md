# Changelog

## 1.1.0-optimized (local fork)

Based on [YunzhouLi-hub/skill-router](https://github.com/YunzhouLi-hub/skill-router).

### Added
- Multi-root scanning (Cursor `.agents`, Claude, Cursor built-in, Codex)
- Dedup by skill name with source priority
- Compact markdown index for large inventories (300+ skills)
- `skills-catalog.json` export
- `--install` flag for Windows/macOS/Linux agent dirs
- Design-skill conflict policy (Hallmark / impeccable / taste-*)
- Ops & Business / Skill Meta categories
- Folded YAML description parsing (`>`, `|`)

### Changed
- Routing: max 1–3 skills per turn (was “load all matches”)
- Usage report: compact one-liner; optional on trivial turns
- Description: softer trigger for Cursor discovery (not “every message”)

### Fixed
- Descriptions that used YAML `>` blocks parsing as `>-`
