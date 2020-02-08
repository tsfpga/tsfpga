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

.. autoclass:: tsfpga.vivado_project.VivadoProject()
    :members:

    .. automethod:: __init__



.. _example_project_class:

Example project class creation
------------------------------

This is an example of project creation, using the ``artyz7`` example project from the `repo <https://gitlab.com/truestream/tsfpga/-/tree/master/examples>`__.

Projects are created by the modules in a file called ``project_<module_name>.py`` within the module root.
It must contain a function called ``get_projects()`` that returns a list of build project objects.

.. literalinclude:: ../../examples/modules/artyz7/project_artyz7.py
   :caption: Example project file `project_artyz7.py`
   :language: python
   :lines: 5-

So there is a lot going on here.
Lets go through what happens in the ``get_projects()`` function step by step.



Get modules
___________

Firstly we need to get a list of modules that shall be included in the build projects.

In this case we use a wrapper ``get_tsfpga_modules()`` around the :ref:`get_modules() <get_modules>` function.
The wrapper sets the correct :ref:`get_modules() <get_modules>` flags (:ref:`default registers <default_registers>` and `library_name_has_lib_suffix`).
It is recommended that you also create a function like this so the arguments don't have to be repeated in many places.

It can also be a good idea to filter what modules are included here.
If you have a huge module tree but your project only uses a subset of the modules, you might not want to slow down Vivado by adding everything.
You might also use primitives and IP cores in some modules that are not available for the target part.
This filtering of modules can be achieved using the arguments to :ref:`get_modules() <get_modules>`.



TCL files
_________
This module has a sub-folder ``tcl`` which contains pinning and a block design.
The block design, which is added to the :class:`.VivadoProject` is a TCL source is simply represented using it's path.
The pinning on the other hand, which is used as a constraint in Vivado, must be represented using the :class:`.Constraint` class.


Creating project objects
________________________

The sources gathered are then use to create project objects which are appended to the ``projects`` list which is returned at the end.

First a :class:`.VivadoProject` object is created with the name ``artyz7``.
The modules, part name, TCL sources and constraints are passed to the constructor.
There is also a ``defined_at`` argument, which is given the path to the ``project_artyz7.py`` file.
This is used to get a useful ``--list`` result in your :ref:`build.py <example_build_py>`.

The second project is created using a child class that inherits :class:`.VivadoProject`.
It showcases how to use :ref:`pre and post build hook functions <pre_post_build>`.



.. _example_build_py:

Example build.py
----------------

.. literalinclude:: ../../examples/build.py
   :caption: Example project file
   :language: python
   :lines: 5-



.. _pre_post_build:

Pre- and post- build function hook
----------------------------------



Constraint files
-----------------------

.. autoclass:: tsfpga.constraint.Constraint()
    :members:

    .. automethod:: __init__




Build step TCL hooks
--------------------

.. autoclass:: tsfpga.build_step_tcl_hook.BuildStepTclHook()
    :members:

    .. automethod:: __init__



.. _project_list:

FPGA project list class
-----------------------

.. autoclass:: tsfpga.fpga_project_list.FPGAProjectList()
    :members:

    .. automethod:: __init__
