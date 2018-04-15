-- @brief AXI-Lite 1-to-N mux.

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

    read_m2s : in axil_read_m2s_t;
    read_s2m : out axil_read_s2m_t := axil_read_s2m_init;

    write_m2s : in axil_write_m2s_t;
    write_s2m : out axil_write_s2m_t := axil_write_s2m_init;

    read_m2s_vec : out axil_read_m2s_vec_t(slave_addrs'range) := (others => axil_read_m2s_init);
    read_s2m_vec : in axil_read_s2m_vec_t(slave_addrs'range);

    write_m2s_vec : out axil_write_m2s_vec_t(slave_addrs'range) := (others => axil_write_m2s_init);
    write_s2m_vec : in axil_write_s2m_vec_t(slave_addrs'range)
  );
end entity;

architecture a of axil_mux is

  constant slave_not_selected : integer := slave_addrs'length;
  signal read_slave_select, write_slave_select : integer range 0 to slave_not_selected := slave_not_selected;

begin

  ------------------------------------------------------------------------------
  assign_read_m2s : process(all)
  begin
    read_m2s_vec <= (others => read_m2s);

    for slave in read_m2s_vec'range loop
      if read_slave_select /= slave then
        read_m2s_vec(slave).ar.valid <= '0';
        read_m2s_vec(slave).r.ready <= '0';
      end if;
    end loop;
  end process;


  ------------------------------------------------------------------------------
  assign_read_s2m : process(all)
  begin
    if read_slave_select = slave_not_selected then
      read_s2m.ar <= (ready => '0');
      read_s2m.r <= (valid => '0', others => (others => '-'));
    else
      read_s2m <= read_s2m_vec(read_slave_select);
    end if;
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
          if read_m2s.ar.valid then
            read_slave_select <= decode(read_m2s.ar.addr, slave_addrs);
            state <= reading;
          end if;

        when reading =>
          if read_m2s.r.ready and read_s2m.r.valid then
            state <= waiting;
            read_slave_select <= slave_not_selected;
          end if;
      end case;
    end process;
  end block;


  ------------------------------------------------------------------------------
  assign_write_m2s : process(all)
  begin
    write_m2s_vec <= (others => write_m2s);

    for slave in write_m2s_vec'range loop
      if write_slave_select /= slave then
        write_m2s_vec(slave).aw.valid <= '0';
        write_m2s_vec(slave).w.valid <= '0';
        write_m2s_vec(slave).b.ready <= '0';
      end if;
    end loop;
  end process;


  ------------------------------------------------------------------------------
  assign_write_s2m : process(all)
  begin
    if write_slave_select = slave_not_selected then
      write_s2m.aw <= (ready => '0');
      write_s2m.w <= (ready => '0');
      write_s2m.b <= (valid => '0', resp => (others => '-'));
    else
      write_s2m <= write_s2m_vec(write_slave_select);
    end if;
  end process;


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
          if write_m2s.aw.valid then
            write_slave_select <= decode(write_m2s.aw.addr, slave_addrs);
            state <= writing;
          end if;

        when writing =>
          if write_m2s.b.ready and write_s2m.b.valid then
            state <= waiting;
            write_slave_select <= slave_not_selected;
          end if;
      end case;
    end process;
  end block;

end architecture;
