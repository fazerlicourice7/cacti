import numpy as np
import sys

# Constants
INF = float('inf')
NUM_DIMM = 1

# External configuration arrays
rtt1_wr_lrdimm_ddr3 = np.array([
    [INF, INF, 120, 120],
    [INF, INF, 120, 120],
    [INF, 120, 120, 80],
    [120, 120, 120, 60],
    [120, 120, 120, 60],
    [120, 80, 80, 60],
    [120, 80, 80, 60],
    [120, 80, 60, 40]
])

rtt2_wr_lrdimm_ddr3 = np.array([
    [INF, INF, INF, INF],  # 1
    [INF, INF, 120, 120],  # 2
    [120, 120, 120, 80],   # 3
    [120, 120, 80, 60],    # 4
    [120, 120, 80, 60],
    [120, 80, 60, 40],     # 6
    [120, 80, 60, 40],
    [80, 80, 40, 30]       # 8
])

rtt1_rd_lrdimm_ddr3 = np.array([
    [INF, INF, 120, 120],  # 1
    [INF, INF, 120, 120],  # 2
    [INF, 120, 120, 80],   # 3
    [120, 120, 120, 60],   # 4
    [120, 120, 120, 60],
    [120, 80, 80, 60],     # 6
    [120, 80, 80, 60],
    [120, 80, 60, 40]      # 8
])

rtt2_rd_lrdimm_ddr3 = np.array([
    [INF, INF, INF, INF],  # 1
    [INF, 120, 80, 60],    # 2
    [120, 80, 80, 40],     # 3
    [120, 80, 60, 40],     # 4
    [120, 80, 60, 40],
    [80, 60, 60, 30],      # 6
    [80, 60, 60, 30],
    [80, 60, 40, 20]       # 8
])

rtt1_wr_host_dimm_ddr3 = np.array([
    [120, 120, 120, 60],
    [120, 80, 80, 60],
    [120, 80, 60, 40]
])

rtt2_wr_host_dimm_ddr3 = np.array([
    [120, 120, 80, 60],
    [120, 80, 60, 40],
    [80, 80, 40, 30]
])

rtt1_rd_host_dimm_ddr3 = np.array([
    [120, 120, 120, 60],
    [120, 80, 80, 60],
    [120, 80, 60, 40]
])

rtt2_rd_host_dimm_ddr3 = np.array([
    [120, 80, 60, 40],
    [80, 60, 60, 30],
    [80, 60, 40, 20]
])

rtt1_wr_bob_dimm_ddr3 = np.array([
    [INF, 120, 120, 80],
    [120, 120, 120, 60],
    [120, 80, 80, 60]
])

rtt2_wr_bob_dimm_ddr3 = np.array([
    [120, 120, 120, 80],
    [120, 120, 80, 60],
    [120, 80, 60, 40]
])

rtt1_rd_bob_dimm_ddr3 = np.array([
    [INF, 120, 120, 80],
    [120, 120, 120, 60],
    [120, 80, 80, 60]
])

rtt2_rd_bob_dimm_ddr3 = np.array([
    [120, 80, 80, 40],
    [120, 80, 60, 40],
    [80, 60, 60, 30]
])

# DDR4
rtt1_wr_lrdimm_ddr4 = np.array([
    [120, 120, 80, 80],   # 1
    [120, 120, 80, 80],   # 2
    [120, 80, 80, 60],    # 3
    [80, 60, 60, 60],     # 4
    [80, 60, 60, 60],
    [60, 60, 60, 40],     # 6
    [60, 60, 60, 40],
    [40, 40, 40, 40]      # 8
])

rtt2_wr_lrdimm_ddr4 = np.array([
    [INF, INF, INF, INF],  # 1
    [120, 120, 120, 80],   # 2
    [120, 80, 80, 80],     # 3
    [80, 80, 80, 60],      # 4
    [80, 80, 80, 60],
    [60, 60, 60, 40],      # 6
    [60, 60, 60, 40],
    [60, 40, 40, 30]       # 8
])

rtt1_rd_lrdimm_ddr4 = np.array([
    [120, 120, 80, 80],   # 1
    [120, 120, 80, 60],   # 2
    [120, 80, 80, 60],    # 3
    [120, 60, 60, 60],    # 4
    [120, 60, 60, 60],
    [80, 60, 60, 40],     # 6
    [80, 60, 60, 40],
    [60, 40, 40, 30]      # 8
])

rtt2_rd_lrdimm_ddr4 = np.array([
    [INF, INF, INF, INF],  # 1
    [80, 60, 60, 60],      # 2
    [60, 60, 40, 40],      # 3
    [60, 40, 40, 40],      # 4
    [60, 40, 40, 40],
    [40, 40, 40, 30],      # 6
    [40, 40, 40, 30],
    [40, 30, 30, 20]       # 8
])

rtt1_wr_host_dimm_ddr4 = np.array([
    [80, 60, 60, 60],
    [60, 60, 60, 60],
    [40, 40, 40, 40]
])

rtt2_wr_host_dimm_ddr4 = np.array([
    [80, 80, 80, 60],
    [60, 60, 60, 40],
    [60, 40, 40, 30]
])

