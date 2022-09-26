# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


def get_slogan():
    result = """\
tsfpga is a development platform that aims to streamline the code structure and user experience in
your FPGA project."""
    return result


def get_short_doc():
    return f"""{get_slogan()}
With its python build/simulation flow it is perfect for CI/CD and test-driven development.
Focus has been placed on flexibility and modularization, achieving scalability even in very large
multi-vendor code bases.
"""


def get_doc():
    """
    Prepend get_short_doc() to this to get the complete doc.
    """
    return """Key features
------------

* Source code centric project structure: Build projects, test configurations, constraints, IP cores,
  etc. are handled close to the source code.
* Automatically adds build/simulation sources if a recognized folder structure is used.
* Enables local VUnit configuration setup without multiple ``run.py``.
* Handling of IP cores and simlib for your simulation project, with automatic re-compile
  when necessary.
* Python-based parallel Vivado build system.
* Tightly integrated with `hdl_registers <https://hdl-registers.com>`__.
  Register code generation will be performed before each simulation and each build.
* Released under the very permissive BSD 3-Clause License.

The maintainers place high focus on quality, with everything having good unit test coverage and a
thought-out structure.
The project is mature and used in many production environments.
"""


def get_readme_rst(
    include_extra_for_gitlab=False,
    include_extra_for_website=False,
    include_extra_for_pypi=False,
):
    """
    Get the complete README.rst for tsfpga (to be used on website and in PyPI release).

    The arguments control some extra text that is included. This is mainly links to the
    other places where you can find information on the project (website, gitlab, PyPI).

    Arguments:
        include_extra_for_gitlab (bool): Include the extra text that shall be included in the
            gitlab README.
        include_extra_for_website (bool): Include the extra text that shall be included in the
            website main page.
      include_extra_for_pypi (bool): Include the extra text that shall be included in the
            PyPI release README.
    """
    if include_extra_for_gitlab:
        extra_rst = """\
**See documentation on the website**: https://tsfpga.com

**See PyPI for installation details**: https://pypi.org/project/tsfpga/
"""
    elif include_extra_for_website:
        extra_rst = """\
This website contains readable documentation for the project.
To check out the source code go to the `gitlab page <https://gitlab.com/tsfpga/tsfpga>`__.
To install see the `PyPI page <https://pypi.org/project/tsfpga/>`__.
"""
    elif include_extra_for_pypi:
        extra_rst = """\
**See documentation on the website**: https://tsfpga.com

**Check out the source code on gitlab**: https://gitlab.com/tsfpga/tsfpga
"""
    else:
        extra_rst = ""

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
