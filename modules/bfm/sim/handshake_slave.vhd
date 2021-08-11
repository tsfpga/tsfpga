-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Toggle the 'ready' signal based on probabilities set via generics.
-- This realizes a handshake slave with jitter that is compliant with the AXI-Stream standard.
-- According to the standard, 'ready' can be lowered at any time, not just after a transaction.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library osvvm;
use osvvm.RandomPkg.RandomPType;


entity handshake_slave is
  generic (
    stall_probability_percent : natural;
    max_stall_cycles : positive;
    random_seed : string := ""
  );
  port (
    clk : in std_logic;
    data_is_ready : in std_logic := '1';
    data_ready : out std_logic := '0'
  );
end entity;

architecture a of handshake_slave is

  signal stall_data : std_logic := '1';

begin

  data_ready <= data_is_ready and not stall_data;


  ------------------------------------------------------------------------------
  main : process
    variable rnd : RandomPType;
  begin
    assert stall_probability_percent >= 0 and stall_probability_percent <= 100
      report "Invalid percentage: " & to_string(stall_probability_percent);

    rnd.InitSeed(rnd'instance_name & random_seed);

    loop
      if rnd.RandInt(1, 100) > (100 - stall_probability_percent) then
        stall_data <= '1';

        for low_cycles in 1 to rnd.FavorSmall(0, max_stall_cycles) loop
          -- Loop collapses for rand = 0 and there is no jitter
          wait until rising_edge(clk);
        end loop;
      end if;

      stall_data <= '0';
      wait until rising_edge(clk);
    end loop;
  end process;

end architecture;
