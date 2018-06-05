-- @brief General register file controlled over AXI-Lite

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
    regs : reg_definition_vec_t
  );
  port (
    clk : in std_logic;

    read_m2s : in axil_read_m2s_t;
    read_s2m : out axil_read_s2m_t := (ar => (ready => '1'), r => axil_s2m_r_init);

    write_m2s : in axil_write_m2s_t;
    write_s2m : out axil_write_s2m_t := (aw => (ready => '1'), w => axil_s2m_w_init, b => axi_s2m_b_init);

    reg_values_in : in reg_vec_t(regs'range);
    reg_values_out : out reg_vec_t(regs'range);
    reg_was_written : out std_logic_vector(regs'range) := (others => '0')
  );
end entity;

architecture a of axil_reg_file is

  constant addr_and_mask_vec : addr_and_mask_vec_t := to_addr_and_mask_vec(regs);

  signal reg_values : reg_vec_t(regs'range) := (others => (others => '0'));

begin

  reg_values_out <= reg_values;


  ------------------------------------------------------------------------------
  read : block
    type state_t is (ar, stall, r);
    signal state : state_t := ar;
    signal addr : addr_t;
  begin
    bus_read_fsm : process
    begin
      wait until rising_edge(clk);

      case state is
        when ar =>
          if read_m2s.ar.valid and read_s2m.ar.ready then
            read_s2m.ar.ready <= '0';
            addr <= read_m2s.ar.addr;
            state <= stall;
          end if;

        when stall =>
          -- Read address decode is pipelined one step, so we need to stall one cycle.
          read_s2m.r.valid <= '1';
          state <= r;

        when r =>
          if read_m2s.r.ready and read_s2m.r.valid then
            read_s2m.ar.ready <= '1';
            read_s2m.r.valid <= '0';
            state <= ar;
          end if;
      end case;
    end process;

    read : process
    begin
      wait until rising_edge(clk);

      read_s2m.r.resp <= axi_resp_slverr;

      for list_idx in regs'range loop
        if is_read_type(regs(list_idx).reg_type) then
          if match(addr, addr_and_mask_vec(list_idx)) then
            read_s2m.r.resp <= axi_resp_okay;

            if is_fabric_gives_value_type(regs(list_idx).reg_type) then
              read_s2m.r.data(reg_values(0)'range) <= reg_values_in(list_idx);
            else
              read_s2m.r.data(reg_values(0)'range) <= reg_values(list_idx);
            end if;
          end if;
        end if;
      end loop;
    end process;
  end block;


  ------------------------------------------------------------------------------
  write : block
    type state_t is (aw, w, b);
    signal state : state_t := aw;
    signal addr : addr_t;
  begin
    bus_write_fsm : process
    begin
      wait until rising_edge(clk);

      case state is
        when aw =>
          if write_m2s.aw.valid and write_s2m.aw.ready then
            write_s2m.aw.ready <= '0';
            write_s2m.w.ready <= '1';
            addr <= write_m2s.aw.addr;
            state <= w;
          end if;

        when w =>
          if write_m2s.w.valid and write_s2m.w.ready then
            write_s2m.w.ready <= '0';
            write_s2m.b.valid <= '1';
            state <= b;
          end if;

        when b =>
          if write_m2s.b.ready and write_s2m.b.valid then
            write_s2m.aw.ready <= '1';
            write_s2m.b.valid <= '0';
            state <= aw;
          end if;
      end case;
    end process;

    write : process
    begin
      wait until rising_edge(clk);

      reg_was_written <= (others => '0');

      for list_idx in regs'range loop
        if is_write_pulse_type(regs(list_idx).reg_type) then
          reg_values(list_idx) <= (others => '0');
        end if;
      end loop;

      write_s2m.b.resp <= axi_resp_slverr;

      for list_idx in regs'range loop
        if is_write_type(regs(list_idx).reg_type) then
          if match(addr, addr_and_mask_vec(list_idx)) then
            write_s2m.b.resp <= axi_resp_okay;

            if write_m2s.w.valid and write_s2m.w.ready then
              reg_values(list_idx) <= write_m2s.w.data(reg_values(0)'range);
              reg_was_written(list_idx) <= '1';
            end if;
          end if;
        end if;
      end loop;
    end process;
  end block;

end architecture;
