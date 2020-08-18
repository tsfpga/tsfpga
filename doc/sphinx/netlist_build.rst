.. _netlist_build:

Netlist builds
==============

Netlist builds are a class of builds that are not meant to result in a binary.
They are typically used to quickly get information about timing or resource utilization for a module/entity.
A netlist build will run the create and synthesis steps of a normal build.
The build result can be checked towards expected resource utilization figures by attaching :ref:`size_checkers`.

Resource utilization if often critical in FPGA projects.
Using netlist builds with size checkers it is possible to quickly and automatically check the utilization.
These builds can form a regression suite to make sure that the design does not deteriorate and grow.
Since these builds are typically very small, it is reasonable to parameterize many builds via generics and synthesize them in parallel.



Python class
------------

The python class for netlist builds is a child class of :class:`.VivadoProject`.
The only real difference is that IO buffers are not included and no pinning/constraining is needed.
By separating these builds into separate classes, top level FPGA builds and netlist builds can be listed and built separately.

.. autoclass:: tsfpga.vivado.project.VivadoNetlistProject()
    :members:

    .. automethod:: __init__



.. _size_checkers:

Size checkers
-------------

Size checkers are executed after the succesful synthesis.
They will fail the build and printout what when wrong if the conditions are not fulfilled.
They are attached to a build in this fashion:

.. code-block:: python
    :caption: Size checker example.

    VivadoNetlistProject(
        ...,
        result_size_checkers=[
            TotalLuts(LessThan(50)),
            Ramb36(EqualTo(0)),
            Ramb18(EqualTo(1)),
        ]
    )

See the repo for other examples.

.. autoclass:: tsfpga.vivado.size_checker.SizeChecker()
    :members:

    .. automethod:: __init__

.. autoclass:: tsfpga.vivado.size_checker.LessThan()
    :members:

    .. automethod:: __init__
