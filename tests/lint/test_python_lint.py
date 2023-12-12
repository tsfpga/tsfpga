# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import sys
from pathlib import Path

# First party libraries
import tsfpga
from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file, run_command
from tsfpga.test.lint.python_lint import run_black, run_flake8_lint, run_isort, run_pylint


def _files_to_check():
    # The conf.py used by sphinx does not conform.
    return [
        str(path)
        for path in find_git_files(
            directory=tsfpga.REPO_ROOT,
            exclude_directories=[
                tsfpga.TSFPGA_DOC / "sphinx" / "conf.py",
                tsfpga.TSFPGA_EXAMPLES / "conf.py",
            ],
            file_endings_include="py",
        )
    ]


def test_pylint():
    run_pylint(_files_to_check())


def test_black_formatting():
    run_black(_files_to_check())


def test_isort_formatting():
    run_isort(files=_files_to_check(), cwd=tsfpga.REPO_ROOT)


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