rtt1_rd_host_dimm_ddr4 = np.array([
    [120, 60, 60, 60],
    [80, 60, 60, 40],
    [60, 40, 40, 30]
])

rtt2_rd_host_dimm_ddr4 = np.array([
    [60, 40, 40, 40],
    [40, 40, 40, 30],
    [40, 30, 30, 20]
])

rtt1_wr_bob_dimm_ddr4 = np.array([
    [120, 80, 80, 60],
    [80, 60, 60, 60],
    [60, 60, 60, 40]
])

rtt2_wr_bob_dimm_ddr4 = np.array([
    [120, 80, 80, 80],
    [80, 80, 80, 60],
    [60, 60, 60, 40]
])

rtt1_rd_bob_dimm_ddr4 = np.array([
    [120, 80, 80, 60],
    [120, 60, 60, 60],
    [80, 60, 60, 40]
])

rtt2_rd_bob_dimm_ddr4 = np.array([
    [60, 60, 40, 40],
    [60, 40, 40, 40],
    [40, 40, 40, 30]
])

import numpy as np

class Mem_IO_type():
    DDR3 = "DDR3"
    DDR4 = "DDR4"
    LPDDR2 = "LPDDR2"
    WideIO = "WideIO"
    Low_Swing_Diff = "Low_Swing_Diff"
    Serial = "Serial"        

