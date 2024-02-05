.. _integration_hdl_registers:

Integration with hdl-registers
==============================

The tsfpga module and source code handling is tightly integrated with its sister project
``hdl-registers`` (https://hdl-registers.com, https://github.com/hdl-registers/hdl-registers),
a register code generator.
To use it simply create a file ``regs_<name>.toml`` in the root of a module
(see :ref:`module structure <folder_structure>`).
It is fast enough that before each build and each simulation run, the modules will re-generate their
VHDL register artifacts making them always up-to-date.
Creating documentation and headers, which are typically distributed as part of FPGA release
artifacts, is simple and easy to integrate in a build script.

Releases to `PyPI <https://pypi.org/project/tsfpga/>`__ of tsfpga list
`hdl-registers <https://pypi.org/project/hdl-registers/>`__ as a dependency, so it will be
installed as well.


Example usage in tsfpga
-----------------------

The `tsfpga/examples/modules/ddr_buffer
<https://github.com/tsfpga/tsfpga/tree/main/tsfpga/examples/modules/ddr_buffer>`__
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



.. _register_artifacts_to_generate:

Choosing what artifacts to generate
-----------------------------------

Per default, the module will generate all register VHDL artifacts.
Which includes register packages, AXI-Lite register file wrapper, and simulation support packages.
The easiest way to disable either of these is to set up a :ref:`folder_structure_project` in the
root of your module and disable either of the class variables below.
They all have default value ``True`` in :class:`.BaseModule`.

* ``create_register_package``, controls whether
  :class:`VhdlRegisterPackageGenerator <hdl_registers.generator.vhdl.register_package.VhdlRegisterPackageGenerator>`
  is generated into the register source folder of the module.
* ``create_record_package``, controls whether
  :class:`VhdlRecordPackageGenerator <hdl_registers.generator.vhdl.record_package.VhdlRecordPackageGenerator>`
  is generated into the register source folder of the module.
* ``create_axi_lite_wrapper``, controls whether
  :class:`VhdlAxiLiteWrapperGenerator <hdl_registers.generator.vhdl.axi_lite.wrapper.VhdlAxiLiteWrapperGenerator>`
  is generated into the register source folder of the module.
* ``create_simulation_read_write_package``, controls whether
  :class:`VhdlSimulationReadWritePackageGenerator <hdl_registers.generator.vhdl.simulation.read_write_package.VhdlSimulationReadWritePackageGenerator>`
  is generated into the register simulation folder of the module.
* ``create_simulation_check_package``, controls whether
  :class:`VhdlSimulationCheckPackageGenerator <hdl_registers.generator.vhdl.simulation.check_package.VhdlSimulationCheckPackageGenerator>`
  is generated into the register simulation folder of the module.
* ``create_simulation_wait_until_package``, controls whether
  :class:`VhdlSimulationWaitUntilPackageGenerator <hdl_registers.generator.vhdl.simulation.wait_until_package.VhdlSimulationWaitUntilPackageGenerator>`
  is generated into the register simulation folder of the module.
