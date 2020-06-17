-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Data types for working with AXI4-Lite interfaces
-- @details Based on the document "ARM IHI 0022E (ID022613): AMBA AXI and ACE Protocol Specification"
-- Available here (after login): http://infocenter.arm.com/help/index.jsp?topic=/com.arm.doc.ihi0022e/index.html
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.axi_pkg.all;


package axil_pkg is

  ------------------------------------------------------------------------------
  -- A (Address Read and Address Write) channels
  ------------------------------------------------------------------------------

  type axil_m2s_a_t is record
    valid : std_logic;
    addr : std_logic_vector(axi_a_addr_sz - 1 downto 0);
    -- @note Excluded members: prot
    -- These are typically not changed on a transfer-to-transfer basis.
  end record;

  constant axil_m2s_a_init : axil_m2s_a_t := (valid => '0', others => (others => '0'));
  function axil_m2s_a_sz(addr_width : natural) return natural;

  type axil_s2m_a_t is record
    ready : std_logic;
  end record;

  constant axil_s2m_a_init : axil_s2m_a_t := (ready => '0');


  ------------------------------------------------------------------------------
  -- W (Write Data) channels
  ------------------------------------------------------------------------------

   -- Max values
  constant axil_data_sz : integer := 64;
  constant axil_w_strb_sz : integer := axil_data_sz / 8;

  type axil_m2s_w_t is record
    valid : std_logic;
    data : std_logic_vector(axil_data_sz - 1 downto 0);
    strb : std_logic_vector(axil_w_strb_sz - 1 downto 0);
  end record;

  constant axil_m2s_w_init : axil_m2s_w_t := (valid => '0', others => (others => '-'));

  function axil_m2s_w_sz(data_width : natural) return natural;
  function to_slv(data : axil_m2s_w_t; data_width : natural) return std_logic_vector;
  function to_axil_m2s_w(data : std_logic_vector; data_width : natural) return axil_m2s_w_t;

  type axil_s2m_w_t is record
    ready : std_logic;
  end record;

  constant axil_s2m_w_init : axil_s2m_w_t := (ready => '0');


  ------------------------------------------------------------------------------
  -- B (Write Response) channels
  ------------------------------------------------------------------------------

  type axil_m2s_b_t is record
    ready : std_logic;
  end record;

  constant axil_m2s_b_init : axil_m2s_b_t := (ready => '0');

  type axil_s2m_b_t is record
    valid : std_logic;
    resp : std_logic_vector(axi_resp_sz - 1 downto 0);
  end record;

  constant axil_s2m_b_init : axil_s2m_b_t := (valid => '0', others => (others => '0'));
  -- Exluded member: valid
  constant axil_s2m_b_sz : integer := axi_resp_sz;


  ------------------------------------------------------------------------------
  -- R (Read Data) channels
  ------------------------------------------------------------------------------

  type axil_m2s_r_t is record
    ready : std_logic;
  end record;

  constant axil_m2s_r_init : axil_m2s_r_t := (ready => '0');

  type axil_s2m_r_t is record
    valid : std_logic;
    data : std_logic_vector(axil_data_sz - 1 downto 0);
    resp : std_logic_vector(axi_resp_sz - 1 downto 0);
  end record;

  constant axil_s2m_r_init : axil_s2m_r_t := (valid => '0', others => (others => '0'));
  function axil_s2m_r_sz(data_width : natural) return natural;
  function to_slv(data : axil_s2m_r_t; data_width : natural) return std_logic_vector;
  function to_axil_s2m_r(data : std_logic_vector; data_width : natural) return axil_s2m_r_t;


  ------------------------------------------------------------------------------
  -- The complete buses
  ------------------------------------------------------------------------------

  type axil_read_m2s_t is record
    ar : axil_m2s_a_t;
    r : axil_m2s_r_t;
  end record;
  type axil_read_m2s_vec_t is array (integer range <>) of axil_read_m2s_t;

  constant axil_read_m2s_init : axil_read_m2s_t := (ar => axil_m2s_a_init, r => axil_m2s_r_init);

  type axil_read_s2m_t is record
    ar : axil_s2m_a_t;
    r : axil_s2m_r_t;
  end record;
  type axil_read_s2m_vec_t is array (integer range <>) of axil_read_s2m_t;

  constant axil_read_s2m_init : axil_read_s2m_t := (ar => axil_s2m_a_init, r => axil_s2m_r_init);

  type axil_write_m2s_t is record
    aw : axil_m2s_a_t;
    w : axil_m2s_w_t;
    b : axil_m2s_b_t;
  end record;
  type axil_write_m2s_vec_t is array (integer range <>) of axil_write_m2s_t;

  constant axil_write_m2s_init : axil_write_m2s_t := (aw => axil_m2s_a_init, w => axil_m2s_w_init, b => axil_m2s_b_init);

  type axil_write_s2m_t is record
    aw : axil_s2m_a_t;
    w : axil_s2m_w_t;
    b : axil_s2m_b_t;
  end record;
  type axil_write_s2m_vec_t is array (integer range <>) of axil_write_s2m_t;

  constant axil_write_s2m_init : axil_write_s2m_t := (aw => axil_s2m_a_init, w => axil_s2m_w_init, b => axil_s2m_b_init);

  type axil_m2s_t is record
    read : axil_read_m2s_t;
    write : axil_write_m2s_t;
  end record;
  type axil_m2s_vec_t is array (integer range <>) of axil_m2s_t;

  constant axil_m2s_init : axil_m2s_t := (read => axil_read_m2s_init, write => axil_write_m2s_init);

  type axil_s2m_t is record
    read : axil_read_s2m_t;
    write : axil_write_s2m_t;
  end record;
  type axil_s2m_vec_t is array (integer range <>) of axil_s2m_t;

  constant axil_s2m_init : axil_s2m_t := (read => axil_read_s2m_init, write => axil_write_s2m_init);

