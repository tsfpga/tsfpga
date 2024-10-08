-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Parameterization and instantiation from AMD Vivado clocking wizard IP with
-- settings 100 MHz -> 25 MHz.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library unisim;
use unisim.vcomponents.all;


entity mmcm_wrapper is
  generic (
    clk_frequency_hz : real
  );
  port (
    clk : in std_ulogic;
    clk_div4 : out std_ulogic := '0'
  );
end entity;

architecture a of mmcm_wrapper is

  constant clk_period_ns : real := 1.0e9 / clk_frequency_hz;

  constant mmcm_d : positive := 1;
  constant mmcm_m : real := 9.125;

  constant mmcm_f_vco_hz : real := clk_frequency_hz * mmcm_m / real(mmcm_d);

  constant mmcm_o : real := 36.5;

  constant result_clk_frequency_hz : real := mmcm_f_vco_hz / mmcm_o;

  signal clk_feedback, clk_feedback_buf, clk_div4_unbuffered : std_logic := '0';

begin

  assert result_clk_frequency_hz = clk_frequency_hz / 4.0
    report "MMCM parameters are not correct"
    severity failure;


  ----------------------------------------------------------------------------
  MMCME2_ADV_inst : MMCME2_ADV
    generic map (
      DIVCLK_DIVIDE => mmcm_d,
      CLKFBOUT_MULT_F => mmcm_m,
      CLKOUT0_DIVIDE_F => mmcm_o,
      CLKIN1_PERIOD => clk_period_ns
    )
    port map (
      CLKFBOUT => clk_feedback,
      CLKOUT0 => clk_div4_unbuffered,
      -- Input clock control.
      -- Tied to always select the primary input clock
      CLKFBIN => clk_feedback_buf,
      CLKIN1 => clk,
      CLKIN2 => '0',
      CLKINSEL => '1',
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
      RST => '0'
    );


  ----------------------------------------------------------------------------
  clk_feedback_bufg_inst : BUFG
    port map (
      I => clk_feedback,
      O => clk_feedback_buf
    );


  ----------------------------------------------------------------------------
  clk_div4_bufg_inst : BUFG
    port map (
      I => clk_div4_unbuffered,
      O => clk_div4
    );

end architecture;