###
class IOTechParam:
    def __init__(self, g_ip, io_type1, num_mem_dq, mem_data_width, num_dq, connection, num_loads, freq):
        # Number of loads on the address bus
        self.num_mem_ca = 0.0
        
        # Number of loads on the clock as total memories in the channel / number of clock lines available
        self.num_mem_clk = 0.0

        # Technology Parameters
        self.vdd_io = 0.0  # IO Supply voltage (V)
        self.v_sw_clk = 0.0  # Voltage swing on CLK/CLKB (V)

        # Loading parameters
        self.c_int = 0.0  # Internal IO loading (pF)
        self.c_tx = 0.0  # IO TX self-load including package (pF)
        self.c_data = 0.0  # Device loading per memory data pin (pF)
        self.c_addr = 0.0  # Device loading per memory address pin (pF)
        self.i_bias = 0.0  # Bias current (mA)
        self.i_leak = 0.0  # Active leakage current per pin (nA)

        # IO Area coefficients
        self.ioarea_c = 0.0  # IO Area baseline coefficient for control circuitry and overhead (sq.mm.)
        self.ioarea_k0 = 0.0  # IO Area coefficient for the driver, for unit drive strength or output impedance (sq.mm * ohms)
        self.ioarea_k1 = 0.0  # IO Area coefficient for the predriver final stage (sq.mm * ohms / MHz)
        self.ioarea_k2 = 0.0  # IO Area coefficient for predriver middle stage (sq.mm * ohms / MHz^2)
        self.ioarea_k3 = 0.0  # IO Area coefficient for predriver first stage (sq.mm * ohms / MHz^3)

        # Timing parameters (ps)
        self.t_ds = 0.0  # DQ setup time at DRAM
        self.t_is = 0.0  # CA setup time at DRAM
        self.t_dh = 0.0  # DQ hold time at DRAM
        self.t_ih = 0.0  # CA hold time at DRAM
        self.t_dcd_soc = 0.0  # Duty-cycle distortion at the CPU/SOC
        self.t_dcd_dram = 0.0  # Duty-cycle distortion at the DRAM
        self.t_error_soc = 0.0  # Timing error due to edge placement uncertainty of the DLL
        self.t_skew_setup = 0.0  # Setup skew between DQ/DQS or CA/CLK after deskewing the lines
        self.t_skew_hold = 0.0  # Hold skew between DQ/DQS or CA/CLK after deskewing the lines
        self.t_dqsq = 0.0  # DQ-DQS skew at the DRAM output during Read
        self.t_soc_setup = 0.0  # Setup time at SOC input during Read
        self.t_soc_hold = 0.0  # Hold time at SOC input during Read
        self.t_jitter_setup = 0.0  # Half-cycle jitter on the DQS at DRAM input affecting setup time
        self.t_jitter_hold = 0.0  # Half-cycle jitter on the DQS at the DRAM input affecting hold time
        self.t_jitter_addr_setup = 0.0  # Half-cycle jitter on the CLK at DRAM input affecting setup time
        self.t_jitter_addr_hold = 0.0  # Half-cycle jitter on the CLK at the DRAM input affecting hold time
        self.t_cor_margin = 0.0  # Statistical correlation margin

        # Termination Parameters
        self.r_diff_term = 0.0  # Differential termination resistor if used for CLK (Ohm)

        # ODT related termination resistor values (Ohm)
        self.rtt1_dq_read = 0.0  # DQ Read termination at CPU
        self.rtt2_dq_read = 0.0  # DQ Read termination at inactive DRAM
        self.rtt1_dq_write = 0.0  # DQ Write termination at active DRAM
        self.rtt2_dq_write = 0.0  # DQ Write termination at inactive DRAM
        self.rtt_ca = 0.0  # CA fly-by termination
        self.rs1_dq = 0.0  # Series resistor at active DRAM
        self.rs2_dq = 0.0  # Series resistor at inactive DRAM
        self.r_stub_ca = 0.0  # Series resistor for the fly-by channel
        self.r_on = 0.0  # Driver impedance
        self.r_on_ca = 0.0  # CA driver impedance

        self.z0 = 0.0  # Line impedance (ohms): Characteristic impedance of the route
        self.t_flight = 0.0  # Flight time of the interconnect (ns)
        self.t_flight_ca = 0.0  # Flight time of the Control/Address (CA) interconnect (ns)

        # Voltage noise coefficients
        self.k_noise_write = 0.0  # Proportional noise coefficient for Write mode
        self.k_noise_read = 0.0  # Proportional noise coefficient for Read mode
        self.k_noise_addr = 0.0  # Proportional noise coefficient for Address bus
        self.v_noise_independent_write = 0.0  # Independent noise voltage for Write mode
        self.v_noise_independent_read = 0.0  # Independent noise voltage for Read mode
        self.v_noise_independent_addr = 0.0  # Independent noise voltage for Address bus

        # Sensitivity Inputs for Timing and Voltage Noise
        self.k_noise_write_sen = 0.0
        self.k_noise_read_sen = 0.0
        self.k_noise_addr_sen = 0.0
        self.t_jitter_setup_sen = 0.0
        self.t_jitter_hold_sen = 0.0
        self.t_jitter_addr_setup_sen = 0.0
        self.t_jitter_addr_hold_sen = 0.0

        # SWING AND TERMINATION CALCULATIONS
        self.rpar_write = 0.0
        self.rpar_read = 0.0

        # Swing calculation
        self.v_sw_data_read_load1 = 0.0  # Swing for DQ at dram1 during READ
        self.v_sw_data_read_load2 = 0.0  # Swing for DQ at dram2 during READ
        self.v_sw_data_read_line = 0.0  # Swing for DQ on the line during READ
        self.v_sw_addr = 0.0  # Swing for the address bus
        self.v_sw_data_write_load1 = 0.0  # Swing for DQ at dram1 during WRITE
        self.v_sw_data_write_load2 = 0.0  # Swing for DQ at dram2 during WRITE
        self.v_sw_data_write_line = 0.0  # Swing for DQ on the line during WRITE

        # PHY Static Power Coefficients (mW)
        self.phy_datapath_s = 0.0  # Datapath Static Power
        self.phy_phase_rotator_s = 0.0  # Phase Rotator Static Power
        self.phy_clock_tree_s = 0.0  # Clock Tree Static Power
        self.phy_rx_s = 0.0  # Receiver Static Power
        self.phy_dcc_s = 0.0  # Duty Cycle Correction Static Power
        self.phy_deskew_s = 0.0  # Deskewing Static Power
        self.phy_leveling_s = 0.0  # Write and Read Leveling Static Power
        self.phy_pll_s = 0.0  # PHY PLL Static Power

        # PHY Dynamic Power Coefficients (mW/Gbps)
        self.phy_datapath_d = 0.0  # Datapath Dynamic Power
        self.phy_phase_rotator_d = 0.0  # Phase Rotator Dynamic Power
        self.phy_clock_tree_d = 0.0  # Clock Tree Dynamic Power
        self.phy_rx_d = 0.0  # Receiver Dynamic Power
        self.phy_dcc_d = 0.0  # Duty Cycle Correction Dynamic Power
        self.phy_deskew_d = 0.0  # Deskewing Dynamic Power
        self.phy_leveling_d = 0.0  # Write and Read Leveling Dynamic Power
        self.phy_pll_d = 0.0  # PHY PLL Dynamic Power

        # PHY Wakeup Times (Sleep to Active) (microseconds)
        self.phy_pll_wtime = 0.0  # PHY PLL Wakeup Time
        self.phy_phase_rotator_wtime = 0.0  # Phase Rotator Wakeup Time
        self.phy_rx_wtime = 0.0  # Receiver Wakeup Time
        self.phy_bandgap_wtime = 0.0  # Bandgap Wakeup Time
        self.phy_deskew_wtime = 0.0  # Deskewing Wakeup Time
        self.phy_vrefgen_wtime = 0.0  # VREF Generator Wakeup Time

        ###
        # io_type1, num_mem_dq, mem_data_width, num_dq, connection, num_loads, freq
        self.io_type = io_type1
        self.num_mem_dq = num_mem_dq
        self.mem_data_width = mem_data_width
        self.num_dq = num_dq
        self.connection = connection if connection != None else "UDIMM"
        self.num_loads = num_loads
        self.frequency = freq

        self.num_mem_ca = num_mem_dq * mem_data_width
        self.num_mem_clk = num_mem_dq * (num_dq / mem_data_width) / (g_ip.num_clk / 2)

        print(f"io type {self.io_type}")
        import time
        time.sleep(5)

        if self.io_type == Mem_IO_type.LPDDR2:
            # Technology Parameters
            self.vdd_io = 1.2
            self.v_sw_clk = 1

            # Loading parameters
            self.c_int = 1.5
            self.c_tx = 2
            self.c_data = 1.5
            self.c_addr = 0.75
            self.i_bias = 5
            self.i_leak = 1000

            # IO Area coefficients
            self.ioarea_c = 0.01
            self.ioarea_k0 = 0.5
            self.ioarea_k1 = 0.00008
            self.ioarea_k2 = 0.000000030
            self.ioarea_k3 = 0.000000000008

            # Timing parameters (ps)
            self.t_ds = 250
            self.t_is = 250
            self.t_dh = 250
            self.t_ih = 250
            self.t_dcd_soc = 50
            self.t_dcd_dram = 50
            self.t_error_soc = 50
            self.t_skew_setup = 50
            self.t_skew_hold = 50
            self.t_dqsq = 250
            self.t_soc_setup = 50
            self.t_soc_hold = 50
            self.t_jitter_setup = 200
            self.t_jitter_hold = 200
            self.t_jitter_addr_setup = 200
            self.t_jitter_addr_hold = 200
            self.t_cor_margin = 40

            # External IO Configuration Parameters
            self.r_diff_term = 480
            self.rtt1_dq_read = 100000
            self.rtt2_dq_read = 100000
            self.rtt1_dq_write = 100000
            self.rtt2_dq_write = 100000
            self.rtt_ca = 240
            self.rs1_dq = 0
            self.rs2_dq = 0
            self.r_stub_ca = 0
            self.r_on = 50
            self.r_on_ca = 50
            self.z0 = 50
            self.t_flight = 0.5
            self.t_flight_ca = 0.5

            # Voltage noise coefficients
            self.k_noise_write = 0.2
            self.k_noise_read = 0.2
            self.k_noise_addr = 0.2
            self.v_noise_independent_write = 0.1
            self.v_noise_independent_read = 0.1
            self.v_noise_independent_addr = 0.1

            # Sensitivity Inputs for Timing and Voltage Noise
            self.k_noise_write_sen = self.k_noise_write * (1 + 0.2 * (self.r_on / 34 - 1) +
                                                           0.2 * (num_mem_dq / 2 - 1))
            self.k_noise_read_sen = self.k_noise_read * (1 + 0.2 * (self.r_on / 34 - 1) +
                                                         0.2 * (num_mem_dq / 2 - 1))
            self.k_noise_addr_sen = self.k_noise_addr * (1 + 0.1 * (self.rtt_ca / 100 - 1) +
                                                         0.2 * (self.r_on / 34 - 1) +
                                                         0.2 * (self.num_mem_ca / 16 - 1))

            self.t_jitter_setup_sen = self.t_jitter_setup * (1 + 0.1 * (self.r_on / 34 - 1) +
                                                             0.3 * (num_mem_dq / 2 - 1))
            self.t_jitter_hold_sen = self.t_jitter_hold * (1 + 0.1 * (self.r_on / 34 - 1) +
                                                           0.3 * (num_mem_dq / 2 - 1))
            self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup * (1 + 0.2 * (self.rtt_ca / 100 - 1) +
                                                                       0.1 * (self.r_on / 34 - 1) +
                                                                       0.4 * (self.num_mem_ca / 16 - 1))
            self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold * (1 + 0.2 * (self.rtt_ca / 100 - 1) +
                                                                     0.1 * (self.r_on / 34 - 1) +
                                                                     0.4 * (self.num_mem_ca / 16 - 1))

            # PHY Static Power Coefficients (mW)
            self.phy_datapath_s = 0
            self.phy_phase_rotator_s = 5
            self.phy_clock_tree_s = 0
            self.phy_rx_s = 3
            self.phy_dcc_s = 0
            self.phy_deskew_s = 0
            self.phy_leveling_s = 0
            self.phy_pll_s = 2

            # PHY Dynamic Power Coefficients (mW/Gbps)
            self.phy_datapath_d = 0.3
            self.phy_phase_rotator_d = 0.01
            self.phy_clock_tree_d = 0.4
            self.phy_rx_d = 0.2
            self.phy_dcc_d = 0
            self.phy_deskew_d = 0
            self.phy_leveling_d = 0
            self.phy_pll_d = 0.05

            # PHY Wakeup Times (Sleep to Active) (microseconds)
            self.phy_pll_wtime = 10
            self.phy_phase_rotator_wtime = 5
            self.phy_rx_wtime = 2
            self.phy_bandgap_wtime = 10
            self.phy_deskew_wtime = 0
            self.phy_vrefgen_wtime = 0

        elif self.io_type == Mem_IO_type.WideIO:
            # Technology Parameters
            self.vdd_io = 1.2
            self.v_sw_clk = 1.2

            # Loading parameters
            self.c_int = 0.5
            self.c_tx = 0.5
            self.c_data = 0.5
            self.c_addr = 0.35
            self.i_bias = 0
            self.i_leak = 500

            # IO Area coefficients
            self.ioarea_c = 0.003
            self.ioarea_k0 = 0.2
            self.ioarea_k1 = 0.00004
            self.ioarea_k2 = 0.000000020
            self.ioarea_k3 = 0.000000000004

            # Timing parameters (ps)
            self.t_ds = 250
            self.t_is = 250
            self.t_dh = 250
            self.t_ih = 250
            self.t_dcd_soc = 50
            self.t_dcd_dram = 50
            self.t_error_soc = 50
            self.t_skew_setup = 50
            self.t_skew_hold = 50
            self.t_dqsq = 250
            self.t_soc_setup = 50
            self.t_soc_hold = 50
            self.t_jitter_setup = 200
            self.t_jitter_hold = 200
            self.t_jitter_addr_setup = 200
            self.t_jitter_addr_hold = 200
            self.t_cor_margin = 50

            # External IO Configuration Parameters
            self.r_diff_term = 100000
            self.rtt1_dq_read = 100000
            self.rtt2_dq_read = 100000
            self.rtt1_dq_write = 100000
            self.rtt2_dq_write = 100000
            self.rtt_ca = 100000
            self.rs1_dq = 0
            self.rs2_dq = 0
            self.r_stub_ca = 0
            self.r_on = 75
            self.r_on_ca = 75
            self.z0 = 50
            self.t_flight = 0.05
            self.t_flight_ca = 0.05

            # Voltage noise coefficients
            self.k_noise_write = 0.2
            self.k_noise_read = 0.2
            self.k_noise_addr = 0.2
            self.v_noise_independent_write = 0.1
            self.v_noise_independent_read = 0.1
            self.v_noise_independent_addr = 0.1

            # Sensitivity Inputs for Timing and Voltage Noise
            self.k_noise_write_sen = self.k_noise_write * (1 + 0.2 * (self.r_on / 50 - 1) +
                                                          0.2 * (self.num_mem_dq / 2 - 1))
            self.k_noise_read_sen = self.k_noise_read * (1 + 0.2 * (self.r_on / 50 - 1) +
                                                        0.2 * (self.num_mem_dq / 2 - 1))
            self.k_noise_addr_sen = self.k_noise_addr * (1 + 0.2 * (self.r_on / 50 - 1) +
                                                        0.2 * (self.num_mem_ca / 16 - 1))

            self.t_jitter_setup_sen = self.t_jitter_setup * (1 + 0.1 * (self.r_on / 50 - 1) +
                                                            0.3 * (self.num_mem_dq / 2 - 1))
            self.t_jitter_hold_sen = self.t_jitter_hold * (1 + 0.1 * (self.r_on / 50 - 1) +
                                                          0.3 * (self.num_mem_dq / 2 - 1))
            self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup * (1 + 0.1 * (self.r_on / 50 - 1) +
                                                                      0.4 * (self.num_mem_ca / 16 - 1))
            self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold * (1 + 0.1 * (self.r_on / 50 - 1) +
                                                                    0.4 * (self.num_mem_ca / 16 - 1))

            # PHY Static Power Coefficients (mW)
            self.phy_datapath_s = 0
            self.phy_phase_rotator_s = 1
            self.phy_clock_tree_s = 0
            self.phy_rx_s = 0
            self.phy_dcc_s = 0
            self.phy_deskew_s = 0
            self.phy_leveling_s = 0
            self.phy_pll_s = 0

            # PHY Dynamic Power Coefficients (mW/Gbps)
            self.phy_datapath_d = 0.3
            self.phy_phase_rotator_d = 0.01
            self.phy_clock_tree_d = 0.2
            self.phy_rx_d = 0.1
            self.phy_dcc_d = 0
            self.phy_deskew_d = 0
            self.phy_leveling_d = 0
            self.phy_pll_d = 0

            # PHY Wakeup Times (Sleep to Active) (microseconds)
            self.phy_pll_wtime = 10
            self.phy_phase_rotator_wtime = 0
            self.phy_rx_wtime = 0
            self.phy_bandgap_wtime = 0
            self.phy_deskew_wtime = 0
            self.phy_vrefgen_wtime = 0

        elif self.io_type == Mem_IO_type.DDR3:
            # Default parameters for DDR3
            self.vdd_io = 1.5
            self.v_sw_clk = 0.75

            # Loading parameters
            self.c_int = 1.5
            self.c_tx = 2
            self.c_data = 1.5
            self.c_addr = 0.75
            self.i_bias = 15
            self.i_leak = 1000

            # IO Area coefficients
            self.ioarea_c = 0.01
            self.ioarea_k0 = 0.5
            self.ioarea_k1 = 0.00015
            self.ioarea_k2 = 0.000000045
            self.ioarea_k3 = 0.000000000015

            # Timing parameters (ps)
            self.t_ds = 150
            self.t_is = 150
            self.t_dh = 150
            self.t_ih = 150
            self.t_dcd_soc = 50
            self.t_dcd_dram = 50
            self.t_error_soc = 25
            self.t_skew_setup = 25
            self.t_skew_hold = 25
            self.t_dqsq = 100
            self.t_soc_setup = 50
            self.t_soc_hold = 50
            self.t_jitter_setup = 100
            self.t_jitter_hold = 100
            self.t_jitter_addr_setup = 100
            self.t_jitter_addr_hold = 100
            self.t_cor_margin = 30

            # External IO Configuration Parameters
            self.r_diff_term = 100

            # Switch case for connection
            if self.connection == "UDIMM":
                self.rtt1_dq_write = rtt1_wr_bob_dimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_write = rtt2_wr_bob_dimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt1_dq_read = rtt1_rd_bob_dimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_read = rtt2_rd_bob_dimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
            elif self.connection == "RDIMM":
                self.rtt1_dq_write = rtt1_wr_host_dimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_write = rtt2_wr_host_dimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt1_dq_read = rtt1_rd_host_dimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_read = rtt2_rd_host_dimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
            elif self.connection == "LRDIMM":
                self.rtt1_dq_write = rtt1_wr_lrdimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_write = rtt2_wr_lrdimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt1_dq_read = rtt1_rd_lrdimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_read = rtt2_rd_lrdimm_ddr3[self.num_loads - 1][self.frequency_index(self.io_type)]

            
            print(f'rtt1_dq_read {self.rtt1_dq_read}; {self.num_loads - 1}; {self.frequency_index(self.io_type)}; {self.connection}')
            time.sleep(5)

            self.rtt_ca = 50
            self.rs1_dq = 15
            self.rs2_dq = 15
            self.r_stub_ca = 0
            self.r_on = g_ip.ron_value
            print(f"IN DDR3 {g_ip.ron_value}")
            self.r_on_ca = 50
            self.z0 = 50
            self.t_flight = g_ip.tflight_value
            self.t_flight_ca = 2

            # Voltage noise coefficients
            self.k_noise_write = 0.2
            self.k_noise_read = 0.2
            self.k_noise_addr = 0.2
            self.v_noise_independent_write = 0.1
            self.v_noise_independent_read = 0.1
            self.v_noise_independent_addr = 0.1

            # Sensitivity Inputs for Timing and Voltage Noise
            self.k_noise_write_sen = self.k_noise_write * (1 + 0.1 * (self.rtt1_dq_write / 60 - 1) +
                                                          0.2 * (self.rtt2_dq_write / 60 - 1) +
                                                          0.2 * (self.r_on / 34 - 1) +
                                                          0.2 * (self.num_mem_dq / 2 - 1))

            self.k_noise_read_sen = self.k_noise_read * (1 + 0.1 * (self.rtt1_dq_read / 60 - 1) +
                                                        0.2 * (self.rtt2_dq_read / 60 - 1) +
                                                        0.2 * (self.r_on / 34 - 1) +
                                                        0.2 * (self.num_mem_dq / 2 - 1))

            self.k_noise_addr_sen = self.k_noise_addr * (1 + 0.1 * (self.rtt_ca / 50 - 1) +
                                                        0.2 * (self.r_on / 34 - 1) +
                                                        0.2 * (self.num_mem_ca / 16 - 1))

            self.t_jitter_setup_sen = self.t_jitter_setup * (1 + 0.2 * (self.rtt1_dq_write / 60 - 1) +
                                                            0.3 * (self.rtt2_dq_write / 60 - 1) +
                                                            0.1 * (self.r_on / 34 - 1) +
                                                            0.3 * (self.num_mem_dq / 2 - 1))

            self.t_jitter_hold_sen = self.t_jitter_hold * (1 + 0.2 * (self.rtt1_dq_write / 60 - 1) +
                                                          0.3 * (self.rtt2_dq_write / 60 - 1) +
                                                          0.1 * (self.r_on / 34 - 1) +
                                                          0.3 * (self.num_mem_dq / 2 - 1))

            self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup * (1 + 0.2 * (self.rtt_ca / 50 - 1) +
                                                                      0.1 * (self.r_on / 34 - 1) +
                                                                      0.4 * (self.num_mem_ca / 16 - 1))

            self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold * (1 + 0.2 * (self.rtt_ca / 50 - 1) +
                                                                    0.1 * (self.r_on / 34 - 1) +
                                                                    0.4 * (self.num_mem_ca / 16 - 1))

            # PHY Static Power Coefficients (mW)
            self.phy_datapath_s = 0
            self.phy_phase_rotator_s = 10
            self.phy_clock_tree_s = 0
            self.phy_rx_s = 10
            self.phy_dcc_s = 0
            self.phy_deskew_s = 0
            self.phy_leveling_s = 0
            self.phy_pll_s = 10

            # PHY Dynamic Power Coefficients (mW/Gbps)
            self.phy_datapath_d = 0.5
            self.phy_phase_rotator_d = 0.01
            self.phy_clock_tree_d = 0.5
            self.phy_rx_d = 0.5
            self.phy_dcc_d = 0.05
            self.phy_deskew_d = 0.1
            self.phy_leveling_d = 0.05
            self.phy_pll_d = 0.05

            # PHY Wakeup Times (Sleep to Active) (microseconds)
            self.phy_pll_wtime = 10
            self.phy_phase_rotator_wtime = 5
            self.phy_rx_wtime = 2
            self.phy_bandgap_wtime = 10
            self.phy_deskew_wtime = 0.003
            self.phy_vrefgen_wtime = 0.5

        elif self.io_type == Mem_IO_type.DDR4:
            # Default parameters for DDR4
            self.vdd_io = 1.2
            self.v_sw_clk = 0.6

            # Loading parameters
            self.c_int = 1.5
            self.c_tx = 2
            self.c_data = 1
            self.c_addr = 0.75
            self.i_bias = 15
            self.i_leak = 1000

            # IO Area coefficients
            self.ioarea_c = 0.01
            self.ioarea_k0 = 0.35
            self.ioarea_k1 = 0.00008
            self.ioarea_k2 = 0.000000035
            self.ioarea_k3 = 0.000000000010

            # Timing parameters (ps)
            self.t_ds = 30
            self.t_is = 60
            self.t_dh = 30
            self.t_ih = 60
            self.t_dcd_soc = 20
            self.t_dcd_dram = 20
            self.t_error_soc = 15
            self.t_skew_setup = 15
            self.t_skew_hold = 15
            self.t_dqsq = 50
            self.t_soc_setup = 20
            self.t_soc_hold = 10
            self.t_jitter_setup = 30
            self.t_jitter_hold = 30
            self.t_jitter_addr_setup = 60
            self.t_jitter_addr_hold = 60
            self.t_cor_margin = 10

            # External IO Configuration Parameters
            self.r_diff_term = 100

            if self.connection == "UDIMM":
                self.rtt1_dq_write = rtt1_wr_bob_dimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_write = rtt2_wr_bob_dimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt1_dq_read = rtt1_rd_bob_dimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_read = rtt2_rd_bob_dimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
            elif self.connection == "RDIMM":
                self.rtt1_dq_write = rtt1_wr_host_dimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_write = rtt2_wr_host_dimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt1_dq_read = rtt1_rd_host_dimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_read = rtt2_rd_host_dimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
            elif self.connection == "LRDIMM":
                self.rtt1_dq_write = rtt1_wr_lrdimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_write = rtt2_wr_lrdimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt1_dq_read = rtt1_rd_lrdimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]
                self.rtt2_dq_read = rtt2_rd_lrdimm_ddr4[self.num_loads - 1][self.frequency_index(self.io_type)]

            self.rtt_ca = 50
            self.rs1_dq = 15
            self.rs2_dq = 15
            self.r_stub_ca = 0
            self.r_on = g_ip.ron_value
            self.r_on_ca = 50
            self.z0 = 50
            self.t_flight = g_ip.tflight_value
            self.t_flight_ca = 2

            # Voltage noise coefficients
            self.k_noise_write = 0.2
            self.k_noise_read = 0.2
            self.k_noise_addr = 0.2
            self.v_noise_independent_write = 0.1
            self.v_noise_independent_read = 0.1
            self.v_noise_independent_addr = 0.1

            # Sensitivity Inputs for Timing and Voltage Noise
            self.k_noise_write_sen = self.k_noise_write * (1 + 0.1 * (self.rtt1_dq_write / 60 - 1) +
                                                          0.2 * (self.rtt2_dq_write / 60 - 1) +
                                                          0.2 * (self.r_on / 34 - 1) +
                                                          0.2 * (self.num_mem_dq / 2 - 1))

            self.k_noise_read_sen = self.k_noise_read * (1 + 0.1 * (self.rtt1_dq_read / 60 - 1) +
                                                        0.2 * (self.rtt2_dq_read / 60 - 1) +
                                                        0.2 * (self.r_on / 34 - 1) +
                                                        0.2 * (self.num_mem_dq / 2 - 1))

            self.k_noise_addr_sen = self.k_noise_addr * (1 + 0.1 * (self.rtt_ca / 50 - 1) +
                                                        0.2 * (self.r_on / 34 - 1) +
                                                        0.2 * (self.num_mem_ca / 16 - 1))

            self.t_jitter_setup_sen = self.t_jitter_setup * (1 + 0.2 * (self.rtt1_dq_write / 60 - 1) +
                                                            0.3 * (self.rtt2_dq_write / 60 - 1) +
                                                            0.1 * (self.r_on / 34 - 1) +
                                                            0.3 * (self.num_mem_dq / 2 - 1))

            self.t_jitter_hold_sen = self.t_jitter_hold * (1 + 0.2 * (self.rtt1_dq_write / 60 - 1) +
                                                          0.3 * (self.rtt2_dq_write / 60 - 1) +
                                                          0.1 * (self.r_on / 34 - 1) +
                                                          0.3 * (self.num_mem_dq / 2 - 1))

            self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup * (1 + 0.2 * (self.rtt_ca / 50 - 1) +
                                                                      0.1 * (self.r_on / 34 - 1) +
                                                                      0.4 * (self.num_mem_ca / 16 - 1))

            self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold * (1 + 0.2 * (self.rtt_ca / 50 - 1) +
                                                                    0.1 * (self.r_on / 34 - 1) +
                                                                    0.4 * (self.num_mem_ca / 16 - 1))

            # PHY Static Power Coefficients (mW)
            self.phy_datapath_s = 0
            self.phy_phase_rotator_s = 10
            self.phy_clock_tree_s = 0
            self.phy_rx_s = 10
            self.phy_dcc_s = 0
            self.phy_deskew_s = 0
            self.phy_leveling_s = 0
            self.phy_pll_s = 10

            # PHY Dynamic Power Coefficients (mW/Gbps)
            self.phy_datapath_d = 0.5
            self.phy_phase_rotator_d = 0.01
            self.phy_clock_tree_d = 0.5
            self.phy_rx_d = 0.5
            self.phy_dcc_d = 0.05
            self.phy_deskew_d = 0.1
            self.phy_leveling_d = 0.05
            self.phy_pll_d = 0.05

            # PHY Wakeup Times (Sleep to Active) (microseconds)
            self.phy_pll_wtime = 10
            self.phy_phase_rotator_wtime = 5
            self.phy_rx_wtime = 2
            self.phy_bandgap_wtime = 10
            self.phy_deskew_wtime = 0.003
            self.phy_vrefgen_wtime = 0.5

        elif self.io_type == Mem_IO_type.Serial:
            # Default parameters for Serial
            # IO Supply voltage (V)
            self.vdd_io = 1.2
            self.v_sw_clk = 0.75

            # IO Area coefficients
            self.ioarea_c = 0.01
            self.ioarea_k0 = 0.15
            self.ioarea_k1 = 0.00005
            self.ioarea_k2 = 0.000000025
            self.ioarea_k3 = 0.000000000005

            # Timing parameters (ps)
            self.t_ds = 15
            self.t_dh = 15
            self.t_dcd_soc = 10
            self.t_dcd_dram = 10
            self.t_soc_setup = 10
            self.t_soc_hold = 10
            self.t_jitter_setup = 20
            self.t_jitter_hold = 20

            # External IO Configuration Parameters
            self.r_diff_term = 100

            self.t_jitter_setup_sen = self.t_jitter_setup
            self.t_jitter_hold_sen = self.t_jitter_hold
            self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup
            self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold

            # PHY Static Power Coefficients (mW)
            self.phy_datapath_s = 0
            self.phy_phase_rotator_s = 10
            self.phy_clock_tree_s = 0
            self.phy_rx_s = 10
            self.phy_dcc_s = 0
            self.phy_deskew_s = 0
            self.phy_leveling_s = 0
            self.phy_pll_s = 10

            # PHY Dynamic Power Coefficients (mW/Gbps)
            self.phy_datapath_d = 0.5
            self.phy_phase_rotator_d = 0.01
            self.phy_clock_tree_d = 0.5
            self.phy_rx_d = 0.5
            self.phy_dcc_d = 0.05
            self.phy_deskew_d = 0.1
            self.phy_leveling_d = 0.05
            self.phy_pll_d = 0.05

            # PHY Wakeup Times (Sleep to Active) (microseconds)
            self.phy_pll_wtime = 10
            self.phy_phase_rotator_wtime = 5
            self.phy_rx_wtime = 2
            self.phy_bandgap_wtime = 10
            self.phy_deskew_wtime = 0.003
            self.phy_vrefgen_wtime = 0.5

        else:
            print("Not Yet supported")
            sys.exit(1)

        # SWING AND TERMINATION CALCULATIONS

        # R|| calculation
        self.rpar_write = (self.rtt1_dq_write + self.rs1_dq) * (self.rtt2_dq_write + self.rs2_dq) / (
            self.rtt1_dq_write + self.rs1_dq + self.rtt2_dq_write + self.rs2_dq)
        self.rpar_read = (self.rtt1_dq_read) * (self.rtt2_dq_read + self.rs2_dq) / (
            self.rtt1_dq_read + self.rtt2_dq_read + self.rs2_dq)

        # Swing calculation
        self.v_sw_data_read_load1 = self.vdd_io * (self.rtt1_dq_read) * (self.rtt2_dq_read + self.rs2_dq) / (
            (self.rtt1_dq_read + self.rtt2_dq_read + self.rs2_dq) * (self.r_on + self.rs1_dq + self.rpar_read))
        self.v_sw_data_read_load2 = self.vdd_io * (self.rtt1_dq_read) * (self.rtt2_dq_read) / (
            (self.rtt1_dq_read + self.rtt2_dq_read + self.rs2_dq) * (self.r_on + self.rs1_dq + self.rpar_read))
        self.v_sw_data_read_line = self.vdd_io * self.rpar_read / (self.r_on + self.rs1_dq + self.rpar_read)
        self.v_sw_addr = self.vdd_io * self.rtt_ca / (50 + self.rtt_ca)
        self.v_sw_data_write_load1 = self.vdd_io * (self.rtt1_dq_write) * (self.rtt2_dq_write + self.rs2_dq) / (
            (self.rtt1_dq_write + self.rs1_dq + self.rtt2_dq_write + self.rs2_dq) * (self.r_on + self.rpar_write))
        self.v_sw_data_write_load2 = self.vdd_io * (self.rtt2_dq_write) * (self.rtt1_dq_write + self.rs1_dq) / (
            (self.rtt1_dq_write + self.rs1_dq + self.rtt2_dq_write + self.rs2_dq) * (self.r_on + self.rpar_write))
        self.v_sw_data_write_line = self.vdd_io * self.rpar_write / (self.r_on + self.rpar_write)

    def frequency_index(self, type: Mem_IO_type):
        if type == Mem_IO_type.DDR3:
            if self.frequency <= 400:
                return 0
            elif self.frequency <= 533:
                return 1
            elif self.frequency <= 667:
                return 2
            else:
                return 3
        elif type == Mem_IO_type.DDR4:
            if self.frequency <= 800:
                return 0
            elif self.frequency <= 933:
                return 1
            elif self.frequency <= 1066:
                return 2
            else:
                return 3
        else:
            raise AssertionError("Invalid Memory IO type")



