.. _build:

FPGA build flow
===============

In tsfpga the build projects are set up by the modules.
Any module can :ref:`set up  a build project <example_project_class>` as long as they follow the :ref:`folder structure <folder_structure_project>`.
The build project is represented using a :class:`Python class <.VivadoProject>` that abstracts all settings and operations.



.. _example_build_py:

Minimal build.py example
------------------------

Given that we follow the :ref:`folder structure <folder_structure>`, and have and least one module that :ref:`sets up  build projects <example_project_class>`, we can utilize a ``build.py`` like this:

.. code-block:: python
    :caption: Minimal ``build.py`` file.

    from pathlib import Path
    from tsfpga.build_project_list import BuildProjectList
    from tsfpga.module import get_modules

    my_modules_folders = [
        Path("path/to/my/modules"),
    ]
    modules = get_modules(my_modules_folders)
    build_path = Path("my_generated_build_projects")
    projects = BuildProjectList(modules, "artyz7*")
    projects.create_unless_exists(project_paths=build_path, num_parallel_builds=4)
    projects.build(project_path=build_path, num_parallel_builds=4, num_threads_per_build=6)

Of course this is incredibly simplified and hard-coded, but it does show the interface to the tsfpga classes.
The :class:`.BuildProjectList` class will work on a list of :class:`build project objects <.VivadoProject>` as supplied by the modules.

An example output from this script is shown below.
It shows to build projects being launched in parallel, and then finishing and roughly the same time.

.. code-block::

    [/home/lukas/work/repo/tsfpga]$ python examples/build.py
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



Note that before a project is built a :ref:`register generation <registers>` is run, so that the project is built using up-to-date register definitions.

Of course a more realistic ``build.py`` would be a little more verbose.
It would probably feature command line arguments that control the behavior, output paths, etc.
And example of this, which also features release artifact packaging, is available in the `repo <https://gitlab.com/tsfpga/tsfpga/-/blob/master/examples/build.py>`__.



.. _example_project_class:

Example project class creation
------------------------------

This is an example of project creation, using the ``artyz7`` example project from the `repo <https://gitlab.com/tsfpga/tsfpga/-/tree/master/examples>`__.

Projects are created by modules using the file ``module_<module_name>.py``, see :ref:`folder structure <folder_structure_project>` for details.
In tsfpga a top-level module that defines build projects is handled just like any other module.
It can use register generation, set up simulations, etc.
The only difference is that it overrides the :meth:`.BaseModule.get_build_projects` method to return a list of :class:`build project objects <.VivadoProject>`.

.. literalinclude:: ../../examples/modules/artyz7/module_artyz7.py
   :caption: Example project creation
   :language: python
   :lines: 9-

There is a lot going on here, so lets go through what happens in ``get_build_projects()``.


Get modules
___________

Firstly we need to get a list of modules that shall be included in the build project.
Source files, IP cores, scoped constraints, etc., from all these modules will be added to the project.

It can be a good idea to filter what modules are included here.
If we have a huge module tree but our project only uses a subset of the modules, we might not want to slow down Vivado by adding everything.
We might also use primitives and IP cores in some modules that are not available for the target part.
This filtering of modules can be achieved using the arguments to :func:`.get_modules`.

In this case we use a wrapper ``get_tsfpga_modules()`` around the :func:`.get_modules` function.
The wrapper sets the correct flags (all modules paths, :ref:`default registers <default_registers>` and ``library_name_has_lib_suffix``).
It is recommended to use a function like this so the arguments don't have to be repeated in many places.



TCL files
_________
This module has a sub-folder ``tcl`` which contains pinning and a block design.
The block design, which is added to the :class:`.VivadoProject` as a TCL source is simply represented using it's path.
The pinning on the other hand, which is used as a constraint in Vivado, must be represented using the :class:`.Constraint` class.


Creating project objects
________________________

The sources gathered are then use to create project objects which are appended to the ``projects`` list which is returned at the end.

First a :class:`.VivadoProject` object is created with the name ``artyz7``.
The modules, part name, TCL sources and constraints are passed to the constructor.
There is also a ``defined_at`` argument, which is given the path to the ``module_artyz7.py`` file.
This is used to get a useful ``--list`` result in our :ref:`build.py <example_build_py>`.

The second project is created using a child class that inherits :class:`.VivadoProject`.
It showcases how to use :ref:`pre and post build hook functions <pre_post_build>`.
The ``post_build()`` function does nothing in this example, but the mechanism can be very useful in real-world cases.

The second project also showcases how to set some generic values.
For the second project we additionally have to specify the ``top`` name.
In the first one it is inferred from the project name to be ``artyz7_top``, whereas in the second one we have to specify it explicitly.



.. _pre_post_build:

Pre- and post- build function hooks
-----------------------------------

The :class:`.VivadoProject` functions :meth:`pre_build() <.VivadoProject.pre_build>` and :meth:`post_build() <.VivadoProject.post_build>` can be convenient in certain use cases.
They will receive all the arguments that are passed to :meth:`.VivadoProject.build`, such as project path and output path.
Additional named arguments sent to :meth:`.VivadoProject.build` will also be available in :meth:`pre_build() <.VivadoProject.pre_build>` and :meth:`post_build() <.VivadoProject.post_build>`.
So in our :ref:`example build.py <example_build_py>` above we could have passed further arguments on the line that says ``project.build(...)``.



Build result with utilization numbers
-------------------------------------

The :meth:`.VivadoProject.build` method will return a :class:`.build_result.BuildResult` object upon completion.
It can be inspected to see if the run passed or failed, and what the resource utilization of the build is.
