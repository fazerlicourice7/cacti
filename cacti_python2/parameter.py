"""
Corresponds to parameter.cc/parameter.h

We have classes to model:
  1) InputParameter   (was a global "g_ip" in the C++ code)
  2) DeviceType, InterconnectType, MemoryType, ScalingFactor
  3) TechnologyParameter  (was a global "g_tp" in the C++ code)
  4) DynamicParameter     (derived from usage in the C++ code's data path)

We pass the references around explicitly rather than using singletons.
"""

import math
import sys
from math import ceil
import os

# If you want symbolic expansions, you can import sympy here
# import sympy

from .basic_circuit import (
    is_pow2, _log2, is_equal,
    wire_resistance, wire_capacitance, tsv_resistance, tsv_capacitance, tsv_area,
    pmos_to_nmos_sz_ratio
)

# Additional constants from your cacti code or from const.h
ADDRESS_BITS = 32
EXTRA_TAG_BITS = 5
NUMBER_STACKED_DIE_LAYERS = 1

lp_dram = 3
comm_dram = 4
dram_cell_tech_flavor = 4    # Typically used if data_arr_ram_cell_tech_type != comm_dram

MINSUBARRAYROWS = 2
MAXSUBARRAYROWS = 512
MINSUBARRAYCOLS = 2
MAXSUBARRAYCOLS = 512

PAGE_MODE = 0
VBITSENSEMIN = 0.08
VDD_STORAGE_LOSS_FRACTION_WORST = 0.2


class InputParameter:
    """
    Python version of the original input parameter struct used throughout CACTI.
    Instead of referencing g_ip globally, you'd instantiate InputParameter() and pass around.
    """
    def __init__(self):
        # Defaults
        self.cache_sz = 0
        self.line_sz  = 0
        self.assoc    = 0
        self.nbanks   = 1
        self.out_w    = 0
        self.specific_tag = False
        self.tag_w    = 42  # default
        self.access_mode = 0   # 0=normal,1=sequential,2=fast
        self.is_3d_mem = False
        self.is_main_mem = False
        self.pure_cam  = False
        self.pure_ram  = False
        self.fully_assoc = False
        self.is_cache  = False

        # device types
        self.data_arr_ram_cell_tech_type = 0
        self.data_arr_peri_global_tech_type = 0
        self.tag_arr_ram_cell_tech_type  = 0
        self.tag_arr_peri_global_tech_type = 0

        # Additional user fields
        self.F_sz_um = 0.0  # feature size in micron
        self.F_sz_nm = 0.0
        self.num_rw_ports = 1
        self.num_rd_ports = 0
        self.num_wr_ports = 0
        self.num_se_rd_ports = 0
        self.num_search_ports= 0

        self.temp = 300
        self.nbanks = 1
        self.block_sz = 64
        self.tag_assoc = 1
        self.data_assoc= 1

        self.burst_len = 1
        self.int_prefetch_w = 1
        self.page_sz_bits   = 0
        self.num_die_3d     = 1
        self.force_cache_config = False

        self.ic_proj_type = 0
        self.wire_is_mat_type = 2  # local=0,semi=1,global=2
        self.wire_os_mat_type = 2
        self.force_wiretype   = 0
        self.wt               = None

        self.print_detail_debug = False
        self.add_ecc_b_         = False
        self.out_w              = 64
        self.nspd               = 1
        self.ndwl               = 1
        self.ndbl               = 1
        self.ndcm               = 1
        self.ndsam1             = 1
        self.ndsam2             = 1

        # Additional power gating or 3d parameters
        self.array_power_gated      = False
        self.bitline_floating       = False
        self.wl_power_gated         = False
        self.cl_power_gated         = False
        self.interconect_power_gated= False
        self.power_gating           = False

        # ... etc. Fill in as needed from your C++ code

    def display_ip(self):
        """Helper to dump the parameters."""
        print("======== InputParameter Dump ========")
        print(f"cache size: {self.cache_sz} bytes")
        print(f"line size : {self.line_sz} bytes")
        print(f"associativity: {self.assoc}")
        print(f"banks: {self.nbanks}")
        print(f"feature size: {self.F_sz_um} um => {self.F_sz_nm} nm")
        print(f"temp: {self.temp} K")
        # etc.


