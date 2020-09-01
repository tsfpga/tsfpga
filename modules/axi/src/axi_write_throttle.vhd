-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Performs throttling of an AXI bus by limiting the number of outstanding
-- transactions.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;

library common;
use common.types_pkg.all;


entity axi_write_throttle is
  generic(
    max_num_outstanding_transactions : positive
  );
  port(
    clk : in std_logic;
    --
    left_m2s : in axi_write_m2s_t := axi_write_m2s_init;
    left_s2m : out axi_write_s2m_t := axi_write_s2m_init;
    --
    right_m2s : out axi_write_m2s_t := axi_write_m2s_init;
    right_s2m : in axi_write_s2m_t := axi_write_s2m_init
  );
end entity;

architecture a of axi_write_throttle is

  signal num_outstanding : integer range 0 to max_num_outstanding_transactions := 0;

begin

  ------------------------------------------------------------------------------
  assign : process(all)
    variable block_address_transactions : boolean;
  begin
    right_m2s <= left_m2s;
    left_s2m <= right_s2m;

    block_address_transactions := num_outstanding >= max_num_outstanding_transactions;
    if block_address_transactions then
      right_m2s.aw.valid <= '0';
      left_s2m.aw.ready <= '0';
    end if;
  end process;


  ------------------------------------------------------------------------------
  count : process
  begin
    wait until rising_edge(clk);

    num_outstanding <= num_outstanding
      + to_int(right_m2s.aw.valid and right_s2m.aw.ready)
      - to_int(left_m2s.b.ready and left_s2m.b.valid);
  end process;

end architecture;
