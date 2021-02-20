.. _simulation:

Simulation flow
===============

This page shows how to run simulations using tsfpga and VUnit.

As far as simulations go tsfpga can be seen as a layer on top of VUnit.
tsfpga helps manage the inputs to the simulation project: source files, test benches, :ref:`test configurations <local_configuration>`, :ref:`register code generation <registers>`, :ref:`IP cores <vivado_ip_cores>`, :ref:`simlib <vivado_simlib>`, ...
All features of VUnit are available as they are, and all simulators are supported (ghdl as well as commercial).



Minimal simulate.py example
---------------------------

If the source code is roughly organized along the :ref:`folder structure <folder_structure>`, running simulations using tsfpga and VUnit is as simple as:

.. code-block:: python
    :caption: Minimal ``simulate.py`` file.

    from pathlib import Path
    from tsfpga.module import get_modules
    from vunit import VUnit

    vunit_proj = VUnit.from_argv()
    my_modules_folders = [
        Path("path/to/my/modules")
    ]
    for module in get_modules(my_modules_folders):
        vunit_library = vunit_proj.add_library(module.library_name)
        for hdl_file in module.get_simulation_files():
             vunit_library.add_source_file(hdl_file.path)
        module.setup_vunit(vunit_proj)

    vunit_proj.main()

The call to :func:`.get_modules` creates :class:`module objects <.BaseModule>` from the directory structure of the folders listed in the argument.
The library name is deduced from the name of each module folder.
Source files, packages and testbenches are collected from a few standard locations within the module folder.

.. note::
    If you use a different folder structure within the modules than what is currently supported by tsfpga, feel free to create an `issue <https://gitlab.com/tsfpga/tsfpga/issues>`__ or a merge request.


The :meth:`module.get_simulation_files() <.BaseModule.get_simulation_files>` call returns a list of files (:class:`.HdlFile` objects) that are to be included in the simulation project.
This includes source files and packages as well as test files.
If you use :ref:`register code generation <registers>`, the call will generate a new VHDL package so that you are always simulating with an up-to-date register definition.

Actually even this example is not truly minimal.
The call to :meth:`module.setup_vunit() <.BaseModule.setup_vunit>` does nothing in default setup, but is used to set up :ref:`local configuration of test cases <local_configuration>` later.



Realistic example
-----------------

If you want to dive into a more realistic example have a look at `examples/simulate.py <https://gitlab.com/tsfpga/tsfpga/blob/master/examples/simulate.py>`__ in the repo.
Or continue reading this document for an explanation of the mechanisms.

This file handles things like

* Only a subset of sources available when using a non-commercial simulator
* Compile :ref:`Vivado simlib <vivado_simlib>` and :ref:`Vivado IP cores <vivado_ip_cores>`



.. _local_configuration:

Local configuration of test cases
---------------------------------

Running test cases in a few different configurations via generics is a common design pattern.
This can be achieved in tsfpga by creating a file ``module_<name>.py`` in the root of the module folder.

Say for example that we want to set some generics for a FIFO testbench, located in a module called ``fifo``, which is located under ``modules``.
We would create the file ``modules/fifo/module_fifo.py``, and fill it with something like this.

.. code-block:: python
    :caption: Example ``module_fifo.py`` that sets up local configuration of test cases.

    from tsfpga.module import BaseModule


    class Module(BaseModule):

        def setup_vunit(self, vunit_proj, **kwargs):
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

So what happens here is that we created a class ``Module`` that inherits from :class:`.BaseModule`.
In this class we override the ``setup_vunit()`` method, which does nothing in the parent class, to set up our simulation configurations.
The :func:`.get_modules` call used in our ``simulate.py`` will recognize that this module has a Python file to set up it's own class.
When creating module objects the function will then use the user-specified class for this module.
Later in ``simulate.py`` when ``setup_vunit()`` is run, the code we specified above will be run.

.. note::
    Note that the class must be called exactly ``Module``.

