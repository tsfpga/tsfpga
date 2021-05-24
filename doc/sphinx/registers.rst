.. _registers:

Register code generation
========================

There is a register code generation eco-system available in tsfpga which generates code from textual configuration files.
To start using it simply create a file ``regs_<name>.toml`` in the root of a module (see :ref:`module structure <folder_structure>`).

From the TOML definition the register generator can create a VHDL package with all registers and their fields.
This VHDL package can then be used with the generic AXI-Lite register file in tsfpga.
Apart from that a C header and a C++ class can be generated, as well as a HTML page with human-readable documentation.
See :ref:`register_examples` for a real-world example of register definitions and the code that it generates.

The register generator is well-integrated in the tsfpga module work flow.
It is fast enough that before each build and each simulation run, the modules will re-generate their VHDL register package so that it is always up-to-date.
Creating documentation and headers, which are typically distributed as part of FPGA release artifacts, is simple and easy to integrate in a build script.

There is also a set of VHDL AXI components that enable the register bus: AXI-to-AXI-Lite converter, AXI/AXI-Lite interconnect, AXI-Lite mux (splitter), AXI-Lite clock domain crossing, AXI-Lite generic register file.
These are found in the repo within the `axi module <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/axi>`__.



.. _register_toml_format:

Register TOML format
--------------------

The register generator parses a TOML file in order to gather all register information.
It is important the the TOML is formatted correctly and has the necessary fields.
The register TOML parser will warn if there are any error in the TOML, such as missing fields, unknown fields, wrong data types for fields, etc.

Below is a compilation of all the TOML properties that are available.
Comments describe what attributes are optional and which are required.


.. code-block:: toml
  :caption: Register TOML format rules.

  ################################################################################
  # This will allocate a register with the name "configuration".
  [register.configuration]

  # The "mode" property MUST be present for a register.
  # The value specified must be a valid mode string value.
  mode = "r_w"
  # The "description" property is optional for a register. Will default to "" if not specified.
  # The value specified must be a string.
  description = """This is the description of my register.

  Rudimentary RST formatting can be used, such as **boldface** and *italics*."""


  # This will allocate a bit field named "enable" in the "configuration" register.
  [register.configuration.bit.enable]

  # The "description" property is optional for a bit field. Will default to "" if not specified.
  # The value specified must be a string.
  description = "Description of the **enable** bit field."
  # The "default_value" property is optional for a bit field.
  # Must hold either of the strings "1" or "0" if specified.
  # Will default to "0" if not specified.
  default_value = "1"


  # This will allocate a bit vector field named "data_tag" in the "configuration" register.
  [register.configuration.bit_vector.data_tag]

  # The "width" property MUST be present for a bit vector field.
  # The value specified must be an integer.
  width = 4
  # The "description" property is optional for a bit vector field. Will default to "" if not specified.
  # The value specified must be a string.
  description = "Description of my **data_tag** bit vector field."
  # The "default_value" property is optional for a bit vector field.
  # The value specified must be a string whose length is the same as the specified **width** property value.
  # May only contain ones and zeros.
  # Will default to all zeros if not specified.
  default_value = "0101"


  ################################################################################
  # This will allocate a register array with the name "base_addresses".
  [register_array.base_addresses]

  # The "array_length" property MUST be present for a register array.
  # The value specified must be an integer.
  # The registers within the array will be repeated this many times.
  array_length = 3
  # The "description" property is optional for a register array. Will default to "" if not specified.
  # The value specified must be a string.
  description = "One set of base addresses for each feature."


  # ------------------------------------------------------------------------------
  # This will allocate a register "read_address" in the "base_addresses" array.
  [register_array.base_addresses.register.read_address]

  # Registers in a register array follow the exact same rules as "plain" registers.
  # The properties that may and must be set are the same.
  # Fields (bits, bit vectors, ...) can be added to array registers in the same way.
  mode = "w"

  # This will allocate a bit vector field named "address" in the "read_address" register within the "base_addresses" array.
  [register_array.base_addresses.register.read_address.bit_vector.address]

  width = 28
  description = "Read address for a 256 MB address space."


  # ------------------------------------------------------------------------------
  # This will allocate a register "write_address" in the "base_addresses" array.
  [register_array.base_addresses.register.write_address]

  mode = "w"

  # This will allocate a bit vector field named "address" in the "write_address" register within the "base_addresses" array.
  [register_array.base_addresses.register.write_address.bit_vector.address]

  width = 28
  description = "Write address for a 256 MB address space."



.. _default_registers:

Default registers
-----------------

A lot of projects use a few default registers in standard locations that shall be present in all modules.
In order to achieve this, without having to duplicate names and descriptions in many places, there is a ``default_registers`` flag to the :func:`.get_modules` function.
Passing a list of :class:`.Register` objects will insert them in the register list of all modules that use registers.


Bus layout
----------

Below is a diagram of the typical layout for a register bus.

