import sys
from hw_symbols import symbol_table as sympy_var

# Constants
INF = float('inf')
NUM_DIMM = 1

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
        self.vdd_io = sympy_var['vdd_io']  # IO Supply voltage (V)
        self.v_sw_clk = sympy_var['v_sw_clk']  # Voltage swing on CLK/CLKB (V)

        # Loading parameters
        self.c_int = sympy_var['c_int']  # Internal IO loading (pF)
        self.c_tx = sympy_var['c_tx']  # IO TX self-load including package (pF)
        self.c_data = sympy_var['c_data']  # Device loading per memory data pin (pF)
        self.c_addr = sympy_var['c_addr']  # Device loading per memory address pin (pF)
        self.i_bias = sympy_var['i_bias']  # Bias current (mA)
        self.i_leak = sympy_var['i_leak']  # Active leakage current per pin (nA)

        # IO Area coefficients
        self.ioarea_c = sympy_var['ioarea_c']  # IO Area baseline coefficient for control circuitry and overhead (sq.mm.)
        self.ioarea_k0 = sympy_var['ioarea_k0']  # IO Area coefficient for the driver, for unit drive strength or output impedance (sq.mm * ohms)
        self.ioarea_k1 = sympy_var['ioarea_k1']  # IO Area coefficient for the predriver final stage (sq.mm * ohms / MHz)
        self.ioarea_k2 = sympy_var['ioarea_k2']  # IO Area coefficient for predriver middle stage (sq.mm * ohms / MHz^2)
        self.ioarea_k3 = sympy_var['ioarea_k3']  # IO Area coefficient for predriver first stage (sq.mm * ohms / MHz^3)

        # Timing parameters (ps)
        self.t_ds = sympy_var['t_ds']  # DQ setup time at DRAM
        self.t_is = sympy_var['t_is']  # CA setup time at DRAM
        self.t_dh = sympy_var['t_dh']  # DQ hold time at DRAM
        self.t_ih = sympy_var['t_ih']  # CA hold time at DRAM
        self.t_dcd_soc = sympy_var['t_dcd_soc']  # Duty-cycle distortion at the CPU/SOC
        self.t_dcd_dram = sympy_var['t_dcd_dram']  # Duty-cycle distortion at the DRAM
        self.t_error_soc = sympy_var['t_error_soc']  # Timing error due to edge placement uncertainty of the DLL
        self.t_skew_setup = sympy_var['t_skew_setup']  # Setup skew between DQ/DQS or CA/CLK after deskewing the lines
        self.t_skew_hold = sympy_var['t_skew_hold']  # Hold skew between DQ/DQS or CA/CLK after deskewing the lines
        self.t_dqsq = sympy_var['t_dqsq']  # DQ-DQS skew at the DRAM output during Read
        self.t_soc_setup = sympy_var['t_soc_setup']  # Setup time at SOC input during Read
        self.t_soc_hold = sympy_var['t_soc_hold']  # Hold time at SOC input during Read
        self.t_jitter_setup = sympy_var['t_jitter_setup']  # Half-cycle jitter on the DQS at DRAM input affecting setup time
        self.t_jitter_hold = sympy_var['t_jitter_hold']  # Half-cycle jitter on the DQS at the DRAM input affecting hold time
        self.t_jitter_addr_setup = sympy_var['t_jitter_addr_setup']  # Half-cycle jitter on the CLK at DRAM input affecting setup time
        self.t_jitter_addr_hold = sympy_var['t_jitter_addr_hold']  # Half-cycle jitter on the CLK at the DRAM input affecting hold time
        self.t_cor_margin = sympy_var['t_cor_margin']  # Statistical correlation margin

        # Termination Parameters
        self.r_diff_term = sympy_var['r_diff_term']  # Differential termination resistor if used for CLK (Ohm)

        # ODT related termination resistor values (Ohm)
        self.rtt1_dq_read = sympy_var['rtt1_dq_read']  # DQ Read termination at CPU
        self.rtt2_dq_read = sympy_var['rtt2_dq_read']  # DQ Read termination at inactive DRAM
        self.rtt1_dq_write = sympy_var['rtt1_dq_write']  # DQ Write termination at active DRAM
        self.rtt2_dq_write = sympy_var['rtt2_dq_write']  # DQ Write termination at inactive DRAM
        self.rtt_ca = sympy_var['rtt_ca']  # CA fly-by termination
        self.rs1_dq = sympy_var['rs1_dq']  # Series resistor at active DRAM
        self.rs2_dq = sympy_var['rs2_dq']  # Series resistor at inactive DRAM
        self.r_stub_ca = sympy_var['r_stub_ca']  # Series resistor for the fly-by channel
        self.r_on = sympy_var['r_on']  # Driver impedance
        self.r_on_ca = sympy_var['r_on_ca']  # CA driver impedance

        self.z0 = sympy_var['z0']  # Line impedance (ohms): Characteristic impedance of the route
        self.t_flight = sympy_var['t_flight']  # Flight time of the interconnect (ns)
        self.t_flight_ca = sympy_var['t_flight_ca']  # Flight time of the Control/Address (CA) interconnect (ns)

        # Voltage noise coefficients
        self.k_noise_write = sympy_var['k_noise_write']  # Proportional noise coefficient for Write mode
        self.k_noise_read = sympy_var['k_noise_read']  # Proportional noise coefficient for Read mode
        self.k_noise_addr = sympy_var['k_noise_addr']  # Proportional noise coefficient for Address bus
        self.v_noise_independent_write = sympy_var['v_noise_independent_write']  # Independent noise voltage for Write mode
        self.v_noise_independent_read = sympy_var['v_noise_independent_read']  # Independent noise voltage for Read mode
        self.v_noise_independent_addr = sympy_var['v_noise_independent_addr']  # Independent noise voltage for Address bus

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
        self.phy_datapath_s = sympy_var['phy_datapath_s']  # Datapath Static Power
        self.phy_phase_rotator_s = sympy_var['phy_phase_rotator_s']  # Phase Rotator Static Power
        self.phy_clock_tree_s = sympy_var['phy_clock_tree_s']  # Clock Tree Static Power
        self.phy_rx_s = sympy_var['phy_rx_s']  # Receiver Static Power
        self.phy_dcc_s = sympy_var['phy_dcc_s']  # Duty Cycle Correction Static Power
        self.phy_deskew_s = sympy_var['phy_deskew_s']  # Deskewing Static Power
        self.phy_leveling_s = sympy_var['phy_leveling_s']  # Write and Read Leveling Static Power
        self.phy_pll_s = sympy_var['phy_pll_s']  # PHY PLL Static Power

        # PHY Dynamic Power Coefficients (mW/Gbps)
        self.phy_datapath_d = sympy_var['phy_datapath_d']  # Datapath Dynamic Power
        self.phy_phase_rotator_d = sympy_var['phy_phase_rotator_d']  # Phase Rotator Dynamic Power
        self.phy_clock_tree_d = sympy_var['phy_clock_tree_d']  # Clock Tree Dynamic Power
        self.phy_rx_d = sympy_var['phy_rx_d']  # Receiver Dynamic Power
        self.phy_dcc_d = sympy_var['phy_dcc_d']  # Duty Cycle Correction Dynamic Power
        self.phy_deskew_d = sympy_var['phy_deskew_d']  # Deskewing Dynamic Power
        self.phy_leveling_d = sympy_var['phy_leveling_d']  # Write and Read Leveling Dynamic Power
        self.phy_pll_d = sympy_var['phy_pll_d']  # PHY PLL Dynamic Power

        # PHY Wakeup Times (Sleep to Active) (microseconds)
        self.phy_pll_wtime = sympy_var['phy_pll_wtime']  # PHY PLL Wakeup Time
        self.phy_phase_rotator_wtime = sympy_var['phy_phase_rotator_wtime']  # Phase Rotator Wakeup Time
        self.phy_rx_wtime = sympy_var['phy_rx_wtime']  # Receiver Wakeup Time
        self.phy_bandgap_wtime = sympy_var['phy_bandgap_wtime']  # Bandgap Wakeup Time
        self.phy_deskew_wtime = sympy_var['phy_deskew_wtime']  # Deskewing Wakeup Time
        self.phy_vrefgen_wtime = sympy_var['phy_vrefgen_wtime']  # VREF Generator Wakeup Time

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

        # print(f"io type {self.io_type}")
        # import time
        # time.sleep(5)

        if self.io_type == Mem_IO_type.LPDDR2:
            # KEEP THIS
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
            # KEEP THIS

        elif self.io_type == Mem_IO_type.WideIO:
            # KEEP THIS
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
            # KEEP THIS

        elif self.io_type == Mem_IO_type.DDR3:
            # KEEP THIS
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
            # KEEP THIS

        elif self.io_type == Mem_IO_type.DDR4:
            # KEEP THIS
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
            # KEEP THIS

        elif self.io_type == Mem_IO_type.Serial:
            # KEEP THIS
            self.t_jitter_setup_sen = self.t_jitter_setup
            self.t_jitter_hold_sen = self.t_jitter_hold
            self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup
            self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold
            # KEEP THIS

        else:
            print("Not Yet supported")
            sys.exit(1)

        # KEEP THIS
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
        # KEEP THIS

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



