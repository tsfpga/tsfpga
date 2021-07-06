# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from os.path import relpath
from pathlib import Path
import sys

from setuptools import setup, find_packages

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

import tsfpga
from tsfpga.about import get_slogan
from tsfpga.git_utils import find_git_files
from tsfpga.system_utils import read_file


README_RST = REPO_ROOT / "readme.rst"
REQUIREMENTS_TXT = REPO_ROOT / "requirements.txt"
REQUIREMENTS_DEVELOP_TXT = REPO_ROOT / "requirements_develop.txt"


def main():
    setup(
        name="tsfpga",
        version=tsfpga.__version__,
        description=get_slogan(),
        long_description=read_file(README_RST),
        long_description_content_type="text/x-rst",
        license="BSD 3-Clause License",
        author="Lukas Vik",
        author_email="2767848-LukasVik@users.noreply.gitlab.com",
        url="https://tsfpga.com",
        python_requires=">=3.6",
        install_requires=read_requirements_file(REQUIREMENTS_TXT),
        extras_require=dict(dev=read_requirements_file(REQUIREMENTS_DEVELOP_TXT)),
        packages=find_packages(),
        package_data={"tsfpga": get_package_data()},
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "License :: OSI Approved :: BSD License",
            "Natural Language :: English",
            "Intended Audience :: Developers",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: POSIX :: Linux",
            "Topic :: Software Development :: Testing",
            "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        ],
        zip_safe=False,
    )


def read_requirements_file(path):
    requirements = []
    with path.open() as file_handle:
        # Requirements file contains one package name per line
        for line_data in file_handle.readlines():
            if line_data:
                requirements.append(line_data.strip())

    return requirements


def get_package_data():
    """
    Additional files that shall be included in the release, apart from the python packages.

    All python files are included as packages by the find_packages() call as long as they have
    an __init__.py file in the folder. Include all other files from the repo as package data.
    This includes non-python files as well as python files that are not part of a package (such
    as various module_*.py, etc).
    """
    non_python_files = list(find_git_files(tsfpga.REPO_ROOT, file_endings_avoid=".py"))

    all_python_files = find_git_files(tsfpga.REPO_ROOT, file_endings_include=".py")
    non_package_python_files = []
    for python_file in all_python_files:
        if not (python_file.parent / "__init__.py").exists():
            non_package_python_files.append(python_file)

    package_data = non_python_files + non_package_python_files

    # Specify path relative to the tsfpga python package folder
    tsfpga_package_root = REPO_ROOT / "tsfpga"
    package_data = [
        path_relative_to_str(file_path, tsfpga_package_root) for file_path in package_data
    ]

    return package_data


def path_relative_to_str(path, other):
    """
    Note Path.relative_to() does not support the use case where e.g. readme.md should get
    relative path "../readme.md". Hence we have to use os.path.
    """
    return relpath(str(path), str(other))


if __name__ == "__main__":
    main()
