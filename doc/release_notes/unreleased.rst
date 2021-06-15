Added

* Add ``resync.resync_slv_level_coherent`` VHDL entity.

* Add :class:`.VivadoIpCoreProject` class which is the default ``vivado_project_class`` for :meth:`.VivadoIpCores.__init__`.
  If you use a custom class it is a good idea to inherit from this new class instead of :class:`.VivadoProject`.

* Add :class:`.IpCoreFile` class to represent IP core files, which adds the possibility of
  parameterizing IP core creation.

Fixed

* Fix bug where Vivado build-time generics dictionary was not copied, which could result in incorrect generic values for parallel builds.

Breaking changes

* Rename all VHDL files/entities/types/constants with prefix ``axil_`` to have prefix ``axi_lite_``.
  This is done in order to be more descriptive, and to be consistent with ``axi_stream`` components.
  A search/replace ``axil_`` -> ``axi_lite_`` on all VHDL in your FPGA project should be able to adapt for this.

* Always call :meth:`.BaseModule.registers_hook` from :meth:`.BaseModule.registers`, even when TOML file does not exists.
  This means that ``self._registers`` might be ``None`` when entering :meth:`.BaseModule.registers_hook`.

* Add mandatory generic ``enable_input_register`` to ``resync.resync_level`` and ``resync.resync_slv_level`` VHDL entities.
  See ``resync_level.vhd`` file header for details.

* Rework testbench helper procedures in ``reg_file.reg_operations_pkg`` completely.

  1. Rename ``bits``/``bits`` argument to ``bit_index``/``bit_indexes``.

  2. Rename ``expected`` argument to ``value``.

  3. Add mandatory ``value``/``values`` argument to ``check_reg_equal_bit``/``check_reg_equal_bits``.

  4. Add optional ``other_bits_value`` argument to ``check_reg_equal_bit``/``check_reg_equal_bits``
     to control what value the non-designated bits are expected to be (default is zero).

  5. Add mandatory ``value``/``values`` argument to
     ``wait_until_reg_equals_bit``/``wait_until_reg_equals_bits``.

  6. Add optional ``other_bits_value`` argument to
     ``wait_until_reg_equals_bit``/``wait_until_reg_equals_bits`` to control what value the
     non-designated bits are expected to be (default is don't care).

  7. Add mandatory ``value``/``values`` argument to ``write_reg_bit``/``write_reg_bits``.

  8. Add optional ``other_bits_value`` argument to ``write_reg_bit``/``write_reg_bits`` to control
     what value is assigned to non-designated bits (default is zero).

  9. Add ``read_modify_write_reg_bit``/``read_modify_write_reg_bits`` which performs a
     read-modify-write where the designated bits are updated.
