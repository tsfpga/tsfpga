-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.com_context;
context vunit_lib.vc_context;

library common;
use common.addr_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library bfm;


entity tb_axi_to_axil_vec is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_axi_to_axil_vec is

  constant axil_slaves : addr_and_mask_vec_t(0 to 6 - 1) := (
    0 => (addr => x"0000_0000", mask => x"0000_7000"),
    1 => (addr => x"0000_1000", mask => x"0000_7000"),
    2 => (addr => x"0000_2000", mask => x"0000_7000"),
    3 => (addr => x"0000_3000", mask => x"0000_7000"),
    4 => (addr => x"0000_4000", mask => x"0000_7000"),
    5 => (addr => x"0000_5000", mask => x"0000_7000")
  );

  constant reg_map : reg_definition_vec_t(0 to 2 - 1) := (
    (idx => 0, reg_type => r_w),
    (idx => 1, reg_type => r_w)
  );

  constant clk_axi_period : time := 7 ns;
  constant clk_axil_slow_period : time := 3 ns;
  constant clk_axil_fast_period : time := 11 ns;

  -- Two of the slaves have same clock as axi clock. Two have a faster clock
  -- and two have a slower. Corresponds to the clock assignments further below.
  constant clocks_are_the_same : boolean_vector(axil_slaves'range) :=
    (0 => true, 1 => true, 2 => false, 3 => false, 4 => false, 5 => false);

  signal clk_axi : std_logic := '0';
  signal clk_axil_vec : std_logic_vector(axil_slaves'range) := (others => '0');

  signal axi_m2s : axi_m2s_t;
  signal axi_s2m : axi_s2m_t;

  signal axil_m2s_vec : axil_m2s_vec_t(axil_slaves'range);
  signal axil_s2m_vec : axil_s2m_vec_t(axil_slaves'range);

  constant axi_master : bus_master_t := new_bus(data_length => 32, address_length => axi_m2s.read.ar.addr'length);

begin

  clk_axi <= not clk_axi after clk_axi_period / 2;
  clk_axil_vec(0) <= not clk_axil_vec(0) after clk_axi_period / 2;
  clk_axil_vec(1) <= not clk_axil_vec(1) after clk_axi_period / 2;
  clk_axil_vec(2) <= not clk_axil_vec(2) after clk_axil_slow_period / 2;
  clk_axil_vec(3) <= not clk_axil_vec(3) after clk_axil_slow_period / 2;
  clk_axil_vec(4) <= not clk_axil_vec(4) after clk_axil_fast_period / 2;
  clk_axil_vec(5) <= not clk_axil_vec(5) after clk_axil_fast_period / 2;

  test_runner_watchdog(runner, 2 ms);


  ------------------------------------------------------------------------------
  main : process
    constant beef : std_logic_vector(32 - 1 downto 0) := x"beef_beef";
    constant dead : std_logic_vector(32 - 1 downto 0) := x"dead_dead";
  begin
    test_runner_setup(runner, runner_cfg);

    for slave_under_test_idx in axil_slaves'range loop
      for slave_idx in axil_slaves'range loop
        -- Write init value to all
        write_bus(net, axi_master, axil_slaves(slave_idx).addr, beef);
        check_bus(net, axi_master, axil_slaves(slave_idx).addr, beef);
      end loop;

      -- Write special value to one of them
      write_bus(net, axi_master, axil_slaves(slave_under_test_idx).addr, dead);

      for slave_idx in axil_slaves'range loop
        if slave_idx = slave_under_test_idx then
          -- Check special value
          check_bus(net, axi_master, axil_slaves(slave_idx).addr, dead);
        else
          -- The others should still have old value
          check_bus(net, axi_master, axil_slaves(slave_idx).addr, beef);
        end if;
      end loop;
    end loop;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  axi_master_inst : entity bfm.axi_master
    generic map (
      bus_handle => axi_master
    )
    port map (
      clk => clk_axi,

      axi_read_m2s => axi_m2s.read,
      axi_read_s2m => axi_s2m.read,

      axi_write_m2s => axi_m2s.write,
      axi_write_s2m => axi_s2m.write
    );


  ------------------------------------------------------------------------------
  register_maps : for slave in axil_slaves'range generate
    axil_reg_file_inst : entity reg_file.axil_reg_file
    generic map (
      regs => reg_map
    )
    port map (
      clk => clk_axil_vec(slave),

      axil_m2s => axil_m2s_vec(slave),
      axil_s2m => axil_s2m_vec(slave)
    );
  end generate;


  ------------------------------------------------------------------------------
  dut : entity work.axi_to_axil_vec
  generic map (
    axil_slaves => axil_slaves,
    clocks_are_the_same => clocks_are_the_same
  )
  port map (
    clk_axi => clk_axi,
    axi_m2s => axi_m2s,
    axi_s2m => axi_s2m,

    clk_axil_vec => clk_axil_vec,
    axil_m2s_vec => axil_m2s_vec,
    axil_s2m_vec => axil_s2m_vec
  );

end architecture;
