library ieee;
use ieee.std_logic_1164.all;


entity edge_detector is
  port (
   clk : in std_logic;

   data_in : in std_logic;
   edge_detected : out std_logic := '0');
end entity;

architecture a of edge_detector is
begin

  main : process
    variable data_in_p1 : std_logic := '0';

    function to_sl(input : boolean) return std_logic is
    begin
      if input then
        return '1';
      end if;
      return '0';
    end function;
  begin
    wait until rising_edge(clk);
    edge_detected <= edge_detected or to_sl(data_in /= data_in_p1);
    data_in_p1 := data_in;
  end process;

end architecture;
