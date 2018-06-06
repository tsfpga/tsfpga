
library ieee;
use ieee.std_logic_1164.all;

library resync;


entity fpga_top is
  port (
    clk_in : in std_logic;
    input : in std_logic;
    clk_out : in std_logic;
    output : out std_logic
  );
end entity;

architecture a of fpga_top is
  signal input_p1 : std_logic;
begin

  pipe_input : process
  begin
    wait until rising_edge(clk_in);
    input_p1 <= input;
  end process;


  assign_output : entity resync.resync
  port map (
    data_in => input_p1,

    clk_out => clk_out,
    data_out => output
  );

end architecture;
