
Modules
=======

Source code management in tsfpga is centered around modules.
They are abstracted using the classes and methods in this file.

Read about :ref:`simulation flow <simulation>` or :ref:`build flow <build>` for how to use them.



.. _get_modules:

The get_modules() method
------------------------

A call to :ref:`get_modules() <get_modules>` creates :ref:`module objects <module_objects>` from the directory structure of the folders listed in the argument.
The library name is deduced from the name of each module folder.
Source files, packages and testbenches are collected from a few standard locations within the module folder.

.. autofunction:: tsfpga.module.get_modules



.. _module_objects:

Module objects
--------------

.. autoclass:: tsfpga.module.BaseModule()
    :members:

    .. automethod:: __init__



.. _hdl_file:

HdlFile objects
---------------

.. autoclass:: tsfpga.hdl_file.HdlFile()
    :members:

    .. automethod:: __init__


