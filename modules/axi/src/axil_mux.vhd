-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief AXI-Lite 1-to-N mux.
--
-- Will respond with AXI decode error if no slave matches.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library math;
use math.math_pkg.all;

library common;
use common.addr_pkg.all;

use work.axil_pkg.all;
use work.axi_pkg.all;


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

  -- Decode function will return upper index + 1 if no slave matched
  constant decode_failed : integer := axil_m2s_vec'length;

  constant slave_decode_error_idx : integer := decode_failed;
  constant slave_not_selected_idx : integer := decode_failed + 1;

  signal read_slave_select, write_slave_select : integer range 0 to slave_not_selected_idx := slave_not_selected_idx;

  signal read_decode_error_s2m : axil_read_s2m_t := axil_read_s2m_init;
  signal write_decode_error_s2m : axil_write_s2m_t := axil_write_s2m_init;

begin

  ------------------------------------------------------------------------------
  assign_s2m_read : process(all)
  begin
    if read_slave_select = slave_decode_error_idx then
      axil_s2m.read.ar <= (ready => read_decode_error_s2m.ar.ready);
      axil_s2m.read.r <= (valid => read_decode_error_s2m.r.valid,
                          resp => axi_resp_decerr,
                          data => (others => '-'));
    elsif read_slave_select = slave_not_selected_idx then
      -- Wait for the master to assert address valid so that we can select the correct slave
      axil_s2m.read.ar <= (ready => '0');
      axil_s2m.read.r <= (valid => '0', others => (others => '-'));
    else
      axil_s2m.read <= axil_s2m_vec(read_slave_select).read;
    end if;
  end process;


  ------------------------------------------------------------------------------
  assign_s2m_write : process(all)
  begin
    if write_slave_select = slave_decode_error_idx then
      axil_s2m.write.aw <= (ready => write_decode_error_s2m.aw.ready);
      axil_s2m.write.w <= (ready => write_decode_error_s2m.w.ready);
      axil_s2m.write.b <= (valid => write_decode_error_s2m.b.valid,
                           resp => axi_resp_decerr);
    elsif write_slave_select = slave_not_selected_idx then
      -- Wait for the master to assert address valid so that we can select the correct slave
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
  select_read : block
    type state_t is (waiting, decode_error, reading);
    signal state : state_t := waiting;
  begin
    select_read_slave : process
      variable decoded_idx : integer range 0 to decode_failed;
    begin
      wait until rising_edge(clk);

      case state is
        when waiting =>
          if axil_m2s.read.ar.valid then
            decoded_idx := decode(axil_m2s.read.ar.addr, slave_addrs);

            if decoded_idx = decode_failed then
              read_slave_select <= slave_decode_error_idx;

              -- Complete the AR transaction.
              -- Note that m2s valid is high, so transaction will occur straight away.
              assert not axil_s2m.read.ar.ready;
              read_decode_error_s2m.ar.ready <= '1';

              assert not axil_s2m.read.r.valid;
              read_decode_error_s2m.r.valid <= '1';

              state <= decode_error;
            else
              read_slave_select <= decoded_idx;
              state <= reading;
            end if;
          end if;

        when decode_error =>
          read_decode_error_s2m.ar.ready <= '0';

          if axil_m2s.read.r.ready and axil_s2m.read.r.valid then
            read_decode_error_s2m.r.valid <= '0';

            read_slave_select <= slave_not_selected_idx;
            state <= waiting;
          end if;

        when reading =>
          if axil_m2s.read.r.ready and axil_s2m.read.r.valid then
            read_slave_select <= slave_not_selected_idx;
            state <= waiting;
          end if;
      end case;
    end process;
  end block;


  ------------------------------------------------------------------------------
  select_write : block
    type state_t is (waiting, decode_error_w, decode_error_b, writing);
    signal state : state_t := waiting;
  begin
    select_write_slave : process
      variable decoded_idx : integer range 0 to decode_failed;
    begin
      wait until rising_edge(clk);

      case state is
        when waiting =>
          if axil_m2s.write.aw.valid then
            decoded_idx := decode(axil_m2s.write.aw.addr, slave_addrs);

            if decoded_idx = decode_failed then
              write_slave_select <= slave_decode_error_idx;

              -- Complete the AW transaction.
              -- Note that m2s valid is high, so transaction will occur straight away.
              assert not axil_s2m.write.aw.ready;
              write_decode_error_s2m.aw.ready <= '1';

              assert not axil_s2m.write.w.ready;
              write_decode_error_s2m.w.ready <= '1';

              state <= decode_error_w;
            else
              write_slave_select <= decoded_idx;
              state <= writing;
            end if;
          end if;

        when decode_error_w =>
          write_decode_error_s2m.aw.ready <= '0';

          if axil_s2m.write.w.ready and axil_m2s.write.w.valid then
            write_decode_error_s2m.w.ready <= '0';

            assert not axil_s2m.write.b.valid;
            write_decode_error_s2m.b.valid <= '1';

            state <= decode_error_b;
          end if;

        when decode_error_b =>
          if axil_m2s.write.b.ready and axil_s2m.write.b.valid then
            write_decode_error_s2m.b.valid <= '0';

            write_slave_select <= slave_not_selected_idx;
            state <= waiting;
          end if;

        when writing =>
          if axil_m2s.write.b.ready and axil_s2m.write.b.valid then
            write_slave_select <= slave_not_selected_idx;
            state <= waiting;
          end if;
      end case;
    end process;
  end block;

end architecture;
