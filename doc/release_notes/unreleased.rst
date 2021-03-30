Added

* Add support for bit vector fields in register code generator.

Breaking changes

* Re-work the format for register definition TOML files.

  - Rename ``register`` property ``bits`` to ``bit``.
  - Move ``default_value`` property from ``register`` to be a property on each register field (bits, bit vectors).

  See :ref:`register_toml_format`.

* Rename generated register C header bit definitions to have ``_SHIFT`` and ``_MASK`` suffix.
  This is to be consistent with the naming for bit vector fields.
