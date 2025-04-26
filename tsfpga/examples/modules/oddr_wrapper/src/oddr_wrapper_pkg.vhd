-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Constants/types/functions for an ODDR primitive wrapper.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;


package oddr_wrapper_pkg is

  ------------------------------------------------------------------------------
  -- Component for the ODDR primitive wrapper so it can be instantiated as a block box,
  -- meaning our design can be simulated even when we don't have access to
  -- Vivado simulation libraries.
  component oddr_primitive is
    generic (
      num_output_clocks : positive
    );
    port (
      internal_clock : in std_ulogic;
      output_clocks : out std_ulogic_vector(num_output_clocks - 1 downto 0) := (others => '0')
    );
  end component;
  ------------------------------------------------------------------------------

end;
