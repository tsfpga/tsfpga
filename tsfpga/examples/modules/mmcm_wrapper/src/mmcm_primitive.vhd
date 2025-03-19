-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Thin wrapper around an MMCM primitive component.
-- Depends on the ``unisim`` library from AMD.
--
--
-- MMCM settings
-- _____________
--
-- When "Phase alignment" is selected in the IP wizard, the feedback goes through a BUFG.
-- But when it is not selected, there is no BUFG on the feedback path.
--
-- Setting "Minimize output jitter" in the IP wizard corresponds to a ``BANDWIDTH`` generic
-- of ``HIGH``.
-- Similarly, "Minimize input jitter" results in the the generic setting ``LOW``.
--
--
-- Finding invalid settings early
-- ______________________________
--
-- Simulate this entity and inspect the printouts for things like e.g. this:
--
--   Warning : [Unisim MMCME2_ADV-103] Attribute CLKOUT2_PHASE of MMCME2_ADV is set to -8.38185e1.
--   Real phase shifting is -8.333333333333331e1.
--   Required phase shifting can not be reached.
--
-- This is just a warning in simulation but will result in a DRC error at the end of the build.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library unisim;
use unisim.vcomponents.all;

library common;
use common.types_pkg.all;

use work.mmcm_wrapper_pkg.all;


entity mmcm_primitive is
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
end entity;

architecture a of mmcm_primitive is

  signal clk_feedback_unbuffered, clk_feedback_buffered : std_logic := '0';
  signal output_clk_unbuffered : std_logic_vector(result_clk'range) := (others => '0');

begin

  ----------------------------------------------------------------------------
  assertions_gen : for result_index in 1 to attributes.outputs'high generate

    assert is_integer(attributes.outputs(result_index).output_divide)
      report "Only output zero may have a non-integer divide value"
      severity failure;

  end generate;


  ----------------------------------------------------------------------------
  MMCME2_ADV_inst : MMCME2_ADV
    generic map (
      CLKFBOUT_MULT_F => attributes.multiply,
      DIVCLK_DIVIDE => attributes.divide,
      CLKIN1_PERIOD => attributes.input_period_ns,
      --
      CLKOUT0_DIVIDE_F => attributes.outputs(0).output_divide,
      CLKOUT1_DIVIDE => integer(attributes.outputs(1).output_divide),
      CLKOUT2_DIVIDE => integer(attributes.outputs(2).output_divide),
      CLKOUT3_DIVIDE => integer(attributes.outputs(3).output_divide),
      CLKOUT4_DIVIDE => integer(attributes.outputs(4).output_divide),
      CLKOUT5_DIVIDE => integer(attributes.outputs(5).output_divide),
      CLKOUT6_DIVIDE => integer(attributes.outputs(6).output_divide),
      --
      CLKOUT0_PHASE => attributes.outputs(0).phase_shift_degrees,
      CLKOUT1_PHASE => attributes.outputs(1).phase_shift_degrees,
      CLKOUT2_PHASE => attributes.outputs(2).phase_shift_degrees,
      CLKOUT3_PHASE => attributes.outputs(3).phase_shift_degrees,
      CLKOUT4_PHASE => attributes.outputs(4).phase_shift_degrees,
      CLKOUT5_PHASE => attributes.outputs(5).phase_shift_degrees,
      CLKOUT6_PHASE => attributes.outputs(6).phase_shift_degrees
    )
    port map (
      CLKFBOUT => clk_feedback_unbuffered,
      -- Output clocks.
      CLKOUT0 => output_clk_unbuffered(0),
      CLKOUT1 => output_clk_unbuffered(1),
      CLKOUT2 => output_clk_unbuffered(2),
      CLKOUT3 => output_clk_unbuffered(3),
      CLKOUT4 => output_clk_unbuffered(4),
      CLKOUT5 => output_clk_unbuffered(5),
      CLKOUT6 => output_clk_unbuffered(6),
      -- Input clock control.
      CLKFBIN => clk_feedback_buffered,
      CLKIN1 => input_clk,
      CLKIN2 => '0',
      -- Tied to always select the primary input clock
      CLKINSEL => '1',
      -- Other control and status.
      LOCKED => locked,
      -- Unused ports for dynamic reconfiguration.
      DADDR => (others => '0'),
      DCLK => '0',
      DEN => '0',
      DI => (others => '0'),
      DWE => '0',
      -- Unused ports for dynamic phase shift.
      PSCLK => '0',
      PSEN => '0',
      PSINCDEC => '0',
      -- Other unused control and status signals.
      PWRDWN => '0',
      -- https://docs.amd.com/r/en-US/ug953-vivado-7series-libraries/MMCME2_ADV
      -- "The MMCM automatically locks after power on, no extra reset is required"
      RST => '0'
    );


  ----------------------------------------------------------------------------
  clk_feedback_bufg_inst : BUFG
    port map (
      I => clk_feedback_unbuffered,
      O => clk_feedback_buffered
    );


  ----------------------------------------------------------------------------
  output_buffer_gen : for result_index in result_clk'range generate

    ----------------------------------------------------------------------------
    is_enabled_gen : if attributes.outputs(result_index).is_enabled generate

      ----------------------------------------------------------------------------
      bufg_inst : BUFG
        port map (
          I => output_clk_unbuffered(result_index),
          O => result_clk(result_index)
        );

    end generate;

  end generate;

end architecture;
