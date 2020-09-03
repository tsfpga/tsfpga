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
    input_m2s : in axi_write_m2s_t := axi_write_m2s_init;
    input_s2m : out axi_write_s2m_t := axi_write_s2m_init;
    --
    throttled_m2s : out axi_write_m2s_t := axi_write_m2s_init;
    throttled_s2m : in axi_write_s2m_t := axi_write_s2m_init
  );
end entity;

architecture a of axi_write_throttle is

  signal num_outstanding : integer range 0 to max_num_outstanding_transactions := 0;

begin

  ------------------------------------------------------------------------------
  assign : process(all)
    variable block_address_transactions : boolean;
  begin
    throttled_m2s <= input_m2s;
    input_s2m <= throttled_s2m;

    block_address_transactions := num_outstanding >= max_num_outstanding_transactions;
    if block_address_transactions then
      throttled_m2s.aw.valid <= '0';
      input_s2m.aw.ready <= '0';
    end if;
  end process;


  ------------------------------------------------------------------------------
  count : process
  begin
    wait until rising_edge(clk);

    num_outstanding <= num_outstanding
      + to_int(throttled_m2s.aw.valid and throttled_s2m.aw.ready)
      - to_int(input_m2s.b.ready and input_s2m.b.valid);
  end process;

end architecture;
