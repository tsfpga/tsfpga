.. _registers:

Register code generation
========================

TBC WIP

.. autoclass:: tsfpga.registers.RegisterList()
    :members:

    .. automethod:: __init__


.. autoclass:: tsfpga.registers.Register()
    :members:

    .. automethod:: __init__

.. autoclass:: tsfpga.registers.Bit()
    :members:

    .. automethod:: __init__



.. _default_registers:

Default registers
-----------------




Register examples
-----------------


JSON
____


.. literalinclude:: ../../generated/registers/json/regs_ddr_buffer.json
   :caption: regs_ddr_buffer.json
   :language: json


C++ class
_________


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


.. literalinclude:: ../../generated/registers/c/ddr_buffer_regs.h
   :caption: ddr_buffer header
   :language: C



HTML table
__________

Generated HTML file here :download:`here <../../generated/registers/doc/tables/ddr_buffer_regs_table.html>`



HTML page
_________

Generated HTML file here :download:`here <../../generated/registers/doc/ddr_buffer_regs.html>`
