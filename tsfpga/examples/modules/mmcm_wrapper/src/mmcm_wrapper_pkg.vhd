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


package mmcm_wrapper_pkg is

  ------------------------------------------------------------------------------
  -- Result is in the same unit as the 'input_frequency'.
  function mmcm_output_frequency(
    input_frequency : real; multiply : real; divide : positive; output_divide : real
  ) return real;
  ------------------------------------------------------------------------------

  ------------------------------------------------------------------------------
  -- Value 0 means it is disabled. The actual value has to be 1 or greater.
  constant mmcm_output_divide_disabled : real := 0.0;

  subtype mmcm_output_divide_t is real range 0.0 to 128.0;
  type mmcm_output_divide_vec_t is array (integer range <>) of mmcm_output_divide_t;
  ------------------------------------------------------------------------------

  ------------------------------------------------------------------------------
  -- A data structure where we save all values that are relevant for the MMCM.
  -- It's not a great data structure since some fields are redundant, i.e. they can be calculated
  -- from the others.
  -- But having them all calculated in one place and then be available everywhere is quite handy.
  type mmcm_clock_settings_t is record
    is_enabled : boolean;
    output_divide : real range 1.0 to 128.0;
    phase_shift_degrees : real;
    phase_shift_ns : real;
    -- These two will not have valid values if 'is_enabled' is false.
    frequency_hz : real;
    period_ns : real;
  end record;
  constant mmcm_clock_settings_init : mmcm_clock_settings_t := (
    is_enabled=>false, output_divide=>1.0, others=>0.0
  );
  type mmcm_clock_settings_vec_t is array (integer range <>) of mmcm_clock_settings_t;

  type mmcm_settings_t is record
    input_clk_period_ns : real range 0.1 to 100.0;
    -- See 'mmcm_wrapper' for documentation of these two.
    multiply : real range 2.0 to 64.0;
    divide : positive range 1 to 106;
    -- Settings for the different outputs.
    outputs : mmcm_clock_settings_vec_t(6 downto 0);
  end record;
  constant mmcm_settings_init : mmcm_settings_t := (
    input_clk_period_ns=>1.0, multiply=>2.0, divide=>1, outputs=>(others=>mmcm_clock_settings_init)
  );
  ------------------------------------------------------------------------------

  ------------------------------------------------------------------------------
  -- Component for the MMCM primitive wrapper so it can be instantiated as a block box,
  -- meaning our design can be simulated even when we don't have access to Vivado simlib.
  component mmcm_primitive is
    generic (
      settings : mmcm_settings_t
    );
    port (
      input_clk : in std_ulogic;
      result_clk : out std_ulogic_vector(settings.outputs'range) := (others => '0');
      locked : out std_ulogic := '0'
    );
  end component;
  ------------------------------------------------------------------------------

end;

package body mmcm_wrapper_pkg is

  ------------------------------------------------------------------------------
  function mmcm_output_frequency(
    input_frequency : real; multiply : real; divide : positive; output_divide : real
  ) return real is
  begin
    return (input_frequency * multiply) / (real(divide) * output_divide);
  end function;
  ------------------------------------------------------------------------------

end;

