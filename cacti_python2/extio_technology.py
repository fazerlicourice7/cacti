import math

INF = float('inf')

from .cacti_interface import Mem_IO_type, InputParameter
from .const import *

# # We define enumerations that appear in the code.
# class Mem_IO_type:
#     DDR3 = 0
#     DDR4 = 1
#     LPDDR2 = 2
#     WideIO = 3
#     Low_Swing_Diff = 4
#     Serial = 5

# # The code references "NCH", "PCH" but not in the snippet. 
# # If needed, define them:
# NCH = 0
# PCH = 1

# # The code references "InputParameter" but also calls it "g_ip".
# # We'll define a minimal placeholder.
# class InputParameter:
#     def __init__(self):
#         # The snippet references these:
#         self.io_type = Mem_IO_type.DDR3
#         self.num_mem_dq = 1
#         self.num_dq = 8
#         self.mem_data_width = 8
#         self.num_clk = 2
#         self.rtt_value = 60
#         self.ron_value = 34
#         self.tflight_value = 2.0

#         # etc. fill in more if needed

# # The code references DRAM models in the constructor "connection" param:
# #  0 => (bob-dimm)
# #  1 => (host-dimm)
# #  2 => (on-dimm) or LRDIMM
# # We'll keep that as numeric constants, or define an enum.

# ------------------------------------------------------------------
# The large data tables from extio_technology.cc:
rtt1_wr_lrdimm_ddr3 = [
    [INF, INF, 120, 120],
    [INF, INF, 120, 120],
    [INF, 120, 120, 80],
    [120,120,120,60],
    [120,120,120,60],
    [120,80,80,60],
    [120,80,80,60],
    [120,80,60,40]
]

rtt2_wr_lrdimm_ddr3 = [
    [INF, INF, INF, INF],
    [INF, INF, 120, 120],
    [120,120,120,80],
    [120,120,80,60],
    [120,120,80,60],
    [120,80,60,40],
    [120,80,60,40],
    [80,80,40,30]
]

rtt1_rd_lrdimm_ddr3 = [
    [INF, INF, 120, 120],
    [INF, INF, 120, 120],
    [INF, 120, 120, 80],
    [120,120,120,60],
    [120,120,120,60],
    [120,80,80,60],
    [120,80,80,60],
    [120,80,60,40]
]

rtt2_rd_lrdimm_ddr3 = [
    [INF, INF, INF, INF],
    [INF, 120, 80, 60],
    [120,80,80,40],
    [120,80,60,40],
    [120,80,60,40],
    [80,60,60,30],
    [80,60,60,30],
    [80,60,40,20]
]

rtt1_wr_host_dimm_ddr3 = [
    [120,120,120,60],
    [120,80,80,60],
    [120,80,60,40]
]
rtt2_wr_host_dimm_ddr3 = [
    [120,120,80,60],
    [120,80,60,40],
    [80,80,40,30]
]
rtt1_rd_host_dimm_ddr3 = [
    [120,120,120,60],
    [120,80,80,60],
    [120,80,60,40]
]
rtt2_rd_host_dimm_ddr3 = [
    [120,80,60,40],
    [80,60,60,30],
    [80,60,40,20]
]

rtt1_wr_bob_dimm_ddr3 = [
    [INF,120,120,80],
    [120,120,120,60],
    [120,80,80,60]
]
rtt2_wr_bob_dimm_ddr3 = [
    [120,120,120,80],
    [120,120,80,60],
    [120,80,60,40]
]
rtt1_rd_bob_dimm_ddr3 = [
    [INF,120,120,80],
    [120,120,120,60],
    [120,80,80,60]
]
rtt2_rd_bob_dimm_ddr3 = [
    [120,80,80,40],
    [120,80,60,40],
    [80,60,60,30]
]

# DDR4
rtt1_wr_lrdimm_ddr4 = [
    [120,120,80,80],
    [120,120,80,80],
    [120,80,80,60],
    [80,60,60,60],
    [80,60,60,60],
    [60,60,60,40],
    [60,60,60,40],
    [40,40,40,40]
]
rtt2_wr_lrdimm_ddr4 = [
    [INF,INF,INF,INF],
    [120,120,120,80],
    [120,80,80,80],
    [80,80,80,60],
    [80,80,80,60],
    [60,60,60,40],
    [60,60,60,40],
    [60,40,40,30]
]
rtt1_rd_lrdimm_ddr4 = [
    [120,120,80,80],
    [120,120,80,60],
    [120,80,80,60],
    [120,60,60,60],
    [120,60,60,60],
    [80,60,60,40],
    [80,60,60,40],
    [60,40,40,30]
]
rtt2_rd_lrdimm_ddr4 = [
    [INF,INF,INF,INF],
    [80,60,60,60],
    [60,60,40,40],
    [60,40,40,40],
    [60,40,40,40],
    [40,40,40,30],
    [40,40,40,30],
    [40,30,30,20]
]

