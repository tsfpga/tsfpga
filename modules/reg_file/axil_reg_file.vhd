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

    axil_m2s : in axil_m2s_t;
    axil_s2m : out axil_s2m_t := (read => (ar => (ready => '1'), r => axil_s2m_r_init), write => (aw => (ready => '1'), w => axil_s2m_w_init, b => axi_s2m_b_init));

    reg_values_in : in reg_vec_t(regs'range) := (others => (others => '0'));
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
          if axil_m2s.read.ar.valid and axil_s2m.read.ar.ready then
            axil_s2m.read.ar.ready <= '0';
            addr <= axil_m2s.read.ar.addr;
            state <= stall;
          end if;

        when stall =>
          -- Read address decode is pipelined one step, so we need to stall one cycle.
          axil_s2m.read.r.valid <= '1';
          state <= r;

        when r =>
          if axil_m2s.read.r.ready and axil_s2m.read.r.valid then
            axil_s2m.read.ar.ready <= '1';
            axil_s2m.read.r.valid <= '0';
            state <= ar;
          end if;
      end case;
    end process;

    read : process
    begin
      wait until rising_edge(clk);

      axil_s2m.read.r.resp <= axi_resp_slverr;

      for list_idx in regs'range loop
        if is_read_type(regs(list_idx).reg_type) then
          if match(addr, addr_and_mask_vec(list_idx)) then
            axil_s2m.read.r.resp <= axi_resp_okay;

            if is_fabric_gives_value_type(regs(list_idx).reg_type) then
              axil_s2m.read.r.data(reg_values(0)'range) <= reg_values_in(list_idx);
            else
              axil_s2m.read.r.data(reg_values(0)'range) <= reg_values(list_idx);
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
          if axil_m2s.write.aw.valid and axil_s2m.write.aw.ready then
            axil_s2m.write.aw.ready <= '0';
            axil_s2m.write.w.ready <= '1';
            addr <= axil_m2s.write.aw.addr;
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

      reg_was_written <= (others => '0');

      for list_idx in regs'range loop
        if is_write_pulse_type(regs(list_idx).reg_type) then
          reg_values(list_idx) <= (others => '0');
        end if;
      end loop;

      axil_s2m.write.b.resp <= axi_resp_slverr;

      for list_idx in regs'range loop
        if is_write_type(regs(list_idx).reg_type) then
          if match(addr, addr_and_mask_vec(list_idx)) then
            axil_s2m.write.b.resp <= axi_resp_okay;

            if axil_m2s.write.w.valid and axil_s2m.write.w.ready then
              reg_values(list_idx) <= axil_m2s.write.w.data(reg_values(0)'range);
              reg_was_written(list_idx) <= '1';
            end if;
          end if;
        end if;
      end loop;
    end process;
  end block;

end architecture;
