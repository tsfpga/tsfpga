Changed

* Change register json definition file name from ``<name>_regs.json`` to ``regs_<name>.json``.
* Refactor register handling to use only one class :class:`.RegisterList`.
* ``default_registers`` passed to :class:`.BaseModule` shall now be a list of :class:`.Register`,
  instead of a dict.
