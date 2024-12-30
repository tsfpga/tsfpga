-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
use vunit_lib.com_pkg.net;
use vunit_lib.run_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.reg_t;
use reg_file.reg_operations_pkg.all;

use work.register_top_level_pkg.all;
use work.register_top_level_register_read_write_pkg.all;
use work.register_top_level_register_check_pkg.all;
use work.register_top_level_regs_pkg.all;


entity tb_register_top_level is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_register_top_level is

begin

  test_runner_watchdog(runner, 200 us);


  ------------------------------------------------------------------------------
  main : process
    procedure run_register_test is
      variable value : natural := 0;
    begin
      for register_list_idx in base_addresses'range loop
        for register_idx in 0 to register_top_level_registers_array_length - 1 loop
          value := register_list_idx * 256 + register_idx;

          report "Writing " & integer'image(value) & " to register " & integer'image(register_idx) & " in register list " & integer'image(register_list_idx);

          write_register_top_level_registers_reg(
            net=>net,
            array_index=>register_idx,
            value=>value,
            base_address=>base_addresses(register_list_idx)
          );
        end loop;
      end loop;

      for register_list_idx in base_addresses'range loop
        for register_idx in 0 to register_top_level_registers_array_length - 1 loop
          value := register_list_idx * 256 + register_idx;

          check_register_top_level_registers_reg_equal(
            net=>net,
            array_index=>register_idx,
            expected=>value,
            base_address=>base_addresses(register_list_idx)
          );
        end loop;
      end loop;
    end procedure;

  begin
    test_runner_setup(runner, runner_cfg);

    if run("test_registers") then
      run_register_test;
    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.axi_lite_register_top_level;

end architecture;
