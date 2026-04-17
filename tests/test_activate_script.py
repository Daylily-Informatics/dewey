from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVATE_SCRIPT = PROJECT_ROOT / "activate"
DEPLOY_NAME = "ab-12cd"


def _write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _build_fake_conda(tmp_path: Path) -> Path:
    conda_base = tmp_path / "fake-conda"
    conda_exe = conda_base / "bin" / "conda"
    env_name = f"DEWEY-{DEPLOY_NAME}"
    env_bin = conda_base / "envs" / env_name / "bin"

    env_bin.mkdir(parents=True, exist_ok=True)
    _write_executable(
        env_bin / "dewey",
        """#!/usr/bin/env bash
set -euo pipefail
printf 'dewey stub\\n'
""",
    )

    _write_executable(
        env_bin / "python",
        f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "pip" && "${{3:-}}" == "install" ]]; then
  if [[ -n "${{FAKE_PIP_INSTALL_LOG:-}}" ]]; then
    printf '%s\\n' "$*" >> "${{FAKE_PIP_INSTALL_LOG}}"
  fi
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "pip" && "${{3:-}}" == "show" ]]; then
  package_name="${{4:-}}"
  if [[ "$package_name" == "dewey-service" ]]; then
    printf 'Name: dewey-service\\n'
    printf 'Editable project location: %s\\n' "{PROJECT_ROOT}"
  fi
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
    printf '# conda environments:\\n#\\nbase * {conda_base}\\n{env_name} {conda_base}/envs/{env_name}\\n'
  else
    printf '# conda environments:\\n#\\nbase * {conda_base}\\n'
  fi
  exit 0
