----------------------------------------------------------------------------------
-- Component generated from Vivado:
-- Go to IP sources, right click your block design and select "Create HDL wrapper".
-- Choose "Copy..." in the popup.
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;


package block_design_pkg is

  component block_design is
  port (
    M_AXI_HPM0_FPD_araddr : out STD_LOGIC_VECTOR ( 39 downto 0 );
    M_AXI_HPM0_FPD_arburst : out STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_HPM0_FPD_arcache : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_HPM0_FPD_arid : out STD_LOGIC_VECTOR ( 15 downto 0 );
    M_AXI_HPM0_FPD_arlen : out STD_LOGIC_VECTOR ( 7 downto 0 );
    M_AXI_HPM0_FPD_arlock : out STD_LOGIC;
    M_AXI_HPM0_FPD_arprot : out STD_LOGIC_VECTOR ( 2 downto 0 );
    M_AXI_HPM0_FPD_arqos : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_HPM0_FPD_arready : in STD_LOGIC;
    M_AXI_HPM0_FPD_arsize : out STD_LOGIC_VECTOR ( 2 downto 0 );
    M_AXI_HPM0_FPD_aruser : out STD_LOGIC_VECTOR ( 15 downto 0 );
    M_AXI_HPM0_FPD_arvalid : out STD_LOGIC;
    M_AXI_HPM0_FPD_awaddr : out STD_LOGIC_VECTOR ( 39 downto 0 );
    M_AXI_HPM0_FPD_awburst : out STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_HPM0_FPD_awcache : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_HPM0_FPD_awid : out STD_LOGIC_VECTOR ( 15 downto 0 );
    M_AXI_HPM0_FPD_awlen : out STD_LOGIC_VECTOR ( 7 downto 0 );
    M_AXI_HPM0_FPD_awlock : out STD_LOGIC;
    M_AXI_HPM0_FPD_awprot : out STD_LOGIC_VECTOR ( 2 downto 0 );
    M_AXI_HPM0_FPD_awqos : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_HPM0_FPD_awready : in STD_LOGIC;
    M_AXI_HPM0_FPD_awsize : out STD_LOGIC_VECTOR ( 2 downto 0 );
    M_AXI_HPM0_FPD_awuser : out STD_LOGIC_VECTOR ( 15 downto 0 );
    M_AXI_HPM0_FPD_awvalid : out STD_LOGIC;
    M_AXI_HPM0_FPD_bid : in STD_LOGIC_VECTOR ( 15 downto 0 );
    M_AXI_HPM0_FPD_bready : out STD_LOGIC;
    M_AXI_HPM0_FPD_bresp : in STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_HPM0_FPD_bvalid : in STD_LOGIC;
    M_AXI_HPM0_FPD_rdata : in STD_LOGIC_VECTOR ( 31 downto 0 );
    M_AXI_HPM0_FPD_rid : in STD_LOGIC_VECTOR ( 15 downto 0 );
    M_AXI_HPM0_FPD_rlast : in STD_LOGIC;
    M_AXI_HPM0_FPD_rready : out STD_LOGIC;
    M_AXI_HPM0_FPD_rresp : in STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_HPM0_FPD_rvalid : in STD_LOGIC;
    M_AXI_HPM0_FPD_wdata : out STD_LOGIC_VECTOR ( 31 downto 0 );
    M_AXI_HPM0_FPD_wlast : out STD_LOGIC;
    M_AXI_HPM0_FPD_wready : in STD_LOGIC;
    M_AXI_HPM0_FPD_wstrb : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_HPM0_FPD_wvalid : out STD_LOGIC;
    S_AXI_HP0_FPD_araddr : in STD_LOGIC_VECTOR ( 48 downto 0 );
    S_AXI_HP0_FPD_arburst : in STD_LOGIC_VECTOR ( 1 downto 0 );
    S_AXI_HP0_FPD_arcache : in STD_LOGIC_VECTOR ( 3 downto 0 );
    S_AXI_HP0_FPD_arid : in STD_LOGIC_VECTOR ( 5 downto 0 );
    S_AXI_HP0_FPD_arlen : in STD_LOGIC_VECTOR ( 7 downto 0 );
    S_AXI_HP0_FPD_arlock : in STD_LOGIC;
    S_AXI_HP0_FPD_arprot : in STD_LOGIC_VECTOR ( 2 downto 0 );
    S_AXI_HP0_FPD_arqos : in STD_LOGIC_VECTOR ( 3 downto 0 );
    S_AXI_HP0_FPD_arready : out STD_LOGIC;
    S_AXI_HP0_FPD_arsize : in STD_LOGIC_VECTOR ( 2 downto 0 );
    S_AXI_HP0_FPD_aruser : in STD_LOGIC;
    S_AXI_HP0_FPD_arvalid : in STD_LOGIC;
    S_AXI_HP0_FPD_awaddr : in STD_LOGIC_VECTOR ( 48 downto 0 );
    S_AXI_HP0_FPD_awburst : in STD_LOGIC_VECTOR ( 1 downto 0 );
    S_AXI_HP0_FPD_awcache : in STD_LOGIC_VECTOR ( 3 downto 0 );
    S_AXI_HP0_FPD_awid : in STD_LOGIC_VECTOR ( 5 downto 0 );
    S_AXI_HP0_FPD_awlen : in STD_LOGIC_VECTOR ( 7 downto 0 );
    S_AXI_HP0_FPD_awlock : in STD_LOGIC;
    S_AXI_HP0_FPD_awprot : in STD_LOGIC_VECTOR ( 2 downto 0 );
    S_AXI_HP0_FPD_awqos : in STD_LOGIC_VECTOR ( 3 downto 0 );
    S_AXI_HP0_FPD_awready : out STD_LOGIC;
    S_AXI_HP0_FPD_awsize : in STD_LOGIC_VECTOR ( 2 downto 0 );
    S_AXI_HP0_FPD_awuser : in STD_LOGIC;
    S_AXI_HP0_FPD_awvalid : in STD_LOGIC;
    S_AXI_HP0_FPD_bid : out STD_LOGIC_VECTOR ( 5 downto 0 );
    S_AXI_HP0_FPD_bready : in STD_LOGIC;
    S_AXI_HP0_FPD_bresp : out STD_LOGIC_VECTOR ( 1 downto 0 );
    S_AXI_HP0_FPD_bvalid : out STD_LOGIC;
    S_AXI_HP0_FPD_rdata : out STD_LOGIC_VECTOR ( 127 downto 0 );
    S_AXI_HP0_FPD_rid : out STD_LOGIC_VECTOR ( 5 downto 0 );
    S_AXI_HP0_FPD_rlast : out STD_LOGIC;
    S_AXI_HP0_FPD_rready : in STD_LOGIC;
    S_AXI_HP0_FPD_rresp : out STD_LOGIC_VECTOR ( 1 downto 0 );
    S_AXI_HP0_FPD_rvalid : out STD_LOGIC;
    S_AXI_HP0_FPD_wdata : in STD_LOGIC_VECTOR ( 127 downto 0 );
    S_AXI_HP0_FPD_wlast : in STD_LOGIC;
    S_AXI_HP0_FPD_wready : out STD_LOGIC;
    S_AXI_HP0_FPD_wstrb : in STD_LOGIC_VECTOR ( 15 downto 0 );
    S_AXI_HP0_FPD_wvalid : in STD_LOGIC;
    maxihpm0_fpd_aclk : in STD_LOGIC;
    saxihp0_fpd_aclk : in STD_LOGIC;
    pl_clk0 : out STD_LOGIC
  );
  end component block_design;

end package;
