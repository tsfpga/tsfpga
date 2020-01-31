.. _folder_structure:

Folder structure
================

Some functions in tsfpga requires that your modules use a certain folder structure.
For example, if you want to set up :ref:`local test configurations <local_configuration>` use
must use a file called ``module_<module_name>.py`` in the root of your module.

Additionaly the :meth:`get_modules() <tsfpga.module.get_modules>` function in tsfpga, which creates
:meth:`module objects <tsfpga.module.BaseModule>` from a source tree, will look for source files only in certain sub-directories.

Below is a recommended folder structure.
The different files and folders are explained further down.

.. code-block:: shell

    modules/
    ├── foo
    │   ├── module_foo.py
    │   ├── project_foo.py
    │   ├── foo_regs.json
    │   ├── ip_cores
    │   │   ├── foo_fifo.tcl
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

So at the top level there is a folder called ``modules`` that contains all your modules.
It does not have to be named that, but it is a name that fits well with the tsfpga nomenclature.
Within this folder there are source code modules: ``foo``, ``bar``, etc.



Sources and testbenches
-----------------------

Source code and packages are recommended to be placed in the ``src`` folder.
There is no distinction made between source files and packages in tsfpga.
The corresponding test benches are recommended to use the ``test`` folder.

You don't have to use these exact folders; :meth:`BaseModule <tsfpga.module.BaseModule>` will look for files in many folder, to accomodate for different projects using different structures.
For example, at the moment :meth:`BaseModule.get_synthesis_files() <tsfpga.module.BaseModule.get_synthesis_files>` will look for source files in

* ``src``
* ``rtl``
* ``hdl/rtl``
* ``hdl/package``

.. note::
    If your project uses a different folder structure, and is locked into using that, tsfpga can be updated to accomodate that as well.
    This goes for most of the folders within the module, described below.
    Feel free to create and `issue <https://gitlab.com/truestream/tsfpga/issues>`__ or a merge request.



module_foo.py
-------------

If you want to do :ref:`local test configurations <local_configuration>`, or overload any other
thing in the :meth:`BaseModule <tsfpga.module.BaseModule>` class, you can use a file called ``module_<module_name>.py``.
The Python file shall contain a class definition called ``Module``.
If you do this it is recommended to inherit the class from :meth:`BaseModule <tsfpga.module.BaseModule>` and override any method you want to change the behavior of.



project_foo.py
--------------

Modules that define FPGA build projects shall have a Python file name ``project_<module_name>.py`` in their root.
The file must contain a function ``get_projects()`` that returns a list of :meth:`FPGA build projects <tsfpga.vivado_project.VivadoProject>`.

An FPGA project like this might need a lot extra files, such as TCL scripts for pinning, block design, etc.
These can be placed in a new folder of your liking within the module.
For example for your TCL scripts you might place them in a sub-directory called ``tcl`` in the module root.
This folder will not have any significance for tsfpga.
For things like TCL sources it is up to the user to point to them when creating the :meth:`FPGA project <tsfpga.vivado_project.VivadoProject>`.



foo_regs.json
-------------

Register definitions used in the tsfpga :ref:`register generator <registers>` are taken from a file called ``<module_name>_regs.json``.
It contains the registers that the module uses and the fields within those registers.
See :ref:`here <registers>` for more information.



IP cores
--------

In tsfpga, IP cores are handled using TCL files that contain the code snippets that generate the core.
These TCL files shall be place in the ``ip_cores`` folder within your module.
The IP cores will be included in all build projects that include the module, and in the simulation project.



Scoped constraints
------------------

Scoped constraints are constraint files that are applied in Vivado relative to a certain entity.
This is handled in :meth:`build projects <tsfpga.vivado_project.VivadoProject>` using the :meth:`Constraint <tsfpga.constraint.Constraint>` class.
The constraint files shall be placed in the ``scoped_constraints`` directory within your module.

The name of scoped constraint file must be the same as the entity name and source file name.
In the example tree above there is a scoped constraint file ``sample_data.tcl`` that will be applied to ``sample_data.vhd``, which presumably contains an entity called ``sample_data``.



