.. _build:

FPGA build flow
===============

Tsfpga enables a build flow where many builds can be executed in parallel from the same script call.
Any module can :ref:`set up build projects <example_project_class>` using its ``module_*.py``.
All project configuration is located in the module, not in any central script.

The build project is represented using a :class:`Python class <.VivadoProject>` that abstracts all
settings and operations.



.. _example_build_py:

Minimal build_fpga.py example
-----------------------------

Given that we follow the :ref:`folder structure <folder_structure>`, and have and least one module
that :ref:`sets up  build projects <example_project_class>`, we can utilize a ``build_fpga.py``
like this:

.. code-block:: python
    :caption: Minimal ``build_fpga.py`` file.

    from pathlib import Path
    from tsfpga.build_project_list import BuildProjectList
    from tsfpga.module import get_modules

    modules = get_modules(modules_folder=Path("path/to/my/modules"))

    build_path = Path("generated/my_build_projects")

    projects = BuildProjectList(modules=modules, project_filters="*")
    projects.create_unless_exists(project_paths=build_path, num_parallel_builds=4)
    projects.build(project_path=build_path, num_parallel_builds=4, num_threads_per_build=6)

Of course this is incredibly simplified and hard coded, but it does show the interface to the
tsfpga classes.
The :class:`.BuildProjectList` class will work on a list of
:class:`build project objects <.VivadoProject>` as supplied by the modules.

An example output from this script is shown below.
It shows the build projects being launched in parallel, and then finishing at roughly the same time.

.. code-block::

    [/home/lukas/work/repo/tsfpga]$ python tsfpga/examples/build_fpga.py
    Starting artyz7
    Output file: /home/lukas/work/repo/tsfpga/generated/projects/artyz7/output.txt
    Starting artyz7_dummy
    Output file: /home/lukas/work/repo/tsfpga/generated/projects/artyz7_dummy/output.txt
    pass (pass=1 fail=0 total=2) artyz7_dummy (229.5 seconds)

    pass (pass=2 fail=0 total=2) artyz7 (229.8 seconds)

    ==== Summary ========================

    Size of artyz7_dummy after implementation:
    {
      "Total LUTs": 804,
      "Logic LUTs": 746,
      "LUTRAMs": 58,
      "SRLs": 0,
      "FFs": 1596,
      "RAMB36": 0,
      "RAMB18": 1,
      "DSP Blocks": 0
    }
    pass artyz7_dummy   (229.5 seconds)


    Size of artyz7 after implementation:
    {
      "Total LUTs": 804,
      "Logic LUTs": 746,
      "LUTRAMs": 58,
      "SRLs": 0,
      "FFs": 1596,
      "RAMB36": 0,
      "RAMB18": 1,
      "DSP Blocks": 0
    }
    pass artyz7         (229.8 seconds)

    =====================================
    pass 2 of 2
    =====================================
    Total time was 459.3 seconds
    Elapsed time was 229.8 seconds
    =====================================
    All passed!



Note that before a project is built a :ref:`register generation <integration_hdl_registers>` is run,
so that the project is built using up-to-date register definitions.

Of course a more realistic ``build_fpga.py`` would be a little more verbose.
It would probably feature command line arguments that control the behavior, output paths, etc.
And example of this, which also features release artifact packaging, is available in the
`repo <https://github.com/tsfpga/tsfpga/blob/main/tsfpga/examples/build_fpga.py>`__.



.. _example_project_class:

Example project class creation
------------------------------

This is an example of project creation, using the ``artyz7`` example project from the
`repo <https://github.com/tsfpga/tsfpga/tree/main/tsfpga/examples>`__.

Projects are created by modules using the file ``module_<module_name>.py``, see
:ref:`folder structure <folder_structure_project>` for details.
In tsfpga a top-level module that defines build projects is handled just like any other module.
It can use register generation, set up simulations, etc.
The only difference is that it overrides the :meth:`.BaseModule.get_build_projects` method to return
a list of :class:`build project objects <.VivadoProject>`.

