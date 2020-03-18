Breaking changes

* Change register json definition file name from ``<name>_regs.json`` to ``regs_<name>.json``.
* ``default_registers`` passed to :class:`.BaseModule` shall now be a list of :class:`.Register`,
  instead of a dict.
* Rename ``axi_pkg.axi_w_strb_width`` to ``axi_pkg.axi_strb_width``.

Internal changes

* Refactor register handling to use only one class :class:`.RegisterList`.
