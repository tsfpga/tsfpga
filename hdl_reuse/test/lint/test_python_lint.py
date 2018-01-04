import os
from os.path import join, dirname, exists
import pytest
import subprocess
import sys
import unittest

from hdl_reuse.system_utils import find_git_files


THIS_DIR = dirname(__file__)


def run_pylint(files):
    config = join(THIS_DIR, "pylintrc")
    command = [sys.executable, "-m", "pylint", "--rcfile=" + config] + files

    subprocess.check_call(command)


def test_pylint():
    files = find_git_files(file_ending="py")
    run_pylint(files)


def run_pycodestyle(files):
    config = join(THIS_DIR, "pycodestylerc")
    command = [sys.executable, "-m", "pycodestyle", "--config=" + config] + files

    subprocess.check_call(command)


def test_pycodestyle():
    files = find_git_files(file_ending="py")
    run_pycodestyle(files)


class TestPythonLintFunctions(unittest.TestCase):

    file = join(THIS_DIR, "dummy_python_file.py")
    ugly_code = """
aa  =
def bb:
cc  = 3
"""

    def setUp(self):
        with open(self.file, "w") as file_handler:
            file_handler.write(self.ugly_code)

    def tearDown(self):
        if exists(self.file):
            os.remove(self.file)

    def test_pylint_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_pylint([self.file])

    def test_pycodestyle_should_raise_exception_if_there_are_ugly_files(self):
        with pytest.raises(subprocess.CalledProcessError):
            run_pycodestyle([self.file])
