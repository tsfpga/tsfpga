.. _registers:

Register code generation
========================

There is a register code generation eco-system available in tsfpga which generates code from textual configuration files.
To start using it simply create a file ``regs_<name>.json`` in the root of a module (see :ref:`module structure <folder_structure>`).

From the JSON definition the register generator can create a VHDL package with all registers and their fields.
This VHDL package can then be used with the generic AXI-Lite register file in tsfpga.
Apart from that a HTML page can be generated for documentation.
There is also support to generate a C header and a C++ class.

The register generator is well-integrated in the tsfpga module work flow.
It is fast enough that before each build and each simulation run, the modules will re-generate their VHDL register package so that it is always up-to-date.
Creating documentation and headers, which are typically distributed as part of FPGA release artifacts, is simple and easy to integrate in a build script.



.. _default_registers:

Default registers
-----------------

A lot of projects use a few default registers in standard locations that shall be present in all modules.
In order to achieve this, without having to duplicate names and descriptions in many places, there is a ``default_registers`` flag to the :ref:`get_modules() <get_modules>` function.
Passing a list of :class:`.Register` objects will insert them in the register list of all modules that use registers.



Register examples
-----------------

Example register code generation from the `ddr_buffer example module <https://gitlab.com/truestream/tsfpga/-/tree/master/examples/modules/ddr_buffer>`__.



JSON file
_________

This is the source JSON file that defines the registers.

.. literalinclude:: ../../generated/registers/json/regs_ddr_buffer.json
   :caption: regs_ddr_buffer.json
   :language: json

In this example module we use a set of default registers that include ``status`` and ``command``.
That is why these registers do not have a ``mode`` set in the JSON, which is otherwise required.
The address registers on the other hand are set to Read/Write.

The register description is also inherited from the register specification.
While a description is not required it used for all registers and bits in this example.



VHDL package
____________

The VHDL package file is designed to be used with the generic AXI-Lite register file `available in tsfpga <https://gitlab.com/truestream/tsfpga/-/tree/master/modules/reg_file>`__.

.. literalinclude:: ../../examples/modules/ddr_buffer/ddr_buffer_regs_pkg.vhd
   :caption: ddr_buffer_regs_pkg.vhd
   :language: vhdl

Note that there is a large eco-system of register related components in tsfpga.
Firstly there are wrappers available for easier working with VUnit verification components.
See the `bfm library <https://gitlab.com/truestream/tsfpga/-/tree/master/modules/bfm/sim>`__ and `reg_operations_pkg <https://gitlab.com/truestream/tsfpga/-/blob/master/modules/reg_file/sim/reg_operations_pkg.vhd>`__.

Furthermore there is a large number of synthesizable AXI components available that enable the register bus: AXI-to-AXI-Lite converter, AXI/AXI-Lite interconnect, AXI-Lite mux (splitter), AXI-Lite clock domain crossing, etc.
See the `axi library <https://gitlab.com/truestream/tsfpga/-/tree/master/modules/axi>`__ for more details.



HTML page
_________

A complete HTML page can be generated with register details as well description of the different modes.
Note that markdown syntax can be used in register and bit descriptions to annotate.
This will be converted to appropriate HTML tags.

Generated HTML file :download:`here <../../generated/registers/doc/ddr_buffer_regs.html>`



HTML table
__________

Optionally only the register description table can be generated to a HTML file.
This can then be included in a separate documentation flow.

Generated HTML file :download:`here <../../generated/registers/doc/tables/ddr_buffer_regs_table.html>`



C++ class
_________

A complete C++ class can be generated with methods that read or write the registers.

There is an abstract interface header available that can be used for mocking in a unit test environment.

.. literalinclude:: ../../generated/registers/cpp/include/i_ddr_buffer.h
   :caption: DdrBuffer interface header
   :language: C++

.. literalinclude:: ../../generated/registers/cpp/include/ddr_buffer.h
   :caption: DdrBuffer class header
   :language: C++

.. literalinclude:: ../../generated/registers/cpp/ddr_buffer.cpp
   :caption: DdrBuffer class implementation
   :language: C++



C header
_________

A C header with register and field definitions can be generated.

.. literalinclude:: ../../generated/registers/c/ddr_buffer_regs.h
   :caption: ddr_buffer header
   :language: C



Python abstraction
------------------

The following classes are used to handle registers in the tsfpga python package.

.. autoclass:: tsfpga.registers.RegisterList()
    :members:

    .. automethod:: __init__


.. autoclass:: tsfpga.registers.Register()
    :members:

    .. automethod:: __init__

.. autoclass:: tsfpga.registers.Bit()
    :members:

    .. automethod:: __init__