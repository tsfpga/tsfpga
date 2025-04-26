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

library resync;

use work.mmcm_wrapper_pkg.all;


entity mmcm_wrapper is
  generic (
    parameters : mmcm_parameters_t;
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
    -- If 'locked' is not used, the port can be left unassigned.
    status_clk : in std_ulogic := '0';
    locked : out std_ulogic := '0'
  );
end entity;

architecture a of mmcm_wrapper is

  signal locked_int : std_ulogic := '0';

begin

  ----------------------------------------------------------------------------
  mmcm_block : block
    constant attributes : mmcm_attributes_t := calculate_attributes(parameters);

    signal result_clk_int : std_ulogic_vector(attributes.outputs'range) := (others => '0');
  begin

    ----------------------------------------------------------------------------
    print_info : process
      constant mmcm_f_vco_hz : real := (
        attributes.input_frequency_hz * attributes.multiply / real(attributes.divide)
      );
    begin
      report (
        "MMCM synthesis from input frequency "
        & real'image(attributes.input_frequency_hz)
        & " Hz ("
        & real'image(attributes.input_period_ns)
        & " ns) to VCO frequency "
        & real'image(mmcm_f_vco_hz)
        & " Hz."
      );

      for result_index in attributes.outputs'range loop
        if attributes.outputs(result_index).is_enabled then
          report "--------------------------------";
          report "MMCM output " & integer'image(result_index);

          report (
            " - Frequency "
            & real'image(attributes.outputs(result_index).frequency_hz)
            & " Hz ("
            & real'image(attributes.outputs(result_index).period_ns)
            & " ns)."
          );

          if attributes.outputs(result_index).phase_shift_degrees /= 0.0 then
            report (" - Phase shift "
              & real'image(attributes.outputs(result_index).phase_shift_degrees)
              & " degrees ("
              & real'image(attributes.outputs(result_index).phase_shift_ns)
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
          attributes => attributes
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
          attributes => attributes
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

    assert result_clk_int'length = 7 report "Vector to flattened wrong count" severity failure;

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
