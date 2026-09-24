-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Small self-contained example entity used to demonstrate :ref:`Yosys netlist builds
-- <yosys_netlist_build>` in ``module_resource_counter.py``.
--
-- Counts upwards, and calculates a combinational ``wrap_next`` flag that is asserted the cycle
-- before the counter wraps around to zero.
-- The ``width`` generic can be used to scale the resource utilization of the design, which is
-- useful when experimenting with netlist build result checkers.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity resource_counter is
  generic (
    width : positive := 8
  );
  port (
    clk : in std_ulogic;
    --# {{}}
    increment : in std_ulogic;
    --# {{}}
    count : out unsigned(width - 1 downto 0) := (others => '0');
    wrap_next : out std_ulogic := '0'
  );
end entity;

architecture a of resource_counter is

  signal count_int : unsigned(width - 1 downto 0) := (others => '0');

begin

  count <= count_int;

  -- Combinational logic that always requires look-up tables to implement, regardless of how
  -- the counter's carry chain above is optimized by the synthesis tool.
  -- Note the VHDL-2008 unary reduction operator used to AND all the bits of 'count_int' together.
  wrap_next <= increment and (and count_int);

  ------------------------------------------------------------------------------
  main : process
  begin
    wait until rising_edge(clk);

    if increment = '1' then
      count_int <= count_int + 1;
    end if;
  end process;

end architecture;
