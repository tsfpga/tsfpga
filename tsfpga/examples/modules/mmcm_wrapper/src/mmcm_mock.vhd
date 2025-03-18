-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Mock behavior for an MMCM.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.time_pkg.all;
use common.types_pkg.all;

use work.mmcm_wrapper_pkg.all;


entity mmcm_mock is
  generic (
    settings : mmcm_settings_t
  );
  port (
    result_clk : out std_ulogic_vector(settings.outputs'range) := (others => '0');
    locked : out std_ulogic := '0'
  );
end entity;

architecture a of mmcm_mock is

  constant input_clk_period : time := to_time(value_s=>settings.input_clk_period_ns / 1.0e9);

  function find_most_negative_phase_shift_ns return real is
    variable result_ns : real := 0.0;
  begin
    for settings_index in settings.outputs'range loop
      if settings.outputs(settings_index).is_enabled then
        result_ns := minimum(result_ns, settings.outputs(settings_index).phase_shift_ns);
      end if;
    end loop;

    return result_ns;
  end function;
  constant most_negative_phase_shift_ns : real := find_most_negative_phase_shift_ns;
  constant most_negative_phase_shift : time := to_time(
    value_s=>most_negative_phase_shift_ns / 1.0e9
  );

begin

  locked <= transport '1' after 10 * input_clk_period;


  ------------------------------------------------------------------------------
  result_clk_gen : for result_index in result_clk'range generate

    ------------------------------------------------------------------------------
    is_enabled_gen : if settings.outputs(result_index).is_enabled generate
      constant period : time := to_time(value_s=>settings.outputs(result_index).period_ns / 1.0e9);
      constant absolute_phase_shift : time := to_time(
        value_s=>settings.outputs(result_index).phase_shift_ns / 1.0e9
      );
      constant relative_phase_shift : time := absolute_phase_shift - most_negative_phase_shift;

      signal base_clock : std_ulogic := '0';

    begin

      base_clock <= not base_clock after period / 2;

      result_clk(result_index) <= transport base_clock after relative_phase_shift;

    end generate;

  end generate;

end architecture;
