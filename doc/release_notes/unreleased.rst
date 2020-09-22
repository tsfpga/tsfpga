Added

* Add optional ``clk_in`` port to ``resync_level`` which enables a more deterministic latency constraint.
* Add support for HTML paragraph breaks in register/bit descriptions.
  Consecutive newlines will be converted to paragraph breaks.
* Add support for parallel builds of FPGA projects using the :class:`.BuildProjectList` class.

Breaking changes

* Rename ``resync_on_signal`` to ``resync_level_on_signal`` and ``resync_slv_on_signal`` to ``resync_slv_level_on_signal``.
  This is more descriptive and follows the naming of the other resync blocks.
* The generated register HTML page no longer supports markdown flavor of using underscores to annotate.
  Instead use **\*\*double asterisks for bold\*\*** and *\*single asterisks for emphasis\**.
  This change is done to make it easier to refer to other registers/constants/signals who very often have underscores in their name.
* Rename ``axi_interconnect`` to ``axi_simple_crossbar`` and ``axil_interconnect`` to ``axil_simple_crossbar``.
  This naming is factual (it is a crossbar, not an interconnect) and more descriptive.
* Rename ``RegisterList.create_html_table()`` to :meth:`.RegisterList.create_html_register_table`.
* Deprecate ``BaseModule.setup_simulations()`` in favor of :meth:`.BaseModule.setup_vunit`.
* Rework :class:`.BuildProjectList` class completely.
  See the :class:`class documentation <.BuildProjectList>`, the :ref:`minimal usage example <example_build_py>` and the `build.py example in the repo <https://gitlab.com/tsfpga/tsfpga/-/blob/master/examples/build.py>`__.
* Change :class:`.VivadoProject` to catch non-zero exit code exception if Vivado call fails.
  If :meth:`.VivadoProject.create` or :meth:`.VivadoProject.open` fail they will return ``False``.
  If :meth:`.VivadoProject.build` fails, the returned :class:`.BuildResult` object will have ``success`` set to ``False``.
