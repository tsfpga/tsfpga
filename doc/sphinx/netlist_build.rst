.. _netlist_build:

Netlist builds
==============

Feedback on timing and resource utilization is critical in the design of an HDL component.
To this purpose, tsfpga has a concept called netlist builds for running synthesis on individual
components or your full project.
The build result can be checked towards expected resource utilization figures by attaching
automated :ref:`build_result_checkers`.

With netlist builds and size checkers you can quickly and automatically check the utilization.
This is a great tool when area optimizing a design, or e.g. trying to make arithmetic map to
DSP blocks.
These builds can form a regression suite to make sure that the design does not deteriorate and grow.
Since the builds are typically very small, it is reasonable to parameterize many builds via generics
and synthesize them in parallel using a :ref:`tsfpga build script <build>`.



.. _build_result_checkers:

Build result checkers
---------------------

Build result checkers are executed after the successful synthesis.
They will fail the build and printout what went wrong if the conditions are not fulfilled.
They are attached to a build in this fashion:

.. code-block:: python
    :caption: Build result checker example.

    VivadoNetlistProject(
        name="result_checker_example",
        modules=modules,
        part="xc7z020clg400-1",
        top="example_top_level",
        build_result_checkers=[
            TotalLuts(LessThan(50)),
            Ramb36(EqualTo(0)),
            Ramb18(EqualTo(1)),
            MaxLogicLevel(EqualTo(4)),
        ]
    )

See the repo for other examples.

There are checkers available for all the Xilinx primitives, e.g. ``Total LUTs``, ``RAMB18``,
``RAMB36``, etc. as shown in the example.
It is also possible to put a condition on the maximum logic level of the design, also shown above.

See the :mod:`API documentation <.build_result_checker>` for more.



Build time
----------

For the netlist builds to be useful they should be fast, so that you get quick feedback when
developing your component.
A typical netlist build takes 30-60 seconds to build.

In order to achieve a fast build time, the clock interaction check which is usually run after
synthesis in :class:`.VivadoProject` is disabled by default.
It can however be enabled with an argument to :meth:`.VivadoNetlistProject.__init__`.

Another way of achieving a fast build is to decrease the number of files/modules that are included
in the Vivado project.
To achieve this, the ``names_include`` flag to :meth:`tsfpga.module.get_modules` can be used to only
include the modules that are used by the entity you want to build.
Specifically, including IP cores that are unused can be very detrimental to build time
(+60% has been observed in extreme cases).
This is probably a limitation in Vivado project handling, since unused sources are disabled at
project creation.

Synthesis in Vivado is multi-threaded based on an RTL partitioning.
For smaller netlist builds it is highly unlikely that a significant portion of the build will be
using multiple threads.
Instead, it is probably more beneficial to execute more builds in parallel than to enable
multiple threads.
This is easily achieved by using the tsfpga :ref:`FPGA project build flow <build>`.



Python class
------------

The python class for netlist builds, :class:`.VivadoNetlistProject`, is a subclass of
:class:`.VivadoProject`, with marginal differences in settings.
By separating these builds into separate classes, top level FPGA builds and netlist builds can be
listed and built separately.



.. _yosys_netlist_build:

Yosys netlist builds
---------------------

As an open-source alternative to the Vivado-based netlist builds above, tsfpga also supports
running netlist synthesis using `Yosys <https://yosyshq.net/yosys/>`__
via the `ghdl-yosys-plugin <https://github.com/ghdl/ghdl-yosys-plugin>`__.
`GHDL <https://ghdl.github.io/ghdl/>`__ is used as the VHDL front end, so the whole flow is
Vivado-free.

.. Note::
  Yosys is not suitable for large builds.
  It takes a very long time and may consume a lot of memory.
  It is recommended for smaller modules, where the intention is a quick verification rather than
  a full fledged build.
  For larger builds, such as top level builds, it is recommended to use the vendor tools.

