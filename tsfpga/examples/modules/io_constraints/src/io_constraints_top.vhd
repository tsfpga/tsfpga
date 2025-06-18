-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Example FPGA top-level that showcases different input/output interfaces.
-- See the corresponding constraint files in the 'tcl' folder also for details.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;

library common;
use common.attribute_pkg.all;

library resync;

library artyz7;
use artyz7.block_design_pkg.all;

library mmcm_wrapper;
use mmcm_wrapper.mmcm_wrapper_pkg.all;

library oddr_wrapper;


entity io_constraints_top is
  generic (
    -- Optionally enable the use of mock MMCM/ODDR primitives.
    -- Useful in simulation when Vivado simulation libraries are not available.
    mock_unisim : boolean := false
  );
  port (
    input_source_synchronous_clock : in std_ulogic;
    input_source_synchronous_data : in std_ulogic_vector(3 downto 0);
    --# {{}}
    input_system_synchronous_clock : in std_ulogic;
    input_system_synchronous_data : in std_ulogic_vector(3 downto 0);
    --# {{}}
    input_sink_synchronous_clock : out std_ulogic := '0';
    input_sink_synchronous_data : in std_ulogic_vector(3 downto 0);
    --# {{}}
    output_source_synchronous_clock : out std_ulogic := '0';
    output_source_synchronous_data : out std_ulogic_vector(3 downto 0) := (others => '0');
    --# {{}}
    output_system_synchronous_clock : in std_ulogic;
    output_system_synchronous_data : out std_ulogic_vector(3 downto 0) := (others => '0');
    --# {{}}
    output_sink_synchronous_clock : in std_ulogic;
    output_sink_synchronous_data : out std_ulogic_vector(3 downto 0) := (others => '0');
    --# {{}}
    ddr : inout zynq7000_ddr_t;
    fixed_io : inout zynq7000_fixed_io_t
  );
end entity;

architecture a of io_constraints_top is

  signal pl_clk : std_ulogic := '0';

  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

