About tsfpga
============

|pic_website| |pic_gitlab| |pic_gitter| |pic_pip_install| |pic_license| |pic_python_line_coverage| |pic_vhdl_line_coverage| |pic_vhdl_branch_coverage|

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

.. |pic_vhdl_line_coverage| image:: https://tsfpga.com/badges/vhdl_line_coverage.svg
  :alt: VHDL line coverage
  :target: https://tsfpga.com/vhdl_coverage_html

.. |pic_vhdl_branch_coverage| image:: https://tsfpga.com/badges/vhdl_branch_coverage.svg
  :alt: VHDL branch coverage
  :target: https://tsfpga.com/vhdl_coverage_html

tsfpga is a development platform that aims to streamline all aspects of your FPGA project.
With its python build/simulation flow, along with complementary VHDL components, it is perfect for CI/CD and test-driven development.
Focus has been placed on flexibility and modularization, achieving scalability even in very large multi-vendor code bases.

**See documentation on the website**: https://tsfpga.com

Key features
------------

* Source code centric project structure: Build projects, test configurations, constraints, IP cores, etc. are handled close to the source code.
* Automatically adds build/simulation sources if a recognized folder structure is used.
* Enables local VUnit configuration setup without multiple ``run.py``.
* Handling of IP cores and simlib for your simulation project, with automatic re-compile when necessary.
* Python-based parallel Vivado build system.
* Register code generation from TOML: VHDL package, HTML documentation, C header, C++ class.
* VHDL AXI components that enable the register bus: AXI-to-AXI-Lite converter, AXI-Lite interconnect, AXI-Lite mux (splitter), AXI-Lite clock domain crossing, AXI-Lite generic register file.

The maintainers place high focus on quality, with everything having good unit test coverage and a thought-out structure.
The project is mature and used in many production environments.
