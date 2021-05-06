.. _netlist_build:

Netlist builds
==============

Feedback on timing and resource utilization is critical in the design of an HDL component.
To this puropse, tsfpga has a concept called netlist builds for running synthesis on individual components or your full project.
The build result can be checked towards expected resource utilization figures by attaching atuomated :ref:`build_result_checkers`.

With netlist builds and size checkers you can quickly and automatically check the utilization.
This is a great tool when area optimizing a design, or e.g. trying to make arithmetic map to DSP blocks.
These builds can form a regression suite to make sure that the design does not deteriorate and grow.
Since the builds are typically very small, it is reasonable to parameterize many builds via generics and synthesize them in parallel.



.. _build_result_checkers:

Build result checkers
---------------------

Build result checkers are executed after the succesful synthesis.
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

There are checkers available for all the Xilinx primitives, e.g. ``Total LUTs``, ``RAMB18``, ``RAMB36``, etc. as shown in the example.
It is also possibe to put a condition on the maximum logic level of the design, also shown above.

See the :mod:`API documentation <.build_result_checker>` for more.



Build time
----------

For the netlist builds to be useful they should be fast, so that you get quick feedback when developing your component.
A typical netlist build takes 30-60 seconds to build.

In order to achieve a fast build time, the clock interaction check which is usually run after synthesis in :class:`.VivadoProject` is disabled by default.
It can however be enabled with an argument to :meth:`.VivadoNetlistProject.__init__`.

Another way of achieving a fast build is to decrease the number of files/modules that are included in the Vivado project.
To achieve this, the ``names_include`` flag to :meth:`tsfpga.module.get_modules` can be used to only
include the modules that are used by the entity you want to build.
Specifically, including IP cores that are unused can be very detrimental to build time (+60% has been observed in extreme cases).
This is probably a limitation in Vivado project handling, since unused sources are disabled at project creation.

Synthesis in Vivado is multi-threaded based on an RTL partitioning.
For smaller netlist builds it is highly unlikely that a significant porition of the build will be using multiple threads.
Instead, it is probably more beneficial to execute more builds in parallel than to enable multiple threads.



Python class
------------

The python class for netlist builds, :class:`.VivadoNetlistProject`, is a child class of :class:`.VivadoProject`, with marginal differences in settings.
By separating these builds into separate classes, top level FPGA builds and netlist builds can be listed and built separately.
