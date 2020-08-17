.. _build:

Build flow
==========

This page shows how to use FPGA build projects with tsfpga.

In tsfpga the build projects are set up by the modules.
Any module can set up a build project as long as they follow the :ref:`folder structure <folder_structure_project>`.
The build project is represented using a :class:`Python class <.VivadoProject>` that abstracts all settings and operations.

An example of how a module sets up build projects is found :ref:`here <example_project_class>`.

The projects are available in a :ref:`project list <project_list>` and are built using a user-created :ref:`build.py <example_build_py>`.



Vivado project class
--------------------

Build projects targetting Xilinx Vivado are represented using this class.
Continue reading this page for explanations on how to use it and the different parameters.

.. autoclass:: tsfpga.vivado.project.VivadoProject()
    :members:

    .. automethod:: __init__



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
   :lines: 5-

There is a lot going on here, so lets go through what happens in ``get_build_projects()``.


Get modules
___________

Firstly we need to get a list of modules that shall be included in the build project.
Source files, IP cores, scoped constraints, etc., from all these modules will be added to the project.

It can be a good idea to filter what modules are included here.
If we have a huge module tree but our project only uses a subset of the modules, we might not want to slow down Vivado by adding everything.
We might also use primitives and IP cores in some modules that are not available for the target part.
This filtering of modules can be achieved using the arguments to :ref:`get_modules() <get_modules>`.

In this case we use a wrapper ``get_tsfpga_modules()`` around the :ref:`get_modules() <get_modules>` function.
The wrapper sets the correct :ref:`get_modules() <get_modules>` flags (all modules paths, :ref:`default registers <default_registers>` and ``library_name_has_lib_suffix``).
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


.. _example_build_py:

Example build.py
----------------

A ``build.py`` in a simplified and hard-coded fashion could look something like this:

.. code-block:: python
    :caption: Minimal ``build.py`` file.

    from pathlib import Path
    from tsfpga.build_project_list import BuildProjectList
    from tsfpga.module import get_modules

    my_modules_folders = [
        Path("path/to/my/modules"),
    ]
    modules = get_modules(my_modules_folders)
    build_path = Path("build_projects")
    for project in BuildProjectList(modules).get_projects("artyz7*"):
        project.create(project_path=build_path / project.name)
        project.build(project_path=build_path / project.name, output_path=build_path / project.name / "artifacts")

Of course this is incredibly simplified, but it does show the interface to the tsfpga classes.
The :class:`.BuildProjectList` function :meth:`.BuildProjectList.get_projects` will return a list of :class:`build project objects <.VivadoProject>` that match the given pattern.
With this objects the ``create()`` and ``build()`` functions are available.

Note that before a project is built a :ref:`register generation <registers>` is run, so that the project is built using up-to-date register definitions.

Of course a more realistic ``build.py`` would be a little more verbose.
It would probably feature command line arguments that control the behavior, output paths, etc.
And example of this, which also features release artifact packaging, is available in the `repo <https://gitlab.com/tsfpga/tsfpga/-/blob/master/examples/build.py>`__.



.. _pre_post_build:

Pre- and post- build function hooks
-----------------------------------

The :class:`.VivadoProject` functions :meth:`pre_build() <.VivadoProject.pre_build>` and :meth:`post_build() <.VivadoProject.post_build>` can be convenient in certain use cases.
They will receive all the arguments that are passed to :meth:`.VivadoProject.build`, such as project path and output path.
Additional named arguments sent to :meth:`.VivadoProject.build` will also be available in :meth:`pre_build() <.VivadoProject.pre_build>` and :meth:`post_build() <.VivadoProject.post_build>`.
So in our :ref:`example build.py <example_build_py>` above we could have passed further arguments on the line that says ``project.build(...)``.



Constraint files
-----------------------

.. autoclass:: tsfpga.constraint.Constraint()
    :members:

    .. automethod:: __init__



Build step TCL hooks
--------------------

TCL scripts can be added as hooks to certain build steps in Vivado.
Scripts like these are passed to the :class:`.VivadoProject` using this class.
It is possible to add more than one hook per step.

.. autoclass:: tsfpga.build_step_tcl_hook.BuildStepTclHook()
    :members:

    .. automethod:: __init__



Netlist build projects
----------------------

tsfpga defines a class for builds that are not meant to result in a binary.
These builds are typically used to quickly get information about timing or resource utilization for a module.
In your ``build.py`` it is possible to parameterize many builds via generics and synthesize them in parallel.
The results can then be aggregated to form a report about e.g. resource utilization for your module.

The only real difference from the base class :class:`.VivadoProject` is that
IO buffers are not included and no pinning is needed. By separating these builds into separate classes,
top level FPGA builds and netlist builds can be listed and built separately.

.. autoclass:: tsfpga.vivado.project.VivadoNetlistProject()
    :members:

    .. automethod:: __init__



Build result
------------

.. autoclass:: tsfpga.vivado.project.BuildResult()
    :members:

    .. automethod:: __init__



.. _project_list:

FPGA build project list
-----------------------

.. autoclass:: tsfpga.build_project_list.BuildProjectList()
    :members:

    .. automethod:: __init__

