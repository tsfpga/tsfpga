Added

* Add ``resync.resync_slv_level_coherent`` VHDL entity.

Breaking changes

* Rename all VHDL files/entities/types/constants with prefix ``axil_`` to have prefix ``axi_lite_``.
  This is done in order to be more descriptive, and to be consistent with ``axi_stream`` components.
  A search/replace ``axil_`` -> ``axi_lite_`` on all VHDL in your FPGA project should be able to adapt for this.

* Always call :meth:`.BaseModule.registers_hook` from :meth:`.BaseModule.registers`, even when TOML file does not exists.
  This means that ``self._registers`` might be ``None`` when entering :meth:`.BaseModule.registers_hook`.

* Add mandatory generic ``enable_input_register`` to ``resync.resync_level`` and ``resync.resync_slv_level`` VHDL entities.
  See ``resync_level.vhd`` file header for details.
