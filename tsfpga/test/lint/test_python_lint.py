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
from tsfpga.system_utils import create_file, delete


THIS_DIR = Path(__file__).parent


def run_pylint(files):
    config = THIS_DIR / "pylintrc"
    command = [sys.executable, "-m", "pylint", f"--rcfile={config}"] + files

    subprocess.check_call(command)


def test_pylint():
    # Exclude doc folder, since conf.py used by sphinx does not conform
    files = list(find_git_files(file_endings_include="py", exclude_directories=[tsfpga.TSFPGA_DOC]))
    run_pylint(files)


def test_black_formatting():
    command = [sys.executable, "-m", "black", "--check", "tsfpga"]
    subprocess.check_call(command, cwd=tsfpga.REPO_ROOT)


def test_flake8_lint():
    command = [sys.executable, "-m", "flake8", "tsfpga"]
    subprocess.check_call(command, cwd=tsfpga.REPO_ROOT)


class TestPythonLintFunctions(unittest.TestCase):
    def setUp(self):
        self.file = THIS_DIR / "dummy_python_file.py"
        ugly_code = "aa  =\ndef bb:\ncc  = 3"
        create_file(self.file, ugly_code)

    def tearDown(self):
        delete(self.file)

    def test_pylint_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_pylint([self.file])

    @staticmethod
    def test_flake8_lint_should_raise_exception_if_there_are_ugly_files():
        with pytest.raises(subprocess.CalledProcessError):
            test_flake8_lint()

    @staticmethod
    def test_black_formatting_should_raise_exception_if_there_are_ugly_files():
        with pytest.raises(subprocess.CalledProcessError):
            test_black_formatting()
