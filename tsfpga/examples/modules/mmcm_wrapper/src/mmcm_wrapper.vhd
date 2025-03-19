-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Generic wrapper around an AMD MMCM primitive.
-- Can be simulated even when Vivado simulation libraries are not available by setting
-- the ``use_mock`` generic.
--
-- It is recommended to inspect the simulation console output to verify the MMCM settings.
-- The entity will print a lot of information about the result frequencies, phase shifts, etc.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.types_pkg.all;

library resync;

use work.mmcm_wrapper_pkg.all;


entity mmcm_wrapper is
  generic (
    input_clk_frequency_hz : real;
    -- MMCM input clock division.
    -- Called 'CLKFBOUT_MULT_F' in the Vivado Clocking Wizard and in the primitive component.
    -- Called 'M' in AMD document UG472.
    multiply : real range 2.0 to 64.0;
    -- MMCM input clock multiplication.
    -- Called 'DIVCLK_DIVIDE' in the Vivado Clocking Wizard and in the primitive component.
    -- Called 'D' in AMD document UG472.
    divide : positive range 1 to 106;
    -- MMCM output clock division, one value for each result clock.
    -- Called 'CLKOUT*_DIVIDE' in the Vivado Clocking Wizard and in the primitive component.
    -- Called 'O' in AMD document UG472.
    -- Note that only index zero may be a non-integer value.
    -- Leaving either of these values at its default value of zero will make that result
    -- clock disabled. The actual value that the user sets has to be 1 or greater.
    output_divide : mmcm_output_divide_vec_t(6 downto 0) := (others => mmcm_output_divide_disabled);
    -- Optionally enable phase shift of the result clocks.
    -- Specify each value either in nanoseconds or in degrees (not both).
    output_phase_shift_ns : real_vec_t(6 downto 0) := (others => 0.0);
    output_phase_shift_degrees : real_vec_t(6 downto 0) := (others => 0.0);
    -- Optionally enable the use of a mock MMCM.
    -- This is useful for simulation where the MMCM primitive is not available.
    -- It will also be a lot faster in terms of execution time.
    use_mock : boolean := false
  );
  port (
    input_clk : in std_ulogic;
    -- Flattened rather than vector since partial 'open' in the port map is not allowed in VHDL.
    result0_clk : out std_ulogic := '0';
    result1_clk : out std_ulogic := '0';
    result2_clk : out std_ulogic := '0';
    result3_clk : out std_ulogic := '0';
    result4_clk : out std_ulogic := '0';
    result5_clk : out std_ulogic := '0';
    result6_clk : out std_ulogic := '0';
    --# {{}}
    -- Clock must be assigned in order to get the 'locked' signal.
    -- Can be one of the result clocks or any other clock.
    status_clk : in std_ulogic := '0';
    locked : out std_ulogic := '0'
  );
end entity;

architecture a of mmcm_wrapper is

  signal locked_int : std_ulogic := '0';

