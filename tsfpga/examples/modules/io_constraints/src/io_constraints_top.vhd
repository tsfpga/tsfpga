-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;

library axi_lite;
use axi_lite.axi_lite_pkg.all;

library common;
use common.common_pkg.all;
use common.attribute_pkg.all;

library resync;

library artyz7;
use artyz7.block_design_pkg.all;

library mmcm_wrapper;
use mmcm_wrapper.mmcm_wrapper_pkg.all;


entity io_constraints_top is
  port (
    input_source_synchronous_clock : in std_ulogic;
    input_source_synchronous_data : in std_ulogic_vector(3 downto 0);
    --# {{}}
    input_system_synchronous_clock : in std_ulogic;
    input_system_synchronous_data : in std_ulogic_vector(3 downto 0);
    --# {{}}
    ddr : inout zynq7000_ddr_t;
    fixed_io : inout zynq7000_fixed_io_t
  );
end entity;

architecture a of io_constraints_top is

  signal pl_clk : std_ulogic := '0';

  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal s_hp0_m2s : axi_m2s_t := axi_m2s_init;
  signal s_hp0_s2m : axi_s2m_t := axi_s2m_init;

begin

  ------------------------------------------------------------------------------
  input_source_synchronous_block : block
    signal data_p1 : std_ulogic_vector(input_source_synchronous_data'range) := (others => '0');
  begin

    -- Register will be placed in IOB thanks to attribute we set in the constraint file.
    data_p1 <= input_source_synchronous_data when rising_edge(input_source_synchronous_clock);


    -----------------------------------------------------------------------
    resync_twophase_inst : entity resync.resync_twophase
      generic map (
        width => data_p1'length
      )
      port map (
        clk_in => input_source_synchronous_clock,
        data_in => data_p1,
        --
        clk_out => pl_clk,
        -- Assign the data to something that will not get stripped by synthesis.
        data_out => m_gp0_s2m.read.r.data(3 downto 0)
      );

  end block;


  ------------------------------------------------------------------------------
  input_system_synchronous_block : block
    constant mmcm_parameters : mmcm_parameters_t := (
      input_frequency_hz => 125.0e6,
      -- Parameterization from AMD Vivado clocking wizard IP with
      -- settings 125 MHz -> 125 MHz and the below phase shift.
      multiply => 8.0,
      divide => 1,
      output_divide => (0=>8.0, others=>mmcm_output_divide_disabled),
      -- Looking at the printouts from the constraint script, the 'max' value is 2.46 and
      -- the size of the valid window is 3.42.
      -- This would place the center of the window at 4.17 ns, which is equivalent to
      -- (4.17 / 8) * 360 = 188 degrees.
      -- However, looking at the 'report_timing -setup/hold' output, the paths that the clock
      -- and data take do not add the same delay, so we need to adjust the phase shift.
      -- Analyzing the data places the center of the valid window around 6 ns or 270 degrees.
      -- This can also be found simply by trial and error.
      -- As long as the constraint is correct, we don't have to be super scientific in how
      -- we find the appropriate phase shift.
      output_phase_shift_degrees => (0=>270.0, others=>0.0)
    );

    signal capture_clock : std_ulogic := '0';
    signal data_p1 : std_ulogic_vector(input_system_synchronous_data'range) := (others => '0');
  begin

    -- Register will be placed in IOB thanks to attribute we set in the constraint file.
    data_p1 <= input_system_synchronous_data when rising_edge(capture_clock);


    ------------------------------------------------------------------------------
    mmcm_wrapper_inst : entity mmcm_wrapper.mmcm_wrapper
      generic map (
        parameters => mmcm_parameters
      )
      port map (
        input_clk => input_system_synchronous_clock,
        result0_clk => capture_clock
      );


    -----------------------------------------------------------------------
    resync_twophase_inst : entity resync.resync_twophase
      generic map (
        width => data_p1'length
      )
      port map (
        clk_in => capture_clock,
        data_in => data_p1,
        --
        clk_out => pl_clk,
        -- Assign the data to something that will not get stripped by synthesis.
        data_out => m_gp0_s2m.read.r.data(7 downto 4)
      );

  end block;


  ------------------------------------------------------------------------------
  block_design : block
  begin

    ------------------------------------------------------------------------------
    block_design_inst : entity artyz7.block_design_wrapper
      port map (
        m_gp0_m2s => m_gp0_m2s,
        m_gp0_s2m => m_gp0_s2m,
        --
        s_hp0_m2s => s_hp0_m2s,
        s_hp0_s2m => s_hp0_s2m,
        --
        pl_clk => pl_clk,
        --
        ddr => ddr,
        fixed_io => fixed_io
      );

  end block;

end architecture;
