Added

* Add ``fifo.fifo_wrapper`` VHDL entity.
* Add ``drop_packet`` support to synchronous and asynchronous FIFOs.
* Add check for pulse width timing violations in synthesized Vivado design.

Breaking changes

* Rename ``fifo.afifo`` to ``fifo.asynchronous_fifo``.
* Rename :class:`.vivado.project.VivadoNetlistProject` constructor
  argument ``analyze_clock_interaction`` to ``analyze_synthesis_timing``.