begin

  ----------------------------------------------------------------------------
  mmcm_block : block

    constant mmcm_f_vco_hz : real := input_clk_frequency_hz * multiply / real(divide);

    impure function calculate_settings return mmcm_settings_t is
      variable result : mmcm_settings_t := (
        input_clk_period_ns => 1.0e9 / input_clk_frequency_hz,
        multiply => multiply,
        divide => divide,
        outputs => (others => mmcm_clock_settings_init)
      );
    begin
      for result_index in result.outputs'range loop
        result.outputs(result_index).is_enabled := (
          output_divide(result_index) /= mmcm_output_divide_disabled
        );

        if result.outputs(result_index).is_enabled then
          result.outputs(result_index).output_divide := output_divide(result_index);

          result.outputs(result_index).frequency_hz := mmcm_f_vco_hz / output_divide(result_index);
          result.outputs(result_index).period_ns := (
            1.0e9 / result.outputs(result_index).frequency_hz
          );

          if output_phase_shift_ns(result_index) /= 0.0 then
            assert output_phase_shift_degrees(result_index) = 0.0
              report "Specify phase shift either in ns or degrees, NOT both"
              severity failure;

            result.outputs(result_index).phase_shift_ns := output_phase_shift_ns(result_index);
            result.outputs(result_index).phase_shift_degrees := (
              360.0 * output_phase_shift_ns(result_index) / result.outputs(result_index).period_ns
            );

          elsif output_phase_shift_degrees(result_index) /= 0.0 then
            assert output_phase_shift_ns(result_index) = 0.0
              report "Specify phase shift either in ns or degrees, NOT both"
              severity failure;

            result.outputs(result_index).phase_shift_degrees := output_phase_shift_degrees(
              result_index
            );
            result.outputs(result_index).phase_shift_ns := (
              result.outputs(result_index).period_ns
              * output_phase_shift_degrees(result_index)
              / 360.0
            );
          end if;
        else
          -- Default generic value in the primitive instance.
          result.outputs(result_index).output_divide := 1.0;
        end if;
      end loop;

      return result;
    end function;
    constant settings : mmcm_settings_t := calculate_settings;

    signal result_clk_int : std_ulogic_vector(settings.outputs'range) := (others => '0');

  begin

    ----------------------------------------------------------------------------
    print_info : process
    begin
      report (
        "MMCM synthesis from input frequency "
        & real'image(input_clk_frequency_hz)
        & " Hz ("
        & real'image(settings.input_clk_period_ns)
        & " ns) to VCO frequency "
        & real'image(mmcm_f_vco_hz)
        & " Hz."
      );

      for result_index in settings.outputs'range loop
        if settings.outputs(result_index).is_enabled then
          report "--------------------------------";
          report "MMCM output " & integer'image(result_index);

          report (
            " - Frequency "
            & real'image(settings.outputs(result_index).frequency_hz)
            & " Hz ("
            & real'image(settings.outputs(result_index).period_ns)
            & " ns)."
          );

          if settings.outputs(result_index).phase_shift_degrees /= 0.0 then
            report (" - Phase shift "
              & real'image(settings.outputs(result_index).phase_shift_degrees)
              & " degrees ("
              & real'image(output_phase_shift_ns(result_index))
              & " ns)."
            );
          end if;
        end if;
      end loop;

      wait;
    end process;


    ----------------------------------------------------------------------------
    mock_or_mmcm_gen : if use_mock generate

      ----------------------------------------------------------------------------
      mmcm_mock_inst : entity work.mmcm_mock
        generic map (
          settings => settings
        )
        port map (
          result_clk => result_clk_int,
          locked => locked_int
        );


    ----------------------------------------------------------------------------
    else generate

      ----------------------------------------------------------------------------
      -- Use black-box component instantiation so this code can be used even
      -- when unisim is not available.
      mmcm_primitive_inst : mmcm_primitive
        generic map (
          settings => settings
        )
        port map (
          input_clk => input_clk,
          result_clk => result_clk_int,
          locked => locked_int
        );

    end generate;

    result0_clk <= result_clk_int(0);
    result1_clk <= result_clk_int(1);
    result2_clk <= result_clk_int(2);
    result3_clk <= result_clk_int(3);
    result4_clk <= result_clk_int(4);
    result5_clk <= result_clk_int(5);
    result6_clk <= result_clk_int(6);

  end block;


  ----------------------------------------------------------------------------
  stable_lock_block : block
    -- Could be made a generic when necessary.
    -- This is quite a big value but since it can be implemented in SRL it is very cheap.
    constant locked_pipe_length : positive := 128;

    signal locked_non_metastable : std_ulogic := '0';
    signal locked_pipe : std_ulogic_vector(locked_pipe_length - 1 downto 0) := (others => '0');
  begin

    ----------------------------------------------------------------------------
    -- Unclear which clock domain the 'locked' signal is in.
    -- Resync just in case so it is not metastable.
    resync_level_inst : entity resync.resync_level
      generic map (
        enable_input_register => false
      )
      port map (
        data_in => locked_int,
        --
        clk_out => status_clk,
        data_out => locked_non_metastable
      );


    ----------------------------------------------------------------------------
    -- We have seen glitches where lock is lost on startup.
    -- This is a simple way to filter this out.
    stable_lock : process
    begin
      wait until rising_edge(status_clk);

      locked_pipe <= (
        locked_non_metastable & locked_pipe(locked_pipe'left downto locked_pipe'right + 1)
      );
    end process;

    locked <= and locked_pipe;

  end block;

end architecture;
