Breaking changes

* Change register json definition file name from ``<name>_regs.json`` to ``regs_<name>.json``.
* ``default_registers`` passed to :class:`.BaseModule` shall now be a list of :class:`.Register`,
  instead of a dict.

Internal changes

* Refactor register handling to use only one class :class:`.RegisterList`.
