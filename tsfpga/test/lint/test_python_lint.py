# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import subprocess
import sys
from pathlib import Path

# Third party libraries
import pytest

# First party libraries
import tsfpga
from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file, run_command

THIS_DIR = Path(__file__).parent


def _files_to_check():
    # Exclude doc folder, since conf.py used by sphinx does not conform
    return [
        str(path)
        for path in find_git_files(
            directory=tsfpga.REPO_ROOT,
            exclude_directories=[tsfpga.TSFPGA_DOC],
            file_endings_include="py",
        )
    ]


def run_pylint(files):
    config = THIS_DIR / "pylintrc"
    command = [sys.executable, "-m", "pylint", f"--rcfile={config}"] + files

    run_command(command)


def test_pylint():
    run_pylint(_files_to_check())


def run_black(files):
    command = [sys.executable, "-m", "black", "--check", "--diff"] + files
    run_command(command, cwd=tsfpga.REPO_ROOT)


def test_black_formatting():
    run_black(_files_to_check())


def run_isort(files, cwd):
    """
    Run ``isort`` Python tool

    Arguments:
        files (list(pathlib.Path)): The files that shall be checked.
        cwd (pathlib.Path): Path where the command shall be executed.
            The ``pyproject.toml`` file should be located here.
    """
    command = [sys.executable, "-m", "isort", "--check", "--diff"] + files
    run_command(command, cwd=cwd)


def test_isort_formatting():
    run_isort(files=_files_to_check(), cwd=tsfpga.REPO_ROOT)


def run_flake8_lint(files):
    command = [sys.executable, "-m", "flake8"] + files
    run_command(command, cwd=tsfpga.REPO_ROOT)


def test_flake8_lint():
    run_flake8_lint(_files_to_check())


def test_mypy():
    command = [sys.executable, "-m", "mypy", "--package", "tsfpga", "--package", "tools"]

    # Add to PYTHONPATH so that mypy can find everything
    sys.path.append(
        str(tsfpga.REPO_ROOT.parent.parent.resolve() / "hdl_registers" / "hdl_registers")
    )
    sys.path.append(str(tsfpga.REPO_ROOT.parent.parent.resolve() / "vunit" / "vunit"))

    # Third party libraries
    import vunit  # pylint: disable=import-outside-toplevel

    # Create the py.typed file that is currently missing in VUnit.
    create_file(Path(vunit.__file__).parent / "py.typed")

    env = dict(PYTHONPATH=":".join(sys.path))
    run_command(command, cwd=tsfpga.REPO_ROOT, env=env)


# pylint: disable=redefined-outer-name
@pytest.fixture
def invalid_python_code_file(tmp_path):
    ugly_code = "aa  =\ndef bb:\ncc  = 3"
    return create_file(tmp_path / "dummy_python_file.py", ugly_code)


def test_pylint_should_raise_exception_if_there_are_ugly_files(invalid_python_code_file):
    with pytest.raises(subprocess.CalledProcessError):
        run_pylint(files=[invalid_python_code_file])


def test_flake8_lint_should_raise_exception_if_there_are_ugly_files(invalid_python_code_file):
    with pytest.raises(subprocess.CalledProcessError):
        run_flake8_lint(files=[invalid_python_code_file])


def test_black_formatting_should_raise_exception_if_there_are_ugly_files(invalid_python_code_file):
    with pytest.raises(subprocess.CalledProcessError):
        run_black(files=[invalid_python_code_file])


def test_isort_formatting_should_raise_exception_if_there_are_ugly_files(tmp_path):
    file_path = create_file(
        file=tmp_path / "dummy_python_file.py",
        contents="""
import b
import a

""",
    )

    with pytest.raises(subprocess.CalledProcessError):
        run_isort(files=[file_path], cwd=tsfpga.REPO_ROOT)