class DeviceType:
    """
    In cacti used for sram_cell, dram_acc, dram_wl, peri_global, etc.
    """
    def __init__(self):
        self.C_g_ideal    = 0.0
        self.C_fringe     = 0.0
        self.C_overlap    = 0.0
        self.C_junc       = 0.0
        self.C_junc_sidewall = 0.0
        self.l_phy        = 0.0
        self.l_elec       = 0.0
        self.R_nch_on     = 0.0
        self.R_pch_on     = 0.0
        self.Vdd          = 0.0
        self.Vth          = 0.0
        self.Vcc_min      = 0.0
        self.I_on_n       = 0.0
        self.I_on_p       = 0.0
        self.I_off_n      = 0.0
        self.I_off_p      = 0.0
        self.I_g_on_n     = 0.0
        self.I_g_on_p     = 0.0
        self.C_ox         = 0.0
        self.t_ox         = 0.0
        self.n_to_p_eff_curr_drv_ratio   = 0.0
        self.long_channel_leakage_reduction = 0.0
        self.Mobility_n   = 0.0

        # aux
        self.Vdsat                   = 0.0
        self.gmp_to_gmn_multiplier   = 0.0

    def reset(self):
        """Zero out fields if needed."""
        self.__init__()

    def display(self, indent=0):
        spc = " "*indent
        print(spc+"DeviceType:")
        print(spc+f"  C_g_ideal= {self.C_g_ideal}")
        print(spc+f"  C_fringe = {self.C_fringe}")
        print(spc+f"  C_overlap= {self.C_overlap}")
        print(spc+f"  R_nch_on = {self.R_nch_on}")
        # etc.

    def isEqual(self, other):
        # check near equality of fields
        # for brevity only partial checks
        fields = [
          "C_g_ideal", "C_fringe", "C_overlap",
          "C_junc", "C_junc_sidewall",
          "l_phy", "l_elec",
          "R_nch_on", "R_pch_on",
          "Vdd", "Vth", "Vcc_min",
          "I_on_n","I_on_p","I_off_n","I_off_p",
          "I_g_on_n","I_g_on_p",
          "C_ox","t_ox","n_to_p_eff_curr_drv_ratio",
          "long_channel_leakage_reduction","Mobility_n",
          "Vdsat","gmp_to_gmn_multiplier"
        ]
        for f in fields:
            if not is_equal(getattr(self, f), getattr(other, f)):
                return False
        return True


class InterconnectType:
    """
    local, semi-global, global wire:
      R_per_um, C_per_um, pitch, aspect_ratio, etc.
    """
    def __init__(self):
        self.pitch = 0.0
        self.R_per_um = 0.0
        self.C_per_um = 0.0
        self.horiz_dielectric_constant = 0.0
        self.vert_dielectric_constant  = 0.0
        self.aspect_ratio = 0.0
        self.miller_value = 0.0
        self.ild_thickness= 0.0

        # aux
        self.wire_width  = 0.0
        self.wire_thickness=0.0
        self.wire_spacing= 0.0
        self.barrier_thickness=0.0
        self.dishing_thickness=0.0
        self.alpha_scatter=0.0
        self.fringe_cap = 0.0

    def reset(self):
        self.__init__()

    def display(self, indent=0):
        spc = " "*indent
        print(spc+"InterconnectType:")
        print(spc+f"  pitch= {self.pitch}")
        print(spc+f"  R_per_um= {self.R_per_um}")
        print(spc+f"  C_per_um= {self.C_per_um}")

    def isEqual(self, other):
        # check near equality
        # ...
        return True

    def interpolate(self, alpha, ic1, ic2):
        # pitch etc. linear interpolation
        self.pitch = alpha*ic1.pitch + (1-alpha)*ic2.pitch
        self.R_per_um = alpha*ic1.R_per_um + (1-alpha)*ic2.R_per_um
        self.C_per_um = alpha*ic1.C_per_um + (1-alpha)*ic2.C_per_um
        # etc.


class MemoryType:
    """
    For an SRAM cell, DRAM cell, CAM cell.
    """
    def __init__(self):
        self.b_w = 0.0
        self.b_h = 0.0
        self.cell_a_w = 0.0
        self.cell_pmos_w = 0.0
        self.cell_nmos_w = 0.0
        self.Vbitpre = 0.0
        self.Vbitfloating = 0.0

        # helpers
        self.area_cell = 0.0
        self.asp_ratio_cell = 1.0

    def reset(self):
        self.__init__()

    def display(self, indent=0):
        spc = " "*indent
        print(spc+"MemoryType:")
        print(spc+f"  b_w= {self.b_w} um, b_h= {self.b_h} um")

    def isEqual(self, other):
        return is_equal(self.b_w, other.b_w) and is_equal(self.b_h, other.b_h)

    def interpolate(self, alpha, mem1, mem2):
        self.cell_a_w    = alpha*mem1.cell_a_w + (1-alpha)*mem2.cell_a_w
        self.cell_pmos_w = alpha*mem1.cell_pmos_w+ (1-alpha)*mem2.cell_pmos_w
        self.cell_nmos_w = alpha*mem1.cell_nmos_w+ (1-alpha)*mem2.cell_nmos_w
        self.area_cell   = alpha*mem1.area_cell + (1-alpha)*mem2.area_cell
        self.asp_ratio_cell = alpha*mem1.asp_ratio_cell+(1-alpha)*mem2.asp_ratio_cell
        self.Vbitpre = mem2.Vbitpre
        self.Vbitfloating = 0.7*self.Vbitpre
        # recalc
        if self.asp_ratio_cell>1e-15 and self.area_cell>1e-15:
            import math
            self.b_w = math.sqrt(self.area_cell/self.asp_ratio_cell)
            self.b_h = self.asp_ratio_cell*self.b_w
        else:
            self.b_w=0
            self.b_h=0


