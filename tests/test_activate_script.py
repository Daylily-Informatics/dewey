from __future__ import annotations

import os
import shlex
import subprocess
import sys
from shutil import copy2
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVATE_SCRIPT = PROJECT_ROOT / "activate"
DEPLOY_NAME = "abc-12345"


def _write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _build_fake_conda(tmp_path: Path) -> Path:
    conda_base = tmp_path / "fake-conda"
    conda_exe = conda_base / "bin" / "conda"
    env_name = f"DEWEY-{DEPLOY_NAME}"
    env_bin = conda_base / "envs" / env_name / "bin"
    scripts_dir = conda_base / "envs" / env_name / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    real_python = str(Path(sys.executable).resolve())

    _write_executable(
        env_bin / "python",
        f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "-c" ]]; then
  if [[ "${{2:-}}" == *'sysconfig.get_path("scripts")'* ]]; then
    printf '%s\\n' "{scripts_dir}"
    exit 0
  fi
  exec "{real_python}" "$@"
fi
if [[ "${{1:-}}" == "-" ]]; then
  script="$(cat)"
  if [[ "$script" == *"project_version()"* ]] || [[ "$script" == *"setuptools_scm_version()"* ]] || [[ "$script" == *"exact_numeric_git_tag()"* ]]; then
    exec "{real_python}" "$@" <<<"$script"
  fi
  if [[ "$script" == *"importlib.import_module(sys.argv[1])"* ]]; then
    exit 0
  fi
  if [[ "$script" == *"importlib.import_module"* ]]; then
    exec "{real_python}" "$@" <<<"$script"
  fi
  exec "{real_python}" "$@" <<<"$script"
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "pip" && "${{3:-}}" == "show" ]]; then
  printf 'Name: dewey-service\\n'
  printf 'Editable project location: %s\\n' "{PROJECT_ROOT}"
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "pip" && "${{3:-}}" == "install" ]]; then
  if [[ -n "${{FAKE_PIP_INSTALL_LOG:-}}" ]]; then
    printf '%s\\n' "$*" >> "${{FAKE_PIP_INSTALL_LOG}}"
  fi
  if [[ "${{FAKE_PIP_INSTALL_FAIL:-0}}" == "1" ]]; then
    exit 1
  fi
  exit 0
fi
exec "{real_python}" "$@"
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
if [[ "${{1:-}}" == "env" && "${{2:-}}" == "remove" ]]; then
  if [[ -n "${{FAKE_CONDA_CALL_LOG:-}}" ]]; then
    printf '%s\\n' "$*" >> "${{FAKE_CONDA_CALL_LOG}}"
  fi
  if [[ "${{FAKE_CONDA_ENV_REMOVE_FAIL:-0}}" == "1" ]]; then
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
    export FAKE_CONDA_PREVIOUS_CONDA_DEFAULT_ENV="${{CONDA_DEFAULT_ENV:-}}"
    export FAKE_CONDA_PREVIOUS_CONDA_PREFIX="${{CONDA_PREFIX:-}}"
    export CONDA_DEFAULT_ENV="{env_name}"
    export CONDA_PREFIX="{conda_base}/envs/{env_name}"
    return 0
  fi
  if [[ "${{1:-}}" == "deactivate" ]]; then
    if [[ -n "${{FAKE_CONDA_CALL_LOG:-}}" ]]; then
      printf 'deactivate:%s\\n' "${{CONDA_DEFAULT_ENV:-}}" >> "${{FAKE_CONDA_CALL_LOG}}"
    fi
    if [[ -n "${{FAKE_CONDA_PREVIOUS_CONDA_DEFAULT_ENV:-}}" ]]; then
      export CONDA_DEFAULT_ENV="${{FAKE_CONDA_PREVIOUS_CONDA_DEFAULT_ENV}}"
      export CONDA_PREFIX="${{FAKE_CONDA_PREVIOUS_CONDA_PREFIX:-}}"
      unset FAKE_CONDA_PREVIOUS_CONDA_DEFAULT_ENV
      unset FAKE_CONDA_PREVIOUS_CONDA_PREFIX
    else
      unset CONDA_DEFAULT_ENV
      unset CONDA_PREFIX
    fi
    return 0
  fi
  command "{conda_exe}" "$@"
}}
""",
        encoding="utf-8",
    )

    return conda_base


def _make_temp_repo(tmp_path: Path, *, pyproject_version: str) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    copy2(ACTIVATE_SCRIPT, repo_root / "activate")
    copy2(PROJECT_ROOT / "environment.yaml", repo_root / "environment.yaml")
    (repo_root / "pyproject.toml").write_text(
        f"""[build-system]
