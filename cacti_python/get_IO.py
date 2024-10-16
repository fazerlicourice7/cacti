import numpy as np
import sys
from hw_symbols import symbol_table as IO_tech_dict

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

def scan_IO(IO_tech_dict, g_ip, io_type1, num_mem_dq, mem_data_width, num_dq, connection, num_loads, freq):
    def frequency_index(mem_type: Mem_IO_type):
      print(f"THIS IS THE TYPE FREAK: {mem_type}")
      if mem_type == "DDR3":
          print(f"IN DDR3 FREAK: {mem_type} {frequency}")
          if frequency <= 400:
              return 0
          elif frequency <= 533:
              return 1
          elif frequency <= 667:
              return 2
          else:
              return 3
      elif mem_type == "DDR4":
          if frequency <= 800:
              return 0
          elif frequency <= 933:
              return 1
          elif frequency <= 1066:
              return 2
          else:
              return 3
      else:
          raise AssertionError("Invalid Memory IO type")
        
    io_type = io_type1
    num_mem_dq = num_mem_dq
    mem_data_width = mem_data_width
    num_dq = num_dq
    print(f"connection is {connection}")
    connection = connection if connection != None else "UDIMM"
    num_loads = num_loads
    frequency = freq

    num_mem_ca = num_mem_dq * mem_data_width
    num_mem_clk = num_mem_dq * (num_dq / mem_data_width) / (g_ip.num_clk / 2)

    print(f"IO_TYPE: {io_type}; CONNECTION: {connection}")
    import time
    time.sleep(6)
    
    if io_type == "LPDDR2":
        # Technology Parameters
        IO_tech_dict['vdd_io'] = 1.2
        IO_tech_dict['v_sw_clk'] = 1

        # Loading parameters
        IO_tech_dict['c_int'] = 1.5
        IO_tech_dict['c_tx'] = 2
        IO_tech_dict['c_data'] = 1.5
        IO_tech_dict['c_addr'] = 0.75
        IO_tech_dict['i_bias'] = 5
        IO_tech_dict['i_leak'] = 1000

        # IO Area coefficients
        IO_tech_dict['ioarea_c'] = 0.01
        IO_tech_dict['ioarea_k0'] = 0.5
        IO_tech_dict['ioarea_k1'] = 0.00008
        IO_tech_dict['ioarea_k2'] = 0.000000030
        IO_tech_dict['ioarea_k3'] = 0.000000000008

        # Timing parameters (ps)
        IO_tech_dict['t_ds'] = 250
        IO_tech_dict['t_is'] = 250
        IO_tech_dict['t_dh'] = 250
        IO_tech_dict['t_ih'] = 250
        IO_tech_dict['t_dcd_soc'] = 50
        IO_tech_dict['t_dcd_dram'] = 50
        IO_tech_dict['t_error_soc'] = 50
        IO_tech_dict['t_skew_setup'] = 50
        IO_tech_dict['t_skew_hold'] = 50
        IO_tech_dict['t_dqsq'] = 250
        IO_tech_dict['t_soc_setup'] = 50
        IO_tech_dict['t_soc_hold'] = 50
        IO_tech_dict['t_jitter_setup'] = 200
        IO_tech_dict['t_jitter_hold'] = 200
        IO_tech_dict['t_jitter_addr_setup'] = 200
        IO_tech_dict['t_jitter_addr_hold'] = 200
        IO_tech_dict['t_cor_margin'] = 40

        # External IO Configuration Parameters
        IO_tech_dict['r_diff_term'] = 480
        IO_tech_dict['rtt1_dq_read'] = 100000
        IO_tech_dict['rtt2_dq_read'] = 100000
        IO_tech_dict['rtt1_dq_write'] = 100000
        IO_tech_dict['rtt2_dq_write'] = 100000
        IO_tech_dict['rtt_ca'] = 240
        IO_tech_dict['rs1_dq'] = 0
        IO_tech_dict['rs2_dq'] = 0
        IO_tech_dict['r_stub_ca'] = 0
        IO_tech_dict['r_on'] = 50
        IO_tech_dict['r_on_ca'] = 50
        IO_tech_dict['z0'] = 50
        IO_tech_dict['t_flight'] = 0.5
        IO_tech_dict['t_flight_ca'] = 0.5

        # Voltage noise coefficients
        IO_tech_dict['k_noise_write'] = 0.2
        IO_tech_dict['k_noise_read'] = 0.2
        IO_tech_dict['k_noise_addr'] = 0.2
        IO_tech_dict['v_noise_independent_write'] = 0.1
        IO_tech_dict['v_noise_independent_read'] = 0.1
        IO_tech_dict['v_noise_independent_addr'] = 0.1

        # KEEP THIS
        # Sensitivity Inputs for Timing and Voltage Noise
        IO_tech_dict['k_noise_write_sen'] = IO_tech_dict['k_noise_write'] * (1 + 0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                      0.2 * (num_mem_dq / 2 - 1))
        IO_tech_dict['k_noise_read_sen'] = IO_tech_dict['k_noise_read'] * (1 + 0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                    0.2 * (num_mem_dq / 2 - 1))
        IO_tech_dict['k_noise_addr_sen'] = IO_tech_dict['k_noise_addr'] * (1 + 0.1 * (IO_tech_dict['rtt_ca'] / 100 - 1) +
                                                                    0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                    0.2 * (num_mem_ca / 16 - 1))

        IO_tech_dict['t_jitter_setup_sen'] = IO_tech_dict['t_jitter_setup'] * (1 + 0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                          0.3 * (num_mem_dq / 2 - 1))
        IO_tech_dict['t_jitter_hold_sen'] = IO_tech_dict['t_jitter_hold'] * (1 + 0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                        0.3 * (num_mem_dq / 2 - 1))
        IO_tech_dict['t_jitter_addr_setup_sen'] = IO_tech_dict['t_jitter_addr_setup'] * (1 + 0.2 * (IO_tech_dict['rtt_ca'] / 100 - 1) +
                                                                                  0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                                  0.4 * (num_mem_ca / 16 - 1))
        IO_tech_dict['t_jitter_addr_hold_sen'] = IO_tech_dict['t_jitter_addr_hold'] * (1 + 0.2 * (IO_tech_dict['rtt_ca'] / 100 - 1) +
                                                                                0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                                0.4 * (num_mem_ca / 16 - 1))
        # KEEP THIS


        # PHY Static Power Coefficients (mW)
        IO_tech_dict['phy_datapath_s'] = 0
        IO_tech_dict['phy_phase_rotator_s'] = 5
        IO_tech_dict['phy_clock_tree_s'] = 0
        IO_tech_dict['phy_rx_s'] = 3
        IO_tech_dict['phy_dcc_s'] = 0
        IO_tech_dict['phy_deskew_s'] = 0
        IO_tech_dict['phy_leveling_s'] = 0
        IO_tech_dict['phy_pll_s'] = 2

        # PHY Dynamic Power Coefficients (mW/Gbps)
        IO_tech_dict['phy_datapath_d'] = 0.3
        IO_tech_dict['phy_phase_rotator_d'] = 0.01
        IO_tech_dict['phy_clock_tree_d'] = 0.4
        IO_tech_dict['phy_rx_d'] = 0.2
        IO_tech_dict['phy_dcc_d'] = 0
        IO_tech_dict['phy_deskew_d'] = 0
        IO_tech_dict['phy_leveling_d'] = 0
        IO_tech_dict['phy_pll_d'] = 0.05

        # PHY Wakeup Times (Sleep to Active) (microseconds)
        IO_tech_dict['phy_pll_wtime'] = 10
        IO_tech_dict['phy_phase_rotator_wtime'] = 5
        IO_tech_dict['phy_rx_wtime'] = 2
        IO_tech_dict['phy_bandgap_wtime'] = 10
        IO_tech_dict['phy_deskew_wtime'] = 0
        IO_tech_dict['phy_vrefgen_wtime'] = 0

    elif io_type == Mem_IO_type.WideIO:
        # Technology Parameters
        IO_tech_dict['vdd_io'] = 1.2
        IO_tech_dict['v_sw_clk'] = 1.2

        # Loading parameters
        IO_tech_dict['c_int'] = 0.5
        IO_tech_dict['c_tx'] = 0.5
        IO_tech_dict['c_data'] = 0.5
        IO_tech_dict['c_addr'] = 0.35
        IO_tech_dict['i_bias'] = 0
        IO_tech_dict['i_leak'] = 500

        # IO Area coefficients
        IO_tech_dict['ioarea_c'] = 0.003
        IO_tech_dict['ioarea_k0'] = 0.2
        IO_tech_dict['ioarea_k1'] = 0.00004
        IO_tech_dict['ioarea_k2'] = 0.000000020
        IO_tech_dict['ioarea_k3'] = 0.000000000004

        # Timing parameters (ps)
        IO_tech_dict['t_ds'] = 250
        IO_tech_dict['t_is'] = 250
        IO_tech_dict['t_dh'] = 250
        IO_tech_dict['t_ih'] = 250
        IO_tech_dict['t_dcd_soc'] = 50
        IO_tech_dict['t_dcd_dram'] = 50
        IO_tech_dict['t_error_soc'] = 50
        IO_tech_dict['t_skew_setup'] = 50
        IO_tech_dict['t_skew_hold'] = 50
        IO_tech_dict['t_dqsq'] = 250
        IO_tech_dict['t_soc_setup'] = 50
        IO_tech_dict['t_soc_hold'] = 50
        IO_tech_dict['t_jitter_setup'] = 200
        IO_tech_dict['t_jitter_hold'] = 200
        IO_tech_dict['t_jitter_addr_setup'] = 200
        IO_tech_dict['t_jitter_addr_hold'] = 200
        IO_tech_dict['t_cor_margin'] = 50

        # External IO Configuration Parameters
        IO_tech_dict['r_diff_term'] = 100000
        IO_tech_dict['rtt1_dq_read'] = 100000
        IO_tech_dict['rtt2_dq_read'] = 100000
        IO_tech_dict['rtt1_dq_write'] = 100000
        IO_tech_dict['rtt2_dq_write'] = 100000
        IO_tech_dict['rtt_ca'] = 100000
        IO_tech_dict['rs1_dq'] = 0
        IO_tech_dict['rs2_dq'] = 0
        IO_tech_dict['r_stub_ca'] = 0
        IO_tech_dict['r_on'] = 75
        IO_tech_dict['r_on_ca'] = 75
        IO_tech_dict['z0'] = 50
        IO_tech_dict['t_flight'] = 0.05
        IO_tech_dict['t_flight_ca'] = 0.05

        # Voltage noise coefficients
        IO_tech_dict['k_noise_write'] = 0.2
        IO_tech_dict['k_noise_read'] = 0.2
        IO_tech_dict['k_noise_addr'] = 0.2
        IO_tech_dict['v_noise_independent_write'] = 0.1
        IO_tech_dict['v_noise_independent_read'] = 0.1
        IO_tech_dict['v_noise_independent_addr'] = 0.1

        # KEEP THIS
        # Sensitivity Inputs for Timing and Voltage Noise
        IO_tech_dict['k_noise_write_sen'] = IO_tech_dict['k_noise_write'] * (1 + 0.2 * (IO_tech_dict['r_on'] / 50 - 1) +
                                                                      0.2 * (num_mem_dq / 2 - 1))
        IO_tech_dict['k_noise_read_sen'] = IO_tech_dict['k_noise_read'] * (1 + 0.2 * (IO_tech_dict['r_on'] / 50 - 1) +
                                                                    0.2 * (num_mem_dq / 2 - 1))
        IO_tech_dict['k_noise_addr_sen'] = IO_tech_dict['k_noise_addr'] * (1 + 0.2 * (IO_tech_dict['r_on'] / 50 - 1) +
                                                                    0.2 * (num_mem_ca / 16 - 1))

        IO_tech_dict['t_jitter_setup_sen'] = IO_tech_dict['t_jitter_setup'] * (1 + 0.1 * (IO_tech_dict['r_on'] / 50 - 1) +
                                                                          0.3 * (num_mem_dq / 2 - 1))
        IO_tech_dict['t_jitter_hold_sen'] = IO_tech_dict['t_jitter_hold'] * (1 + 0.1 * (IO_tech_dict['r_on'] / 50 - 1) +
                                                                        0.3 * (num_mem_dq / 2 - 1))
        IO_tech_dict['t_jitter_addr_setup_sen'] = IO_tech_dict['t_jitter_addr_setup'] * (1 + 0.1 * (IO_tech_dict['r_on'] / 50 - 1) +
                                                                                  0.4 * (num_mem_ca / 16 - 1))
        IO_tech_dict['t_jitter_addr_hold_sen'] = IO_tech_dict['t_jitter_addr_hold'] * (1 + 0.1 * (IO_tech_dict['r_on'] / 50 - 1) +
                                                                                0.4 * (num_mem_ca / 16 - 1))
        # KEEP THIS

        # PHY Static Power Coefficients (mW)
        IO_tech_dict['phy_datapath_s'] = 0
        IO_tech_dict['phy_phase_rotator_s'] = 1
        IO_tech_dict['phy_clock_tree_s'] = 0
        IO_tech_dict['phy_rx_s'] = 0
        IO_tech_dict['phy_dcc_s'] = 0
        IO_tech_dict['phy_deskew_s'] = 0
        IO_tech_dict['phy_leveling_s'] = 0
        IO_tech_dict['phy_pll_s'] = 0

        # PHY Dynamic Power Coefficients (mW/Gbps)
        IO_tech_dict['phy_datapath_d'] = 0.3
        IO_tech_dict['phy_phase_rotator_d'] = 0.01
        IO_tech_dict['phy_clock_tree_d'] = 0.2
        IO_tech_dict['phy_rx_d'] = 0.1
        IO_tech_dict['phy_dcc_d'] = 0
        IO_tech_dict['phy_deskew_d'] = 0
        IO_tech_dict['phy_leveling_d'] = 0
        IO_tech_dict['phy_pll_d'] = 0

        # PHY Wakeup Times (Sleep to Active) (microseconds)
        IO_tech_dict['phy_pll_wtime'] = 10
        IO_tech_dict['phy_phase_rotator_wtime'] = 0
        IO_tech_dict['phy_rx_wtime'] = 0
        IO_tech_dict['phy_bandgap_wtime'] = 0
        IO_tech_dict['phy_deskew_wtime'] = 0
        IO_tech_dict['phy_vrefgen_wtime'] = 0

    elif io_type == "DDR3":
        # Default parameters for DDR3
        IO_tech_dict['vdd_io'] = 1.5
        IO_tech_dict['v_sw_clk'] = 0.75

        # Loading parameters
        IO_tech_dict['c_int'] = 1.5
        IO_tech_dict['c_tx'] = 2
        IO_tech_dict['c_data'] = 1.5
        IO_tech_dict['c_addr'] = 0.75
        IO_tech_dict['i_bias'] = 15
        IO_tech_dict['i_leak'] = 1000

        # IO Area coefficients
        IO_tech_dict['ioarea_c'] = 0.01
        IO_tech_dict['ioarea_k0'] = 0.5
        IO_tech_dict['ioarea_k1'] = 0.00015
        IO_tech_dict['ioarea_k2'] = 0.000000045
        IO_tech_dict['ioarea_k3'] = 0.000000000015

        # Timing parameters (ps)
        IO_tech_dict['t_ds'] = 150
        IO_tech_dict['t_is'] = 150
        IO_tech_dict['t_dh'] = 150
        IO_tech_dict['t_ih'] = 150
        IO_tech_dict['t_dcd_soc'] = 50
        IO_tech_dict['t_dcd_dram'] = 50
        IO_tech_dict['t_error_soc'] = 25
        IO_tech_dict['t_skew_setup'] = 25
        IO_tech_dict['t_skew_hold'] = 25
        IO_tech_dict['t_dqsq'] = 100
        IO_tech_dict['t_soc_setup'] = 50
        IO_tech_dict['t_soc_hold'] = 50
        IO_tech_dict['t_jitter_setup'] = 100
        IO_tech_dict['t_jitter_hold'] = 100
        IO_tech_dict['t_jitter_addr_setup'] = 100
        IO_tech_dict['t_jitter_addr_hold'] = 100
        IO_tech_dict['t_cor_margin'] = 30

        # External IO Configuration Parameters
        IO_tech_dict['r_diff_term'] = 100

        # Switch case for connection
        if connection == "UDIMM":
            IO_tech_dict['rtt1_dq_write'] = rtt1_wr_bob_dimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_write'] = rtt2_wr_bob_dimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt1_dq_read'] = rtt1_rd_bob_dimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_read'] = rtt2_rd_bob_dimm_ddr3[num_loads - 1][frequency_index(io_type)]
        elif connection == "RDIMM":
            IO_tech_dict['rtt1_dq_write'] = rtt1_wr_host_dimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_write'] = rtt2_wr_host_dimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt1_dq_read'] = rtt1_rd_host_dimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_read'] = rtt2_rd_host_dimm_ddr3[num_loads - 1][frequency_index(io_type)]
        elif connection == "LRDIMM":
            IO_tech_dict['rtt1_dq_write'] = rtt1_wr_lrdimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_write'] = rtt2_wr_lrdimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt1_dq_read'] = rtt1_rd_lrdimm_ddr3[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_read'] = rtt2_rd_lrdimm_ddr3[num_loads - 1][frequency_index(io_type)]

        # print(f'rtt1_dq_read {IO_tech_dict["rtt1_dq_read"]}; {num_loads - 1}; {frequency_index(io_type)}; {connection}')
        # Printing with f-strings
        print(f"rtt1_dq_write: {IO_tech_dict['rtt1_dq_write']}")
        print(f"rtt2_dq_write: {IO_tech_dict['rtt2_dq_write']}")
        print(f"rtt1_dq_read: {IO_tech_dict['rtt1_dq_read']}")
        print(f"rtt2_dq_read: {IO_tech_dict['rtt2_dq_read']}")

        # Example for printing num_loads and g_ip.ron_value (assuming g_ip is defined)
        print(f"num_loads: {num_loads}")
        print(f"ron_value: {g_ip.ron_value}")

        IO_tech_dict['rtt_ca'] = 50
        IO_tech_dict['rs1_dq'] = 15
        IO_tech_dict['rs2_dq'] = 15
        IO_tech_dict['r_stub_ca'] = 0
        IO_tech_dict['r_on'] = g_ip.ron_value
        print(f"IN DDR3 {g_ip.ron_value}")
        IO_tech_dict['r_on_ca'] = 50
        IO_tech_dict['z0'] = 50
        IO_tech_dict['t_flight'] = g_ip.tflight_value
        IO_tech_dict['t_flight_ca'] = 2

        # Voltage noise coefficients
        IO_tech_dict['k_noise_write'] = 0.2
        IO_tech_dict['k_noise_read'] = 0.2
        IO_tech_dict['k_noise_addr'] = 0.2
        IO_tech_dict['v_noise_independent_write'] = 0.1
        IO_tech_dict['v_noise_independent_read'] = 0.1
        IO_tech_dict['v_noise_independent_addr'] = 0.1

        # KEEP THIS
        # Sensitivity Inputs for Timing and Voltage Noise
        IO_tech_dict['k_noise_write_sen'] = IO_tech_dict['k_noise_write'] * (1 + 0.1 * (IO_tech_dict['rtt1_dq_write'] / 60 - 1) +
                                                               0.2 * (IO_tech_dict['rtt2_dq_write'] / 60 - 1) +
                                                               0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                               0.2 * (num_mem_dq / 2 - 1))

        IO_tech_dict['k_noise_read_sen'] = IO_tech_dict['k_noise_read'] * (1 + 0.1 * (IO_tech_dict['rtt1_dq_read'] / 60 - 1) +
                                                                    0.2 * (IO_tech_dict['rtt2_dq_read'] / 60 - 1) +
                                                                    0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                    0.2 * (num_mem_dq / 2 - 1))

        IO_tech_dict['k_noise_addr_sen'] = IO_tech_dict['k_noise_addr'] * (1 + 0.1 * (IO_tech_dict['rtt_ca'] / 50 - 1) +
                                                                    0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                    0.2 * (num_mem_ca / 16 - 1))

        IO_tech_dict['t_jitter_setup_sen'] = IO_tech_dict['t_jitter_setup'] * (1 + 0.2 * (IO_tech_dict['rtt1_dq_write'] / 60 - 1) +
                                                                          0.3 * (IO_tech_dict['rtt2_dq_write'] / 60 - 1) +
                                                                          0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                          0.3 * (num_mem_dq / 2 - 1))

        IO_tech_dict['t_jitter_hold_sen'] = IO_tech_dict['t_jitter_hold'] * (1 + 0.2 * (IO_tech_dict['rtt1_dq_write'] / 60 - 1) +
                                                                        0.3 * (IO_tech_dict['rtt2_dq_write'] / 60 - 1) +
                                                                        0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                        0.3 * (num_mem_dq / 2 - 1))

        IO_tech_dict['t_jitter_addr_setup_sen'] = IO_tech_dict['t_jitter_addr_setup'] * (1 + 0.2 * (IO_tech_dict['rtt_ca'] / 50 - 1) +
                                                                                  0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                                  0.4 * (num_mem_ca / 16 - 1))

        IO_tech_dict['t_jitter_addr_hold_sen'] = IO_tech_dict['t_jitter_addr_hold'] * (1 + 0.2 * (IO_tech_dict['rtt_ca'] / 50 - 1) +
                                                                                0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                                0.4 * (num_mem_ca / 16 - 1))

        # KEEP THIS

        # PHY Static Power Coefficients (mW)
        IO_tech_dict['phy_datapath_s'] = 0
        IO_tech_dict['phy_phase_rotator_s'] = 10
        IO_tech_dict['phy_clock_tree_s'] = 0
        IO_tech_dict['phy_rx_s'] = 10
        IO_tech_dict['phy_dcc_s'] = 0
        IO_tech_dict['phy_deskew_s'] = 0
        IO_tech_dict['phy_leveling_s'] = 0
        IO_tech_dict['phy_pll_s'] = 10

        # PHY Dynamic Power Coefficients (mW/Gbps)
        IO_tech_dict['phy_datapath_d'] = 0.5
        IO_tech_dict['phy_phase_rotator_d'] = 0.01
        IO_tech_dict['phy_clock_tree_d'] = 0.5
        IO_tech_dict['phy_rx_d'] = 0.5
        IO_tech_dict['phy_dcc_d'] = 0.05
        IO_tech_dict['phy_deskew_d'] = 0.1
        IO_tech_dict['phy_leveling_d'] = 0.05
        IO_tech_dict['phy_pll_d'] = 0.05

        # PHY Wakeup Times (Sleep to Active) (microseconds)
        IO_tech_dict['phy_pll_wtime'] = 10
        IO_tech_dict['phy_phase_rotator_wtime'] = 5
        IO_tech_dict['phy_rx_wtime'] = 2
        IO_tech_dict['phy_bandgap_wtime'] = 10
        IO_tech_dict['phy_deskew_wtime'] = 0.003
        IO_tech_dict['phy_vrefgen_wtime'] = 0.5


    elif io_type == "DDR4":
        # Default parameters for DDR4
        IO_tech_dict['vdd_io'] = 1.2
        IO_tech_dict['v_sw_clk'] = 0.6

        # Loading parameters
        IO_tech_dict['c_int'] = 1.5
        IO_tech_dict['c_tx'] = 2
        IO_tech_dict['c_data'] = 1
        IO_tech_dict['c_addr'] = 0.75
        IO_tech_dict['i_bias'] = 15
        IO_tech_dict['i_leak'] = 1000

        # IO Area coefficients
        IO_tech_dict['ioarea_c'] = 0.01
        IO_tech_dict['ioarea_k0'] = 0.35
        IO_tech_dict['ioarea_k1'] = 0.00008
        IO_tech_dict['ioarea_k2'] = 0.000000035
        IO_tech_dict['ioarea_k3'] = 0.000000000010

        # Timing parameters (ps)
        IO_tech_dict['t_ds'] = 30
        IO_tech_dict['t_is'] = 60
        IO_tech_dict['t_dh'] = 30
        IO_tech_dict['t_ih'] = 60
        IO_tech_dict['t_dcd_soc'] = 20
        IO_tech_dict['t_dcd_dram'] = 20
        IO_tech_dict['t_error_soc'] = 15
        IO_tech_dict['t_skew_setup'] = 15
        IO_tech_dict['t_skew_hold'] = 15
        IO_tech_dict['t_dqsq'] = 50
        IO_tech_dict['t_soc_setup'] = 20
        IO_tech_dict['t_soc_hold'] = 10
        IO_tech_dict['t_jitter_setup'] = 30
        IO_tech_dict['t_jitter_hold'] = 30
        IO_tech_dict['t_jitter_addr_setup'] = 60
        IO_tech_dict['t_jitter_addr_hold'] = 60
        IO_tech_dict['t_cor_margin'] = 10

        # External IO Configuration Parameters
        IO_tech_dict['r_diff_term'] = 100

        if connection == "UDIMM":
            IO_tech_dict['rtt1_dq_write'] = rtt1_wr_bob_dimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_write'] = rtt2_wr_bob_dimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt1_dq_read'] = rtt1_rd_bob_dimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_read'] = rtt2_rd_bob_dimm_ddr4[num_loads - 1][frequency_index(io_type)]
        elif connection == "RDIMM":
            IO_tech_dict['rtt1_dq_write'] = rtt1_wr_host_dimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_write'] = rtt2_wr_host_dimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt1_dq_read'] = rtt1_rd_host_dimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_read'] = rtt2_rd_host_dimm_ddr4[num_loads - 1][frequency_index(io_type)]
        elif connection == "LRDIMM":
            IO_tech_dict['rtt1_dq_write'] = rtt1_wr_lrdimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_write'] = rtt2_wr_lrdimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt1_dq_read'] = rtt1_rd_lrdimm_ddr4[num_loads - 1][frequency_index(io_type)]
            IO_tech_dict['rtt2_dq_read'] = rtt2_rd_lrdimm_ddr4[num_loads - 1][frequency_index(io_type)]

        IO_tech_dict['rtt_ca'] = 50
        IO_tech_dict['rs1_dq'] = 15
        IO_tech_dict['rs2_dq'] = 15
        IO_tech_dict['r_stub_ca'] = 0
        IO_tech_dict['r_on'] = g_ip.ron_value
        IO_tech_dict['r_on_ca'] = 50
        IO_tech_dict['z0'] = 50
        IO_tech_dict['t_flight'] = g_ip.tflight_value
        IO_tech_dict['t_flight_ca'] = 2

        # Voltage noise coefficients
        IO_tech_dict['k_noise_write'] = 0.2
        IO_tech_dict['k_noise_read'] = 0.2
        IO_tech_dict['k_noise_addr'] = 0.2
        IO_tech_dict['v_noise_independent_write'] = 0.1
        IO_tech_dict['v_noise_independent_read'] = 0.1
        IO_tech_dict['v_noise_independent_addr'] = 0.1

        # KEEP THIS
        # Sensitivity Inputs for Timing and Voltage Noise
        IO_tech_dict['k_noise_write_sen'] = IO_tech_dict['k_noise_write'] * (1 + 0.1 * (IO_tech_dict['rtt1_dq_write'] / 60 - 1) +
                                                                      0.2 * (IO_tech_dict['rtt2_dq_write'] / 60 - 1) +
                                                                      0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                      0.2 * (num_mem_dq / 2 - 1))

        IO_tech_dict['k_noise_read_sen'] = IO_tech_dict['k_noise_read'] * (1 + 0.1 * (IO_tech_dict['rtt1_dq_read'] / 60 - 1) +
                                                                    0.2 * (IO_tech_dict['rtt2_dq_read'] / 60 - 1) +
                                                                    0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                    0.2 * (num_mem_dq / 2 - 1))

        IO_tech_dict['k_noise_addr_sen'] = IO_tech_dict['k_noise_addr'] * (1 + 0.1 * (IO_tech_dict['rtt_ca'] / 50 - 1) +
                                                                    0.2 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                    0.2 * (num_mem_ca / 16 - 1))

        IO_tech_dict['t_jitter_setup_sen'] = IO_tech_dict['t_jitter_setup'] * (1 + 0.2 * (IO_tech_dict['rtt1_dq_write'] / 60 - 1) +
                                                                          0.3 * (IO_tech_dict['rtt2_dq_write'] / 60 - 1) +
                                                                          0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                          0.3 * (num_mem_dq / 2 - 1))

        IO_tech_dict['t_jitter_hold_sen'] = IO_tech_dict['t_jitter_hold'] * (1 + 0.2 * (IO_tech_dict['rtt1_dq_write'] / 60 - 1) +
                                                                        0.3 * (IO_tech_dict['rtt2_dq_write'] / 60 - 1) +
                                                                        0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                        0.3 * (num_mem_dq / 2 - 1))

        IO_tech_dict['t_jitter_addr_setup_sen'] = IO_tech_dict['t_jitter_addr_setup'] * (1 + 0.2 * (IO_tech_dict['rtt_ca'] / 50 - 1) +
                                                                                  0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                                  0.4 * (num_mem_ca / 16 - 1))

        IO_tech_dict['t_jitter_addr_hold_sen'] = IO_tech_dict['t_jitter_addr_hold'] * (1 + 0.2 * (IO_tech_dict['rtt_ca'] / 50 - 1) +
                                                                                0.1 * (IO_tech_dict['r_on'] / 34 - 1) +
                                                                                0.4 * (num_mem_ca / 16 - 1))
        # KEEP THIS


        # PHY Static Power Coefficients (mW)
        IO_tech_dict['phy_datapath_s'] = 0
        IO_tech_dict['phy_phase_rotator_s'] = 10
        IO_tech_dict['phy_clock_tree_s'] = 0
        IO_tech_dict['phy_rx_s'] = 10
        IO_tech_dict['phy_dcc_s'] = 0
        IO_tech_dict['phy_deskew_s'] = 0
        IO_tech_dict['phy_leveling_s'] = 0
        IO_tech_dict['phy_pll_s'] = 10

        # PHY Dynamic Power Coefficients (mW/Gbps)
        IO_tech_dict['phy_datapath_d'] = 0.5
        IO_tech_dict['phy_phase_rotator_d'] = 0.01
        IO_tech_dict['phy_clock_tree_d'] = 0.5
        IO_tech_dict['phy_rx_d'] = 0.5
        IO_tech_dict['phy_dcc_d'] = 0.05
        IO_tech_dict['phy_deskew_d'] = 0.1
        IO_tech_dict['phy_leveling_d'] = 0.05
        IO_tech_dict['phy_pll_d'] = 0.05

        # PHY Wakeup Times (Sleep to Active) (microseconds)
        IO_tech_dict['phy_pll_wtime'] = 10
        IO_tech_dict['phy_phase_rotator_wtime'] = 5
        IO_tech_dict['phy_rx_wtime'] = 2
        IO_tech_dict['phy_bandgap_wtime'] = 10
        IO_tech_dict['phy_deskew_wtime'] = 0.003
        IO_tech_dict['phy_vrefgen_wtime'] = 0.5


    elif io_type == "Serial":
        # Default parameters for Serial
        # IO Supply voltage (V)
        IO_tech_dict['vdd_io'] = 1.2
        IO_tech_dict['v_sw_clk'] = 0.75

        # IO Area coefficients
        IO_tech_dict['ioarea_c'] = 0.01
        IO_tech_dict['ioarea_k0'] = 0.15
        IO_tech_dict['ioarea_k1'] = 0.00005
        IO_tech_dict['ioarea_k2'] = 0.000000025
        IO_tech_dict['ioarea_k3'] = 0.000000000005

        # Timing parameters (ps)
        IO_tech_dict['t_ds'] = 15
        IO_tech_dict['t_dh'] = 15
        IO_tech_dict['t_dcd_soc'] = 10
        IO_tech_dict['t_dcd_dram'] = 10
        IO_tech_dict['t_soc_setup'] = 10
        IO_tech_dict['t_soc_hold'] = 10
        IO_tech_dict['t_jitter_setup'] = 20
        IO_tech_dict['t_jitter_hold'] = 20

        # External IO Configuration Parameters
        IO_tech_dict['r_diff_term'] = 100

        # KEEP THIS
        t_jitter_setup_sen = IO_tech_dict['t_jitter_setup']
        t_jitter_hold_sen = IO_tech_dict['t_jitter_hold']
        t_jitter_addr_setup_sen = IO_tech_dict['t_jitter_addr_setup']
        t_jitter_addr_hold_sen = IO_tech_dict['t_jitter_addr_hold']
        # KEEP THIS

        # PHY Static Power Coefficients (mW)
        IO_tech_dict['phy_datapath_s'] = 0
        IO_tech_dict['phy_phase_rotator_s'] = 10
        IO_tech_dict['phy_clock_tree_s'] = 0
        IO_tech_dict['phy_rx_s'] = 10
        IO_tech_dict['phy_dcc_s'] = 0
        IO_tech_dict['phy_deskew_s'] = 0
        IO_tech_dict['phy_leveling_s'] = 0
        IO_tech_dict['phy_pll_s'] = 10

        # PHY Dynamic Power Coefficients (mW/Gbps)
        IO_tech_dict['phy_datapath_d'] = 0.5
        IO_tech_dict['phy_phase_rotator_d'] = 0.01
        IO_tech_dict['phy_clock_tree_d'] = 0.5
        IO_tech_dict['phy_rx_d'] = 0.5
        IO_tech_dict['phy_dcc_d'] = 0.05
        IO_tech_dict['phy_deskew_d'] = 0.1
        IO_tech_dict['phy_leveling_d'] = 0.05
        IO_tech_dict['phy_pll_d'] = 0.05

        # PHY Wakeup Times (Sleep to Active) (microseconds)
        IO_tech_dict['phy_pll_wtime'] = 10
        IO_tech_dict['phy_phase_rotator_wtime'] = 5
        IO_tech_dict['phy_rx_wtime'] = 2
        IO_tech_dict['phy_bandgap_wtime'] = 10
        IO_tech_dict['phy_deskew_wtime'] = 0.003
        IO_tech_dict['phy_vrefgen_wtime'] = 0.5

    else:
        print("Not Yet supported")
        sys.exit(1)

    # SWING AND TERMINATION CALCULATIONS

    # KEEP THIS
    # R|| calculation
    IO_tech_dict['rpar_write'] = (IO_tech_dict['rtt1_dq_write'] + IO_tech_dict['rs1_dq']) * (IO_tech_dict['rtt2_dq_write'] + IO_tech_dict['rs2_dq']) / (
        IO_tech_dict['rtt1_dq_write'] + IO_tech_dict['rs1_dq'] + IO_tech_dict['rtt2_dq_write'] + IO_tech_dict['rs2_dq'])
    IO_tech_dict['rpar_read'] = (IO_tech_dict['rtt1_dq_read']) * (IO_tech_dict['rtt2_dq_read'] + IO_tech_dict['rs2_dq']) / (
        IO_tech_dict['rtt1_dq_read'] + IO_tech_dict['rtt2_dq_read'] + IO_tech_dict['rs2_dq'])

    # Swing calculation
    IO_tech_dict['v_sw_data_read_load1'] = IO_tech_dict['vdd_io'] * (IO_tech_dict['rtt1_dq_read']) * (IO_tech_dict['rtt2_dq_read'] + IO_tech_dict['rs2_dq']) / (
        (IO_tech_dict['rtt1_dq_read'] + IO_tech_dict['rtt2_dq_read'] + IO_tech_dict['rs2_dq']) * (IO_tech_dict['r_on'] + IO_tech_dict['rs1_dq'] + IO_tech_dict['rpar_read']))
    IO_tech_dict['v_sw_data_read_load2'] = IO_tech_dict['vdd_io'] * (IO_tech_dict['rtt1_dq_read']) * (IO_tech_dict['rtt2_dq_read']) / (
        (IO_tech_dict['rtt1_dq_read'] + IO_tech_dict['rtt2_dq_read'] + IO_tech_dict['rs2_dq']) * (IO_tech_dict['r_on'] + IO_tech_dict['rs1_dq'] + IO_tech_dict['rpar_read']))
    IO_tech_dict['v_sw_data_read_line'] = IO_tech_dict['vdd_io'] * IO_tech_dict['rpar_read'] / (IO_tech_dict['r_on'] + IO_tech_dict['rs1_dq'] + IO_tech_dict['rpar_read'])
    IO_tech_dict['v_sw_addr'] = IO_tech_dict['vdd_io'] * IO_tech_dict['rtt_ca'] / (50 + IO_tech_dict['rtt_ca'])
    IO_tech_dict['v_sw_data_write_load1'] = IO_tech_dict['vdd_io'] * (IO_tech_dict['rtt1_dq_write']) * (IO_tech_dict['rtt2_dq_write'] + IO_tech_dict['rs2_dq']) / (
        (IO_tech_dict['rtt1_dq_write'] + IO_tech_dict['rs1_dq'] + IO_tech_dict['rtt2_dq_write'] + IO_tech_dict['rs2_dq']) * (IO_tech_dict['r_on'] + IO_tech_dict['rpar_write']))
    IO_tech_dict['v_sw_data_write_load2'] = IO_tech_dict['vdd_io'] * (IO_tech_dict['rtt2_dq_write']) * (IO_tech_dict['rtt1_dq_write'] + IO_tech_dict['rs1_dq']) / (
        (IO_tech_dict['rtt1_dq_write'] + IO_tech_dict['rs1_dq'] + IO_tech_dict['rtt2_dq_write'] + IO_tech_dict['rs2_dq']) * (IO_tech_dict['r_on'] + IO_tech_dict['rpar_write']))
    IO_tech_dict['v_sw_data_write_line'] = IO_tech_dict['vdd_io'] * IO_tech_dict['rpar_write'] / (IO_tech_dict['r_on'] + IO_tech_dict['rpar_write'])
    # KEEP THIS
    
    return IO_tech_dict



