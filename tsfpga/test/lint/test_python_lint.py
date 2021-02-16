# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import subprocess
import sys
import unittest

from pathlib import Path
import pytest

import tsfpga
from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file


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

    subprocess.check_call(command)


def test_pylint():
    run_pylint(_files_to_check())


def run_black(files):
    command = [sys.executable, "-m", "black", "--check"] + files
    subprocess.check_call(command, cwd=tsfpga.REPO_ROOT)


def test_black_formatting():
    run_black(_files_to_check())


def run_flake8_lint(files):
    command = [sys.executable, "-m", "flake8"] + files
    subprocess.check_call(command, cwd=tsfpga.REPO_ROOT)


def test_flake8_lint():
    run_flake8_lint(_files_to_check())


@pytest.mark.usefixtures("fixture_tmp_path")
class TestPythonLintFunctions(unittest.TestCase):
    tmp_path = None

    def setUp(self):
        ugly_code = "aa  =\ndef bb:\ncc  = 3"
        self.file = str(create_file(self.tmp_path / "dummy_python_file.py", ugly_code))

    def test_pylint_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_pylint([self.file])

    def test_flake8_lint_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_flake8_lint([self.file])

    def test_black_formatting_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_black([self.file])
