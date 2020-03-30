Breaking changes

* Change register json definition file name from ``<name>_regs.json`` to ``regs_<name>.json``.
* ``default_registers`` passed to :class:`.BaseModule` shall now be a list of :class:`.Register`,
  instead of a dict.
* FPGA build projects shall now be set up with :meth:`.BaseModule.get_build_projects` using ``module_<name>.py`` rather than with ``project_<name>.py``. See :ref:`documentation <example_project_class>`.
* Rename ``FpgaProjectList`` to :class:`.BuildProjectList` to get a consistent naming.
* Constructor argument to :class:`.BuildProjectList` shall now be a list of modules rather than a list of modules folders.
* Rename ``axi_pkg.axi_w_strb_width`` to ``axi_pkg.axi_strb_width``.

Internal changes

* Refactor register handling to use only one class :class:`.RegisterList`.
