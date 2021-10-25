# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import tsfpga
from tsfpga.system_utils import create_file, read_file


def get_slogan():
    return (
        "tsfpga is a development platform that aims to streamline all aspects of your FPGA project."
    )


def get_short_doc():
    return f"""{get_slogan()}
With its python build/simulation flow, along with complementary VHDL components, it is perfect \
for CI/CD and test-driven development.
Focus has been placed on flexibility and modularization, achieving scalability even in very \
large multi-vendor code bases.
"""


def get_doc():
    """
    Prepend get_short_doc() to this to get the complete doc.
    """
    return """Key features
------------

* Source code centric project structure: Build projects, test configurations, constraints, \
IP cores, etc. are handled close to the source code.
* Automatically adds build/simulation sources if a recognized folder structure is used.
* Enables local VUnit configuration setup without multiple ``run.py``.
* Handling of IP cores and simlib for your simulation project, with automatic re-compile when \
necessary.
* Python-based parallel Vivado build system.
* Tightly integrated with `hdl_registers <https://hdl-registers.com>`__.
  Register code generation will be performed before each simulation and each build.
* Released under the very permissive BSD 3-Clause License.

The maintainers place high focus on quality, with everything having good unit test coverage and a \
thought-out structure.
The project is mature and used in many production environments.
"""


def get_readme_rst(include_website_link, verify=True):
    """
    Get the complete README.rst for tsfpga (to be used on website and in PyPI release).

    Also possible to verify that readme.rst in the project root is identical.
    RST file inclusion in README.rst does not work on gitlab unfortunately, hence this
    cumbersome handling where the README is duplicated in two places.

    Arguments:
        include_website_link (bool): Include a link to the website in README.
        verify (bool): Verify that the readme.rst in repo root (which is shown on gitlab)
            corresponds to the string produced by this function.
    """

    def get_rst(include_link):
        extra_rst = (
            "**See documentation on the website**: https://tsfpga.com\n" if include_link else ""
        )
        readme_rst = f"""\
About tsfpga
============

|pic_website| |pic_gitlab| |pic_gitter| |pic_pip_install| |pic_license| |pic_python_line_coverage|

.. |pic_website| image:: https://tsfpga.com/badges/website.svg
  :alt: Website
  :target: https://tsfpga.com

.. |pic_gitlab| image:: https://tsfpga.com/badges/gitlab.svg
  :alt: Gitlab
  :target: https://gitlab.com/tsfpga/tsfpga

.. |pic_gitter| image:: https://badges.gitter.im/owner/repo.png
  :alt: Gitter
  :target: https://gitter.im/tsfpga/tsfpga

.. |pic_pip_install| image:: https://tsfpga.com/badges/pip_install.svg
  :alt: pypi
  :target: https://pypi.org/project/tsfpga/

.. |pic_license| image:: https://tsfpga.com/badges/license.svg
  :alt: License
  :target: https://tsfpga.com/license_information.html

.. |pic_python_line_coverage| image:: https://tsfpga.com/badges/python_coverage.svg
  :alt: Python line coverage
  :target: https://tsfpga.com/python_coverage_html

{get_short_doc()}
{extra_rst}
{get_doc()}"""

        return readme_rst

    if verify:
        readme_rst = get_rst(include_link=True)
        if read_file(tsfpga.REPO_ROOT / "readme.rst") != readme_rst:
            file_path = create_file(tsfpga.TSFPGA_GENERATED / "sphinx" / "readme.rst", readme_rst)
            assert (
                False
            ), f"readme.rst in repo root not correct. Compare to reference in python: {file_path}"

    return get_rst(include_link=include_website_link)