rtt1_wr_host_dimm_ddr4 = [
    [80,60,60,60],
    [60,60,60,60],
    [40,40,40,40]
]
rtt2_wr_host_dimm_ddr4 = [
    [80,80,80,60],
    [60,60,60,40],
    [60,40,40,30]
]
rtt1_rd_host_dimm_ddr4 = [
    [120,60,60,60],
    [80,60,60,40],
    [60,40,40,30]
]
rtt2_rd_host_dimm_ddr4 = [
    [60,40,40,40],
    [40,40,40,30],
    [40,30,30,20]
]

rtt1_wr_bob_dimm_ddr4 = [
    [120,80,80,60],
    [80,60,60,60],
    [60,60,60,40]
]
rtt2_wr_bob_dimm_ddr4 = [
    [120,80,80,80],
    [80,80,80,60],
    [60,60,60,40]
]
rtt1_rd_bob_dimm_ddr4 = [
    [120,80,80,60],
    [120,60,60,60],
    [80,60,60,40]
]
rtt2_rd_bob_dimm_ddr4 = [
    [60,60,40,40],
    [60,40,40,40],
    [40,40,40,30]
]

# ------------------------------------------------------------------

class IOTechParam:
    """
    Python version of the C++ class IOTechParam.
    In C++, it has two constructors:
       IOTechParam(InputParameter *),
       IOTechParam(InputParameter *, Mem_IO_type, int num_mem_dq, int mem_data_width, etc.)
    In Python, we can't overload constructors easily. We'll unify them:
    
    We replicate each field and the same logic.  Also note we remove references to
    global singletons like g_ip-> or g_tp->, and we expect you to pass in needed values.
    """
    def __init__(self,
                 g_ip=None,
                 custom=False,
                 io_type=None,
                 num_mem_dq=0,
                 mem_data_width=0,
                 num_dq=0,
                 connection=0,
                 num_loads=0,
                 freq=0.0):
        """
        If custom=False, we do the single-constructor behavior (IOTechParam(InputParameter *)).
        If custom=True, we do the second constructor's logic with the extra parameters.
        """
        # In case user did not pass a valid g_ip:
        if g_ip is None:
            g_ip = InputParameter()  # default

        # We'll define all the public members from the .h:
        self.num_mem_ca = 0.0
        self.num_mem_clk = 0.0
        self.vdd_io = 0.0
        self.v_sw_clk = 0.0
        self.c_int = 0.0
        self.c_tx = 0.0
        self.c_data = 0.0
        self.c_addr = 0.0
        self.i_bias = 0.0
        self.i_leak = 0.0
        self.ioarea_c = 0.0
        self.ioarea_k0 = 0.0
        self.ioarea_k1 = 0.0
        self.ioarea_k2 = 0.0
        self.ioarea_k3 = 0.0
        self.t_ds = 0.0
        self.t_is = 0.0
        self.t_dh = 0.0
        self.t_ih = 0.0
        self.t_dcd_soc = 0.0
        self.t_dcd_dram = 0.0
        self.t_error_soc = 0.0
        self.t_skew_setup = 0.0
        self.t_skew_hold = 0.0
        self.t_dqsq = 0.0
        self.t_soc_setup = 0.0
        self.t_soc_hold = 0.0
        self.t_jitter_setup = 0.0
        self.t_jitter_hold = 0.0
        self.t_jitter_addr_setup = 0.0
        self.t_jitter_addr_hold = 0.0
        self.t_cor_margin = 0.0
        self.r_diff_term = 0.0
        self.rtt1_dq_read = 0.0
        self.rtt2_dq_read = 0.0
        self.rtt1_dq_write = 0.0
        self.rtt2_dq_write = 0.0
        self.rtt_ca = 0.0
        self.rs1_dq = 0.0
        self.rs2_dq = 0.0
        self.r_stub_ca = 0.0
        self.r_on = 0.0
        self.r_on_ca = 0.0
        self.z0 = 0.0
        self.t_flight = 0.0
        self.t_flight_ca = 0.0
        self.k_noise_write = 0.0
        self.k_noise_read = 0.0
        self.k_noise_addr = 0.0
        self.v_noise_independent_write = 0.0
        self.v_noise_independent_read = 0.0
        self.v_noise_independent_addr = 0.0
        self.k_noise_write_sen = 0.0
        self.k_noise_read_sen = 0.0
        self.k_noise_addr_sen = 0.0
        self.t_jitter_setup_sen = 0.0
        self.t_jitter_hold_sen = 0.0
        self.t_jitter_addr_setup_sen = 0.0
        self.t_jitter_addr_hold_sen = 0.0
        self.rpar_write = 0.0
        self.rpar_read = 0.0
        self.v_sw_data_read_load1 = 0.0
        self.v_sw_data_read_load2 = 0.0
        self.v_sw_data_read_line = 0.0
        self.v_sw_addr = 0.0
        self.v_sw_data_write_load1 = 0.0
        self.v_sw_data_write_load2 = 0.0
        self.v_sw_data_write_line = 0.0
        self.phy_datapath_s = 0.0
        self.phy_phase_rotator_s = 0.0
        self.phy_clock_tree_s = 0.0
        self.phy_rx_s = 0.0
        self.phy_dcc_s = 0.0
        self.phy_deskew_s = 0.0
        self.phy_leveling_s = 0.0
        self.phy_pll_s = 0.0
        self.phy_datapath_d = 0.0
        self.phy_phase_rotator_d = 0.0
        self.phy_clock_tree_d = 0.0
        self.phy_rx_d = 0.0
        self.phy_dcc_d = 0.0
        self.phy_deskew_d = 0.0
        self.phy_leveling_d = 0.0
        self.phy_pll_d = 0.0
        self.phy_pll_wtime = 0.0
        self.phy_phase_rotator_wtime = 0.0
        self.phy_rx_wtime = 0.0
        self.phy_bandgap_wtime = 0.0
        self.phy_deskew_wtime = 0.0
        self.phy_vrefgen_wtime = 0.0
        self.frequency = 0.0
        self.io_type = Mem_IO_type.DDR3

        if not custom:
            # This is the logic from IOTechParam(InputParameter*) constructor.
            # We'll replicate the entire big if-else from extio_technology.cc.
            self._init_from_g_ip(g_ip)
        else:
            # This replicates the logic from the second constructor:
            #   IOTechParam(InputParameter *, Mem_IO_type io_type, int num_mem_dq,
            #               int mem_data_width, int num_dq, int connection,
            #               int num_loads, double freq)
            self._init_custom(g_ip, io_type, num_mem_dq, mem_data_width, num_dq, connection, num_loads, freq)

    def frequnecy_index(self, type_):
        """
        This replicates IOTechParam::frequnecy_index(Mem_IO_type)
        """
        if type_ == Mem_IO_type.DDR3:
            if self.frequency <= 400: return 0
            elif self.frequency <= 533: return 1
            elif self.frequency <= 667: return 2
            else: return 3
        elif type_ == Mem_IO_type.DDR4:
            if self.frequency <= 800: return 0
            elif self.frequency <= 933: return 1
            elif self.frequency <= 1066: return 2
            else: return 3
        else:
            # The code: assert(false)
            raise ValueError("Invalid IO_type for frequency_index")
        return 0

    def _init_from_g_ip(self, g_ip):
        """
        The monolithic constructor from extio_technology.cc that sets default
        parameters based on g_ip->io_type.
        """
        # The code sets num_mem_ca = g_ip->num_mem_dq * (g_ip->num_dq / g_ip->mem_data_width)
        # plus so forth.  We'll replicate:
        self.num_mem_ca = g_ip.num_mem_dq * (g_ip.num_dq/g_ip.mem_data_width)
        # similarly for self.num_mem_clk:
        self.num_mem_clk = g_ip.num_mem_dq * (g_ip.num_dq/g_ip.mem_data_width)/(g_ip.num_clk/2)

        self.io_type = g_ip.io_type

        # The big if-else for each DDR standard:
        if g_ip.io_type == Mem_IO_type.LPDDR2:
            # set all the fields
            self._init_lpddr2(g_ip)
        elif g_ip.io_type == Mem_IO_type.WideIO:
            self._init_wideio(g_ip)
        elif g_ip.io_type == Mem_IO_type.DDR3:
            self._init_ddr3(g_ip)
        elif g_ip.io_type == Mem_IO_type.DDR4:
            self._init_ddr4(g_ip)
        elif g_ip.io_type == Mem_IO_type.Serial:
            self._init_serial(g_ip)
        else:
            print("Not yet supported.")
            raise ValueError("Not yet supported IO_type")

        # Then do R|| and swing calculations:
        self._calc_rpar_and_swing()

    def _init_custom(self, g_ip,
                     io_type,
                     num_mem_dq,
                     mem_data_width,
                     num_dq,
                     connection,
                     num_loads,
                     freq):
        """
        The second constructor logic from extio_technology.cc
        """
        self.io_type = io_type
        self.frequency = freq

        self.num_mem_ca = num_mem_dq * mem_data_width
        self.num_mem_clk = num_mem_dq * (num_dq / mem_data_width) / (g_ip.num_clk / 2)

        # replicate the big if-else from the code:
        if io_type == Mem_IO_type.LPDDR2:
            self._init_lpddr2(g_ip)
        elif io_type == Mem_IO_type.WideIO:
            self._init_wideio(g_ip)
        elif io_type == Mem_IO_type.DDR3:
            self._init_ddr3(g_ip, connection, num_loads)
        elif io_type == Mem_IO_type.DDR4:
            self._init_ddr4(g_ip, connection, num_loads)
        elif io_type == Mem_IO_type.Serial:
            self._init_serial(g_ip)
        else:
            print("Not Yet supported.")
            raise ValueError("Unsupported IO type")

        # re-calc rpar, swings:
        self._calc_rpar_and_swing()

    # The following private helpers replicate each DDR standard's logic:

    def _init_lpddr2(self, g_ip):
        # from the snippet in extio_technology.cc
        self.vdd_io = 1.2
        self.v_sw_clk = 1.0
        self.c_int = 1.5
        self.c_tx = 2.0
        self.c_data = 1.5
        self.c_addr = 0.75
        self.i_bias = 5
        self.i_leak = 1000
        self.ioarea_c = 0.01
        self.ioarea_k0 = 0.5
        self.ioarea_k1 = 0.00008
        self.ioarea_k2 = 0.00000003
        self.ioarea_k3 = 0.000000000008

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

        self.k_noise_write = 0.2
        self.k_noise_read = 0.2
        self.k_noise_addr = 0.2
        self.v_noise_independent_write = 0.1
        self.v_noise_independent_read = 0.1
        self.v_noise_independent_addr = 0.1

        # Sensitivity code:
        self.k_noise_write_sen = self.k_noise_write * (1 + 0.2*(self.r_on/34 - 1) +
                                                       0.2*(self.num_mem_ca/2 - 1))
        self.k_noise_read_sen = self.k_noise_read * (1 + 0.2*(self.r_on/34 - 1) +
                                                     0.2*(self.num_mem_ca/2 - 1))
        self.k_noise_addr_sen = self.k_noise_addr * (1 + 0.1*(self.rtt_ca/100 - 1) +
                                                     0.2*(self.r_on/34 - 1) +
                                                     0.2*(self.num_mem_ca/16 - 1))

        self.t_jitter_setup_sen = self.t_jitter_setup * (1 + 0.1*(self.r_on/34 - 1) +
                                                         0.3*(self.num_mem_ca/2 - 1))
        self.t_jitter_hold_sen = self.t_jitter_hold * (1 + 0.1*(self.r_on/34 - 1) +
                                                       0.3*(self.num_mem_ca/2 - 1))
        self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup * (1 + 0.2*(self.rtt_ca/100 - 1) +
                                                                   0.1*(self.r_on/34 - 1) +
                                                                   0.4*(self.num_mem_ca/16 - 1))
        self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold * (1 + 0.2*(self.rtt_ca/100 - 1) +
                                                                 0.1*(self.r_on/34 - 1) +
                                                                 0.4*(self.num_mem_ca/16 - 1))

        # PHY static power
        self.phy_datapath_s = 0
        self.phy_phase_rotator_s = 5
        self.phy_clock_tree_s = 0
        self.phy_rx_s = 3
        self.phy_dcc_s = 0
        self.phy_deskew_s = 0
        self.phy_leveling_s = 0
        self.phy_pll_s = 2

        # PHY dynamic power
        self.phy_datapath_d = 0.3
        self.phy_phase_rotator_d = 0.01
        self.phy_clock_tree_d = 0.4
        self.phy_rx_d = 0.2
        self.phy_dcc_d = 0
        self.phy_deskew_d = 0
        self.phy_leveling_d = 0
        self.phy_pll_d = 0.05

        # Wakeup times
        self.phy_pll_wtime = 10
        self.phy_phase_rotator_wtime = 5
        self.phy_rx_wtime = 2
        self.phy_bandgap_wtime = 10
        self.phy_deskew_wtime = 0
        self.phy_vrefgen_wtime = 0

    def _init_wideio(self, g_ip):
        self.vdd_io = 1.2
        self.v_sw_clk = 1.2
        self.c_int = 0.5
        self.c_tx = 0.5
        self.c_data = 0.5
        self.c_addr = 0.35
        self.i_bias = 0
        self.i_leak = 500
        self.ioarea_c = 0.003
        self.ioarea_k0 = 0.2
        self.ioarea_k1 = 0.00004
        self.ioarea_k2 = 0.00000002
        self.ioarea_k3 = 0.000000000004

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

        self.k_noise_write = 0.2
        self.k_noise_read = 0.2
        self.k_noise_addr = 0.2
        self.v_noise_independent_write = 0.1
        self.v_noise_independent_read = 0.1
        self.v_noise_independent_addr = 0.1

        self.k_noise_write_sen = self.k_noise_write * (1 + 0.2*(self.r_on/50 - 1) +
                                                       0.2*(self.num_mem_ca/2 - 1))
        self.k_noise_read_sen = self.k_noise_read * (1 + 0.2*(self.r_on/50 - 1) +
                                                     0.2*(self.num_mem_ca/2 - 1))
        self.k_noise_addr_sen = self.k_noise_addr * (1 + 0.2*(self.r_on/50 - 1) +
                                                     0.2*(self.num_mem_ca/16 - 1))

        self.t_jitter_setup_sen = self.t_jitter_setup * (1 + 0.1*(self.r_on/50 - 1) +
                                                         0.3*(self.num_mem_ca/2 - 1))
        self.t_jitter_hold_sen = self.t_jitter_hold * (1 + 0.1*(self.r_on/50 - 1) +
                                                       0.3*(self.num_mem_ca/2 - 1))
        self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup * (1 + 0.1*(self.r_on/50 - 1) +
                                                                   0.4*(self.num_mem_ca/16 - 1))
        self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold * (1 + 0.1*(self.r_on/50 - 1) +
                                                                 0.4*(self.num_mem_ca/16 - 1))

        self.phy_datapath_s = 0
        self.phy_phase_rotator_s = 1
        self.phy_clock_tree_s = 0
        self.phy_rx_s = 0
        self.phy_dcc_s = 0
        self.phy_deskew_s = 0
        self.phy_leveling_s = 0
        self.phy_pll_s = 0

        self.phy_datapath_d = 0.3
        self.phy_phase_rotator_d = 0.01
        self.phy_clock_tree_d = 0.2
        self.phy_rx_d = 0.1
        self.phy_dcc_d = 0
        self.phy_deskew_d = 0
        self.phy_leveling_d = 0
        self.phy_pll_d = 0

        self.phy_pll_wtime = 10
        self.phy_phase_rotator_wtime = 0
        self.phy_rx_wtime = 0
        self.phy_bandgap_wtime = 0
        self.phy_deskew_wtime = 0
        self.phy_vrefgen_wtime = 0

    def _init_ddr3(self, g_ip, connection=None, num_loads=None):
        # "connection" and "num_loads" are used only in the second constructor logic.
        # So if we are in the single-constructor path, they may be None.
        self.vdd_io = 1.5
        self.v_sw_clk = 0.75
        self.c_int = 1.5
        self.c_tx = 2
        self.c_data = 1.5
        self.c_addr = 0.75
        self.i_bias = 15
        self.i_leak = 1000
        self.ioarea_c = 0.01
        self.ioarea_k0 = 0.5
        self.ioarea_k1 = 0.00015
        self.ioarea_k2 = 0.000000045
        self.ioarea_k3 = 0.000000000015
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
        self.r_diff_term = 100

        # If we are in the second constructor, we override rtt1_dq, etc. based on "connection" and "num_loads".
        if connection is not None and num_loads is not None:
            # select the relevant table
            # connection: 0 => bob-dimm, 1 => host-dimm, 2 => lrdimm
            freq_index = self.frequnecy_index(Mem_IO_type.DDR3)
            if connection == 0:
                self.rtt1_dq_write = rtt1_wr_bob_dimm_ddr3[num_loads-1][freq_index]
                self.rtt2_dq_write = rtt2_wr_bob_dimm_ddr3[num_loads-1][freq_index]
                self.rtt1_dq_read  = rtt1_rd_bob_dimm_ddr3[num_loads-1][freq_index]
                self.rtt2_dq_read  = rtt2_rd_bob_dimm_ddr3[num_loads-1][freq_index]
            elif connection == 1:
                self.rtt1_dq_write = rtt1_wr_host_dimm_ddr3[num_loads-1][freq_index]
                self.rtt2_dq_write = rtt2_wr_host_dimm_ddr3[num_loads-1][freq_index]
                self.rtt1_dq_read  = rtt1_rd_host_dimm_ddr3[num_loads-1][freq_index]
                self.rtt2_dq_read  = rtt2_rd_host_dimm_ddr3[num_loads-1][freq_index]
            elif connection == 2:
                self.rtt1_dq_write = rtt1_wr_lrdimm_ddr3[num_loads-1][freq_index]
                self.rtt2_dq_write = rtt2_wr_lrdimm_ddr3[num_loads-1][freq_index]
                self.rtt1_dq_read  = rtt1_rd_lrdimm_ddr3[num_loads-1][freq_index]
                self.rtt2_dq_read  = rtt2_rd_lrdimm_ddr3[num_loads-1][freq_index]
            else:
                pass
        else:
            # defaults from the single-constructor path
            self.rtt1_dq_read = g_ip.rtt_value
            self.rtt2_dq_read = g_ip.rtt_value
            self.rtt1_dq_write= g_ip.rtt_value
            self.rtt2_dq_write= g_ip.rtt_value

        self.rtt_ca = 50
        self.rs1_dq = 15
        self.rs2_dq = 15
        self.r_stub_ca = 0
        self.r_on = g_ip.ron_value
        self.r_on_ca = 50
        self.z0 = 50
        self.t_flight = g_ip.tflight_value
        self.t_flight_ca = 2

        self.k_noise_write = 0.2
        self.k_noise_read = 0.2
        self.k_noise_addr = 0.2
        self.v_noise_independent_write = 0.1
        self.v_noise_independent_read = 0.1
        self.v_noise_independent_addr = 0.1

        # Sensitivity:
        self.k_noise_write_sen = self.k_noise_write * (
            1 + 0.1*(self.rtt1_dq_write/60 - 1) +
            0.2*(self.rtt2_dq_write/60 - 1) +
            0.2*(self.r_on/34 - 1) +
            0.2*(g_ip.num_mem_dq/2 - 1)
        )
        self.k_noise_read_sen = self.k_noise_read * (
            1 + 0.1*(self.rtt1_dq_read/60 - 1) +
            0.2*(self.rtt2_dq_read/60 - 1) +
            0.2*(self.r_on/34 - 1) +
            0.2*(g_ip.num_mem_dq/2 - 1)
        )
        self.k_noise_addr_sen = self.k_noise_addr * (
            1 + 0.1*(self.rtt_ca/50 - 1) +
            0.2*(self.r_on/34 - 1) +
            0.2*(self.num_mem_ca/16 - 1)
        )

        self.t_jitter_setup_sen = self.t_jitter_setup * (
            1 + 0.2*(self.rtt1_dq_write/60 - 1) +
            0.3*(self.rtt2_dq_write/60 - 1) +
            0.1*(self.r_on/34 - 1) +
            0.3*(g_ip.num_mem_dq/2 - 1)
        )
        self.t_jitter_hold_sen = self.t_jitter_hold * (
            1 + 0.2*(self.rtt1_dq_write/60 - 1) +
            0.3*(self.rtt2_dq_write/60 - 1) +
            0.1*(self.r_on/34 - 1) +
            0.3*(g_ip.num_mem_dq/2 - 1)
        )
        self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup * (
            1 + 0.2*(self.rtt_ca/50 - 1) +
            0.1*(self.r_on/34 - 1) +
            0.4*(self.num_mem_ca/16 - 1)
        )
        self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold * (
            1 + 0.2*(self.rtt_ca/50 - 1) +
            0.1*(self.r_on/34 - 1) +
            0.4*(self.num_mem_ca/16 - 1)
        )

        self.phy_datapath_s = 0
        self.phy_phase_rotator_s = 10
        self.phy_clock_tree_s = 0
        self.phy_rx_s = 10
        self.phy_dcc_s = 0
        self.phy_deskew_s = 0
        self.phy_leveling_s = 0
        self.phy_pll_s = 10

        self.phy_datapath_d = 0.5
        self.phy_phase_rotator_d = 0.01
        self.phy_clock_tree_d = 0.5
        self.phy_rx_d = 0.5
        self.phy_dcc_d = 0.05
        self.phy_deskew_d = 0.1
        self.phy_leveling_d = 0.05
        self.phy_pll_d = 0.05

        self.phy_pll_wtime = 10
        self.phy_phase_rotator_wtime = 5
        self.phy_rx_wtime = 2
        self.phy_bandgap_wtime = 10
        self.phy_deskew_wtime = 0.003
        self.phy_vrefgen_wtime = 0.5

    def _init_ddr4(self, g_ip, connection=None, num_loads=None):
        self.vdd_io = 1.2
        self.v_sw_clk = 0.6
        self.c_int = 1.5
        self.c_tx = 2
        self.c_data = 1
        self.c_addr = 0.75
        self.i_bias = 15
        self.i_leak = 1000
        self.ioarea_c = 0.01
        self.ioarea_k0 = 0.35
        self.ioarea_k1 = 0.00008
        self.ioarea_k2 = 0.000000035
        self.ioarea_k3 = 0.00000000001
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
        self.r_diff_term = 100

        if connection is not None and num_loads is not None:
            freq_index = self.frequnecy_index(Mem_IO_type.DDR4)
            if connection == 0:
                self.rtt1_dq_write = rtt1_wr_bob_dimm_ddr4[num_loads-1][freq_index]
                self.rtt2_dq_write = rtt2_wr_bob_dimm_ddr4[num_loads-1][freq_index]
                self.rtt1_dq_read  = rtt1_rd_bob_dimm_ddr4[num_loads-1][freq_index]
                self.rtt2_dq_read  = rtt2_rd_bob_dimm_ddr4[num_loads-1][freq_index]
            elif connection == 1:
                self.rtt1_dq_write = rtt1_wr_host_dimm_ddr4[num_loads-1][freq_index]
                self.rtt2_dq_write = rtt2_wr_host_dimm_ddr4[num_loads-1][freq_index]
                self.rtt1_dq_read  = rtt1_rd_host_dimm_ddr4[num_loads-1][freq_index]
                self.rtt2_dq_read  = rtt2_rd_host_dimm_ddr4[num_loads-1][freq_index]
            elif connection == 2:
                self.rtt1_dq_write = rtt1_wr_lrdimm_ddr4[num_loads-1][freq_index]
                self.rtt2_dq_write = rtt2_wr_lrdimm_ddr4[num_loads-1][freq_index]
                self.rtt1_dq_read  = rtt1_rd_lrdimm_ddr4[num_loads-1][freq_index]
                self.rtt2_dq_read  = rtt2_rd_lrdimm_ddr4[num_loads-1][freq_index]
            else:
                pass
        else:
            self.rtt1_dq_read = g_ip.rtt_value
            self.rtt2_dq_read = g_ip.rtt_value
            self.rtt1_dq_write= g_ip.rtt_value
            self.rtt2_dq_write= g_ip.rtt_value

        self.rtt_ca = 50
        self.rs1_dq = 15
        self.rs2_dq = 15
        self.r_stub_ca = 0
        self.r_on = g_ip.ron_value
        self.r_on_ca = 50
        self.z0 = 50
        self.t_flight = g_ip.tflight_value
        self.t_flight_ca = 2

        self.k_noise_write = 0.2
        self.k_noise_read = 0.2
        self.k_noise_addr = 0.2
        self.v_noise_independent_write = 0.1
        self.v_noise_independent_read = 0.1
        self.v_noise_independent_addr = 0.1

        self.k_noise_write_sen = self.k_noise_write * (
            1 + 0.1*(self.rtt1_dq_write/60 - 1) +
            0.2*(self.rtt2_dq_write/60 - 1) +
            0.2*(self.r_on/34 - 1) +
            0.2*(g_ip.num_mem_dq/2 - 1)
        )
        self.k_noise_read_sen = self.k_noise_read * (
            1 + 0.1*(self.rtt1_dq_read/60 - 1) +
            0.2*(self.rtt2_dq_read/60 - 1) +
            0.2*(self.r_on/34 - 1) +
            0.2*(g_ip.num_mem_dq/2 - 1)
        )
        self.k_noise_addr_sen = self.k_noise_addr * (
            1 + 0.1*(self.rtt_ca/50 - 1) +
            0.2*(self.r_on/34 - 1) +
            0.2*(self.num_mem_ca/16 - 1)
        )

        self.t_jitter_setup_sen = self.t_jitter_setup * (
            1 + 0.2*(self.rtt1_dq_write/60 - 1) +
            0.3*(self.rtt2_dq_write/60 - 1) +
            0.1*(self.r_on/34 - 1) +
            0.3*(g_ip.num_mem_dq/2 - 1)
        )
        self.t_jitter_hold_sen = self.t_jitter_hold * (
            1 + 0.2*(self.rtt1_dq_write/60 - 1) +
            0.3*(self.rtt2_dq_write/60 - 1) +
            0.1*(self.r_on/34 - 1) +
            0.3*(g_ip.num_mem_dq/2 - 1)
        )
        self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup * (
            1 + 0.2*(self.rtt_ca/50 - 1) +
            0.1*(self.r_on/34 - 1) +
            0.4*(self.num_mem_ca/16 - 1)
        )
        self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold * (
            1 + 0.2*(self.rtt_ca/50 - 1) +
            0.1*(self.r_on/34 - 1) +
            0.4*(self.num_mem_ca/16 - 1)
        )

        self.phy_datapath_s = 0
        self.phy_phase_rotator_s = 10
        self.phy_clock_tree_s = 0
        self.phy_rx_s = 10
        self.phy_dcc_s = 0
        self.phy_deskew_s = 0
        self.phy_leveling_s = 0
        self.phy_pll_s = 10

        self.phy_datapath_d = 0.5
        self.phy_phase_rotator_d = 0.01
        self.phy_clock_tree_d = 0.5
        self.phy_rx_d = 0.5
        self.phy_dcc_d = 0.05
        self.phy_deskew_d = 0.1
        self.phy_leveling_d = 0.05
        self.phy_pll_d = 0.05

        self.phy_pll_wtime = 10
        self.phy_phase_rotator_wtime = 5
        self.phy_rx_wtime = 2
        self.phy_bandgap_wtime = 10
        self.phy_deskew_wtime = 0.003
        self.phy_vrefgen_wtime = 0.5

    def _init_serial(self, g_ip):
        self.vdd_io = 1.2
        self.v_sw_clk = 0.75
        self.ioarea_c = 0.01
        self.ioarea_k0 = 0.15
        self.ioarea_k1 = 0.00005
        self.ioarea_k2 = 0.000000025
        self.ioarea_k3 = 0.000000000005
        self.t_ds = 15
        self.t_dh = 15
        self.t_dcd_soc = 10
        self.t_dcd_dram = 10
        self.t_soc_setup = 10
        self.t_soc_hold = 10
        self.t_jitter_setup = 20
        self.t_jitter_hold = 20

        self.r_diff_term = 100
        # no mention of rtt1_dq*, etc.  We'll keep them at 0 unless you want a placeholder.

        self.t_jitter_setup_sen = self.t_jitter_setup
        self.t_jitter_hold_sen = self.t_jitter_hold
        self.t_jitter_addr_setup_sen = self.t_jitter_addr_setup
        self.t_jitter_addr_hold_sen = self.t_jitter_addr_hold

        self.phy_datapath_s = 0
        self.phy_phase_rotator_s = 10
        self.phy_clock_tree_s = 0
        self.phy_rx_s = 10
        self.phy_dcc_s = 0
        self.phy_deskew_s = 0
        self.phy_leveling_s = 0
        self.phy_pll_s = 10

        self.phy_datapath_d = 0.5
        self.phy_phase_rotator_d = 0.01
        self.phy_clock_tree_d = 0.5
        self.phy_rx_d = 0.5
        self.phy_dcc_d = 0.05
        self.phy_deskew_d = 0.1
        self.phy_leveling_d = 0.05
        self.phy_pll_d = 0.05

        self.phy_pll_wtime = 10
        self.phy_phase_rotator_wtime = 5
        self.phy_rx_wtime = 2
        self.phy_bandgap_wtime = 10
        self.phy_deskew_wtime = 0.003
        self.phy_vrefgen_wtime = 0.5

    def _calc_rpar_and_swing(self):
        """
        The final lines in each constructor that do:
          rpar_write, rpar_read, v_sw_data_read_load1, etc.
        """
        # rpar_write = (rtt1_dq_write + rs1_dq)*(rtt2_dq_write + rs2_dq)/(rtt1_dq_write + rs1_dq + rtt2_dq_write + rs2_dq)
        # same for rpar_read, etc.
        denom_write = (self.rtt1_dq_write + self.rs1_dq + self.rtt2_dq_write + self.rs2_dq)
        if abs(denom_write) < 1e-15:
            self.rpar_write = 0
        else:
            self.rpar_write = (self.rtt1_dq_write + self.rs1_dq)*(self.rtt2_dq_write + self.rs2_dq)/denom_write

        denom_read = (self.rtt1_dq_read + self.rtt2_dq_read + self.rs2_dq)
        if abs(denom_read) < 1e-15:
            self.rpar_read = 0
        else:
            self.rpar_read = (self.rtt1_dq_read)*(self.rtt2_dq_read + self.rs2_dq)/denom_read

        # v_sw_data_read_load1, etc.
        denom_r_read = (self.r_on + self.rs1_dq + self.rpar_read)
        if abs(denom_r_read) < 1e-15:
            self.v_sw_data_read_load1 = 0
            self.v_sw_data_read_load2 = 0
            self.v_sw_data_read_line = 0
        else:
            self.v_sw_data_read_load1 = self.vdd_io*(self.rtt1_dq_read)*(self.rtt2_dq_read+self.rs2_dq)/((self.rtt1_dq_read+self.rtt2_dq_read+self.rs2_dq)*denom_r_read)
            self.v_sw_data_read_load2 = self.vdd_io*(self.rtt1_dq_read)*(self.rtt2_dq_read)/((self.rtt1_dq_read+self.rtt2_dq_read+self.rs2_dq)*denom_r_read)
            self.v_sw_data_read_line  = self.vdd_io*self.rpar_read/denom_r_read

        self.v_sw_addr = self.vdd_io*self.rtt_ca/(50 + self.rtt_ca) if abs(50+self.rtt_ca)>1e-15 else 0

        denom_r_write = (self.r_on + self.rpar_write)
        if abs(denom_r_write) < 1e-15:
            self.v_sw_data_write_load1 = 0
            self.v_sw_data_write_load2 = 0
            self.v_sw_data_write_line = 0
        else:
            top_load1 = (self.rtt1_dq_write + self.rs1_dq)*(self.rtt2_dq_write+self.rs2_dq)
            top_load2 = (self.rtt2_dq_write)*(self.rtt1_dq_write+self.rs1_dq)
            denom_load1 = (self.rtt1_dq_write + self.rs1_dq + self.rtt2_dq_write + self.rs2_dq)*denom_r_write
            if abs(denom_load1)<1e-15:
                self.v_sw_data_write_load1=0
            else:
                self.v_sw_data_write_load1 = self.vdd_io*(self.rtt1_dq_write)*(self.rtt2_dq_write+self.rs2_dq)/denom_load1
            if abs(denom_load1)<1e-15:
                self.v_sw_data_write_load2=0
            else:
                self.v_sw_data_write_load2 = self.vdd_io*(self.rtt2_dq_write)*(self.rtt1_dq_write+self.rs1_dq)/denom_load1
            self.v_sw_data_write_line = self.vdd_io*self.rpar_write/denom_r_write
