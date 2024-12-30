-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Settings in the Zynq block design.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;


package block_design_pkg is

  ------------------------------------------------------------------------------
  -- PL clock settings.
  constant pl_clk_frequency_hz : real := 100.0e6;

  ------------------------------------------------------------------------------
  -- AXI ports.
  constant m_gp0_id_width : natural := 12;
  constant m_gp0_addr_width : positive := 32;
  constant m_gp0_data_width : positive := 32;

  constant s_hp0_id_width : natural := 6;
  constant s_hp0_addr_width : positive := 32;
  constant s_hp0_data_width : positive := 64;

  ------------------------------------------------------------------------------
  -- AXI settings.
  constant artyz7_axi_default_axlock : axi3_a_lock_t := axi3_a_lock_normal;
  constant artyz7_axi_default_axprot : axi_a_prot_t := (
    axi_a_prot_unprivileged or axi_a_prot_secure or axi_a_prot_data
  );
  constant artyz7_axi_default_axcache : axi_a_cache_t := axi_a_cache_device_non_bufferable;
  -- No QoS scheme
  constant artyz7_axi_default_axqos : std_ulogic_vector(4 - 1 downto 0) := (others => '0');

  ------------------------------------------------------------------------------
  -- Types for PS MIO pins.
  type zynq7000_ddr_t is record
    cas_n : std_ulogic;
    cke : std_ulogic;
    ck_n : std_ulogic;
    ck_p : std_ulogic;
    cs_n : std_ulogic;
    reset_n : std_ulogic;
    odt : std_ulogic;
    ras_n : std_ulogic;
    we_n : std_ulogic;
    ba : std_ulogic_vector(2 downto 0);
    addr : std_ulogic_vector(14 downto 0);
    dm : std_ulogic_vector(3 downto 0);
    dq : std_ulogic_vector(31 downto 0);
    dqs_n : std_ulogic_vector(3 downto 0);
    dqs_p : std_ulogic_vector(3 downto 0);
  end record;

  type zynq7000_fixed_io_t is record
    mio : std_ulogic_vector(53 downto 0);
    ddr_vrn : std_ulogic;
    ddr_vrp : std_ulogic;
    ps_srstb : std_ulogic;
    ps_clk : std_ulogic;
    ps_porb : std_ulogic;
  end record;

end package;
