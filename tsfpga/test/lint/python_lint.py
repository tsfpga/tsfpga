# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Reusable code for Python linting.
# --------------------------------------------------------------------------------------------------

# Standard libraries
import subprocess
import sys
from pathlib import Path

# Third party libraries
import pytest

# First party libraries
import tsfpga
from tsfpga.system_utils import create_file, run_command

THIS_DIR = Path(__file__).parent.resolve()


def run_pylint(files: list[Path]) -> None:
    """
    Will raise exception if any of the ``files`` does not pass the 'pylint' lint check.
    """
    command = [sys.executable, "-m", "pylint", "--rcfile", str(THIS_DIR / "pylintrc")] + [
        str(file_path) for file_path in files
    ]

    run_command(command)


def run_black(files: list[Path]) -> None:
    """
    Will raise exception if any of the ``files`` does not pass the 'black' formatting check.
    """
    command = [sys.executable, "-m", "black", "--check", "--diff"] + [
        str(file_path) for file_path in files
    ]
    run_command(command)


def run_isort(files: list[Path], cwd: Path) -> None:
    """
    Run the 'isort' Python tool.
    Will raise exception if any of the ``files`` does not pass the check.

    Arguments:
        files: The files that shall be checked.
        cwd: Path where the command shall be executed.
            The ``pyproject.toml`` file should be located here.
    """
    command = [sys.executable, "-m", "isort", "--check", "--diff"] + [
        str(file_path) for file_path in files
    ]
    run_command(command, cwd=cwd)


def run_flake8_lint(files: list[Path]) -> None:
    """
    Will raise exception if any of the ``files`` does not pass the 'flake8' lint check.
    """
    command = [sys.executable, "-m", "flake8"] + [str(file_path) for file_path in files]
    run_command(command, cwd=tsfpga.REPO_ROOT)


# pylint: disable=redefined-outer-name
@pytest.fixture
def invalid_python_code_file(tmp_path: Path) -> Path:
    ugly_code = "aa  =\ndef bb:\ncc  = 3"
    return create_file(tmp_path / "dummy_python_file.py", ugly_code)


def test_pylint_should_raise_exception_if_there_are_ugly_files(
    invalid_python_code_file: Path,
) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_pylint(files=[invalid_python_code_file])


def test_flake8_lint_should_raise_exception_if_there_are_ugly_files(
    invalid_python_code_file: Path,
) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_flake8_lint(files=[invalid_python_code_file])


def test_black_formatting_should_raise_exception_if_there_are_ugly_files(
    invalid_python_code_file: Path,
) -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_black(files=[invalid_python_code_file])


def test_isort_formatting_should_raise_exception_if_there_are_ugly_files(tmp_path: Path) -> None:
    file_path = create_file(
        file=tmp_path / "dummy_python_file.py",
        contents="""
import b
import a

""",
    )

    with pytest.raises(subprocess.CalledProcessError):
        run_isort(files=[file_path], cwd=tsfpga.REPO_ROOT)