requires = ["setuptools>=64", "setuptools_scm>=8", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dewey-service"
version = "{pyproject_version}"
""",
        encoding="utf-8",
    )
    (repo_root / "activate").chmod(0o755)
    return repo_root


def _source_activate(
    env: dict[str, str],
    *,
    script_path: Path = ACTIVATE_SCRIPT,
    deploy_name: str | None = DEPLOY_NAME,
    extra_args: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    argv = [f"source {shlex.quote(str(script_path))}"]
    if deploy_name is not None:
        argv.append(shlex.quote(deploy_name))
    argv.extend(shlex.quote(arg) for arg in extra_args)
    command = " ".join(argv)
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


def test_activate_rejects_invalid_deploy_name_without_conda() -> None:
    result = _source_activate(os.environ.copy(), deploy_name="ab")

    assert result.returncode == 1
    assert "deploy-name must match ^[A-Za-z0-9-]{3,9}$" in result.stderr


def test_activate_rejects_extra_arguments() -> None:
    result = _source_activate(os.environ.copy(), extra_args=("extra",))

    assert result.returncode == 1
    assert "Usage: source ./activate [deploy-name] [--debug]" in result.stdout


def test_activate_uses_static_project_version_when_deploy_name_is_omitted(tmp_path: Path) -> None:
    repo_root = _make_temp_repo(tmp_path, pyproject_version="v1.2.3.45")
    conda_base = _build_fake_conda(tmp_path)

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_DEWEY_ENV_PRESENT"] = "0"
    env["FAKE_CONDA_ENV_CREATE_FAIL"] = "1"
    env.pop("CONDA_DEFAULT_ENV", None)
    env.pop("CONDA_PREFIX", None)

    result = _source_activate(env, script_path=repo_root / "activate", deploy_name=None)

    assert result.returncode == 1
    assert "Conda environment 'DEWEY-v1-2-3-45' not found." in result.stdout
    assert "Installing conda environment from environment.yaml..." in result.stdout


def test_activate_cleans_up_created_env_and_restores_previous_env_on_failure(tmp_path: Path) -> None:
    repo_root = _make_temp_repo(tmp_path, pyproject_version="v1.2.3.4.5")
    conda_base = _build_fake_conda(tmp_path)
    call_log = tmp_path / "conda-calls.log"
    pip_install_log = tmp_path / "pip-install.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_DEWEY_ENV_PRESENT"] = "0"
    env["FAKE_CONDA_CALL_LOG"] = str(call_log)
    env["FAKE_PIP_INSTALL_LOG"] = str(pip_install_log)
    env["FAKE_PIP_INSTALL_FAIL"] = "1"
    env["CONDA_DEFAULT_ENV"] = "DEWEY-preexisting"
    env["CONDA_PREFIX"] = str(conda_base / "envs" / "DEWEY-preexisting")

    result = _source_activate(env, script_path=repo_root / "activate", deploy_name=DEPLOY_NAME)

    assert result.returncode == 1
    stdout = result.stdout + result.stderr
    assert "Restoring previously active conda environment: DEWEY-preexisting" in stdout
    assert f"Removing conda environment created by this attempt: DEWEY-{DEPLOY_NAME}" in stdout
    call_log_text = call_log.read_text(encoding="utf-8")
    assert f"deactivate:DEWEY-{DEPLOY_NAME}" in call_log_text
    assert f"env remove -n DEWEY-{DEPLOY_NAME} -y" in call_log_text
    assert pip_install_log.read_text(encoding="utf-8")


def test_activate_debug_skips_environment_removal_on_failure(tmp_path: Path) -> None:
    repo_root = _make_temp_repo(tmp_path, pyproject_version="v1.2.3.4.5")
    conda_base = _build_fake_conda(tmp_path)
    call_log = tmp_path / "conda-calls.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_DEWEY_ENV_PRESENT"] = "0"
    env["FAKE_CONDA_CALL_LOG"] = str(call_log)
    env["FAKE_PIP_INSTALL_FAIL"] = "1"
    env["CONDA_DEFAULT_ENV"] = "DEWEY-preexisting"
    env["CONDA_PREFIX"] = str(conda_base / "envs" / "DEWEY-preexisting")

    result = _source_activate(
        env,
        script_path=repo_root / "activate",
        deploy_name=DEPLOY_NAME,
        extra_args=("--debug",),
    )

    assert result.returncode == 1
    stdout = result.stdout + result.stderr
    assert f"--debug set; leaving DEWEY-{DEPLOY_NAME} in place" in stdout
    assert f"env remove -n DEWEY-{DEPLOY_NAME} -y" not in call_log.read_text(encoding="utf-8")


def test_activate_hardfails_when_conda_env_creation_fails(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)
    conda_call_log = tmp_path / "conda-calls.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_DEWEY_ENV_PRESENT"] = "0"
    env["FAKE_CONDA_ENV_CREATE_FAIL"] = "1"
    env["FAKE_CONDA_CALL_LOG"] = str(conda_call_log)
    env.pop("CONDA_DEFAULT_ENV", None)
    env.pop("CONDA_PREFIX", None)

    result = _source_activate(env)

    assert result.returncode == 1
    assert "Failed to create conda environment from environment.yaml." in result.stderr
    assert (
        f"env create -n DEWEY-{DEPLOY_NAME} -f {PROJECT_ROOT / 'environment.yaml'}"
        in conda_call_log.read_text(encoding="utf-8")
    )
    assert "Installing dewey CLI..." not in result.stdout


def test_activate_hardfails_when_conda_activation_fails(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_CONDA_ACTIVATE_FAIL"] = "1"
    env.pop("CONDA_DEFAULT_ENV", None)
    env.pop("CONDA_PREFIX", None)

    result = _source_activate(env)

    assert result.returncode == 1
    assert f"Failed to activate conda environment: DEWEY-{DEPLOY_NAME}" in result.stderr
    assert "Installing dewey CLI..." not in result.stdout


def test_activate_accepts_preloaded_dewey_conda_env(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)
    call_log = tmp_path / "conda-calls.log"
    pip_install_log = tmp_path / "pip-install.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["CONDA_DEFAULT_ENV"] = f"DEWEY-{DEPLOY_NAME}"
    env["CONDA_PREFIX"] = str(conda_base / "envs" / f"DEWEY-{DEPLOY_NAME}")
    env["FAKE_CONDA_CALL_LOG"] = str(call_log)
    env["FAKE_PIP_INSTALL_LOG"] = str(pip_install_log)

    result = _source_activate(env)

    assert result.returncode == 0
    assert f"Conda environment already active: DEWEY-{DEPLOY_NAME}" in result.stdout
    assert "build, seed, reset, nuke" in result.stdout
    assert not call_log.exists()
    assert "Using local Dewey checkout" in result.stdout
    assert not pip_install_log.exists()


def test_activate_installs_local_checkout_with_packaged_dependencies(tmp_path: Path) -> None:
    conda_base = _build_fake_conda(tmp_path)
    pip_install_log = tmp_path / "pip-install.log"

    env = os.environ.copy()
    env["PATH"] = f"{conda_base / 'bin'}:/usr/bin:/bin"
    env["FAKE_DEWEY_ENV_PRESENT"] = "0"
    env.pop("CONDA_DEFAULT_ENV", None)
    env.pop("CONDA_PREFIX", None)
    env["FAKE_PIP_INSTALL_LOG"] = str(pip_install_log)

    result = _source_activate(env)

    assert result.returncode == 0
    assert f"Conda environment 'DEWEY-{DEPLOY_NAME}' not found." in result.stdout
    assert "Installing conda environment from environment.yaml..." in result.stdout
    pip_install_lines = pip_install_log.read_text(encoding="utf-8").splitlines()
    assert any(
        "pip install -e " in line and "[dev]" in line and "--no-deps" not in line
        for line in pip_install_lines
    )
    assert any(str(PROJECT_ROOT) in line for line in pip_install_lines)
