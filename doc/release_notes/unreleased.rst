Added

* Add ``fifo.fifo_wrapper`` VHDL entity.
* Add ``drop_packet`` support to synchronous and asynchronous FIFOs.
* Add check for pulse width timing violations after implementation in Vivado build system.
* Check clock interaction after implementation as well in Vivado build system.

Breaking changes

* Rename ``fifo.afifo`` to ``fifo.asynchronous_fifo``.
* Rename :class:`.vivado.project.VivadoNetlistProject` constructor
  argument ``analyze_clock_interaction`` to ``analyze_synthesis_timing``.
* Remove ``tsfpga.vivado.size_checker.Dsp48Blocks`` in favor of :class:`.vivado.size_checker.DspBlocks`.

Changes

* Update timing of ``fifo.fifo`` port ``read_ready`` to get lower fanout and shorter critial path.
  The change implies an increased latency from a read transaction until ``write_ready`` is raised.
