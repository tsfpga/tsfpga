-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Clock domain crossing for an AXI read bus.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.attribute_pkg.all;

library fifo;

use work.axi_pkg.all;


entity axi_read_cdc is
  generic (
    id_width : natural;
    addr_width : positive;
    data_width : positive;
    address_fifo_depth : positive;
    address_fifo_ram_type : ram_style_t := ram_style_auto;
    data_fifo_depth : positive;
    data_fifo_ram_type : ram_style_t := ram_style_auto
  );
  port (
    clk_input : in std_logic;
    input_m2s : in axi_read_m2s_t;
    input_s2m : out axi_read_s2m_t := axi_read_s2m_init;
    --
    clk_output : in std_logic;
    output_m2s : out axi_read_m2s_t := axi_read_m2s_init;
    output_s2m : in axi_read_s2m_t
  );
end entity;

architecture a of axi_read_cdc is

begin

  ------------------------------------------------------------------------------
  axi_address_inst : entity work.axi_address_fifo
    generic map (
      id_width => id_width,
      addr_width => addr_width,
      asynchronous => true,
      depth => address_fifo_depth,
      ram_type => address_fifo_ram_type
    )
    port map (
      clk => clk_output,
      --
      input_m2s => input_m2s.ar,
      input_s2m => input_s2m.ar,
      --
      output_m2s => output_m2s.ar,
      output_s2m => output_s2m.ar,
      --
      clk_input => clk_input
    );


  ------------------------------------------------------------------------------
  axi_r_fifo_inst : entity work.axi_r_fifo
    generic map (
      id_width => id_width,
      data_width => data_width,
      asynchronous => true,
      depth => data_fifo_depth,
      ram_type => data_fifo_ram_type
    )
    port map (
      clk => clk_output,
      --
      input_m2s => input_m2s.r,
      input_s2m => input_s2m.r,
      --
      output_m2s => output_m2s.r,
      output_s2m => output_s2m.r,
      --
      clk_input => clk_input
    );

end architecture;
