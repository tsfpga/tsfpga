# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from subprocess import check_call
from os.path import abspath, dirname, join


ROOT = abspath(join(dirname(__file__), ".."))


def main():
    cmd = [
        "sphinx-build",
        "-EanWT",
        join(ROOT, "doc"),
        join(ROOT, "generated", "sphinx_html"),
    ]
    check_call(cmd)


if __name__ == "__main__":
    main()