begin

  ------------------------------------------------------------------------------
  -- See the constraints file 'input_source_synchronous.tcl' in the 'tcl' folder, and the article
  -- https://linkedin.com/pulse/io-timing-constraints-fpgaasic-1-source-synchronous-input-lukas-vik-0xslf
  -- for details.
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
  -- See the constraints file 'input_system_synchronous.tcl' in the 'tcl' folder, and the article
  -- https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-2-system-synchronous-input-lukas-vik-gpnkf
  -- for details.
  input_system_synchronous_block : block
    constant mmcm_parameters : mmcm_parameters_t := (
      input_frequency_hz => 125.0e6,
      -- Parameterization from AMD Vivado clocking wizard IP with
      -- settings 125 MHz -> 125 MHz and the below phase shift.
      multiply => 6.0,
      divide => 1,
      output_divide => (0=>6.0, others=>mmcm_output_divide_disabled),
      -- Looking at the printouts from the constraint script, the 'max' value is 2.46 and
      -- the size of the valid window is 3.42.
      -- This would place the center of the window at 4.17 ns, which is equivalent to
      -- (4.17 / 8) * 360 = 188 degrees.
      -- But the paths that the clock and data take to the capture FF do not add to the same delay.
      -- The clock goes through more buffers and more routing delay, and the MMCM
      -- subtracts roughly 5 ns.
      -- Reasoning about the necessary phase shift based on the min/max values
      -- is not really useful.
      -- I would instead recommend trail and error.
      -- As long as we are confident that the constraint is correct, we don't have to be super
      -- scientific in how we find the appropriate phase shift.
      -- In Vivado you can do e.g.
      --   set mmcm_wrapper "input_system_synchronous_block.mmcm_wrapper_inst"
      --   set mmcm_primitive "${mmcm_wrapper}/mmcm_block.mock_or_mmcm_gen.mmcm_primitive_inst"
      --   set mmcm [get_cells "${mmcm_primitive}/MMCME2_ADV_inst"]
      --   set_property "CLKOUT0_PHASE" -95 ${mmcm}
      -- on an implemented design to test a new shift without rebuilding.
      -- After changing the shift a new timing report will show the updated setup/hold skew.
      -- With this method and some trial and error you can find the phase shift that places the
      -- clock edge in the middle of the valid data window at the FF.
      output_phase_shift_degrees => (0=>-90.0, others=>0.0)
    );

    signal capture_clock : std_ulogic := '0';
    signal data_p1 : std_ulogic_vector(input_system_synchronous_data'range) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    mmcm_wrapper_inst : entity mmcm_wrapper.mmcm_wrapper
      generic map (
        parameters => mmcm_parameters,
        use_mock => mock_unisim
      )
      port map (
        input_clk => input_system_synchronous_clock,
        result0_clk => capture_clock
      );


    -- Register will be placed in IOB thanks to attribute we set in the constraint file.
    data_p1 <= input_system_synchronous_data when rising_edge(capture_clock);


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
  -- See the constraints file 'input_sink_synchronous.tcl' in the 'tcl' folder, and the article
  -- https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-3-sink-synchronous-input-lukas-vik-iuxuf/
  -- for details.
  input_sink_synchronous_block : block
    signal data_p1 : std_ulogic_vector(input_sink_synchronous_data'range) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    -- Use the ODDR primitive for better jitter properties.
    -- Could also just assign 'input_sink_synchronous_clock <= pl_clk;' directly,
    -- would technically work but our valid timing window would be smaller.
    oddr_wrapper_inst : entity oddr_wrapper.oddr_wrapper
      generic map (
        use_mock => mock_unisim
      )
      port map (
        internal_clock => pl_clk,
        output_clocks(0) => input_sink_synchronous_clock
      );

    -- Register will be placed in IOB thanks to attribute we set in the constraint file.
    data_p1 <= input_sink_synchronous_data when rising_edge(pl_clk);

    -- Assign the data to something that will not get stripped by synthesis.
    m_gp0_s2m.read.r.data(11 downto 8) <= data_p1 when rising_edge(pl_clk);

  end block;


  ------------------------------------------------------------------------------
  -- See the constraints file 'output_source_synchronous.tcl' in the 'tcl' folder, and the article
  -- https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-4-source-synchronous-output-lukas-vik-fudxc
  -- for details.
  output_source_synchronous_block : block
    -- See comments in the 'input_system_synchronous' block for details.
    constant mmcm_parameters : mmcm_parameters_t := (
      input_frequency_hz => pl_clk_frequency_hz,
      multiply => 6.0,
      divide => 1,
      output_divide => (0=>6.0, others=>mmcm_output_divide_disabled),
      output_phase_shift_degrees => (0=>-157.5, others=>0.0)
    );

    signal launch_clock : std_ulogic := '0';
    signal data : std_ulogic_vector(output_source_synchronous_data'range) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    -- Use the ODDR primitive for better jitter properties.
    -- Could also just assign 'output_source_synchronous_clock <= pl_clk;' directly,
    -- would technically work but our valid timing window would be smaller.
    oddr_wrapper_inst : entity oddr_wrapper.oddr_wrapper
      generic map (
        use_mock => mock_unisim
      )
      port map (
        internal_clock => pl_clk,
        output_clocks(0) => output_source_synchronous_clock
      );


    ------------------------------------------------------------------------------
    mmcm_wrapper_inst : entity mmcm_wrapper.mmcm_wrapper
      generic map (
        parameters => mmcm_parameters,
        use_mock => mock_unisim
      )
      port map (
        input_clk => pl_clk,
        result0_clk => launch_clock
      );


    -- Register will be placed in IOB thanks to attribute we set in the constraint file.
    output_source_synchronous_data <= data when rising_edge(launch_clock);

    -- Assign some data that will not get stripped by synthesis.
    data <= m_gp0_m2s.write.w.data(3 downto 0) when rising_edge(pl_clk);

  end block;


  ------------------------------------------------------------------------------
  -- See the constraints file 'output_system_synchronous.tcl' in the 'tcl' folder, and the article
  -- https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-5-system-synchronous-output-lukas-vik-bv86f
  -- for details.
  output_system_synchronous_block : block
    constant mmcm_parameters : mmcm_parameters_t := (
      input_frequency_hz => 125.0e6,
      -- Parameterization from AMD Vivado clocking wizard IP with
      -- settings 125 MHz -> 125 MHz and the below phase shift.
      multiply => 6.0,
      divide => 1,
      output_divide => (0=>6.0, others=>mmcm_output_divide_disabled),
      output_phase_shift_degrees => (0=>30.0, others=>0.0)
    );

    signal launch_clock : std_ulogic := '0';
    signal data : std_ulogic_vector(output_system_synchronous_data'range) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    mmcm_wrapper_inst : entity mmcm_wrapper.mmcm_wrapper
      generic map (
        parameters => mmcm_parameters,
        use_mock => mock_unisim
      )
      port map (
        input_clk => output_system_synchronous_clock,
        result0_clk => launch_clock
      );


    -----------------------------------------------------------------------
    resync_twophase_inst : entity resync.resync_twophase
      generic map (
        width => data'length
      )
      port map (
        clk_in => pl_clk,
        -- Assign some data that will not get stripped by synthesis.
        data_in => m_gp0_m2s.write.w.data(7 downto 4),
        --
        clk_out => launch_clock,
        data_out => data
      );

    -- Register will be placed in IOB thanks to attribute we set in the constraint file.
    output_system_synchronous_data <= data when rising_edge(launch_clock);

  end block;


  ------------------------------------------------------------------------------
  -- See the constraints file 'output_sink_synchronous.tcl' in the 'tcl' folder, and the article
  -- https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-6-sink-synchronous-output-lukas-vik-yod6f
  -- for details.
  output_sink_synchronous_block : block
    constant mmcm_parameters : mmcm_parameters_t := (
      input_frequency_hz => 125.0e6,
      -- Parameterization from AMD Vivado clocking wizard IP with
      -- settings 125 MHz -> 125 MHz and the below phase shift.
      multiply => 6.0,
      divide => 1,
      output_divide => (0=>6.0, others=>mmcm_output_divide_disabled),
      output_phase_shift_degrees => (0=>262.5, others=>0.0)
    );

    signal launch_clock : std_ulogic := '0';
    signal data : std_ulogic_vector(output_sink_synchronous_data'range) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    mmcm_wrapper_inst : entity mmcm_wrapper.mmcm_wrapper
      generic map (
        parameters => mmcm_parameters,
        use_mock => mock_unisim
      )
      port map (
        input_clk => output_sink_synchronous_clock,
        result0_clk => launch_clock
      );


    -----------------------------------------------------------------------
    resync_twophase_inst : entity resync.resync_twophase
      generic map (
        width => data'length
      )
      port map (
        clk_in => pl_clk,
        -- Assign some data that will not get stripped by synthesis.
        data_in => m_gp0_m2s.write.w.data(7 downto 4),
        --
        clk_out => launch_clock,
        data_out => data
      );

    -- Register will be placed in IOB thanks to attribute we set in the constraint file.
    output_sink_synchronous_data <= data when rising_edge(launch_clock);

  end block;


  ------------------------------------------------------------------------------
  block_design_inst : entity artyz7.block_design_wrapper
    port map (
      pl_clk => pl_clk,
      --
      m_gp0_m2s => m_gp0_m2s,
      m_gp0_s2m => m_gp0_s2m,
      --
      ddr => ddr,
      fixed_io => fixed_io
    );

end architecture;
