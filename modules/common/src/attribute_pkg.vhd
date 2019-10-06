-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

package attribute_pkg is

  -- Commonly used attributes. Descriptions from UG901.

  -- Prevent optimizations where signals are either optimized or absorbed into logic blocks.
  -- Works in the same way as KEEP or KEEP_HIERARCHY attributes; However unlike KEEP and KEEP_HIERARCHY,
  -- DONT_TOUCH is forward-annotated to place and route to prevent logic optimization.
  -- @note Use the DONT_TOUCH attribute in place of KEEP or KEEP_HIERARCHY.
  attribute dont_touch : string;

  -- Inform the tool that a register is capable of receiving asynchronous data in the D input pin relative to the source clock,
  -- or that the register is a synchronizing register within a synchronization chain.
  attribute async_reg : string;

  -- Instructs the Vivado synthesis tool on how to infer memory. Accepted values are:
  -- * block: Instructs the tool to infer RAMB type components.
  -- * distributed: Instructs the tool to infer the LUT RAMs.
  -- * registers: Instructs the tool to infer registers instead of RAMs.
  -- * ultra: Instructs the tool to use the UltraScale+TM URAM primitives.
  attribute ram_style : string;

  -- instructs the synthesis tool how to deal with synthesis arithmetic structures. By default, unless there are timing concerns
  -- or threshold limits, synthesis attempts to infer mults, mult-add, mult-sub, and mult-accumulate type structures into DSP blocks.
  -- Adders, subtracters, and accumulators can go into these blocks also, but by default are implemented with the logic instead of with DSP blocks.
  attribute use_dsp : string;

  -- Indicates if a register should go into the I/O buffer. Place this attribute on the register that you want in the I/O buffer.
  attribute iob : string;

end package;
