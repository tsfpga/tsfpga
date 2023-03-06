# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


def get_pypi_slogan():
    """
    Short slogan used on pypi.org and in Python package.
    Note that there seems to be an upper limit of 98 characters, so it can't be the same as the one
    on the website.

    Note that this slogan is also listed (manually duplicated) in license.rst for
    academic citations.
    If you change in one place you should change in both.
    """
    result = "A flexible and scalable development platform for modern FPGA projects."
    return result


def get_short_doc():
    return """\
tsfpga is a flexible and scalable development platform for modern FPGA projects.
With its Python-based build/simulation flow it is perfect for CI/CD and test-driven development.
The API is simple and easy to use
(a complete `simulation project <https://tsfpga.com/simulation.html>`__ is set up in less than
15 lines).
"""


def get_doc():
    """
    Prepend get_short_doc() to this to get the complete doc.
    """
    return """\
Key features
------------

* Source code centric `project structure <https://tsfpga.com/module_structure.html>`__:
  Build projects, test configurations, constraints, IP cores, etc. are handled close to the
  source code.
* Automatically adds build/simulation sources if a recognized folder structure is used.
* Enables `local VUnit test configuration
  <https://tsfpga.com/simulation.html#local-configuration-of-test-cases>`__ without
  multiple ``run.py``.
* Handling of `IP cores <https://tsfpga.com/simulation.html#simulating-with-vivado-ip-cores>`__
  and `simlib <https://tsfpga.com/simulation.html#vivado-simulation-libraries>`__
  for your simulation project, with automatic re-compile when needed.
* Python-based `Vivado build system <https://tsfpga.com/fpga_build.html>`__ where many builds can
  be run in parallel.
* Tightly integrated with `hdl_registers <https://hdl-registers.com>`__.
  Register code generation is performed before each simulation and each build.
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
        readme_rst = ""
        extra_rst = """\
**See documentation on the website**: https://tsfpga.com

**See PyPI for installation details**: https://pypi.org/project/tsfpga/
"""
    elif include_extra_for_website:
        # The website needs the initial heading, in order for the landing page to get
        # the correct title.
        # The others do not need this initial heading, it justs makes the gitlab/pypi page
        # more clunky.
        readme_rst = """\
About tsfpga
============

"""
        extra_rst = """\
To install the Python package, see :ref:`installation`.
To check out the source code go to the `gitlab page <https://gitlab.com/tsfpga/tsfpga>`__.
"""
    elif include_extra_for_pypi:
        readme_rst = ""
        extra_rst = """\
**See documentation on the website**: https://tsfpga.com

**Check out the source code on gitlab**: https://gitlab.com/tsfpga/tsfpga
"""
    else:
        readme_rst = ""
        extra_rst = ""

    readme_rst += f"""\
|pic_website| |pic_gitlab| |pic_gitter| |pic_pip_install| |pic_license| |pic_python_line_coverage|

.. |pic_website| image:: https://tsfpga.com/badges/website.svg
  :alt: Website
  :target: https://tsfpga.com

.. |pic_gitlab| image:: https://tsfpga.com/badges/gitlab.svg
  :alt: Gitlab
  :target: https://gitlab.com/tsfpga/tsfpga

.. |pic_gitter| image:: https://tsfpga.com/badges/gitter.svg
  :alt: Gitter
  :target: https://app.gitter.im/#/room/#60a276916da03739847cca54:gitter.im

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