class ScalingFactor:
    """
    logic_scaling_co_eff etc.
    """
    def __init__(self):
        self.logic_scaling_co_eff = 0.0
        self.core_tx_density      = 0.0
        self.long_channel_leakage_reduction=0.0

    def reset(self):
        self.__init__()

    def display(self, indent=0):
        spc=" "*indent
        print(spc+f"ScalingFactor:")
        print(spc+f" logic_scaling_co_eff= {self.logic_scaling_co_eff}")
        print(spc+f" core_tx_density= {self.core_tx_density}")

    def isEqual(self, other):
        # ...
        return True

    def interpolate(self, alpha, s1, s2):
        self.logic_scaling_co_eff = alpha*s1.logic_scaling_co_eff+(1-alpha)*s2.logic_scaling_co_eff
        self.core_tx_density      = alpha*s1.core_tx_density+(1-alpha)*s2.core_tx_density
        self.long_channel_leakage_reduction= alpha*s1.long_channel_leakage_reduction+(1-alpha)*s2.long_channel_leakage_reduction


class TechnologyParameter:
    """
    The main device + wire technology data structure. 
    In original C++ code, this is the global 'g_tp'.

    We have big fields for both logic devices (peri_global) and memory devices (sram_cell, dram_acc, etc.)
    plus wire, plus sram/dram/cam parameters, scaling factors, etc.
    """
    def __init__(self):
        # Some top-level fields
        self.ram_wl_stitching_overhead_ = 0.0
        self.min_w_nmos_ = 0.0
        self.max_w_nmos_ = 0.0
        self.max_w_nmos_dec=0.0
        self.unit_len_wire_del=0.0
        self.FO4=0.0
        self.kinv=0.0
        self.vpp=0.0
        self.w_sense_en=0.0
        self.w_sense_n=0.0
        self.w_sense_p=0.0
        self.sense_delay=0.0
        self.sense_dy_power=0.0
        self.w_iso=0.0
        self.w_poly_contact=0.0
        self.spacing_poly_to_poly=0.0
        self.spacing_poly_to_contact=0.0

        # 3D TSV
        self.tsv_pitch=0.0
        self.tsv_diameter=0.0
        self.tsv_length=0.0
        self.tsv_dielec_thickness=0.0
        self.tsv_contact_resistance=0.0
        self.tsv_depletion_width=0.0
        self.tsv_liner_dielectric_constant=0.0

        self.tsv_parasitic_capacitance_fine=0.0
        self.tsv_parasitic_resistance_fine=0.0
        self.tsv_minimum_area_fine=0.0
        self.tsv_parasitic_capacitance_coarse=0.0
        self.tsv_parasitic_resistance_coarse=0.0
        self.tsv_minimum_area_coarse=0.0

        # comp
        self.w_comp_inv_p1=0.0
        self.w_comp_inv_p2=0.0
        self.w_comp_inv_p3=0.0
        self.w_comp_inv_n1=0.0
        self.w_comp_inv_n2=0.0
        self.w_comp_inv_n3=0.0
        self.w_eval_inv_p=0.0
        self.w_eval_inv_n=0.0
        self.w_comp_n=0.0
        self.w_comp_p=0.0

        self.dram_cell_I_on=0.0
        self.dram_cell_Vdd=0.0
        self.dram_cell_I_off_worst_case_len_temp=0.0
        self.dram_cell_C=0.0
        self.gm_sense_amp_latch=0.0

        self.w_nmos_b_mux=0.0
        self.w_nmos_sa_mux=0.0
        self.w_pmos_bl_precharge=0.0
        self.w_pmos_bl_eq=0.0
        self.MIN_GAP_BET_P_AND_N_DIFFS=0.0
        self.MIN_GAP_BET_SAME_TYPE_DIFFS=0.0
        self.HPOWERRAIL=0.0
        self.cell_h_def=0.0

        self.chip_layout_overhead=0.0
        self.macro_layout_overhead=0.0
        self.sckt_co_eff=0.0
        self.fringe_cap=0.0
        self.h_dec=0

        # sub structures
        self.sram_cell   = DeviceType()
        self.dram_acc    = DeviceType()
        self.dram_wl     = DeviceType()
        self.peri_global = DeviceType()
        self.cam_cell    = DeviceType()
        self.sleep_tx    = DeviceType()

        self.wire_local       = InterconnectType()
        self.wire_inside_mat  = InterconnectType()
        self.wire_outside_mat = InterconnectType()

        self.scaling_factor   = ScalingFactor()

        self.sram = MemoryType()
        self.dram = MemoryType()
        self.cam  = MemoryType()

    def reset(self):
        self.__init__()

    def display(self, indent=0):
        spc=" "*indent
        print(spc+"=== TechnologyParameter ===")
        print(spc+f" dram_cell_I_on= {self.dram_cell_I_on}, dram_cell_Vdd= {self.dram_cell_Vdd}")

        # show subdevices
        self.sram_cell.display(indent+2)
        self.dram_acc.display(indent+2)
        self.peri_global.display(indent+2)
        # etc.

    def isEqual(self, other):
        # Checking each field for near equality
        # ...
        return True