fi
if [[ "${{1:-}}" == "env" && "${{2:-}}" == "create" ]]; then
  if [[ -n "${{FAKE_CONDA_CALL_LOG:-}}" ]]; then
    printf '%s\\n' "$*" >> "${{FAKE_CONDA_CALL_LOG}}"
  fi
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
  if [[ "${{1:-}}" == "activate" && "${{2:-}}" == "{env_name}" ]]; then
    if [[ -n "${{FAKE_CONDA_CALL_LOG:-}}" ]]; then
      printf 'activate\\n' >> "${{FAKE_CONDA_CALL_LOG}}"
    fi
    if [[ "${{FAKE_CONDA_ACTIVATE_FAIL:-0}}" == "1" ]]; then
      return 1
    fi
    export CONDA_DEFAULT_ENV="{env_name}"
    export CONDA_PREFIX="{conda_base}/envs/{env_name}"
    export PATH="{env_bin}:$PATH"
    return 0
  fi
  command "{conda_exe}" "$@"
}}
""",
        encoding="utf-8",
    )

    return conda_base


def _source_activate(
    env: dict[str, str],
    *,
    deploy_name: str | None = DEPLOY_NAME,
    extra_args: tuple[str, ...] = (),
    post_command: str | None = None,
) -> subprocess.CompletedProcess[str]:
    argv = [f"source {shlex.quote(str(ACTIVATE_SCRIPT))}"]
    if deploy_name is not None:
        argv.append(shlex.quote(deploy_name))
    argv.extend(shlex.quote(arg) for arg in extra_args)
    command = " ".join(argv)
    if post_command:
        command = f"{command} && {post_command}"
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
    for utility in ("dirname", "sed"):
        source = Path("/usr/bin") / utility
        if not source.exists():
            source = Path("/bin") / utility
        assert source.exists(), f"missing test utility: {utility}"
        (empty_bin / utility).symlink_to(source)

    env = os.environ.copy()
    env["PATH"] = str(empty_bin)
    for key in list(env):
        if key.startswith("BASH_FUNC_conda"):
            env.pop(key, None)
    env.pop("CONDA_EXE", None)
    env.pop("_CONDA_EXE", None)
    env.pop("CONDA_SHLVL", None)
    env.pop("MAMBA_EXE", None)
    env.pop("MAMBA_ROOT_PREFIX", None)
    env.pop("CONDA_DEFAULT_ENV", None)
    env.pop("CONDA_PREFIX", None)

    result = _source_activate(env)

    assert result.returncode == 1
    assert "Conda is required but was not found on PATH." in result.stderr


def test_activate_requires_deploy_name_argument() -> None:
    result = _source_activate(os.environ.copy(), deploy_name=None)

    assert result.returncode == 1
    assert "Dewey activation requires exactly one positional deploy-name." in result.stdout


def test_activate_rejects_invalid_deploy_name_without_conda() -> None:
    result = _source_activate(os.environ.copy(), deploy_name="bad_name")

    assert result.returncode == 1
    assert "deploy-name must match ^[A-Za-z0-9-]{2,8}$" in result.stderr


def test_activate_rejects_extra_arguments() -> None:
    result = _source_activate(os.environ.copy(), extra_args=("extra",))

    assert result.returncode == 1
    assert "Dewey activation requires exactly one positional deploy-name." in result.stdout


def test_activate_creates_env_and_installs_repo_editable_once(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)
    conda_call_log = tmp_path / "conda-calls.log"
    pip_install_log = tmp_path / "pip-install.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_DEWEY_ENV_PRESENT"] = "0"
    env["FAKE_CONDA_CALL_LOG"] = str(conda_call_log)
    env["FAKE_PIP_INSTALL_LOG"] = str(pip_install_log)
    env.pop("CONDA_DEFAULT_ENV", None)
    env.pop("CONDA_PREFIX", None)

    result = _source_activate(env, post_command="command -v dewey")

    assert result.returncode == 0
    assert f"Conda environment 'DEWEY-{DEPLOY_NAME}' not found." in result.stdout
    assert "Installing conda environment from environment.yaml..." in result.stdout
    assert "Installing editable Dewey checkout..." in result.stdout
    assert conda_call_log.read_text(encoding="utf-8").splitlines() == [
        f"env create -n DEWEY-{DEPLOY_NAME} -f {PROJECT_ROOT / 'environment.yaml'}",
        "activate",
    ]
    pip_install_lines = pip_install_log.read_text(encoding="utf-8").splitlines()
    assert pip_install_lines == [f"-m pip install -e {PROJECT_ROOT} -q"]
    assert result.stdout.strip().splitlines()[-1] == str(
        conda_base / "envs" / f"DEWEY-{DEPLOY_NAME}" / "bin" / "dewey"
    )


def test_activate_accepts_preloaded_dewey_conda_env(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)
    pip_install_log = tmp_path / "pip-install.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'envs' / f'DEWEY-{DEPLOY_NAME}' / 'bin'}:{conda_base / 'bin'}:/usr/bin:/bin"
    env["CONDA_DEFAULT_ENV"] = f"DEWEY-{DEPLOY_NAME}"
    env["CONDA_PREFIX"] = str(conda_base / "envs" / f"DEWEY-{DEPLOY_NAME}")
    env["FAKE_DEWEY_ENV_PRESENT"] = "1"
    env["FAKE_PIP_INSTALL_LOG"] = str(pip_install_log)

    result = _source_activate(env, post_command="command -v dewey")

    assert result.returncode == 0
    assert f"Conda environment already active: DEWEY-{DEPLOY_NAME}" in result.stdout
    assert not pip_install_log.exists()
    assert result.stdout.strip().splitlines()[-1] == str(
        conda_base / "envs" / f"DEWEY-{DEPLOY_NAME}" / "bin" / "dewey"
    )


def test_activate_activates_preexisting_dewey_conda_env(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)
    conda_call_log = tmp_path / "conda-calls.log"
    pip_install_log = tmp_path / "pip-install.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_DEWEY_ENV_PRESENT"] = "1"
    env["FAKE_CONDA_CALL_LOG"] = str(conda_call_log)
    env["FAKE_PIP_INSTALL_LOG"] = str(pip_install_log)
    env.pop("CONDA_DEFAULT_ENV", None)
    env.pop("CONDA_PREFIX", None)

    result = _source_activate(env, post_command="command -v dewey")

    assert result.returncode == 0
    assert f"Activating conda environment: DEWEY-{DEPLOY_NAME}" in result.stdout
    assert conda_call_log.read_text(encoding="utf-8").splitlines() == ["activate"]
    assert not pip_install_log.exists()
    assert result.stdout.strip().splitlines()[-1] == str(
        conda_base / "envs" / f"DEWEY-{DEPLOY_NAME}" / "bin" / "dewey"
    )
