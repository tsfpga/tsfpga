Fixes

* Fix synchronous FIFO signal ``almost_empty`` being de-asserted too early when ``almost_empty_level`` is zero.

Breaking changes

* Area optimize the synchronous FIFO.
  A generic ``include_level_counter`` is introduced that must be set to ``true`` for the level counter output to be valid.
  Depth must be a power of two.
* Change meaning of ``almost_empty`` FIFO signal to be "'1' if there are almost_full_level or more words available in the FIFO".
  Used to be "fewer than almost_full_level".
* Change register json definition file name from ``<name>_regs.json`` to ``regs_<name>.json``.
* ``default_registers`` passed to :class:`.BaseModule` shall now be a list of :class:`.Register`,
  instead of a dict.
* FPGA build projects shall now be set up with :meth:`.BaseModule.get_build_projects` using ``module_<name>.py`` rather than with ``project_<name>.py``. See :ref:`documentation <example_project_class>`.
* Rename ``FpgaProjectList`` to :class:`.BuildProjectList` to get a consistent naming.
* Constructor argument to :class:`.BuildProjectList` shall now be a list of modules rather than a list of modules folders.
* Rename ``axi_pkg.axi_w_strb_width`` to ``axi_pkg.axi_strb_width``.

Internal changes

* Refactor register handling to use only one class :class:`.RegisterList`.