end;

package body axil_pkg is

  function axil_m2s_a_sz(addr_width : natural) return natural is
  begin
    -- Excluded membed: valid.
    return addr_width;
  end function;

  function axil_m2s_w_sz(data_width : natural) return natural is
  begin
    assert data_width = 32 or data_width = 64 report "AXI4-Lite protocol only supports data width 32 or 64" severity failure;
    -- Exluded member: valid
    return data_width + axi_w_strb_width(data_width);
  end function;

  function to_slv(data : axil_m2s_w_t; data_width : natural) return std_logic_vector is
    variable result : std_logic_vector(axil_m2s_w_sz(data_width) - 1 downto 0);
    variable lo, hi : natural := 0;
  begin
    lo := 0;
    hi := lo + data_width - 1;
    result(hi downto lo) := data.data(data_width - 1 downto 0);
    lo := hi + 1;
    hi := lo + axi_w_strb_width(data_width) - 1;
    result(hi downto lo) := data.strb(axi_w_strb_width(data_width) - 1 downto 0);
    assert hi = result'high severity failure;
    return result;
  end function;

  function to_axil_m2s_w(data : std_logic_vector; data_width : natural) return axil_m2s_w_t is
    variable result : axil_m2s_w_t := axil_m2s_w_init;
    variable lo, hi : natural := 0;
  begin
    lo := 0;
    hi := lo + data_width - 1;
    result.data(data_width - 1 downto 0) := data(hi downto lo);
    lo := hi + 1;
    hi := lo + axi_w_strb_width(data_width) - 1;
    result.strb(axi_w_strb_width(data_width) - 1 downto 0) := data(hi downto lo);
    assert hi = data'high severity failure;
    return result;
  end function;

  function axil_s2m_r_sz(data_width : natural)  return natural is
  begin
    -- Exluded member: valid
    return data_width + axi_resp_sz;
  end function;

  function to_slv(data : axil_s2m_r_t; data_width : natural) return std_logic_vector is
    variable result : std_logic_vector(axil_s2m_r_sz(data_width) - 1 downto 0);
    variable lo, hi : natural := 0;
  begin
    lo := 0;
    hi := lo + data_width - 1;
    result(hi downto lo) := data.data(data_width - 1 downto 0);
    lo := hi + 1;
    hi := lo + axi_resp_sz - 1;
    result(hi downto lo) := data.resp;
    assert hi = result'high severity failure;
    return result;
  end function;

  function to_axil_s2m_r(data : std_logic_vector; data_width : natural) return axil_s2m_r_t is
    variable result : axil_s2m_r_t := axil_s2m_r_init;
    variable lo, hi : natural := 0;
  begin
    lo := 0;
    hi := lo + data_width - 1;
    result.data(data_width - 1 downto 0) := data(hi downto lo);
    lo := hi + 1;
    hi := lo + axi_resp_sz - 1;
    result.resp := data(hi downto lo);
    assert hi = data'high severity failure;
    return result;
  end function;

end;
