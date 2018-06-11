library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
use vunit_lib.bus_master_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.com_context;

library common;
use common.addr_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library bfm;


entity tb_axi_to_regs is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_axi_to_regs is

  constant reg_slaves : addr_and_mask_vec_t(0 to 2 - 1) := (
    0 => (addr => x"0000_0000", mask => x"0000_1000"),
    1 => (addr => x"0000_1000", mask => x"0000_1000")
  );

  constant reg_map : reg_definition_vec_t(0 to 2 - 1) := (
    (idx => 0, reg_type => r_w),
    (idx => 1, reg_type => r_w)
  );

  signal clk_axi : std_logic := '0';

  signal axi_m2s : axi_m2s_t;
  signal axi_s2m : axi_s2m_t;

  signal regs_m2s : axil_m2s_vec_t(reg_slaves'range);
  signal regs_s2m : axil_s2m_vec_t(reg_slaves'range);

  constant axi_master : bus_master_t := new_bus(data_length => 32, address_length => axi_m2s.read.ar.addr'length);

begin

  clk_axi <= not clk_axi after 2 ns;
  test_runner_watchdog(runner, 2 ms);


  ------------------------------------------------------------------------------
  main : process
    constant beef : std_logic_vector(32 - 1 downto 0) := x"beef_beef";
    constant dead : std_logic_vector(32 - 1 downto 0) := x"dead_dead";
  begin
    test_runner_setup(runner, runner_cfg);

    -- Basic connectivity test

    write_bus(net, axi_master, reg_slaves(0).addr, beef);
    check_bus(net, axi_master, reg_slaves(0).addr, beef);

    write_bus(net, axi_master, reg_slaves(1).addr, dead);
    check_bus(net, axi_master, reg_slaves(1).addr, dead);

    check_bus(net, axi_master, reg_slaves(0).addr, beef);

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
  register_maps : for slave in reg_slaves'range generate
    axil_reg_file_inst : entity reg_file.axil_reg_file
    generic map (
      regs => reg_map
    )
    port map (
      clk => clk_axi,

      axil_m2s => regs_m2s(slave),
      axil_s2m => regs_s2m(slave),

      reg_values_in => (others => (others => '0'))
    );
  end generate;


  ------------------------------------------------------------------------------
  dut : entity work.axi_to_regs
  generic map (
    reg_slaves => reg_slaves)
  port map (
    clk_axi => clk_axi,

    axi_m2s => axi_m2s,
    axi_s2m => axi_s2m,

    regs_m2s => regs_m2s,
    regs_s2m => regs_s2m
  );

end architecture;
