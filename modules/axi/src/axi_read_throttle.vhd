-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Performs throttling of an AXI bus by limiting the number of outstanding
-- transactions.
--
-- This entity is to be used in conjuction with a data FIFO on the input.r side.
-- Using the level from that FIFO, the throttling will make sure that address
-- transactions are not made that would result in the FIFO becoming full. This
-- avoids stalling on the throttled_s2m.r channel.
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


entity axi_read_throttle is
  generic(
    data_fifo_depth : positive;
    max_burst_length_beats : positive
  );
  port(
    clk : in std_logic;
    --
    data_fifo_level : in integer range 0 to data_fifo_depth;
    --
    input_m2s : in axi_read_m2s_t := axi_read_m2s_init;
    input_s2m : out axi_read_s2m_t := axi_read_s2m_init;
    --
    throttled_m2s : out axi_read_m2s_t := axi_read_m2s_init;
    throttled_s2m : in axi_read_s2m_t := axi_read_s2m_init
  );
end entity;

architecture a of axi_read_throttle is

  subtype data_counter_t is integer range 0 to data_fifo_depth;

  -- Number of data beats that have been negotiated via address transactions,
  -- but have not yet been sent by the master. Aka outstanding beats.
  signal num_beats_negotiated_but_not_sent : data_counter_t := 0;

  -- Number of data beat words available in the FIFO, that have not been claimed
  -- by oustanding transactions.
  signal num_empty_words_in_fifo_that_have_not_been_negotiated : data_counter_t := 0;

  signal burst_length_beats : integer range 0 to max_burst_length_beats;

begin

  burst_length_beats <= to_integer(unsigned(input_m2s.ar.len)) + 1;

  ------------------------------------------------------------------------------
  assign : process(all)
    variable block_address_transactions : boolean;
  begin
    throttled_m2s <= input_m2s;
    input_s2m <= throttled_s2m;

    block_address_transactions :=
      burst_length_beats >= num_empty_words_in_fifo_that_have_not_been_negotiated;
    if block_address_transactions then
      throttled_m2s.ar.valid <= '0';
      input_s2m.ar.ready <= '0';
    end if;
  end process;


  ------------------------------------------------------------------------------
  count : process
    variable num_empty_words_in_fifo, num_beats_negotiated_but_not_sent_int
      : data_counter_t := 0;
  begin
    wait until rising_edge(clk);

    num_beats_negotiated_but_not_sent_int := num_beats_negotiated_but_not_sent
      + to_int(throttled_m2s.ar.valid and throttled_s2m.ar.ready) * burst_length_beats
      - to_int(input_m2s.r.ready and input_s2m.r.valid);

    num_empty_words_in_fifo := data_fifo_depth - data_fifo_level;
    num_empty_words_in_fifo_that_have_not_been_negotiated <=
      num_empty_words_in_fifo - num_beats_negotiated_but_not_sent_int;

    num_beats_negotiated_but_not_sent <= num_beats_negotiated_but_not_sent_int;
  end process;

end architecture;
