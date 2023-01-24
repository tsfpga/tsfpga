# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import sys
from pathlib import Path

# Third party libraries
from setuptools import find_packages, setup

# Do PYTHONPATH insert() instead of append() to prefer any local repo checkout over any pip install
REPO_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# First party libraries
import tsfpga
from tsfpga.about import get_readme_rst, get_slogan
from tsfpga.system_utils import path_relative_to

REQUIREMENTS_TXT = tsfpga.TSFPGA_PATH / "requirements.txt"
REQUIREMENTS_DEVELOP_TXT = tsfpga.TSFPGA_PATH / "requirements_develop.txt"


def main():
    """
    Be extremely careful when making changes to this setup script. It is hard to see what is
    actually included and what is missing. Also the package data, and where it gets placed in the
    release tree, is very messy.

    When making changes it is recommended to try the release locally before committing to main.
    To test in a docker image do, e.g:

    python tools/build_pypi_release.py --clean-and-build
    docker run --rm --interactive --tty --volume $(pwd)/dist:/dist:ro --workdir /dist \
        python:3.8-slim-buster /bin/bash
    python -m pip install tsfpga-8.0.2.tar.gz

    The install should pass and you should be able to run python and "import tsfpga".
    You should see all the files in "/usr/local/lib/python3.8/site-packages/tsfpga". Check that
    e.g. pylintrc, vivado_settings.tcl, module_fifo.py, etc. are there.
    Test to run "python -m pip uninstall tsfpga" and see that it passes. Check the output to see
    that there are not package files installed in weird locations (such as /usr/local/lib/).
    """
    setup(
        name="tsfpga",
        version=tsfpga.__version__,
        description=get_slogan(),
        long_description=get_readme_rst(include_extra_for_pypi=True),
        long_description_content_type="text/x-rst",
        license="BSD 3-Clause License",
        author="Lukas Vik",
        author_email="2767848-LukasVik@users.noreply.gitlab.com",
        url="https://tsfpga.com",
        project_urls={
            "Documentation": "https://tsfpga.com/",
            "Changelog": "https://tsfpga.com/release_notes.html",
            "Source": "https://gitlab.com/tsfpga/tsfpga",
            "Issues": "https://gitlab.com/tsfpga/tsfpga/-/issues",
        },
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
    with open(path, encoding=tsfpga.DEFAULT_FILE_ENCODING) as file_handle:
        # Requirements file contains one package name per line
        for line_data in file_handle.readlines():
            if line_data:
                requirements.append(line_data.strip())

    return requirements


def get_package_data():
    """
    Get all files that shall be include with the release, apart from the package python files
    that are already there.

    Note that this will include all matching files in the file system. Highly recommended to run
    from a clean repo.
    """
    files = get_package_files(tsfpga.TSFPGA_PATH)

    # Specify path relative to the tsfpga python package folder
    package_data = [str(path_relative_to(file_path, tsfpga.TSFPGA_PATH)) for file_path in files]

    return package_data


def get_package_files(folder):
    """
    Find non-python files and non-package python files (namely, module_*.py) to include.
    """
    assert folder.exists(), folder

    all_files_and_folders = folder.glob("**/*")
    non_python_files = []
    for path in all_files_and_folders:
        if path.is_file() and path.suffix != ".py" and path.suffix != ".pyc":
            non_python_files.append(path)

    all_python_files = folder.glob("**/*.py")
    non_package_python_files = []
    for python_file in all_python_files:
        if not (python_file.parent / "__init__.py").exists():
            non_package_python_files.append(python_file)

    return non_python_files + non_package_python_files


if __name__ == "__main__":
    main()
