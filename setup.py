# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import relpath
from pathlib import Path
import sys

from setuptools import setup, find_packages

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))
import tsfpga
from tsfpga.about import get_slogan
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
        zip_safe=False
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
    Additional files that shall be included in the release, apart from the python packages
    """
    package_data = [
        README_RST,
        REQUIREMENTS_TXT,
        REQUIREMENTS_DEVELOP_TXT,
        tsfpga.TSFPGA_PATH / "test" / "lint" / "pylintrc",
        tsfpga.TSFPGA_PATH / "test" / "lint" / "pycodestylerc",
    ]
    package_data += find_package_files(tsfpga.TSFPGA_TCL)
    package_data += find_package_files(tsfpga.TSFPGA_MODULES)

    # Specify path relative to the tsfpga python package folder
    tsfpga_root = Path(REPO_ROOT, "tsfpga")
    package_data = [path_relative_to_str(file, tsfpga_root) for file in package_data]
    return package_data


def path_relative_to_str(path, other):
    """
    Note Path.relative_to() does not support the use case where e.g. readme.md should get
    relative path "../readme.md". Hence we have to use os.path.
    """
    return relpath(str(path), str(other))


def find_package_files(directory):
    """
    Find files to include in the package, ignoring temporary files.
    """
    files = []
    for file in directory.glob("**/*"):
        if not file.suffix.endswith("pyc"):
            files.append(file)
    return files


if __name__ == "__main__":
    main()
