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
    M_AXI_GP0_arvalid : out STD_LOGIC;
    M_AXI_GP0_awvalid : out STD_LOGIC;
    M_AXI_GP0_bready : out STD_LOGIC;
    M_AXI_GP0_rready : out STD_LOGIC;
    M_AXI_GP0_wlast : out STD_LOGIC;
    M_AXI_GP0_wvalid : out STD_LOGIC;
    M_AXI_GP0_arid : out STD_LOGIC_VECTOR ( 11 downto 0 );
    M_AXI_GP0_awid : out STD_LOGIC_VECTOR ( 11 downto 0 );
    M_AXI_GP0_wid : out STD_LOGIC_VECTOR ( 11 downto 0 );
    M_AXI_GP0_arburst : out STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_GP0_arlock : out STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_GP0_arsize : out STD_LOGIC_VECTOR ( 2 downto 0 );
    M_AXI_GP0_awburst : out STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_GP0_awlock : out STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_GP0_awsize : out STD_LOGIC_VECTOR ( 2 downto 0 );
    M_AXI_GP0_arprot : out STD_LOGIC_VECTOR ( 2 downto 0 );
    M_AXI_GP0_awprot : out STD_LOGIC_VECTOR ( 2 downto 0 );
    M_AXI_GP0_araddr : out STD_LOGIC_VECTOR ( 31 downto 0 );
    M_AXI_GP0_awaddr : out STD_LOGIC_VECTOR ( 31 downto 0 );
    M_AXI_GP0_wdata : out STD_LOGIC_VECTOR ( 31 downto 0 );
    M_AXI_GP0_arcache : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_GP0_arlen : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_GP0_arqos : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_GP0_awcache : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_GP0_awlen : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_GP0_awqos : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_GP0_wstrb : out STD_LOGIC_VECTOR ( 3 downto 0 );
    M_AXI_GP0_arready : in STD_LOGIC;
    M_AXI_GP0_awready : in STD_LOGIC;
    M_AXI_GP0_bvalid : in STD_LOGIC;
    M_AXI_GP0_rlast : in STD_LOGIC;
    M_AXI_GP0_rvalid : in STD_LOGIC;
    M_AXI_GP0_wready : in STD_LOGIC;
    M_AXI_GP0_bid : in STD_LOGIC_VECTOR ( 11 downto 0 );
    M_AXI_GP0_rid : in STD_LOGIC_VECTOR ( 11 downto 0 );
    M_AXI_GP0_bresp : in STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_GP0_rresp : in STD_LOGIC_VECTOR ( 1 downto 0 );
    M_AXI_GP0_rdata : in STD_LOGIC_VECTOR ( 31 downto 0 );
    M_AXI_GP0_ACLK : in STD_LOGIC;
    FCLK_CLK0 : out STD_LOGIC
  );
  end component block_design;

end package;
