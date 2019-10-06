-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief AXI-Lite 1-to-N mux.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library math;
use math.math_pkg.all;

library common;
use common.addr_pkg.all;

use work.axil_pkg.all;


entity axil_mux is
  generic (
    slave_addrs : addr_and_mask_vec_t
  );
  port (
    clk : in std_logic;

    axil_m2s : in axil_m2s_t;
    axil_s2m : out axil_s2m_t := axil_s2m_init;

    axil_m2s_vec : out axil_m2s_vec_t(slave_addrs'range) := (others => axil_m2s_init);
    axil_s2m_vec : in axil_s2m_vec_t(slave_addrs'range)
  );
end entity;

architecture a of axil_mux is

  constant slave_not_selected : integer := slave_addrs'length;
  signal read_slave_select, write_slave_select : integer range 0 to slave_not_selected := slave_not_selected;

begin

  ------------------------------------------------------------------------------
  assign_s2m_read : process(all)
  begin
    if read_slave_select = slave_not_selected then
      axil_s2m.read.ar <= (ready => '0');
      axil_s2m.read.r <= (valid => '0', others => (others => '-'));
    else
      axil_s2m.read <= axil_s2m_vec(read_slave_select).read;
    end if;
  end process;


  ------------------------------------------------------------------------------
  assign_s2m_write : process(all)
  begin
    if write_slave_select = slave_not_selected then
      axil_s2m.write.aw <= (ready => '0');
      axil_s2m.write.w <= (ready => '0');
      axil_s2m.write.b <= (valid => '0', others => (others => '-'));
    else
      axil_s2m.write <= axil_s2m_vec(write_slave_select).write;
    end if;
  end process;


  ------------------------------------------------------------------------------
  assign_m2s_vec : process(all)
  begin
    for slave in axil_m2s_vec'range loop
      axil_m2s_vec(slave) <= axil_m2s;

      if write_slave_select /= slave then
        axil_m2s_vec(slave).write.aw.valid <= '0';
        axil_m2s_vec(slave).write.w.valid <= '0';
        axil_m2s_vec(slave).write.b.ready <= '0';
      end if;

      if read_slave_select /= slave then
        axil_m2s_vec(slave).read.ar.valid <= '0';
        axil_m2s_vec(slave).read.r.ready <= '0';
      end if;
    end loop;
  end process;


  ------------------------------------------------------------------------------
  select_read_slave : block
    type state_t is (waiting, reading);
    signal state : state_t := waiting;
  begin
    select_read_slave : process
    begin
      wait until rising_edge(clk);

      case state is
        when waiting =>
          if axil_m2s.read.ar.valid then
            read_slave_select <= decode(axil_m2s.read.ar.addr, slave_addrs);
            state <= reading;
          end if;

        when reading =>
          if axil_m2s.read.r.ready and axil_s2m.read.r.valid then
            state <= waiting;
            read_slave_select <= slave_not_selected;
          end if;
      end case;
    end process;
  end block;


  ------------------------------------------------------------------------------
  select_write_slave : block
    type state_t is (waiting, writing);
    signal state : state_t := waiting;
  begin
    select_write_slave : process
    begin
      wait until rising_edge(clk);

      case state is
        when waiting =>
          if axil_m2s.write.aw.valid then
            write_slave_select <= decode(axil_m2s.write.aw.addr, slave_addrs);
            state <= writing;
          end if;

        when writing =>
          if axil_m2s.write.b.ready and axil_s2m.write.b.valid then
            state <= waiting;
            write_slave_select <= slave_not_selected;
          end if;
      end case;
    end process;
  end block;

end architecture;
