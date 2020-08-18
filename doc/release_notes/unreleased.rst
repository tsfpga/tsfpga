Added

* Add automatic size checkers for netlist builds: :ref:`size_checkers`.

Breaking changes

* Change address types (in ``axi_pkg``, ``axil_pkg`` and ``addr_pkg``) to be ``unsigned`` rather than ``std_logic_vector``.
  Do the same for AXI ``id``, ``addr``, ``len`` and ``size``.
* Change register definition file from JSON (``regs_<name>.json``) to TOML (``regs_<name>.toml``).
  See example syntax :ref:`here <toml_file>`.
* Build result, as returned by :meth:`.VivadoProject.build`, is now a :class:`.BuildResult` object instead of a ``dict``.
* The hooks :meth:`.VivadoProject.pre_build` and :meth:`.VivadoProject.post_build` must now return ``True`` upon success.
* Rename ``types_pkg.natural_vector`` to ``natural_vec_t`` and ``types_pkg.positive_vector`` to ``positive_vec_t``.
* Move Vivado-related Python code from ``tsfpga`` package to sub-package ``tsfpga.vivado``.
  The Python modules are renamed accordingly:

  * ``tsfpga.vivado_utills`` -> ``tsfpga.vivado.common``
  * ``tsfpga.vivado_ip_cores`` -> ``tsfpga.vivado.ip_cores``
  * ``tsfpga.vivado_project`` -> ``tsfpga.vivado.project``
  * ``tsfpga.vivado_simlib`` -> ``tsfpga.vivado.simlib``
  * ``tsfpga.vivado_simlib_commercial`` -> ``tsfpga.vivado.simlib_commercial``
  * ``tsfpga.vivado_simlib_ghdl`` -> ``tsfpga.vivado.simlib_ghdl``
  * ``tsfpga.vivado_tcl`` -> ``tsfpga.vivado.tcl``
  * ``tsfpga.utilization_parser`` -> ``tsfpga.vivado.utilization_parser``
