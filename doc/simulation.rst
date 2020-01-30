.. _simulation_flow:

Simulation flow
===============

This page how to run simulations using tsfpga and VUnit.

As far as simulations go tsfpga can be seen as layer on top of VUnit.
tsfpga helps manage the inuts to your simulation project: source files, test benches, :ref:`test configurations <local_configuration>`, register code generation, IP cores, :ref:`simlib <vivado_simlib>`,...
As such all features of VUnit are available as they are, and all simulators are supported (ghdl as well as commercial).


Minimal example
---------------

If your source code is roughly organized along the :ref:`folder structure <folder_structure>`, running simulations using tsfpga and VUnit is as simple as:

.. code-block:: python
    :caption: Minimal ``simulate.py`` file.

    from vunit import VUnit
    from tsfpga.module import get_modules

    vunit_proj = VUnit.from_argv()
    my_modules_folders = [
        join("path", "to", "my", "modules")
    ]
    for module in get_modules(my_modules_folders):
        vunit_library = vunit_proj.add_library(module.library_name)
        for hdl_file in module.get_simulation_files():
             vunit_library.add_source_file(hdl_file.filename)
        module.setup_simulations(vunit_proj)

Actually even this example is not truly minimal.
The call to ``module.setup_simulations()`` does nothing in default setup, but is used to set up :ref:`local configuration of test cases <local_configuration>` later.


.. _get_modules_method:

The get_modules() method
------------------------

.. autofunction:: tsfpga.module.get_modules


.. _module_objects:

Module objects
--------------

.. autoclass:: tsfpga.module.BaseModule()
    :members:

    .. automethod:: __init__


.. _local_configuration:

Local configuration of test cases
---------------------------------

TBC


.. _vivado_simlib:

Simulating with Vivado simlib
-----------------------------

TBC



.. _hdl_file:

HdlFile objects
---------------

.. autoclass:: tsfpga.hdl_file.HdlFile()
    :members:

    .. automethod:: __init__

