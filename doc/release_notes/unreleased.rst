Breaking changes

* Update/simplify :class:`.GitSimulationSubset` to use new test pattern feature in VUnit 6.0.0.
* Move project filtering from :class:`.BuildProjectList` constructor
  to :func:`.get_build_project_list`.

Requires VUnit version 5.0.0.dev6 or later.

Added

* Add support for :ref:`netlist builds <yosys_netlist_build>` using Yosys and the
  ``ghdl-yosys-plugin``, as an open-source alternative to :class:`.VivadoNetlistProject`.
  Supports Xilinx, Intel and Microchip devices, mixed VHDL/Verilog/SystemVerilog designs, and
  generic resource counting.
* Allow :class:`.YosysNetlistBuild` projects (in addition to :class:`.VivadoProject`) to be
  returned from :meth:`.BaseModule.get_build_projects` and handled by
  :class:`.BuildProjectList`, so a project's standard build script (e.g. ``build_fpga.py``) can
  drive Yosys netlist builds the same way it drives Vivado builds.

Fixed

* Fix a race in ``run_ghdl``/``run_yosys`` where a failing GHDL/Yosys process could raise
  ``ValueError: I/O operation on closed file`` instead of surfacing its real error message, when
  the build was driven through VUnit's own test-runner machinery (e.g.
  :func:`.setup_and_run`), which temporarily redirects stdout per test.
* Fix the same closed-stdout race in :meth:`.BuildReport.print_latest_status`, which could raise
  the same ``ValueError`` (instead of printing the build's pass/fail status) when called from a
  background VUnit test-runner thread while another build's stdout redirection was being torn
  down.
* Fix the same closed-stdout race in :class:`.BuildRunner`'s ``_add_results``, which reused
  VUnit's base ``TestRunner`` implementation verbatim and so still had a bare ``print()`` that
  could raise the same ``ValueError`` instead of printing the trailing blank line after a build's
  status.
* Fix the internal VUnit project used to resolve compile order for
  :ref:`netlist builds <yosys_netlist_build>` compiling VUnit's own simulation builtins (on
  VUnit's released API, ``compile_builtins`` defaults to ``True``) in addition to the design's own
  sources, running GHDL over dozens of unnecessary VUnit-internal VHDL files on every netlist
  build.
