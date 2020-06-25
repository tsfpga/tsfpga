Breaking changes

* Change address types (in ``axi_pkg``, ``axil_pkg`` and ``addr_pkg``) to ``unsigned`` rather than ``std_logic_vector``.
  Do the same for AXI ``id``, ``addr``, ``len`` and ``size``.
* Change register definition file from JSON (``regs_<name>.json``) to TOML (``regs_<name>.toml``).
