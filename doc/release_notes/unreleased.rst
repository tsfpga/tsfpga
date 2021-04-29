Added

* Add support for bit vector fields in register code generator.

* Add optional ``vivado_project_class`` argument to :class:`.VivadoIpCores` constructor.

* Add :meth:`.RegisterList.create_python_class`, :meth:`.RegisterList.get_register_array` and
  :meth:`.RegisterList.get_register_index` methods.

* Add ``axi.axi_stream_pkg`` VHDL package and ``axi.axi_stream_fifo`` VHDL entity.

* Add ``common.periodic_pulser`` VHDL entity.

* Add support for byte strobe and unaligned burst length in ``common.width_conversion``.


Breaking changes

* Re-work the format for register definition TOML files.

  - Rename ``register`` property ``bits`` to ``bit``.
  - Move ``default_value`` property from ``register`` to be a property on each register
    field (bits, bit vectors).

  See :ref:`register_toml_format`.

* Rename generated register C header bit definitions to have ``_SHIFT`` and ``_MASK`` suffix.
  This is to be consistent with the naming for bit vector fields.

* Remove ``#pragma pack(push, 1)`` and ``#pragma pack(pop)`` from register C header.

* The methods :meth:`.RegisterList.get_register`, :meth:`.RegisterList.get_constant`,
  :meth:`.RegisterArray.get_register`, :meth:`.Register.get_field`,
  will now raise exception if nothing matches, instead of returning ``None``.


Changes

* Switch to using python package ``tomlkit`` instead of ``toml`` for parsing register TOML files.

Fixed

* Fix bug in synchronous FIFO when ``drop_packet`` is asserted in same cycle as ``write_last``.
