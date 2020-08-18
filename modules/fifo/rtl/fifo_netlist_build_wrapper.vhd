-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- A wrapper of the FIFO with only the "barebone" ports routed. To be used
-- for size assertions in netlist builds.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;


entity fifo_netlist_build_wrapper is
  generic (
    width : positive;
    depth : positive
  );
  port (
    clk : in std_logic;

    read_ready : in std_logic;
    read_valid : out std_logic := '0';
    read_data : out std_logic_vector(width - 1 downto 0);

    write_ready : out std_logic := '1';
    write_valid : in std_logic;
    write_data : in std_logic_vector(width - 1 downto 0)
  );
end entity;

architecture a of fifo_netlist_build_wrapper is

begin

  fifo_inst : entity work.fifo
    generic map (
      width => width,
      depth => depth
    )
    port map (
      clk => clk,

      read_ready => read_ready,
      read_valid => read_valid,
      read_data => read_data,

      write_ready => write_ready,
      write_valid => write_valid,
      write_data => write_data
    );

end architecture;
