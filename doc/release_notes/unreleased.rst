Changed
_______

* Add :meth:`.VivadoProject.open` method.
* Refactor to use ``pathlib.Path`` instead of strings to represent file system paths.
  All paths supplied to tsfpga must now be ``pathlib.Path`` objects.
* Rename ``HdlFile.filename`` to :class:`HdlFile.path <.HdlFile>`.
* Adjust axi_to_axil to not allow more than one outstanding transaction.
* Analyze Vivado build timing using a TCL hook instead of reopening the implemented design.
* Rename ``FPGAProjectList`` to :class:`.FpgaProjectList`
* axil_mux now responds with ``DECERR`` if no slave matches, instead of timing out
* Update interface to vivado simlib API with a factory class. See :ref:`here <vivado_simlib>`.
