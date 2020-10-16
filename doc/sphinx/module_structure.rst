.. _folder_structure:

Module structure
================

Source code management in tsfpga is centered around modules.
This page describes how modules must be structured in the file system.
It also shows how modules and files are abstracted in python classes and methods.


Folder structure
________________

Some functions in tsfpga require that modules use a certain folder structure.
For example, if we want to set up :ref:`local test configurations <local_configuration>` we
must use a file called exactly ``module_<name>.py`` in the root of the module.

Additionally the :meth:`get_modules() <tsfpga.module.get_modules>` function in tsfpga, which creates
:class:`module objects <tsfpga.module.BaseModule>` from a source tree, will look for source files only in certain sub-directories.

Below is a recommended folder structure.
The different files and folders are explained further down.

.. code-block:: none

    modules/
    ├── foo
    │   ├── module_foo.py
    │   ├── regs_foo.toml
    │   ├── ip_cores
    │   │   ├── fifo.tcl
    │   │   └── ...
    │   ├── scoped_constraints
    │   │   ├── sample_data.tcl
    │   │   └── ...
    │   ├── src
    │   │   ├── foo_top.vhd
    │   │   ├── foo_pkg.vhd
    │   │   ├── sample_data.vhd
    │   │   └── ...
    │   └── test
    │       ├── tb_foo_top.vhd
    │       └── ...
    │
    ├── bar
    │   └── ...
    │
    └── ...

At the top level there is a folder called ``modules`` that contains all available modules.
It does not have to be named that, but it is a name that fits well with the tsfpga nomenclature.
Within this folder there are source code modules: ``foo``, ``bar``, etc.



Sources and testbenches
-----------------------

Source code and packages are recommended to be placed in the ``src`` folder.
There is no distinction made between entity source files and packages in tsfpga.
The corresponding test benches are recommended to use the ``test`` folder.

We don't have to use these exact folders; :class:`BaseModule <tsfpga.module.BaseModule>` will look for files in many folders, to accommodate for different projects using different structures.
For example, at the moment :meth:`BaseModule.get_synthesis_files() <tsfpga.module.BaseModule.get_synthesis_files>` will look for source files in

* ``src``
* ``rtl``
* ``hdl/rtl``
* ``hdl/package``

.. note::
    If your project uses a different folder structure, and is locked into using it, tsfpga can be updated to accommodate that as well.
    This goes for most of the folders within the module, described below.
    Feel free to create and `issue <https://gitlab.com/tsfpga/tsfpga/issues>`__ or a merge request.



.. _folder_structure_project:

module_foo.py
-------------

If we want to, e.g., set up :ref:`FPGA build projects <example_project_class>` or do :ref:`local test configurations <local_configuration>` we can use a file called ``module_<name>.py``.
The Python file shall contain a class definition called ``Module`` that inherits from :class:`.BaseModule`.
Methods from :class:`.BaseModule` can then be overridden to achieve the desired behavior.


Extra files
+++++++++++

An FPGA build project might need a lot extra files, such as TCL scripts for pinning, block design, etc.
Or maybe some simulations need data files stored on disk.
It is perfectly valid to create other folders within the module, e.g. `tcl` or `test/data`, and place files there.
Extra folders like these can be used freely and will not have any significance to tsfpga.



regs_foo.toml
-------------

Register definitions used in the tsfpga :ref:`register generator <registers>` are taken from a file called ``regs_<module_name>.toml``.
It contains the registers that the module uses and the fields within those registers.



.. _ip_cores_folder:

IP cores
--------

In tsfpga, IP cores are handled using TCL files that contain the code snippet that generates the core.
This TCL snippet can be found in the Vivado TCL console when creating or modifying the IP.
It typically looks something like this:

.. literalinclude:: ../../examples/modules_with_ip/module_with_ip_cores/ip_cores/mult_u12_u5.tcl
   :caption: Example TCL that creates an IP core
   :language: none
   :lines: 5-

These TCL files shall be place in the ``ip_cores`` folder within the module.
The IP cores will be included in all build projects that include the module, and in the simulation project.



Scoped constraints
------------------

Scoped constraints are constraint files that are applied in Vivado relative to a certain entity.
This is handled in :meth:`build projects <tsfpga.vivado.project.VivadoProject>` using the :meth:`Constraint <tsfpga.constraint.Constraint>` class.
Constraint files in the ``scoped_constraints`` directory will be automatically added to :ref:`build projects <build>` as scoped constraints.

The name of a scoped constraint file must be the same as the entity name and source file name.
In the example tree above there is a scoped constraint file ``sample_data.tcl`` that will be applied to ``sample_data.vhd``, which presumably contains an entity called ``sample_data``.
