# Dewey CLI Policy

## Session Setup

Always start by activating the repo environment:

```bash
source ./activate
```

## Command Ownership

- Use `dewey ...` as the primary interface for normal Dewey work.
- Use `tapdb ...` only when Dewey explicitly delegates low-level DB/runtime lifecycle to TapDB.
- Use `daycog ...` only when Dewey explicitly delegates shared Cognito lifecycle to Daycog.

## No Circumvention Policy

- Do not bypass `dewey`, `tapdb`, or `daycog` with raw tools just because something is missing or broken.
- Do not treat direct `python -m ...`, raw `postgres`, raw AWS CLI mutations, or direct config-file edits as automatic fallbacks.
- If the intended CLI path is broken or incomplete, stop, diagnose, and ask for permission before circumventing it.
- Prefer patience and repair of the intended CLI workflow over inventing a shortcut.

## Dewey Examples

- Start with `source ./activate`
- Use `dewey config init`
- Use `dewey db build --target local`
- Use `dewey server start --port 8914`
- Use `tapdb ...` and `daycog ...` only where Dewey docs or Dewey CLI explicitly delegate to them
