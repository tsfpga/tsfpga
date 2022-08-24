.. _integration_hdl_modules:

Integration with hdl_modules
============================

The ``tsfpga`` project can with great benefit be used with its sister project ``hdl_modules`` (
https://hdl-modules.com, https://gitlab.com/tsfpga/hdl_modules).
The hdl_modules project is a collection of reusable, high-quality, peer-reviewed VHDL
building blocks.
Its modules use the suggested tsfpga :ref:`module structure <folder_structure>`, so they can be
loaded straight away in a tsfpga project without effort.

Releases to `PyPI <https://pypi.org/project/tsfpga/>`__ of tsfpga are bundled with the latest
release version of hdl_modules.
There is a convenience method :func:`.get_hdl_modules` for getting a :class:`.ModuleList` of the
modules from hdl_modules.
This module list can then be added to the list of modules when setting up a simulation project,
build projects, etc.


Example usage in tsfpga
-----------------------

The example modules in tsfpga depend on the hdl_modules, hence ``simulate.py`` and ``build.py``
can not be run without adding these modules to the project.

The `tsfpga/examples/simulate.py <https://gitlab.com/tsfpga/tsfpga/blob/main/tsfpga/examples/simulate.py>`__
script showcases an example of a simulation project where hdl_modules are added as modules that
shall be compiled but who's tests shall not be run.

The `tsfpga/examples/build.py <https://gitlab.com/tsfpga/tsfpga/blob/main/tsfpga/examples/build.py>`__
script adds only the tsfpga example modules to the list of modules to gather build projects from.
However `tsfpga/examples/modules/artyz7/module_artyz7.py <https://gitlab.com/tsfpga/tsfpga/blob/main/tsfpga/examples/modules/artyz7/module_artyz7.py>`__
includes hdl_modules in the list of sources that shall be included in the Vivado project.
See also :ref:`example_project_class`.
