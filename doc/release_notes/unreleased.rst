Breaking changes

* Change address types (in ``axi_pkg``, ``axil_pkg`` and ``addr_pkg``) to ``unsigned`` rather than ``std_logic_vector``.
  Do the same for AXI ``id``, ``addr``, ``len`` and ``size``.
* Change register definition file from JSON (``regs_<name>.json``) to TOML (``regs_<name>.toml``).
* Build result, as returned by :meth:`.VivadoProject.build`, is now a :class:`.BuildResult` object instead of a ``dict``.
* The hooks :meth:`.VivadoProject.pre_build` and :meth:`.VivadoProject.post_build` must now return ``True`` upon success.
* Rename ``types_pkg.natural_vector`` to ``natural_vec_t`` and ``types_pkg.positive_vector`` to ``positive_vec_t``.
