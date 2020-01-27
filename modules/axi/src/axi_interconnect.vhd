-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Simple N-to-1 interconnect for connecting multiple AXI masters to one port.
--
-- Uses round-robin scheduling for the inputs.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;

library common;
use common.types_pkg.all;


entity axi_interconnect is
  generic(
    num_inputs : integer
  );
  port(
    clk : in std_logic;
    --
    inputs_read_m2s : in axi_read_m2s_vec_t(0 to num_inputs - 1) := (others => axi_read_m2s_init);
    inputs_read_s2m : out axi_read_s2m_vec_t(0 to num_inputs - 1) := (others => axi_read_s2m_init);
    --
    inputs_write_m2s : in axi_write_m2s_vec_t(0 to num_inputs - 1) := (others => axi_write_m2s_init);
    inputs_write_s2m : out axi_write_s2m_vec_t(0 to num_inputs - 1) := (others => axi_write_s2m_init);
    --
    output_read_m2s : out axi_read_m2s_t := axi_read_m2s_init;
    output_read_s2m : in axi_read_s2m_t := axi_read_s2m_init;
    --
    output_write_m2s : out axi_write_m2s_t := axi_write_m2s_init;
    output_write_s2m : in axi_write_s2m_t := axi_write_s2m_init
  );
end entity;

architecture a of axi_interconnect is

  constant no_input_selected : integer := inputs_read_m2s'high + 1;

  -- Max num outstanding address transactions
  constant max_addr_fifo_depth : integer := 128;

begin

  ------------------------------------------------------------------------------
  read_block : block
    signal input_select : integer range 0 to no_input_selected := no_input_selected;
    signal input_select_turn_counter : integer range inputs_read_m2s'range := 0;

    type state_t is (wait_for_ar_valid, wait_for_ar_done, wait_for_r_done);
    signal state : state_t := wait_for_ar_valid;
  begin

    ----------------------------------------------------------------------------
    select_input : process
      variable ar_done, r_done : std_logic;
      variable num_outstanding_addr_transactions : integer range 0 to max_addr_fifo_depth := 0;
    begin
      wait until rising_edge(clk);

      ar_done := output_read_s2m.ar.ready and output_read_m2s.ar.valid;
      r_done := output_read_m2s.r.ready and output_read_s2m.r.valid and output_read_s2m.r.last;

      num_outstanding_addr_transactions := num_outstanding_addr_transactions
        + to_int(ar_done) - to_int(r_done);

      case state is
        when wait_for_ar_valid =>
          -- Rotate around to find an input that requests a transaction
          if inputs_read_m2s(input_select_turn_counter).ar.valid then
            input_select <= input_select_turn_counter;
            state <= wait_for_ar_done;
          end if;

          if input_select_turn_counter = inputs_read_m2s'high then
            input_select_turn_counter <= 0;
          else
            input_select_turn_counter <= input_select_turn_counter + 1;
          end if;

        when wait_for_ar_done =>
          -- Wait for address transaction so that num_outstanding_addr_transactions
          -- is updated and this input actually gets to do a transaction
          if ar_done then
            state <= wait_for_r_done;
          end if;

        when wait_for_r_done =>
          -- Wait until all of this input's negotiated bursts are done, and then
          -- go back to choose a new input
          if num_outstanding_addr_transactions = 0 then
            input_select <= no_input_selected;
            state <= wait_for_ar_valid;
          end if;

      end case;
    end process;


    ----------------------------------------------------------------------------
    assign_bus : process(all)
    begin
      output_read_m2s.ar <= (valid => '0', others => (others => '-'));
      output_read_m2s.r <= (ready => '0');

      for idx in inputs_read_m2s'range loop
        -- Default assignment of all members. Non-selected inputs will be zero'd out below.
        inputs_read_s2m(idx) <= output_read_s2m;

        if idx = input_select then
          -- Assign whole M2S bus from the selected input
          output_read_m2s <= inputs_read_m2s(idx);
        else
          -- Non-selected inputs shall have their control signal zero'd out.
          -- Other members of the bus (r.data, etc.) can still be assigned.
          inputs_read_s2m(idx).ar.ready <= '0';
          inputs_read_s2m(idx).r.valid <= '0';
        end if;
      end loop;
    end process;
  end block;


  ------------------------------------------------------------------------------
  write_block : block
    signal input_select : integer range 0 to no_input_selected := no_input_selected;
    signal input_select_turn_counter : integer range inputs_write_s2m'range := 0;

    type state_t is (wait_for_aw_valid, wait_for_aw_done, wait_for_b_done);
    signal state : state_t := wait_for_aw_valid;
  begin

    ----------------------------------------------------------------------------
    select_input : process
      variable aw_done, b_done : std_logic;
      variable num_outstanding_addr_transactions : integer range 0 to max_addr_fifo_depth := 0;
    begin
      wait until rising_edge(clk);

      aw_done := output_write_s2m.aw.ready and output_write_m2s.aw.valid;
      b_done := output_write_m2s.b.ready and output_write_s2m.b.valid;

      num_outstanding_addr_transactions := num_outstanding_addr_transactions
        + to_int(aw_done) - to_int(b_done);

      case state is
        when wait_for_aw_valid =>
          -- Rotate around to find an input that requests a transaction
          if inputs_write_m2s(input_select_turn_counter).aw.valid then
            input_select <= input_select_turn_counter;
            state <= wait_for_aw_done;
          end if;

          if input_select_turn_counter = inputs_write_m2s'high then
            input_select_turn_counter <= 0;
          else
            input_select_turn_counter <= input_select_turn_counter + 1;
          end if;

        when wait_for_aw_done =>
          -- Wait for address transaction so that num_outstanding_addr_transactions
          -- is updated and this input actually gets to do a transaction
          if aw_done then
            state <= wait_for_b_done;
          end if;

        when wait_for_b_done =>
          -- Wait until all of this input's negotiated bursts are done, and then
          -- go back to choose a new input
          if num_outstanding_addr_transactions = 0 then
            input_select <= no_input_selected;
            state <= wait_for_aw_valid;
          end if;

      end case;
    end process;


    ----------------------------------------------------------------------------
    assign_bus : process(all)
    begin
      output_write_m2s.aw <= (valid => '0', others => (others => '-'));
      output_write_m2s.w <= (valid => '0', last => '-', others => (others => '-'));
      output_write_m2s.b <= (ready => '0');

      for idx in inputs_write_s2m'range loop
        -- Default assignment of all members. Non-selected inputs will be zero'd out below.
        inputs_write_s2m(idx) <= output_write_s2m;

        if idx = input_select then
          -- Assign whole M2S bus from the selected input
          output_write_m2s <= inputs_write_m2s(idx);
        else
          -- Non-selected inputs shall have their control signal zero'd out.
          -- Other members of the bus (b.resp, etc.) can still be assigned.
          inputs_write_s2m(idx).aw.ready <= '0';
          inputs_write_s2m(idx).w.ready <= '0';
          inputs_write_s2m(idx).b.valid <= '0';
        end if;
      end loop;
    end process;
  end block;

end architecture;
