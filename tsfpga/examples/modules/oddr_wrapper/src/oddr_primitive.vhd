-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Thin wrapper around an ODDR primitive component.
-- Depends on the ``unisim`` library from AMD.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library unisim;
use unisim.vcomponents.all;


entity oddr_primitive is
  generic (
    num_output_clocks : positive
  );
  port (
    internal_clock : in std_ulogic;
    output_clocks : out std_ulogic_vector(num_output_clocks - 1 downto 0) := (others => '0')
  );
end entity;

architecture a of oddr_primitive is

begin

  ----------------------------------------------------------------------------
  oddr_gen : for oddr_idx in output_clocks'range generate

    ----------------------------------------------------------------------------
    ODDR_inst : ODDR
      port map (
        Q => output_clocks(oddr_idx),
        C => internal_clock,
        CE => '1',
        D1 => '1',
        D2 => '0',
        R => '0',
        S => '0'
      );

  end generate;

end architecture;
