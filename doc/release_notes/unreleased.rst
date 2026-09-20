Breaking changes

* Update/simplify :class:`.GitSimulationSubset` to use new test pattern feature in VUnit 6.0.0.
* Move project filtering from :class:`.BuildProjectList` constructor
  to :func:`.get_build_project_list`.

Requires VUnit version 5.0.0.dev6 or later.

Added

* Add support for :ref:`netlist builds <yosys_netlist_build>` using Yosys and the
  ``ghdl-yosys-plugin``, as an open-source alternative to :class:`.VivadoNetlistProject`.
* Allow :class:`.YosysNetlistBuild` projects to be returned from
  :meth:`.BaseModule.get_build_projects` and handled by :class:`.BuildProjectList`.

Fixed

* Fix ``ValueError: I/O operation on closed file`` being raised instead of the real GHDL/Yosys
  error message when a build is driven through VUnit's test runner.
* Fix the internal VUnit project used to resolve compile order for netlist builds compiling
  VUnit's simulation builtins.
