.. _simulation:

Simulation flow
===============

This page shows how to run simulations using tsfpga and VUnit.

As far as simulations go tsfpga can be seen as layer on top of VUnit.
tsfpga helps manage the inputs to your simulation project: source files, test benches, :ref:`test configurations <local_configuration>`, :ref:`register code generation <registers>`, :ref:`IP cores <vivado_ip_cores>`, :ref:`simlib <vivado_simlib>`,...
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
        "path/to/my/modules"
    ]
    for module in get_modules(my_modules_folders):
        vunit_library = vunit_proj.add_library(module.library_name)
        for hdl_file in module.get_simulation_files():
             vunit_library.add_source_file(hdl_file.filename)
        module.setup_simulations(vunit_proj)

The call to :ref:`get_modules() <get_modules>` creates :ref:`module objects <module_objects>` from the directory structure of the folders listed in the argument.
The library name is deduced from the name of each module folder.
Source files, packages and testbenches are collected from a few standard locations within the module folder.

.. note::
    If you use a different folder structure within the modules then what is currently supported by tsfpga, feel free to create an `issue <https://gitlab.com/truestream/tsfpga/issues>`__ or a merge request.


The ``module.get_simulation_files()`` call returns a list of files (:ref:`HdlFile objects <hdl_file>`) that are to be included in the simulation project.
This includes source files and packages as well as test files.
If you use :ref:`register code generation <registers>`, the call to ``module.get_simulation_files()`` will generate a new VHDL package so that you are always simulating with an up-to-date register definition.

Actually even this example is not truly minimal.
The call to ``module.setup_simulations()`` does nothing in default setup, but is used to set up :ref:`local configuration of test cases <local_configuration>` later.



Realistic example
-----------------

If you want to dive into a more realistic example have a look at `examples/simulate.py <https://gitlab.com/truestream/tsfpga/blob/master/examples/simulate.py>`__ in the repo.
Or continue reading this document for an explanation of the mechanisms.

This file handles things like

* Only a subset of sources available when using a non-commercial simulator
* Compile :ref:`Vivado simlib <vivado_simlib>` and :ref:`Vivado IP cores <vivado_ip_cores>`



.. _local_configuration:

Local configuration of test cases
---------------------------------

Running test cases in a few different configurations via generics is a common design pattern.
This can be achieved in tsfpga by creating a file ``module_<module_name>.py`` in the root of the module folder.

Say for example if we want to set some generics for a FIFO testbench, located in a module called ``fifo``, which is located under ``modules``.
We would create the file ``modules/fifo/module_fifo.py``, and fill it with something like this.

.. code-block:: python
    :caption: Example ``module_fifo.py`` that sets up local configuration of test cases.

    from tsfpga.module import BaseModule


    class Module(BaseModule):

        def setup_simulations(self, vunit_proj, **kwargs):
            tb = vunit_proj.library(self.library_name).test_bench("tb_fifo")
            for width in [8, 24]:
                for depth in [16, 1024]:
                    name = f"width_{width}.depth_{depth}"
                    tb.add_config(name=name, generics=dict(width=width, depth=depth))

This will result in the tests

.. code-block:: shell

    fifo.tb_fifo.width_8.depth_16.all
    fifo.tb_fifo.width_8.depth_1024.all
    fifo.tb_fifo.width_24.depth_16.all
    fifo.tb_fifo.width_24.depth_1024.all

So what happens here is that we created a class ``Module`` that inherits from :ref:`BaseModule <module_objects>`.
In this class we overloaded the ``setup_simulations()`` method, which does nothing in the parent class, to set up our simulation configurations.
The :ref:`get_modules() <get_modules>` call used in our ``simulate.py`` will recognize that this module has a Python file to set up it's own class.
When creating module objects the function will then use the user-specified class for this module.
Later in ``simulate.py`` when ``setup_simulations()`` is run, the code we specified above will be run.

.. note::
    Note that the class must be called exactly ``Module``.

There is also a ``kwargs`` argument available in the ``setup_simulations()`` signature which can be used to send arbitrary parameters from ``simulate.py`` to the module.
This can be used for example to point out the location of test data.
Or maybe select some test mode with a parameter to your ``simulate.py``.
This is pure Python so you can get as fancy as you want to.



.. _vivado_simlib:

Vivado simulation libraries
---------------------------

Compiled Vivado simulation libraries (unisim, xpm, etc.) are often need in the simulation project.
The ``VivadoSimlib`` class provides an easy interface for handling simlib.
It will run Vivado with a TCL script that compiles simlib, and will only do a recompile when necessary (new Vivado or simulator version, etc.).

.. autoclass:: tsfpga.vivado_simlib.VivadoSimlib()
    :members:

    .. automethod:: __init__

Adding simlib to you simulation project using this class is achieved by simply doing:

.. code-block:: python
    :caption: Adding simlib to your simulation project in ``simulate.py``.

    from tsfpga.vivado_simlib import VivadoSimlib

    ...

    vivado_simlib = VivadoSimlib(vunit_proj, temp_dir)
    vivado_simlib.compile_if_needed()
    vivado_simlib.add_to_vunit_project()



.. _vivado_ip_cores:

Simulating with Vivado IP cores
-------------------------------

There is a class available in tsfpga for handling the IP cores that shall be included in the simulation project.
From your list of modules it will create a Vivado project with all the IP cores.
This project shall then be used to generate the simulation models for the IP cores, which shall then be added to the simulation project.

Note that you must follow the :ref:`folder structure <ip_cores_folder>` for this to work.

.. autoclass:: tsfpga.vivado_ip_cores.VivadoIpCores()
    :members:

    .. automethod:: __init__

Adding IP cores to your simulation project can be done like this:

.. code-block:: python
    :caption: Adding Vivado IP cores to your simulation project in ``simulate.py``.

    from tsfpga.vivado_ip_cores import VivadoIpCores
    from vunit.vivado.vivado import create_compile_order_file, add_from_compile_order_file

    ...

    vivado_ip_cores = VivadoIpCores(modules, temp_dir, "xc7z020clg400-1")
    vivado_project_created = vivado_ip_cores.create_vivado_project_if_needed()

    if vivado_project_created:
        # If the IP core Vivado project has been (re)created we need to create
        # a new compile order file
        create_compile_order_file(vivado_ip_cores.vivado_project_file,
                                  vivado_ip_cores.compile_order_file)

    add_from_compile_order_file(vunit_proj, vivado_ip_cores.compile_order_file)

Note that we use functions from VUnit to handle parts of this.
The ``create_compile_order_file()`` function will run a TCL script on the project that generates simulation models and saves a compile order to file.
The ``add_from_compile_order_file()`` function will then add the files in said compile order to the VUnit project.
