.. _integration_hdl_registers:

Integration with hdl_registers
==============================

The tsfpga module and source code handling is tightly integrated with its sister project
``hdl_registers`` (https://hdl-registers.com, https://gitlab.com/hdl_registers/hdl_registers),
a register code generator.
To use it simply create a file ``regs_<name>.toml`` in the root of a module
(see :ref:`module structure <folder_structure>`).
It is fast enough that before each build and each simulation run the modules will re-generate their
VHDL register package making it always up-to-date.
Creating documentation and headers, which are typically distributed as part of FPGA release
artifacts, is simple and easy to integrate in a build script.

Releases to `PyPI <https://pypi.org/project/tsfpga/>`__ of tsfpga list
`hdl_registers <https://pypi.org/project/hdl-registers/>`__ as a dependency, so it will be
installed as well.


Example usage in tsfpga
-----------------------

The `tsfpga/examples/modules/ddr_buffer
<https://gitlab.com/tsfpga/tsfpga/-/tree/main/tsfpga/examples/modules/ddr_buffer>`__
example module is heavily reliant on generated register information, both in the implementation
and testbench.


.. _default_registers:

Default registers
-----------------

A lot of projects use a few default registers in standard locations that shall be present in
all modules.
For example, very commonly the first register of a module is an interrupt status register and the
second one is an interrupt mask.
In order to achieve this, without having to duplicate names and descriptions in many places, there
is a ``default_registers`` flag to the :func:`.get_modules` function.
Passing a list of :class:`hdl_registers.register.Register` objects will insert them in the register
list of all modules that use registers.



Manipulating registers from Python
----------------------------------

The ``ddr_buffer`` example module also showcases how to manipulate registers from Python via
tsfpga's module system.
This method for manipulating registers can be very useful for information that is known in the
Python realm, but is not convenient to add to the TOML file.

.. literalinclude:: ../../tsfpga/examples/modules/ddr_buffer/module_ddr_buffer.py
   :caption: module_ddr_buffer.py
   :language: python
   :lines: 9-

Using :meth:`.BaseModule.registers_hook` we add a constant as well as a read-only register for the
module's version number.
The idea behind this example is that a software that uses this module will read the ``version``
register and compare to the static constant that shows up in the header.
This will make sure that the software is running against the correct FPGA with expected
module version.
