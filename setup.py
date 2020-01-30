# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import dirname, join, relpath
from setuptools import setup, find_packages
import sys

ROOT = join(dirname(__file__))
sys.path.append(ROOT)
from tsfpga.about import get_version
from tsfpga.git_utils import find_git_files


def main():
    setup(
        name="tsfpga",
        version=get_version(),
        description="A project platform for modern FPGA development",
        long_description=get_readme_description(),
        long_description_content_type="text/markdown",
        license="BSD 3-Clause License",
        author="Lukas Vik",
        author_email="2767848-LukasVik@users.noreply.gitlab.com",
        url="https://gitlab.com/truestream/tsfpga",
        python_requires=">=3.6",
        install_requires=get_package_requirements(),
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


def get_readme_description():
    with open(join(ROOT, "readme.md")) as file_handle:
        return file_handle.read()


def get_package_requirements():
    requirements = []
    with open(join(ROOT, "requirements.txt")) as file_handle:
        # Requirements file contains one package name per line
        for line_data in file_handle.readlines():
            if line_data:
                requirements.append(line_data.strip())

    return requirements


def get_package_data():
    """
    Additional files that shall be included in the release, apart from the python packages
    """
    package_data = []
    package_data += list(find_git_files(directory=join(ROOT, "tsfpga", "tcl")))
    package_data += list(find_git_files(directory=join(ROOT, "modules")))

    # Specify path relative to the tsfpga python package folder
    package_data = [relpath(file_name, join(ROOT, "tsfpga")) for file_name in package_data]
    return package_data


if __name__ == "__main__":
    main()
