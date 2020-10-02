# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import subprocess
import sys
import unittest

from pathlib import Path
import pytest

import tsfpga
from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import create_file


THIS_DIR = Path(__file__).parent


def run_pylint(files):
    config = THIS_DIR / "pylintrc"
    command = [sys.executable, "-m", "pylint", f"--rcfile={config}"] + files

    subprocess.check_call(command)


def test_pylint():
    # Exclude doc folder, since conf.py used by sphinx does not conform
    files = list(find_git_files(file_endings_include="py", exclude_directories=[tsfpga.TSFPGA_DOC]))
    run_pylint(files)


def test_black_formatting(file_or_directory="tsfpga"):
    command = [sys.executable, "-m", "black", "--check", file_or_directory]
    subprocess.check_call(command, cwd=tsfpga.REPO_ROOT)


def test_flake8_lint(file_or_directory="tsfpga"):
    command = [sys.executable, "-m", "flake8", file_or_directory]
    subprocess.check_call(command, cwd=tsfpga.REPO_ROOT)


@pytest.mark.usefixtures("fixture_tmp_path")
class TestPythonLintFunctions(unittest.TestCase):
    tmp_path = None

    def setUp(self):
        self.file = self.tmp_path / "dummy_python_file.py"
        ugly_code = "aa  =\ndef bb:\ncc  = 3"
        create_file(self.file, ugly_code)

    def test_pylint_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_pylint([self.file])

    def test_flake8_lint_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            test_flake8_lint(self.file)

    def test_black_formatting_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            test_black_formatting(self.file)
