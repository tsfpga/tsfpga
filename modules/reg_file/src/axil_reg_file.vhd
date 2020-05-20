-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief General register file controlled over AXI-Lite
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.addr_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

use work.reg_file_pkg.all;


entity axil_reg_file is
  generic (
    regs : reg_definition_vec_t;
    default_values : reg_vec_t(regs'range) := (others => (others => '0'))
  );
  port (
    clk : in std_logic;

    axil_m2s : in axil_m2s_t;
    axil_s2m : out axil_s2m_t := (read => (
                                    ar => (ready => '1'),
                                    r => axil_s2m_r_init),
                                  write => (
                                    aw => (ready => '1'),
                                    w => axil_s2m_w_init,
                                    b => axil_s2m_b_init)
                                 );

    regs_up : in reg_vec_t(regs'range) := default_values;
    regs_down : out reg_vec_t(regs'range) := default_values;
    reg_was_written : out std_logic_vector(regs'range) := (others => '0')
  );
end entity;

architecture a of axil_reg_file is

  constant addr_and_mask_vec : addr_and_mask_vec_t := to_addr_and_mask_vec(regs);

  signal reg_values : reg_vec_t(regs'range) := default_values;

  constant invalid_addr : integer := regs'length;
  subtype decoded_idx_t is integer range 0 to invalid_addr;

begin

  regs_down <= reg_values;


  ------------------------------------------------------------------------------
  read : block
    type state_t is (ar, r);
    signal state : state_t := ar;
    signal decoded_idx : decoded_idx_t := invalid_addr;
  begin
    bus_read_fsm : process
    begin
      wait until rising_edge(clk);

      axil_s2m.read.r.valid <= '0';

      case state is
        when ar =>
          if axil_m2s.read.ar.valid and axil_s2m.read.ar.ready then
            axil_s2m.read.ar.ready <= '0';
            decoded_idx <= decode(axil_m2s.read.ar.addr, addr_and_mask_vec);

            -- Read address decode is pipelined one step, can not set r axil_s2m.read.r.valid
            -- until next clock cycle.
            state <= r;
          end if;

        when r =>
          axil_s2m.read.r.valid <= '1';
          if axil_m2s.read.r.ready and axil_s2m.read.r.valid then
            axil_s2m.read.r.valid <= '0';
            axil_s2m.read.ar.ready <= '1';
            state <= ar;
          end if;
      end case;
    end process;

    read : process
    begin
      wait until rising_edge(clk);

      if decoded_idx = invalid_addr or not is_read_type(regs(decoded_idx).reg_type) then
        axil_s2m.read.r.resp <= axi_resp_slverr;
        axil_s2m.read.r.data <= (others => '-');
      else
        axil_s2m.read.r.resp <= axi_resp_okay;

        if is_fabric_gives_value_type(regs(decoded_idx).reg_type) then
          axil_s2m.read.r.data(reg_values(0)'range) <= regs_up(decoded_idx);
        else
          axil_s2m.read.r.data(reg_values(0)'range) <= reg_values(decoded_idx);
        end if;
      end if;
    end process;
  end block;


  ------------------------------------------------------------------------------
  write : block
    type state_t is (aw, w, b);
    signal state : state_t := aw;
    signal decoded_idx : decoded_idx_t := invalid_addr;
  begin
    bus_write_fsm : process
    begin
      wait until rising_edge(clk);

      case state is
        when aw =>
          if axil_m2s.write.aw.valid and axil_s2m.write.aw.ready then
            axil_s2m.write.aw.ready <= '0';
            axil_s2m.write.w.ready <= '1';
            decoded_idx <= decode(axil_m2s.write.aw.addr, addr_and_mask_vec);
            state <= w;
          end if;

        when w =>
          if axil_m2s.write.w.valid and axil_s2m.write.w.ready then
            axil_s2m.write.w.ready <= '0';
            axil_s2m.write.b.valid <= '1';
            state <= b;
          end if;

        when b =>
          if axil_m2s.write.b.ready and axil_s2m.write.b.valid then
            axil_s2m.write.aw.ready <= '1';
            axil_s2m.write.b.valid <= '0';
            state <= aw;
          end if;
      end case;
    end process;

    write : process
    begin
      wait until rising_edge(clk);

      for list_idx in regs'range loop
        if is_write_pulse_type(regs(list_idx).reg_type) then
          reg_values(list_idx) <= (others => '0');
        end if;
      end loop;

      reg_was_written <= (others => '0');
      if decoded_idx = invalid_addr or not is_write_type(regs(decoded_idx).reg_type) then
        axil_s2m.write.b.resp <= axi_resp_slverr;
      else
        axil_s2m.write.b.resp <= axi_resp_okay;

        if axil_m2s.write.w.valid and axil_s2m.write.w.ready then
          reg_values(decoded_idx) <= axil_m2s.write.w.data(reg_values(0)'range);
          reg_was_written(decoded_idx) <= '1';
        end if;
      end if;
    end process;
  end block;

end architecture;
