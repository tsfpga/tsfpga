# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


REPOSITORY_URL = "https://github.com/tsfpga/tsfpga"
WEBSITE_URL = "https://tsfpga.com"


def get_short_slogan() -> str:
    """
    Short slogan used e.g. on pypi.org.
    Note that there seems to be an upper limit of 98 characters when rendering the slogan
    on pypi.org.

    Note that this slogan should be the same as the one used in the readme and on the website below.
    The difference is capitalization and whether the project name is included.
    """
    result = "A flexible and scalable development platform for modern FPGA projects"
    return result


def get_readme_rst(
    include_extra_for_github: bool = False,
    include_extra_for_website: bool = False,
    include_extra_for_pypi: bool = False,
) -> str:
    """
    Get the complete README.rst for tsfpga (to be used on website and in PyPI release).

    The arguments control some extra text that is included. This is mainly links to the
    other places where you can find information on the project (website, GitHub, PyPI).

    Arguments:
        include_extra_for_github (bool): Include the extra text that shall be included in the
            GitHub README.
        include_extra_for_website (bool): Include the extra text that shall be included in the
            website main page.
      include_extra_for_pypi (bool): Include the extra text that shall be included in the
            PyPI release README.
    """
    if include_extra_for_github:
        readme_rst = ""
        extra_rst = f"""\
**See documentation on the website**: {WEBSITE_URL}

**See PyPI for installation details**: https://pypi.org/project/tsfpga/
"""
    elif include_extra_for_website:
        # The website needs the initial heading, in order for the landing page to get
        # the correct title.
        # The others do not need this initial heading, it just makes the GitHub/PyPI page
        # more clunky.
        readme_rst = """\
About tsfpga
============

"""
        extra_rst = f"""\
To install the Python package, see :ref:`installation`.
To check out the source code go to the `GitHub page <{REPOSITORY_URL}>`__.
"""
    elif include_extra_for_pypi:
        readme_rst = ""
        extra_rst = f"""\
**See documentation on the website**: {WEBSITE_URL}

**Check out the source code on GitHub**: {REPOSITORY_URL}
"""
    else:
        readme_rst = ""
        extra_rst = ""

    readme_rst += f"""\
.. image:: {WEBSITE_URL}/logos/banner.png
  :alt: Project banner
  :align: center

|

.. |pic_website| image:: {WEBSITE_URL}/badges/website.svg
  :alt: Website
  :target: {WEBSITE_URL}

.. |pic_repository| image:: {WEBSITE_URL}/badges/repository.svg
  :alt: Repository
  :target: {REPOSITORY_URL}

.. |pic_chat| image:: {WEBSITE_URL}/badges/chat.svg
  :alt: Chat
  :target: {REPOSITORY_URL}/discussions

.. |pic_pip_install| image:: {WEBSITE_URL}/badges/pip_install.svg
  :alt: pypi
  :target: https://pypi.org/project/tsfpga/

.. |pic_license| image:: {WEBSITE_URL}/badges/license.svg
  :alt: License
  :target: {WEBSITE_URL}/license_information.html

.. |pic_ci_status| image:: {REPOSITORY_URL}/actions/workflows/ci.yml/\
badge.svg?branch=main
  :alt: CI status
  :target: {REPOSITORY_URL}/actions/workflows/ci.yml

.. |pic_python_line_coverage| image:: {WEBSITE_URL}/badges/python_coverage.svg
  :alt: Python line coverage
  :target: {WEBSITE_URL}/python_coverage_html

|pic_website| |pic_repository| |pic_pip_install| |pic_license| |pic_chat| |pic_ci_status|
|pic_python_line_coverage|

tsfpga is a flexible and scalable development platform for modern FPGA projects.
With its Python-based build/simulation flow it is perfect for CI/CD and test-driven development.
The API is simple and easy to use
(a complete `simulation project <{WEBSITE_URL}/simulation.html>`__ is set up in less than
15 lines).

{extra_rst}
Key features
------------

* Source code-centric `project structure <{WEBSITE_URL}/module_structure.html>`__
  for scalability.
  Build projects, test configurations, constraints, IP cores, etc. are handled close to the
  source code, not in a central monolithic script.
* Automatically adds build/simulation sources if a recognized folder structure is used.
* Enables `local VUnit test configuration
  <{WEBSITE_URL}/simulation.html#local-configuration-of-test-cases>`__ without
  multiple ``run.py``.
* Handling of `IP cores <{WEBSITE_URL}/simulation.html#simulating-with-vivado-ip-cores>`__
  and `simlib <{WEBSITE_URL}/simulation.html#vivado-simulation-libraries>`__
  for your simulation project, with automatic re-compile when needed.
* Python-based `Vivado build system <{WEBSITE_URL}/fpga_build.html>`__ where many builds can
  be run in parallel.
* Tightly integrated with `hdl-registers <https://hdl-registers.com>`__.
  Register code generation is performed before each simulation and each build.
* Released under the very permissive BSD 3-Clause License.

The maintainers place high focus on quality, with everything having good unit test coverage and a
thought-out structure.
The project is mature and used in many production environments.
"""

    return readme_rst