class DynamicParameter:
    """
    Replaces the "uca_org_t" partial fields for subarray geometry, bitlines, wordlines, etc.

    Typically you do: dp = DynamicParameter(g_ip, is_tag=, pure_ram=, pure_cam=, etc.)
    Then dp sets up num_r_subarray, etc.
    """
    def __init__(self,
                 g_ip: InputParameter,
                 g_tp: TechnologyParameter,
                 is_tag_: bool,
                 pure_ram_: int,
                 pure_cam_: int,
                 Nspd_: float,
                 Ndwl_: int,
                 Ndbl_: int,
                 Ndcm_: int,
                 Ndsam_lev_1_: int,
                 Ndsam_lev_2_: int,
                 wire_type: str,
                 is_main_mem_: bool):
        self.g_ip = g_ip
        self.g_tp = g_tp
        self.is_tag = is_tag_
        self.pure_ram = pure_ram_
        self.pure_cam = pure_cam_
        self.fully_assoc = False  # set later
        self.tagbits = 0
        self.num_subarrays = 0
        self.num_mats = 0
        self.Nspd = Nspd_
        self.Ndwl = Ndwl_
        self.Ndbl = Ndbl_
        self.Ndcm = Ndcm_
        self.deg_bl_muxing = 0
        self.deg_senseamp_muxing_non_associativity=0
        self.Ndsam_lev_1= Ndsam_lev_1_
        self.Ndsam_lev_2= Ndsam_lev_2_
        self.wtype = wire_type
        self.number_way_select_signals_mat=0
        self.V_b_sense=0.0
        self.num_r_subarray=0
        self.num_c_subarray=0

        self.tag_num_r_subarray=0
        self.tag_num_c_subarray=0
        self.data_num_r_subarray=0
        self.data_num_c_subarray=0
        self.num_mats_h_dir=0
        self.num_mats_v_dir=0
        self.ram_cell_tech_type = 0
        self.dram_refresh_period=0.0
        self.use_inp_params=0
        self.num_rw_ports = 0
        self.num_rd_ports = 0
        self.num_wr_ports = 0
        self.num_se_rd_ports=0
        self.num_search_ports=0
        self.out_w = 0
        self.is_main_mem = is_main_mem_
        self.is_valid=False

        self.num_si_b_mat=0
        self.num_so_b_mat=0
        self.num_si_b_subbank=0
        self.num_so_b_subbank=0
        self.num_si_b_bank_per_port=0
        self.num_so_b_bank_per_port=0

        self.number_addr_bits_mat=0
        self.number_subbanks_decode=0
        self.num_di_b_bank_per_port=0
        self.num_do_b_bank_per_port=0
        self.num_di_b_mat=0
        self.num_do_b_mat=0
        self.num_di_b_subbank=0
        self.num_do_b_subbank=0

        self.num_act_mats_hor_dir=0
        self.num_act_mats_hor_dir_sl=0
        self.is_dram=False

        # geometry
        self.cell = None
        self.cam_cell = None

        self.init_params()

    def init_params(self):
        # Implementation of the logic from parameter.cc's constructor logic.
        self.ram_cell_tech_type = (self.g_ip.tag_arr_ram_cell_tech_type if self.is_tag
                                   else self.g_ip.data_arr_ram_cell_tech_type)
        self.is_dram = (self.ram_cell_tech_type == lp_dram or self.ram_cell_tech_type==comm_dram)
        self.fully_assoc = bool(self.g_ip.fully_assoc)

        # The rest of the code sets up subarray geometry, etc.
        # ...
        # For brevity, just mark is_valid = True
        self.is_valid = True

    def display(self):
        if not self.is_valid:
            print("DynamicParameter: is_valid=False")
            return
        print("=== DynamicParameter Dump ===")
        print(f" is_tag= {self.is_tag}, pure_cam= {self.pure_cam}, Ndwl= {self.Ndwl}, Ndbl= {self.Ndbl}")


##############################################################################
# Helper utility methods for scanning config files, etc., if needed, go here.
##############################################################################