.. literalinclude:: ../../tsfpga/examples/modules/artyz7/module_artyz7.py
   :caption: Example project creation
   :language: python
   :lines: 9-78
   :linenos:

There is a lot going on here, so lets go through what happens in ``get_build_projects()``.


Line 17: Get modules
____________________

Firstly we need to get a list of modules that shall be included in the build project.
Source files, IP cores, scoped constraints, etc., from all these modules will be added to
the project.

It can be a good idea to filter what modules are included here.
If we have a huge module tree but our project only uses a subset of the modules, we might not want
to slow down Vivado by adding everything.
We might also use primitives and IP cores in some modules that are not available for the
target part.
This filtering of modules can be achieved using the arguments to :func:`.get_modules`.

In this case we use two wrappers, :func:`.get_hdl_modules` and :func:`.get_tsfpga_example_modules`,
around the :func:`.get_modules` function.
They set the correct flags (modules paths, :ref:`default registers <default_registers>`
and ``library_name_has_lib_suffix``).
It is recommended to use functions like these so the arguments don't have to be repeated in
many places.



Line 20-22: TCL files
_____________________

This module has a sub-folder ``tcl`` which contains pinning and a block design.
The block design, which is added to the :class:`.VivadoProject` as a TCL source is simply
represented using it's path.
The pinning on the other hand, which is used as a constraint in Vivado, must be represented using
the :class:`.Constraint` class.


Line 24-68: Creating project objects
____________________________________

The sources gathered are then use to create project objects that are appended to the ``projects``
list, which is returned at the end of the method.

First a :class:`.VivadoProject` object is created with the name ``artyz7``.
The modules, part name, TCL sources and constraints are passed to the constructor.
There is also a ``defined_at`` argument, which is given the path to the ``module_artyz7.py`` file.
This is used to get a useful ``--list`` result in our :ref:`build_fpga.py <example_build_py>`.

The first project does not have the ``top`` argument set, which means it will be inferred from
the provided ``name``.
After the first project, a few other projects are set up with different top levels and
different settings.
This is where we could also set different ``generics`` for the projects via the
:meth:`.VivadoProject.__init__` constructor.

Note that all of these projects use a project subclass that inherits :class:`.VivadoProject`.
In this case, the project subclass only adds a few more TCL sources with some further
message severity settings.
But using the project subclass concept we could do some more advanced things, for example
setting up build hooks, as decsribed below.


.. _pre_post_build:

Pre- and post- build function hooks
-----------------------------------

The :class:`.VivadoProject` functions :meth:`pre_build() <.VivadoProject.pre_build>` and
:meth:`post_build() <.VivadoProject.post_build>` can be convenient in certain use cases.
They will receive all the arguments that are passed to :meth:`.VivadoProject.build`, such as project
path, output path, etc.
Additional named arguments sent to :meth:`.VivadoProject.build` will also be available in
:meth:`pre_build() <.VivadoProject.pre_build>` and :meth:`post_build() <.VivadoProject.post_build>`.



Build result with utilization numbers
-------------------------------------

The :meth:`.VivadoProject.build` method will return a :class:`.build_result.BuildResult` object
upon completion.
It can be inspected to see if the run passed or failed, and what the resource utilization of the
build is.



Example generated TCL
---------------------

The TCL files below are generated by the :class:`.VivadoProject` class when calling the
:meth:`.VivadoProject.create` and :meth:`.VivadoProject.build` methods as part of a build flow.


Create Vivado project
_____________________

.. collapse:: Click to expand/collapse code.

  .. literalinclude:: ../../generated/sphinx_rst/projects/artyz7/create_vivado_project.tcl
     :caption: Example generated TCL that creates a Vivado project.
     :language: tcl
     :linenos:

|


Build Vivado project
_____________________

.. collapse:: Click to expand/collapse code.

  .. literalinclude:: ../../generated/sphinx_rst/projects/artyz7/build_vivado_project.tcl
     :caption: Example generated TCL that builds a Vivado project.
     :language: tcl
     :linenos:

|
