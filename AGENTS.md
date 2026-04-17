# Dewey CLI Policy

## Session Setup

Always start by activating the repo environment:

```bash
source ./activate <deploy-name>
```

## Command Ownership

- Use `dewey ...` as the primary interface for normal Dewey work.
- Use `tapdb ...` only when Dewey explicitly delegates low-level DB/runtime lifecycle to TapDB.
- Use `daycog ...` only when Dewey explicitly delegates shared Cognito lifecycle to Daycog.

## Activate Contract

- Keep `source ./activate <deploy-name>` environment-only:
  - create the conda env if missing,
  - activate the env,
  - run exactly one `python -m pip install -e .` on first create,
  - do nothing else.
- Do not add a separate dev extra, extra `pip install` calls, `conda install`, config copying, PATH rebinding, runtime env exports, or bootstrap work to `activate`.
- Do not add any secondary install set such as `.[dev]`, `.[test]`, `requirements-dev.txt`, or `[project.optional-dependencies]`.
- `environment.yaml` is only for Python, pip/setuptools bootstrap, and non-Python system packages.
- All Python deps needed by the repo live in `project.dependencies`.
- If a CLI is missing from `PATH` after activation, fix packaging or entrypoints, not `activate`.
- Repo-solo config ownership stays in `dewey config init`; deployment-scoped runtime wiring stays out of `activate`.

## No Circumvention Policy

- Do not bypass `dewey`, `tapdb`, or `daycog` with raw tools just because something is missing or broken.
- Do not treat direct `python -m ...`, raw `postgres`, raw AWS CLI mutations, or direct config-file edits as automatic fallbacks.
- If the intended CLI path is broken or incomplete, stop, diagnose, and ask for permission before circumventing it.
- Prefer patience and repair of the intended CLI workflow over inventing a shortcut.

## Dewey Examples

- Start with `source ./activate <deploy-name>`
- Use `dewey config init`
- Use `dewey db build --target local`
- Use `dewey server start --port 8914`
- Use `tapdb ...` and `daycog ...` only where Dewey docs or Dewey CLI explicitly delegate to them
