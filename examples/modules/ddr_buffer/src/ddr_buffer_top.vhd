-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library reg_file;

use work.ddr_buffer_pkg.all;
use work.ddr_buffer_regs_pkg.all;


entity ddr_buffer_top is
  port (
    clk_axi_read : in std_logic;
    axi_read_m2s : out axi_read_m2s_t := axi_read_m2s_init;
    axi_read_s2m : in axi_read_s2m_t;

    clk_axi_write : in std_logic;
    axi_write_m2s : out axi_write_m2s_t := axi_write_m2s_init;
    axi_write_s2m : in axi_write_s2m_t;

    clk_regs : in std_logic;
    regs_m2s : in axil_m2s_t;
    regs_s2m : out axil_s2m_t := axil_s2m_init
  );
end entity;

architecture a of ddr_buffer_top is

  type ctrl_state_t is (idle, start, wait_for_address_transactions, running);
  signal ctrl_state : ctrl_state_t := idle;

  signal current_addr_index : integer range 0 to ddr_buffer_addrs_array_length - 1 := 0;

  signal regs_up, regs_down : ddr_buffer_regs_t := ddr_buffer_regs_init;

  alias command_start is regs_down(ddr_buffer_command)(ddr_buffer_command_start);
  alias status_idle is regs_up(ddr_buffer_status)(ddr_buffer_status_idle);

begin

  ------------------------------------------------------------------------------
  axi_read_m2s.ar.addr(regs_down(0)'range) <= regs_down(ddr_buffer_addrs_read_addr(current_addr_index));
  axi_read_m2s.ar.len <= to_len(burst_length_beats);
  axi_read_m2s.ar.size <= to_size(axi_width);
  axi_read_m2s.ar.burst <= axi_a_burst_incr;


  ------------------------------------------------------------------------------
  axi_write_m2s.aw.addr(regs_down(0)'range) <= regs_down(ddr_buffer_addrs_write_addr(current_addr_index));
  axi_write_m2s.aw.len <= to_len(burst_length_beats);
  axi_write_m2s.aw.size <= to_size(axi_width);
  axi_write_m2s.aw.burst <= axi_a_burst_incr;

  axi_write_m2s.w.strb <= to_strb(axi_width);

  axi_write_m2s.b.ready <= '1';


  ------------------------------------------------------------------------------
  axi_read_m2s.r.ready <= axi_write_s2m.w.ready;

  axi_write_m2s.w.valid <= axi_read_s2m.r.valid and axi_read_m2s.r.ready;
  axi_write_m2s.w.data <= axi_read_s2m.r.data;
  axi_write_m2s.w.last <= axi_read_s2m.r.last;


  ------------------------------------------------------------------------------
  ctrl : process
    variable ar_done, aw_done : boolean := false;
  begin
    wait until rising_edge(clk_regs);

    case ctrl_state is
      when idle =>
        status_idle <= '1';
        ar_done := false;
        aw_done := false;

        if command_start then
          ctrl_state <= start;
          status_idle <= '0';
        end if;

      when start =>
        axi_read_m2s.ar.valid <= '1';
        axi_write_m2s.aw.valid <= '1';
        ctrl_state <= wait_for_address_transactions;

      when wait_for_address_transactions =>
        if axi_read_m2s.ar.valid and axi_read_s2m.ar.ready then
          axi_read_m2s.ar.valid <= '0';
          ar_done := true;
        end if;
        if axi_write_m2s.aw.valid and axi_write_s2m.aw.ready then
          axi_write_m2s.aw.valid <= '0';
          aw_done := true;
        end if;

        if ar_done and aw_done then
          ctrl_state <= running;
        end if;

      when running =>
        if axi_write_m2s.w.valid and axi_write_s2m.w.ready and axi_write_m2s.w.last then
          if current_addr_index = ddr_buffer_addrs_array_length - 1 then
            current_addr_index <= 0;
            ctrl_state <= idle;
          else
            current_addr_index <= current_addr_index + 1;
            ctrl_state <= start;
          end if;
        end if;
    end case;
  end process;


  ------------------------------------------------------------------------------
  axil_reg_file_inst : entity reg_file.axil_reg_file
    generic map (
      regs => ddr_buffer_reg_map,
      default_values => ddr_buffer_regs_init
    )
    port map (
      clk => clk_regs,

      axil_m2s => regs_m2s,
      axil_s2m => regs_s2m,

      regs_up => regs_up,
      regs_down => regs_down
    );

end architecture;