.. digraph:: my_graph

  graph [ dpi = 300 splines=ortho ];
  rankdir="LR";

  cpu [ label="AXI master\n(CPU)" shape=box ];
  cpu -> axi_to_axi_lite [label="AXI"];

  axi_to_axi_lite [ label="axi_to_axi_lite" shape=box ];
  axi_to_axi_lite -> axi_lite_mux  [label="AXI-Lite" ];

  axi_lite_mux [ label="axi_lite_mux" shape=box height=3.5 ];

  axi_lite_mux -> axi_lite_reg_file0;
  axi_lite_reg_file0 [ label="axi_lite_reg_file" shape=box ];

  axi_lite_mux -> axi_lite_reg_file1;
  axi_lite_reg_file1 [ label="axi_lite_reg_file" shape=box ];

  axi_lite_mux -> axi_lite_cdc2;
  axi_lite_cdc2 [ label="axi_lite_cdc" shape=box ];
  axi_lite_cdc2 -> axi_lite_reg_file2;
  axi_lite_reg_file2 [ label="axi_lite_reg_file" shape=box ];

  axi_lite_mux -> axi_lite_cdc3;
  axi_lite_cdc3 [ label="axi_lite_cdc" shape=box ];
  axi_lite_cdc3 -> axi_lite_reg_file3;
  axi_lite_reg_file3 [ label="axi_lite_reg_file" shape=box ];

  dots [ shape=none label="..."];
  axi_lite_mux -> dots;

In tsfpga, the register bus used is AXI-Lite.
In cases where a module uses a different clock than the AXI master (CPU), the bus must be resynchronized.
This makes sure that each module's register values are always in the clock domain where they are used.
This means that the module design does not have to worry about metastability, vector coherency, pulse resynchronization, etc.

* ``axi_to_axi_lite`` is a simple protocol converter between AXI and AXI-Lite.
  It does not perform any burst splitting or handling of write strobes, but instead assumes the master to be well behaved.
  If this is not the case, AXI slave error (``SLVERR``) will be sent on the response channel (``R``/``B``).

* ``axi_lite_mux`` is a 1-to-N AXI-Lite multiplexer that operates based on base addresses and address masks specified via a generic.
  If the address requested by the master does not match any slave, AXI decode error (``DECERR``) will be sent on the response channel (``R``/``B``).
  There will still be proper AXI handshaking done, so the master will not be stalled.

* ``axi_lite_cdc`` is an asynchronous FIFO-based clock domain crossing (CDC) for AXI-Lite buses.
  It must be used in the cases where the ``axi_lite_reg_file`` (i.e. your module) is in a different clock domain than the CPU AXI master.

* ``axi_lite_reg_file`` is a generic, parameterizable, register file for AXI-Lite register buses.
  It is parameterizable via a generic that sets the list of registers, with their modes and their default values.
  A constant with this generic is generated from :ref:`TOML <toml_file>` in the :ref:`VHDL package <vhdl_package>`.
  If the address requested by the master does not match any register, or there is a
  mode mismatch (e.g. write to a read-only register), AXI slave error (``SLVERR``) will be sent on the response channel (``R``/``B``).

All these entities are available in the repo in the `axi <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/axi>`__
and `reg_file <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/reg_file>`__ modules.
Note that there is a convenience wrapper
`axi.axi_to_axi_lite_vec <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/axi/src/axi_to_axi_lite_vec.vhd>`__
that instantiates ``axi_to_axi_lite``, ``axi_lite_mux`` and any necessary ``axi_lite_cdc`` based on the appropriate generics.



.. _register_examples:

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
   :lines: 9-

Using :meth:`.BaseModule.registers_hook` we add a constant as well as a read-only register for the module's version number.
The idea behind this example is that a software that uses this module will read the ``version`` register and compare to the static constant that shows up in :ref:`the header <regs_cpp>`.
This will make sure that the software is running against the correct FPGA with expected module version.


.. _vhdl_package:

VHDL package
____________

The VHDL package file is designed to be used with the generic AXI-Lite register file `available in tsfpga <https://gitlab.com/tsfpga/tsfpga/-/tree/master/modules/reg_file>`__.

Since generation of VHDL packages is usually run in real time (e.g. before running a simulation) the speed of the tool is important.
In order the save time, :meth:`.RegisterList.create_vhdl_package` maintains a hash of the register definitions, and will only generate the VHDL when necessary.

.. literalinclude:: ../../generated/registers/vhdl/ddr_buffer_regs_pkg.vhd
   :caption: ddr_buffer_regs_pkg.vhd
   :language: vhdl

For the plain registers the register index is simply an integer, e.g. ``ddr_buffer_config``, but for the register arrays is is a function, e.g. ``ddr_buffer_addrs_read_addr()``.
The function takes an array index argument and will assert if it is out of bounds of the array.

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


Generated HTML file here: :download:`ddr_buffer_regs.html <../../generated/registers/html/ddr_buffer_regs.html>`



HTML tables
___________

Optionally, only the tables with register and constant descriptions can be generated to HTML.
These can then be included in a separate documentation flow.

Generated HTML file here: :download:`ddr_buffer_register_table.html <../../generated/registers/html/tables/ddr_buffer_register_table.html>`

Generated HTML file here: :download:`ddr_buffer_constant_table.html <../../generated/registers/html/tables/ddr_buffer_constant_table.html>`



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
