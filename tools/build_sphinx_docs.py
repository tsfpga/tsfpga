# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import abspath, dirname, join
from subprocess import check_call
import sys


REPO_ROOT = abspath(join(dirname(__file__), ".."))
sys.path.append(REPO_ROOT)
import tsfpga


def main():
    generate_registers()
    build_documentation()


def generate_registers():
    cmd = [
        sys.executable,
        join(tsfpga.TSFPGA_EXAMPLES, "build.py"),
        "--generate-registers-only",
    ]
    check_call(cmd)


def build_documentation():
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-EanWT",
        join(REPO_ROOT, "doc", "sphinx"),
        join(REPO_ROOT, "generated", "sphinx_html"),
    ]
    check_call(cmd)


if __name__ == "__main__":
    main()
