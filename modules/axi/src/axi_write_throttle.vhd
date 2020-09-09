-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Performs throttling of an AXI bus by limiting the number of outstanding
-- transactions.
--
-- This entity is to be used in conjuctin with a data FIFO on the input.w side.
-- Using the level from that FIFO, the throttling will make sure that address
-- transactions are not until all data for that transaction is available in
-- the FIFO, to avoid stalling the throttled_m2s.w channel.
--
-- To achieve this it keeps track of the number of outstanding beats
-- that have been negotiated but not yet sent.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;

library common;
use common.types_pkg.all;


entity axi_write_throttle is
  generic(
    data_fifo_depth : positive;
    max_burst_length_beats : positive
  );
  port(
    clk : in std_logic;
    --
    data_fifo_level : in integer range 0 to data_fifo_depth;
    --
    input_m2s : in axi_write_m2s_t := axi_write_m2s_init;
    input_s2m : out axi_write_s2m_t := axi_write_s2m_init;
    --
    throttled_m2s : out axi_write_m2s_t := axi_write_m2s_init;
    throttled_s2m : in axi_write_s2m_t := axi_write_s2m_init
  );
end entity;

architecture a of axi_write_throttle is

  -- Since W transactions can happen before AW transaction,
  -- the counters can become negative as well.
  subtype data_counter_t is integer range -data_fifo_depth to data_fifo_depth;

  -- Data beats that are available in the FIFO, but have not yet been claimed by
  -- an address transaction.
  signal num_beats_available_but_not_negotiated : data_counter_t := 0;

  -- Number of data beats that have been negotiated through an address transaction,
  -- but have not yet been sent via data transactions. Aka outstanding beats.
  signal num_beats_negotiated_but_not_sent : data_counter_t := 0;

  signal burst_length_beats : integer range 0 to max_burst_length_beats;

begin

  burst_length_beats <= to_integer(unsigned(input_m2s.aw.len)) + 1;

  ------------------------------------------------------------------------------
  assign : process(all)
    variable block_address_transactions : boolean;
  begin
    throttled_m2s <= input_m2s;
    input_s2m <= throttled_s2m;

    block_address_transactions :=
      num_beats_available_but_not_negotiated < burst_length_beats;
    if block_address_transactions then
      throttled_m2s.aw.valid <= '0';
      input_s2m.aw.ready <= '0';
    end if;
  end process;


  ------------------------------------------------------------------------------
  count : process
    variable num_beats_negotiated_but_not_sent_int : data_counter_t := 0;
  begin
    wait until rising_edge(clk);

    num_beats_negotiated_but_not_sent_int := num_beats_negotiated_but_not_sent
      + to_int(throttled_s2m.aw.ready and throttled_m2s.aw.valid) * burst_length_beats
      - to_int(throttled_s2m.w.ready and throttled_m2s.w.valid);

    num_beats_available_but_not_negotiated <=
      data_fifo_level - num_beats_negotiated_but_not_sent_int;

    num_beats_negotiated_but_not_sent <= num_beats_negotiated_but_not_sent_int;
  end process;

end architecture;
