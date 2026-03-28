from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVATE_SCRIPT = PROJECT_ROOT / "dewey_activate"


def _write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _build_fake_conda(tmp_path: Path) -> Path:
    conda_base = tmp_path / "fake-conda"
    conda_exe = conda_base / "bin" / "conda"
    env_bin = conda_base / "envs" / "DEWEY" / "bin"
    scripts_dir = conda_base / "envs" / "DEWEY" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    _write_executable(
        env_bin / "python",
        f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "-c" ]]; then
  if [[ "${{2:-}}" == *'sysconfig.get_path("scripts")'* ]]; then
    printf '%s\\n' "{scripts_dir}"
  fi
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "pip" && "${{3:-}}" == "show" ]]; then
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "pip" && "${{3:-}}" == "install" ]]; then
  exit 0
fi
exit 0
""",
    )

    _write_executable(
        conda_exe,
        f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "info" && "${{2:-}}" == "--base" ]]; then
  printf '%s\\n' "{conda_base}"
  exit 0
fi
if [[ "${{1:-}}" == "info" && "${{2:-}}" == "--envs" ]]; then
  if [[ "${{FAKE_DEWEY_ENV_PRESENT:-1}}" == "1" ]]; then
    printf '# conda environments:\\n#\\nbase * {conda_base}\\nDEWEY {conda_base}/envs/DEWEY\\n'
  else
    printf '# conda environments:\\n#\\nbase * {conda_base}\\n'
  fi
  exit 0
fi
if [[ "${{1:-}}" == "env" && "${{2:-}}" == "create" ]]; then
  if [[ "${{FAKE_CONDA_ENV_CREATE_FAIL:-0}}" == "1" ]]; then
    exit 1
  fi
  exit 0
fi
echo "unexpected conda executable call: $*" >&2
exit 1
""",
    )

    conda_sh = conda_base / "etc" / "profile.d" / "conda.sh"
    conda_sh.parent.mkdir(parents=True, exist_ok=True)
    conda_sh.write_text(
        f"""conda() {{
  if [[ "${{1:-}}" == "activate" && "${{2:-}}" == "DEWEY" ]]; then
    if [[ -n "${{FAKE_CONDA_CALL_LOG:-}}" ]]; then
      printf 'activate\\n' >> "${{FAKE_CONDA_CALL_LOG}}"
    fi
    if [[ "${{FAKE_CONDA_ACTIVATE_FAIL:-0}}" == "1" ]]; then
      return 1
    fi
    export CONDA_DEFAULT_ENV="DEWEY"
    export CONDA_PREFIX="{conda_base}/envs/DEWEY"
    return 0
  fi
  command "{conda_exe}" "$@"
}}
""",
        encoding="utf-8",
    )

    return conda_base


def _source_activate(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    command = f"source {shlex.quote(str(ACTIVATE_SCRIPT))}"
    return subprocess.run(
        ["/bin/bash", "--noprofile", "--norc", "-c", command],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )


def test_activate_requires_conda_on_path(tmp_path: Path) -> None:
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()

    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin"

    result = _source_activate(env)

    assert result.returncode == 1
    assert "Conda is required but was not found on PATH." in result.stderr


def test_activate_hardfails_when_conda_env_creation_fails(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_DEWEY_ENV_PRESENT"] = "0"
    env["FAKE_CONDA_ENV_CREATE_FAIL"] = "1"

    result = _source_activate(env)

    assert result.returncode == 1
    assert "Failed to create conda environment from dewey_env.yaml." in result.stderr
    assert "Installing dewey CLI..." not in result.stdout


def test_activate_hardfails_when_conda_activation_fails(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_CONDA_ACTIVATE_FAIL"] = "1"

    result = _source_activate(env)

    assert result.returncode == 1
    assert "Failed to activate conda environment: DEWEY" in result.stderr
    assert "Installing dewey CLI..." not in result.stdout


def test_activate_accepts_preloaded_dewey_conda_env(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)
    call_log = tmp_path / "conda-calls.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["CONDA_DEFAULT_ENV"] = "DEWEY"
    env["CONDA_PREFIX"] = str(conda_base / "envs" / "DEWEY")
    env["FAKE_CONDA_CALL_LOG"] = str(call_log)

    result = _source_activate(env)

    assert result.returncode == 0
    assert "Conda environment already active: DEWEY" in result.stdout
    assert not call_log.exists()
