.. _registers:

Register code generation
========================

There is a register code generation eco-system available in tsfpga which generates code from textual configuration files.
To start using it simply create a file ``regs_<name>.toml`` in the root of a module (see :ref:`module structure <folder_structure>`).

From the TOML definition the register generator can create a VHDL package with all registers and their fields.
This VHDL package can then be used with the generic AXI-Lite register file in tsfpga.
Apart from that a C header and a C++ class can be generaterd, as well as a HTML page with human-readable documentation.

The register generator is well-integrated in the tsfpga module work flow.
It is fast enough that before each build and each simulation run, the modules will re-generate their VHDL register package so that it is always up-to-date.
Creating documentation and headers, which are typically distributed as part of FPGA release artifacts, is simple and easy to integrate in a build script.

There is also a set of VHDL AXI components that enable the register bus: AXI-to-AXI-Lite converter, AXI/AXI-Lite interconnect, AXI-Lite mux (splitter), AXI-Lite clock domain crossing, AXI-Lite generic register file.
These are found in the repo within the `axi module <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/axi>`__.


.. _default_registers:

Default registers
-----------------

A lot of projects use a few default registers in standard locations that shall be present in all modules.
In order to achieve this, without having to duplicate names and descriptions in many places, there is a ``default_registers`` flag to the :ref:`get_modules() <get_modules>` function.
Passing a list of :class:`.Register` objects will insert them in the register list of all modules that use registers.



Register examples
-----------------

Example register code generation from the `ddr_buffer example module <https://gitlab.com/tsfpga/tsfpga/-/tree/master/examples/modules/ddr_buffer>`__.


.. _toml_file:

TOML file
_________

This is the source TOML file that defines the registers.

.. literalinclude:: ../../generated/registers/toml/regs_ddr_buffer.toml
   :caption: regs_ddr_buffer.toml
   :language: toml

In this example module we use a set of default registers that include ``status`` and ``command``.
That is why these registers do not have a ``mode`` set in the TOML, which is otherwise required.
For the other registers we have to explicitly set a mode.

For default registers, the register description is also inherited from the default specification.
While a description is not strictly required it is used for all registers and bits in this example.

In this example we use a register array for the read and write addresses.
The registers ``read_addr`` and ``write_addr`` will be repeated two times in the register list.



Manipulating registers from Pyhton
__________________________________

The ``ddr_buffer`` example module also showcases how to manipulate registers from Python via tsfpga's module system.
This method for manipulating registers can be very useful for information that is known in the Python realm, but is not convenient to add to the TOML file.

.. literalinclude:: ../../examples/modules/ddr_buffer/module_ddr_buffer.py
   :caption: module_ddr_buffer.py
   :language: python
   :lines: 5-

Using :meth:`.BaseModule.registers_hook` we add a constant as well as a read-only register for the module's version number.
The idea behind this example is that a software that uses this module will read the ``version`` register and compare to the static constant that shows up in :ref:`the header <regs_cpp>`.
This will make sure that the software is running against the correct FPGA with expected module version.



VHDL package
____________

The VHDL package file is designed to be used with the generic AXI-Lite register file `available in tsfpga <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/reg_file>`__.

.. literalinclude:: ../../examples/modules/ddr_buffer/ddr_buffer_regs_pkg.vhd
   :caption: ddr_buffer_regs_pkg.vhd
   :language: vhdl

For the plain registers the register index is simply an integer, e.g. ``ddr_buffer_config``, but for the register arrays is is a function, e.g. ``ddr_buffer_addrs_read_addr()``.
The function takes an array index arguments and will assert if it is out of bounds of the array.

Note that there is a large eco-system of register related components in tsfpga.
Firstly there are wrappers available for easier working with VUnit verification components.
See the `bfm library <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/bfm/sim>`__ and `reg_operations_pkg <https://gitlab.com/tsfpga/tsfpga/-/blob/master/modules/reg_file/sim/reg_operations_pkg.vhd>`__.
Furthermore there is a large number of synthesizable AXI components available that enable the register bus: AXI-to-AXI-Lite converter, AXI/AXI-Lite interconnect, AXI-Lite mux (splitter), AXI-Lite clock domain crossing, etc.
See the `axi library <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/axi>`__ for more details.



HTML page
_________

A complete HTML page can be generated, with register details as well as textual description of the different register modes.

.. note::
   Markdown/reStructuredText syntax can be used in register and bit descriptions, which will be converted to appropriate HTML tags.
   Text can be set bold with double asterisks, and italicised with a single asterisk.
   A paragraph break can be inserted with consecutive newlines.


Generated HTML file :download:`here <../../generated/registers/doc/ddr_buffer_regs.html>`



HTML table
__________

Optionally only the register description table can be generated to a HTML file.
This can then be included in a separate documentation flow.

Generated HTML file :download:`here <../../generated/registers/doc/tables/ddr_buffer_regs_table.html>`



.. _regs_cpp:

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

Note that when the register is part of an array, the setter/getter takes a second argument ``array_index``.
There is an assert that the user-provided array index is within the bounds of the array.


C header
_________

A C header with register and field definitions can be generated.

.. literalinclude:: ../../generated/registers/c/ddr_buffer_regs.h
   :caption: ddr_buffer header
   :language: C

It provides two methods for usage: A struct that can be memory mapped, or address definitions that can be offset a base address.
For the addresses, array registers use a macro with an array index argument.



Python abstraction
------------------

The following classes are used to handle registers in the tsfpga python package.

.. autoclass:: tsfpga.register_list.RegisterList()
    :members:

    .. automethod:: __init__


.. autoclass:: tsfpga.register_types.Register()
    :members:

    .. automethod:: __init__

.. autoclass:: tsfpga.register_types.RegisterArray()
    :members:

    .. automethod:: __init__

.. autoclass:: tsfpga.register_types.Bit()
    :members:

    .. automethod:: __init__
