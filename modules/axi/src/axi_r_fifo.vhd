-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- FIFO for AXI read response channel (R). Can be used as clock crossing by setting
-- the "asynchronous" generic.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.attribute_pkg.all;

library fifo;

use work.axi_pkg.all;


entity axi_r_fifo is
  generic (
    id_width : natural;
    data_width : positive;
    asynchronous : boolean;
    depth : natural := 16;
    almost_full_level : natural := depth;
    ram_type : ram_style_t := ram_style_auto
  );
  port (
    clk : in std_logic;
    --
    input_m2s : in axi_m2s_r_t;
    input_s2m : out axi_s2m_r_t := axi_s2m_r_init;
    --
    output_m2s : out axi_m2s_r_t := axi_m2s_r_init;
    output_s2m : in axi_s2m_r_t;
    --
    almost_full : out std_logic := '0';
    -- Only need to assign the clock if generic asynchronous is "True"
    clk_input : in std_logic := '0'
  );
end entity;

architecture a of axi_r_fifo is

begin

  passthrough_or_fifo : if depth = 0 generate
    output_m2s <= input_m2s;
    input_s2m <= output_s2m;

  else generate

    constant r_width : integer := axi_s2m_r_sz(data_width, id_width);

    signal read_valid : std_logic := '0';
    signal read_data, write_data : std_logic_vector(r_width - 1 downto 0);

  begin

    ------------------------------------------------------------------------------
    assign : process(all)
    begin
      input_s2m <= to_axi_s2m_r(read_data, data_width, id_width);
      input_s2m.valid <= read_valid;

      write_data <= to_slv(output_s2m, data_width, id_width);
    end process;


    ------------------------------------------------------------------------------
    fifo_gen : if asynchronous generate
    begin

      afifo_inst : entity fifo.afifo
        generic map (
          width => r_width,
          depth => depth,
          almost_full_level => almost_full_level,
          ram_type => ram_type
        )
        port map(
          clk_read => clk_input,
          read_ready => input_m2s.ready,
          read_valid => read_valid,
          read_data => read_data,
          --
          clk_write => clk,
          write_ready => output_m2s.ready,
          write_valid => output_s2m.valid,
          write_data => write_data,
          write_almost_full => almost_full
        );

    else generate

      fifo_inst : entity fifo.fifo
        generic map (
          width => r_width,
          depth => depth,
          almost_full_level => almost_full_level,
          ram_type => ram_type
        )
        port map(
          clk => clk,
          --
          almost_full => almost_full,
          --
          read_ready => input_m2s.ready,
          read_valid => read_valid,
          read_data => read_data,
          --
          write_ready => output_m2s.ready,
          write_valid => output_s2m.valid,
          write_data => write_data
        );

    end generate;

  end generate;

end architecture;
