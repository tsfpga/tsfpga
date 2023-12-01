.. image:: https://tsfpga.com/logos/banner.png
  :alt: Project banner
  :align: center

|

.. |pic_website| image:: https://tsfpga.com/badges/website.svg
  :alt: Website
  :target: https://tsfpga.com

.. |pic_repository| image:: https://tsfpga.com/badges/repository.svg
  :alt: Repository
  :target: https://github.com/tsfpga/tsfpga

.. |pic_chat| image:: https://tsfpga.com/badges/chat.svg
  :alt: Chat
  :target: https://github.com/tsfpga/tsfpga/discussions

.. |pic_pip_install| image:: https://tsfpga.com/badges/pip_install.svg
  :alt: pypi
  :target: https://pypi.org/project/tsfpga/

.. |pic_license| image:: https://tsfpga.com/badges/license.svg
  :alt: License
  :target: https://tsfpga.com/license_information.html

.. |pic_ci_status| image:: https://github.com/tsfpga/tsfpga/actions/workflows/ci.yml/badge.svg?branch=main
  :alt: CI status
  :target: https://github.com/tsfpga/tsfpga/actions/workflows/ci.yml

.. |pic_python_line_coverage| image:: https://tsfpga.com/badges/python_coverage.svg
  :alt: Python line coverage
  :target: https://tsfpga.com/python_coverage_html

|pic_website| |pic_repository| |pic_pip_install| |pic_license| |pic_chat| |pic_ci_status|
|pic_python_line_coverage|

tsfpga is a flexible and scalable development platform for modern FPGA projects.
With its Python-based build/simulation flow it is perfect for CI/CD and test-driven development.
The API is simple and easy to use
(a complete `simulation project <https://tsfpga.com/simulation.html>`__ is set up in less than
15 lines).

**See documentation on the website**: https://tsfpga.com

**See PyPI for installation details**: https://pypi.org/project/tsfpga/

Key features
------------

* Source code centric `project structure <https://tsfpga.com/module_structure.html>`__
  for scalability.
  Build projects, test configurations, constraints, IP cores, etc. are handled close to the
  source code, not in a central monolithic script.
* Automatically adds build/simulation sources if a recognized folder structure is used.
* Enables `local VUnit test configuration
  <https://tsfpga.com/simulation.html#local-configuration-of-test-cases>`__ without
  multiple ``run.py``.
* Handling of `IP cores <https://tsfpga.com/simulation.html#simulating-with-vivado-ip-cores>`__
  and `simlib <https://tsfpga.com/simulation.html#vivado-simulation-libraries>`__
  for your simulation project, with automatic re-compile when needed.
* Python-based `Vivado build system <https://tsfpga.com/fpga_build.html>`__ where many builds can
  be run in parallel.
* Tightly integrated with `hdl-registers <https://hdl-registers.com>`__.
  Register code generation is performed before each simulation and each build.
* Released under the very permissive BSD 3-Clause License.

The maintainers place high focus on quality, with everything having good unit test coverage and a
thought-out structure.
The project is mature and used in many production environments.