There is also a ``kwargs`` argument available in the ``setup_vunit()`` signature which can be used to send arbitrary parameters from ``simulate.py`` to the module.
This can be used for example to point out the location of test data.
Or maybe select some test mode with a parameter to our ``simulate.py``.
This is pure Python so we can get as fancy as we want to.



.. _vivado_simlib:

Vivado simulation libraries
---------------------------

Compiled Vivado simulation libraries (unisim, xpm, etc.) are often need in the simulation project.
The :class:`.VivadoSimlib` class provides an easy interface for handling simlib.

There are different implementations depending on the simulator currently in use.
The implementation for commercial simulators will compile simlib by calling Vivado with a TCL script containing a ``compile_simlib ...`` call.
For GHDL the implementation contains hard coded ghdl compile calls of the needed files.

All implementations are interface compatible with the :class:`.VivadoSimlibCommon` class.
They will only do a recompile when necessary (new Vivado or simulator version, etc.).

Adding simlib to a simulation project using this class is achieved by simply doing:

.. code-block:: python
    :caption: Adding simlib to the simulation project in ``simulate.py``.

    from tsfpga.vivado.simlib import VivadoSimlib

    ...

    vivado_simlib = VivadoSimlib.init(temp_dir, vunit_proj)
    vivado_simlib.compile_if_needed()
    vivado_simlib.add_to_vunit_project()


Versioning of simlib artifacts
______________________________

Compiling simlib takes quite a while.
It might not be convenient to recompile on each workstation and in each CI run.
Instead storing compiled simlib in, e.g., Artifactory or on a network drive is a good idea.

In ``simulate.py`` we can query :meth:`compile_is_needed <.VivadoSimlibCommon.compile_is_needed>` and :meth:`artifact_name <.VivadoSimlibCommon.artifact_name>` to see if simlib will be compiled and with what version tag.
If compile is needed, i.e. compiled simlib does not exist, they could instead be fetched from a server somewhere.
The :meth:`from_archive <.VivadoSimlibCommon.from_archive>` and :meth:`to_archive <.VivadoSimlibCommon.to_archive>` are useful for this.


.. _vivado_ip_cores:

Simulating with Vivado IP cores
-------------------------------

The :class:`.VivadoIpCores` class handles the IP cores that shall be included in a simulation project.
From the list of modules it will create a Vivado project with all the IP cores.
This project shall then be used to generate the simulation models for the IP cores, which shall then be added to the simulation project.

.. note::
    The :ref:`folder structure <ip_cores_folder>` must be followed for this to work.

Adding IP cores to a simulation project can be done like this:

.. code-block:: python
    :caption: Adding Vivado IP cores to a simulation project in ``simulate.py``.

    from tsfpga.vivado.ip_cores import VivadoIpCores
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


.. _git_simulation_subset:

Simulating a subset based on git history
----------------------------------------

When the number of tests available in a project starts to grow, it becomes interesting to simulate only what has changed.
This saves a lot of time, both in CI as well as when developing on your desktop.

There is a tool in tsfpga called :class:`.GitSimulationSubset` which helps find a minimal subset of testbenches that shall be compiled and run based on the git history.
A testbench shall be compiled and executed if

1. the testbench itself has changed, or if
2. any of the VHDL files the testbench depends on have changed.

Whether or not a file has changed is determined based on git information, by comparing the local branch and working tree with a reference branch.
The reference would be ``origin/master`` most of the time.
The subset of tests returned by the class can then be used as the ``test_pattern`` argument when setting up your VUnit project.

This tools is used in tsfpga CI to make sure that for merge requests only the minimal set of tests is run.
This saves an immense amount of CI time, especially for commits that do not alter any VHDL code.
For nightly master runs the full set of tests shall still be run.

See the :class:`class documentation <.GitSimulationSubset>` for more information,
and `examples/simulate.py <https://gitlab.com/tsfpga/tsfpga/blob/master/examples/simulate.py>`__ in the repo for a usage example.
