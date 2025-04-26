-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Wrapper around AMD primitives for sending out a clock to an FPGA pin through an ODDR primitive.
-- Results in better jitter properties for the board clock signal compared to just assigning
-- the clock to the pin directly.
-- This is since the clock signal never has to leave the FPGA-internal clock network.
--
-- Benchmarking a sink-synchronous input interface, the setup+hold slack window was 0.8 ns larger
-- when using an ODDR compared to assigning the pin directly.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.oddr_wrapper_pkg.all;


entity oddr_wrapper is
  generic (
    -- The number of ODDR primitives to instantiate.
    num_output_clocks : positive := 1;
    -- Optionally enable the use of a mock ODDR.
    -- This is useful for simulation where the ODDR primitive is not available.
    -- It will also be a lot faster in terms of execution time.
    use_mock : boolean := false
  );
  port (
    internal_clock : in std_ulogic;
    output_clocks : out std_ulogic_vector(num_output_clocks - 1 downto 0) := (others => '0')
  );
end entity;

architecture a of oddr_wrapper is

begin

  ----------------------------------------------------------------------------
  mock_or_oddr_gen : if use_mock generate

    output_clocks <= (others => internal_clock);


  ----------------------------------------------------------------------------
  else generate

    ----------------------------------------------------------------------------
    -- Use black-box component instantiation so this code can be used even
    -- when unisim is not available.
    oddr_primitive_inst : oddr_primitive
      generic map (
        num_output_clocks => num_output_clocks
      )
      port map (
        internal_clock => internal_clock,
        output_clocks => output_clocks
      );

  end generate;

end architecture;
