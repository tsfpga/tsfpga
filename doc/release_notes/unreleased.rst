Fixes

* Compile Vivado simlib library-by-library with GHDL instead of file-by-file.
  Reduces compile time from 7 minutes to 5 seconds.
* Make the error message for bad generic value type a little more helpful.
* Add assertions that some :class:`.VivadoProject` arguments are the correct type.
