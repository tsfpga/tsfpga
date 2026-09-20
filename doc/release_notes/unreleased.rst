Breaking changes

* Move project filtering from :class:`.BuildProjectList` constructor
  to :func:`.get_build_project_list`.

Requires VUnit version 4.7.1.

Added

* Add support for :ref:`netlist builds <yosys_netlist_build>` using Yosys and the
  ``ghdl-yosys-plugin``, as an open-source alternative to :class:`.VivadoNetlistProject`.
* Allow :class:`.YosysNetlistBuild` projects to be returned from
  :meth:`.BaseModule.get_build_projects` and handled by :class:`.BuildProjectList`.
* Add support for generics when the :class:`.YosysNetlistBuild` top level is a
  Verilog/SystemVerilog module, where they are applied as parameters.

Fixed

* Fix ``ValueError: I/O operation on closed file`` being raised instead of the real GHDL/Yosys
  error message when a build is driven through VUnit's test runner.
