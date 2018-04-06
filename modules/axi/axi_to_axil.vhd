-- @brief Convert AXI transfers to AXI-Lite transfers, along with some checks.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.math_pkg.all;

use work.axi_pkg.all;
use work.axil_pkg.all;


entity axi_to_axil is
  generic (
    data_width : integer
  );
  port (
    clk : in std_logic;

    axi_read_m2s : in axi_read_m2s_t := axi_read_m2s_init;
    axi_read_s2m : out axi_read_s2m_t := axi_read_s2m_init;

    axi_write_m2s : in axi_write_m2s_t := axi_write_m2s_init;
    axi_write_s2m : out axi_write_s2m_t := axi_write_s2m_init;

    axil_read_m2s : out axil_read_m2s_t := axil_read_m2s_init;
    axil_read_s2m : in axil_read_s2m_t := axil_read_s2m_init;

    axil_write_m2s : out axil_write_m2s_t := axil_write_m2s_init;
    axil_write_s2m : in axil_write_s2m_t := axil_write_s2m_init
  );
end entity;

architecture a of axi_to_axil is

  constant len : integer := 0;
  constant size : integer := log2(data_width / 8);

  subtype data_rng is integer range data_width - 1 downto 0;
  subtype strb_rng is integer range data_width / 8 - 1 downto 0;

  signal read_error, write_error : boolean := false;

begin

  ------------------------------------------------------------------------------
  axil_read_m2s.ar.valid <= axi_read_m2s.ar.valid;
  axil_read_m2s.ar.addr <= axi_read_m2s.ar.addr;

  axi_read_s2m.ar.ready <= axil_read_s2m.ar.ready;

  axil_read_m2s.r.ready <= axi_read_m2s.r.ready;

  axi_read_s2m.r.valid <= axil_read_s2m.r.valid;
  axi_read_s2m.r.data(data_rng) <= axil_read_s2m.r.data(data_rng);
  axi_read_s2m.r.resp <= axi_resp_slverr when read_error else axil_read_s2m.r.resp;
  axi_read_s2m.r.last <= '1';


  ------------------------------------------------------------------------------
  axil_write_m2s.aw.valid <= axi_write_m2s.aw.valid;
  axil_write_m2s.aw.addr <= axi_write_m2s.aw.addr;

  axi_write_s2m.aw.ready <= axil_write_s2m.aw.ready;

  axil_write_m2s.w.valid <= axi_write_m2s.w.valid;
  axil_write_m2s.w.data(data_rng) <= axi_write_m2s.w.data(data_rng);
  axil_write_m2s.w.strb(strb_rng) <= axi_write_m2s.w.strb(strb_rng);

  axi_write_s2m.w.ready <= axil_write_s2m.w.ready;


  ------------------------------------------------------------------------------
  axil_write_m2s.b.ready <= axi_write_m2s.b.ready;

  axi_write_s2m.b.valid <= axil_write_s2m.b.valid;
  axi_write_s2m.b.resp <= axi_resp_slverr when write_error else axil_write_s2m.b.resp;


  ------------------------------------------------------------------------------
  check_for_bus_error : process
  begin
    wait until rising_edge(clk);

    -- If an error occurs the bus will return an error not only for the offending transaction, but for all upcoming transactions as well.
    -- The software making the memory access will usually hard crash with "Bus error" message if the AXI bus returns an error.
    -- Hence it should not be a problem to block the bus forever.

    if (axi_write_m2s.aw.valid and axi_write_s2m.aw.ready) = '1' then
      if to_integer(unsigned(axi_write_m2s.aw.len)) /= len or to_integer(unsigned(axi_write_m2s.aw.size)) /= size then
        write_error <= true;
      end if;
    end if;

    if (axi_read_m2s.ar.valid and axi_read_s2m.ar.ready) = '1' then
      if to_integer(unsigned(axi_read_m2s.ar.len)) /= len or to_integer(unsigned(axi_read_m2s.ar.size)) /= size then
        read_error <= true;
      end if;
    end if;
  end process;

end architecture;
