-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Constants/types/functions for a general MMCM wrapper.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.types_pkg.all;
use common.time_pkg.all;


package mmcm_wrapper_pkg is

  constant max_num_output_clocks : positive := 7;

  ------------------------------------------------------------------------------
  -- Value 0 means it is disabled. The actual value has to be 1 or greater.
  constant mmcm_output_divide_disabled : real := 0.0;

  subtype mmcm_output_divide_t is real range 0.0 to 128.0;
  type mmcm_output_divide_vec_t is array (integer range <>) of mmcm_output_divide_t;

  type mmcm_parameters_t is record
    input_frequency_hz : real;
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
    output_divide : mmcm_output_divide_vec_t(max_num_output_clocks - 1 downto 0);
    -- Optionally enable phase shift of the result clocks.
    -- The phase shift is specified in degrees relative to the output period.
    -- I.e: 360 * phase_shift_ns / output_period_ns.
    -- This is how it is specified in the Vivado Clocking Wizard also.
    -- The wrapper will printout to console how many nanoseconds the degree value corresponds to.
    output_phase_shift_degrees : real_vec_t(max_num_output_clocks - 1 downto 0);
  end record;
  constant mmcm_parameters_init : mmcm_parameters_t := (
    input_frequency_hz => 1.0,
    multiply => 2.0,
    divide => 1,
    output_divide => (others => mmcm_output_divide_disabled),
    output_phase_shift_degrees => (others => 0.0)
  );
  ------------------------------------------------------------------------------

  ------------------------------------------------------------------------------
  -- A data structure where we save all values that are relevant for the MMCM.
  -- It's not a great data structure since many fields are redundant, i.e. they can be calculated
  -- from the others.
  -- But having them all calculated in one place and then be available everywhere is quite handy.
  type mmcm_clock_attributes_t is record
    is_enabled : boolean;
    output_divide : real range 1.0 to 128.0;
    --
    phase_shift_degrees : real;
    phase_shift_ns : real;
    phase_shift : time;
    -- These three will not have valid values if 'is_enabled' is false.
    frequency_hz : real;
    period_ns : real;
    period : time;
  end record;
  constant mmcm_clock_attributes_init : mmcm_clock_attributes_t := (
    is_enabled=>false, output_divide=>1.0, phase_shift=>0 fs, period=>0 fs, others=>0.0
  );
  type mmcm_clock_attributes_vec_t is array (integer range <>) of mmcm_clock_attributes_t;

  type mmcm_attributes_t is record
    input_frequency_hz : real;
    input_period_ns : real range 0.1 to 100.0;
    input_period : time;
    -- See the 'mmcm_parameters_t' type above for documentation of these two.
    multiply : real range 2.0 to 64.0;
    divide : positive range 1 to 106;
    -- Settings for the different outputs.
    outputs : mmcm_clock_attributes_vec_t(mmcm_parameters_init.output_divide'range);
  end record;
  constant mmcm_attributes_init : mmcm_attributes_t := (
    input_frequency_hz=>1.0,
    input_period_ns=>1.0,
    input_period=>1 fs,
    multiply=>mmcm_parameters_init.multiply,
    divide=>mmcm_parameters_init.divide,
    outputs=>(others=>mmcm_clock_attributes_init)
  );

  function calculate_attributes(parameters : mmcm_parameters_t) return mmcm_attributes_t;
  ------------------------------------------------------------------------------

  ------------------------------------------------------------------------------
  -- Component for the MMCM primitive wrapper so it can be instantiated as a block box,
  -- meaning our design can be simulated even when we don't have access to
  -- Vivado simulation libraries.
  component mmcm_primitive is
    generic (
      -- Should be given by the 'calculate_attributes()' function based on a
      -- 'mmcm_parameters_t' set.
      attributes : mmcm_attributes_t
    );
    port (
      input_clk : in std_ulogic;
      result_clk : out std_ulogic_vector(attributes.outputs'range) := (others => '0');
      locked : out std_ulogic := '0'
    );
  end component;
  ------------------------------------------------------------------------------

end;

package body mmcm_wrapper_pkg is

  ------------------------------------------------------------------------------
  function calculate_attributes(parameters : mmcm_parameters_t) return mmcm_attributes_t is
    variable result : mmcm_attributes_t := (
      input_frequency_hz => parameters.input_frequency_hz,
      input_period_ns => 1.0e9 / parameters.input_frequency_hz,
      input_period => to_period(frequency_hz=>parameters.input_frequency_hz),
      --
      multiply => parameters.multiply,
      divide => parameters.divide,
      --
      outputs => (others => mmcm_clock_attributes_init)
    );
  begin
    for clock_index in result.outputs'range loop
      if parameters.output_divide(clock_index) /= mmcm_output_divide_disabled then
        result.outputs(clock_index).output_divide := parameters.output_divide(clock_index);
        result.outputs(clock_index).is_enabled := true;

        result.outputs(clock_index).frequency_hz := (
          (parameters.input_frequency_hz * parameters.multiply)
          / (real(parameters.divide) * result.outputs(clock_index).output_divide)
        );
        result.outputs(clock_index).period_ns := 1.0e9 / result.outputs(clock_index).frequency_hz;
        result.outputs(clock_index).period := to_period(
          frequency_hz=>result.outputs(clock_index).frequency_hz
        );

        result.outputs(clock_index).phase_shift_degrees := (
          parameters.output_phase_shift_degrees(clock_index)
        );
        result.outputs(clock_index).phase_shift_ns := (
          result.outputs(clock_index).period_ns
          * result.outputs(clock_index).phase_shift_degrees
          / 360.0
        );
        result.outputs(clock_index).phase_shift := ns_to_time(
          value_ns=>result.outputs(clock_index).phase_shift_ns
        );
      else
        -- Default generic value in the primitive instance.
        result.outputs(clock_index).output_divide := 1.0;
      end if;
    end loop;

    return result;
  end function;
  ------------------------------------------------------------------------------

end;