The ``top`` level is typically a VHDL entity, in which case all of its VHDL dependencies are
found automatically by resolving the compile order.
Any Verilog and SystemVerilog source files found among the modules are read directly by Yosys
(bypassing GHDL), and may be instantiated from the VHDL design as unbound components, as long as
the component name matches the Verilog/SystemVerilog module name.
This is useful for e.g. vendor IP delivered as Verilog, instantiated from an otherwise VHDL
design.

The ``top`` level can also be a Verilog/SystemVerilog module (or the design can have no VHDL top
level at all).
In that case there is no single VHDL top level to automatically resolve dependencies from, so the
names of the VHDL entities that shall be made available for instantiation from the non-VHDL top
level (or from other VHDL entities) must be listed explicitly using the ``vhdl_entities`` argument
to :meth:`.YosysNetlistBuild.__init__`.
Note that build-time and static generics are only supported when ``top`` is a VHDL entity.

This is done using the :class:`.YosysNetlistBuild` class, or one of the architecture-specific
subclasses that target a certain vendor's primitives via a specific Yosys ``synth_*`` command:

* :class:`.YosysXilinxNetlistBuild` targets Xilinx primitives (LUTs, FDs, RAMBs, DSP48s, ...) via
  the Yosys ``synth_xilinx`` command.
* :class:`.YosysIntelNetlistBuild` targets Intel (Altera) primitives (LEs, ``dffeas``,
  ``altsyncram``, ...) via the Yosys ``synth_intel`` command.
* :class:`.YosysMicrochipNetlistBuild` targets Microchip primitives (``CFG*``, ``SLE``,
  ``RAM1K20``, ...) via the Yosys ``synth_microchip`` command.

.. code-block:: python
    :caption: Yosys netlist build example.

    YosysXilinxNetlistBuild(
        name="result_checker_example",
        modules=modules,
        top="example_top_level",
        family="xc7",
        build_result_checkers=[
            TotalLuts(LessThan(50)),
            Ramb36(EqualTo(0)),
            Ramb18(EqualTo(1)),
        ]
    )

All the architecture-specific subclasses produce a utilization report that uses (at least a
subset of) the same resource naming convention as the Vivado utilization report (e.g.
``"Total LUTs"``, ``"FFs"``, ``"DSP Blocks"``), so the checkers in
:mod:`.vivado.build_result_checker` can be used directly, just like for the Vivado-based netlist
builds.
Since the exact block RAM architecture (e.g. "RAMB36"/"RAMB18") differs between vendors, the
generic :class:`.BlockRams` checker shall be used instead of :class:`.Ramb`/:class:`.Ramb36`/
:class:`.Ramb18` (which are Xilinx-specific) when targeting Intel or Microchip.

The base :class:`.YosysNetlistBuild` class uses the generic Yosys ``synth`` command by default,
which does not target any specific architecture. This is useful for getting a quick, tool- and
vendor-agnostic resource count of a design, but note that no aggregated resource counts (e.g.
``"Total LUTs"``) are available in this case -- only the raw Yosys primitive cell counts (e.g.
``"$_DFF_P_"``).

Note that the ``MaximumLogicLevel`` checker is not supported, since that concept does not apply to
a Yosys synthesis result.

Troubleshooting
_______________

The ``ghdl-yosys-plugin`` module, running inside Yosys, is not able to locate GHDL's standard
libraries (``std``, ``ieee``, ...) on its own.
This is handled automatically: each build runs ``ghdl --disp-config`` to find the
"library prefix" and forwards it to the plugin.
If this auto-detection fails, or finds the wrong GHDL installation, set the ``ghdl_prefix``
argument explicitly to override it.
Likewise, if the ``ghdl-yosys-plugin`` is not installed in a location where Yosys finds it
automatically, set the ``ghdl_plugin_path`` argument to point at the plugin module
(typically named ``ghdl.so``).
