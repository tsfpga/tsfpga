.. _formal:

Formal verification flow
========================

The tsfpga tools for formal verification allow you to run formal test cases without creating a SymbiYosys ``.sby`` file by hand.
It also adds powerful features such as parallel runs, test filtering, XML reports, etc.
The goal is to have an automated and scalable ecosystem where no configuration files are hand made, and all compile orders and dependencies are resolved automatically.
It should also be module-centric so that the formal checks are defined locally in the modules, not in a central script.

tsfpga acts on top of several tools to run formal verification:

* VUnit is used to handle compilation of the source files in correct order.
* SymbiYosys runs the formal verification.
* GHDL is used by VUnit to compile, and by SymbiYosys to synthesise the source code.

The role of tsfpga is to keep track of the project sources and checkers.
It will generate a SymbiYosys ``.sby`` file for each formal project, with the correct settings and an updated source file list.

Formal checks are defined similarly to local simulation configurations, as described in :ref:`simulation`.
For formal checks, the :meth:`setup_formal() <tsfpga.module.BaseModule.setup_formal>` method shall be overloaded in your ``module_*.py`` whenever you want to add a formal check.
The checks are run using VUnit's test runner, so the command line interface is similar to that of the simulation flow.
It supports multiple formal checks in parallel, test filtering, verbosity level, XML reports, etc.


Minimal example
---------------

If the source code is roughly organized along the :ref:`folder structure <folder_structure>`,
running formal verification through tsfpga can be done with this script:

.. code-block:: python
    :caption: Minimal ``formal.py`` file.

    from pathlib import Path
    from tsfpga.module import get_modules
    from tsfpga.formal_project import FormalProject

    my_modules_folders = [
        Path("path/to/my/modules")
    ]

    formal_project = FormalProject(
        modules=get_modules(my_modules_folders),
        project_path=Path("formal_project_path"))

    for module in get_modules(my_modules_folders):
        module.setup_formal(formal_project)

    formal_project.run()

A realistic example, used for tsfpga's own checks, is available at `examples/formal.py <https://gitlab.com/tsfpga/tsfpga/blob/master/examples/formal.py>`__ in the repo.

Formal checks need to be explicitly defined by implementing :meth:`setup_formal() <tsfpga.module.BaseModule.setup_formal>` within each module:

.. code-block:: python
    :caption: Implementation of :meth:`setup_formal() <tsfpga.module.BaseModule.setup_formal>`.

    from tsfpga.module import BaseModule


    class Module(BaseModule):

        def setup_formal(self, formal_proj, **kwargs):
            formal_proj.add_config(
                top="example_top",
                generics=dict(some_generic=True),
                engine_command="smtbmc",
                solver_command="z3",
                depth=20,
                mode="prove")

.. note::
    The top entity name must match its file name, so that ``example_top`` in this example is defined in a file named ``example_top.vhd``.

.. note::
    Settings for ``engine_command``, ``solver_command``, ``depth`` and ``mode`` options are described in the
    `SymbiYosys documentation <https://symbiyosys.readthedocs.io>`__.



Generated .sby file
-------------------

Below is an example generated ``.sby`` file, that is take from a formal check in the tsfpga repo.

.. literalinclude:: files/formal_sby_example.sby
    :caption: Generated SymbiYosys .sby file.

It contains the settings (``mode``, ``depth``, etc.) that were set in the ``module_*.py``.
The module list given to the :class:`.FormalProject` has been read to find a list of sources, that are then compiled with VUnit and GHDL.
This forms the list of compiled libraries that is seen in the GHDL call under ``[script]``.
The file list ``[files]`` is also based on this list of modules.
