import math
from typing import List
from threading import Thread
from .cacti_interface import *
from .cacti_interface import MemArray
from .nuca import NucaOrgT
from .parameter import g_ip, g_tp
from .parameter import *
from .uca import UCA
from .parameter import _log2
import sympy as sp

BIGNUM = float('inf')
NTHREADS = 4
MAXDATAN = 4
MAX_COL_MUX = 4
MAXDATASPD = 4.0
Full_swing, Global, Low_swing = 0, 1, 2  # Just example values
Nspd, Ndwl, Ndbl, Ndcm, Ndsam_lev_1, Ndsam_lev_2, wr = sp.symbols('Nspd Ndwl Ndbl Ndcm Ndsam_lev_1 Ndsam_lev_2 wr')

class MinValuesT:
    def __init__(self):
        self.min_delay = BIGNUM
        self.min_dyn = BIGNUM
        self.min_leakage = BIGNUM
        self.min_area = BIGNUM
        self.min_cyc = BIGNUM

    def update_min_values(self, val):
        self.min_delay = sp.Min(self.min_delay, val.min_delay)
        self.min_dyn = sp.Min(self.min_dyn, val.min_dyn)
        self.min_leakage = sp.Min(self.min_leakage, val.min_leakage)
        self.min_area = sp.Min(self.min_area, val.min_area)
        self.min_cyc = sp.Min(self.min_cyc, val.min_cyc)

    def update_min_values_from_uca(self, res: uca_org_t):
        self.min_delay = sp.Min(self.min_delay, res.access_time)
        self.min_dyn = sp.Min(self.min_dyn, res.power.readOp.dynamic)
        self.min_leakage = sp.Min(self.min_leakage, res.power.readOp.leakage)
        self.min_area = sp.Min(self.min_area, res.area)
        self.min_cyc = sp.Min(self.min_cyc, res.cycle_time)

    def update_min_values_from_nuca(self, res: NucaOrgT):
        self.min_delay = sp.Min(self.min_delay, res.nuca_pda.access_time)
        self.min_dyn = sp.Min(self.min_dyn, res.nuca_pda.power.readOp.dynamic)
        self.min_leakage = sp.Min(self.min_leakage, res.nuca_pda.power.readOp.leakage)
        self.min_area = sp.Min(self.min_area, res.nuca_pda.area)
        self.min_cyc = sp.Min(self.min_cyc, res.nuca_pda.cycle_time)

    def update_min_values_from_mem_array(self, res: MemArray):
        if(not contains_any_symbol(self.min_delay) and math.isnan(self.min_delay)):
            self.min_delay = res.access_time
        elif(not contains_any_symbol(res.access_time) and math.isnan(res.access_time)):
            self.min_delay = self.min_delay
        else:
            self.min_delay = sp.Min(self.min_delay, res.access_time)

        if not sp.contains_any_symbol(self.min_dyn) and math.isnan(self.min_dyn):
            self.min_dyn = res.power.readOp.dynamic
        elif not sp.contains_any_symbol(res.power.readOp.dynamic) and math.isnan(res.power.readOp.dynamic):
            self.min_dyn = self.min_dyn
        else:
            self.min_dyn = sp.Min(self.min_dyn, res.power.readOp.dynamic)

        if not sp.contains_any_symbol(self.min_leakage) and math.isnan(self.min_leakage):
            self.min_leakage = res.power.readOp.leakage
        elif not sp.contains_any_symbol(res.power.readOp.leakage) and math.isnan(res.power.readOp.leakage):
            self.min_leakage = self.min_leakage
        else:
            self.min_leakage = sp.Min(self.min_leakage, res.power.readOp.leakage)

        if not sp.contains_any_symbol(self.min_area) and math.isnan(self.min_area):
            self.min_area = res.area
        elif not sp.contains_any_symbol(res.area) and math.isnan(res.area):
            self.min_area = self.min_area
        else:
            self.min_area = sp.Min(self.min_area, res.area)

        if not sp.contains_any_symbol(self.min_cyc) and math.isnan(self.min_cyc):
            self.min_cyc = res.cycle_time
        elif not sp.contains_any_symbol(res.cycle_time) and math.isnan(res.cycle_time):
            self.min_cyc = self.min_cyc
        else:
            self.min_cyc = sp.Min(self.min_cyc, res.cycle_time)

        # self.min_dyn = sp.Min(self.min_dyn, res.power.readOp.dynamic)
        # self.min_leakage = sp.Min(self.min_leakage, res.power.readOp.leakage)
        # self.min_area = sp.Min(self.min_area, res.area)
        # self.min_cyc = sp.Min(self.min_cyc, res.cycle_time)

class CalcTimeMtWrapperStruct:
    def __init__(self):
        self.tid = 0
        self.is_tag = False
        self.pure_ram = False
        self.pure_cam = False
        self.is_main_mem = False
        self.Nspd_min = 0.0
        self.data_res = None  # Assuming min_values_t is another class or type, set to None by default
        self.tag_res = None  # Assuming min_values_t is another class or type, set to None by default
        self.data_arr = []  # list<mem_array *> is translated to a list in Python
        self.tag_arr = []  # list<mem_array *> is translated to a list in Python

def calc_time_mt_wrapper(void_obj):
    calc_obj = void_obj
    tid = calc_obj.tid
    data_arr = calc_obj.data_arr
    tag_arr = calc_obj.tag_arr
    is_tag = calc_obj.is_tag
    pure_ram = calc_obj.pure_ram
    pure_cam = calc_obj.pure_cam
    is_main_mem = calc_obj.is_main_mem
    Nspd_min = calc_obj.Nspd_min
    data_res = calc_obj.data_res
    tag_res = calc_obj.tag_res

    data_arr.clear()
    data_arr.append(MemArray())
    tag_arr.clear()
    tag_arr.append(MemArray())

    Ndwl_niter = int(_log2(MAXDATAN)) + 1
    Ndbl_niter = int(_log2(MAXDATAN)) + 1
    Ndcm_niter = int(_log2(MAX_COL_MUX)) + 1
    niter = Ndwl_niter * Ndbl_niter * Ndcm_niter

    is_valid_partition = False
    wt_min = 0
    wt_max = 0

    if g_ip.force_wiretype:
        if g_ip.wt == 'Full_swing':
            wt_min = 'Global'
            wt_max = 'Low_swing'-1
        else:
            if g_ip.wt == 'Global':
                wt_min = wt_max = 'Global'
            elif g_ip.wt == 'Global_5':
                wt_min = wt_max = 'Global_5'
            elif g_ip.wt == 'Global_10':
                wt_min = wt_max = 'Global_10'
            elif g_ip.wt == 'Global_20':
                wt_min = wt_max = 'Global_20'
            elif g_ip.wt == 'Global_30':
                wt_min = wt_max = 'Global_30'
            elif g_ip.wt == 'Low_swing':
                wt_min = wt_max = 'Low_swing'
            else:
                raise ValueError("Unknown wire type!")
    else:
        wt_min = 'Global'
        wt_max = 'Low_swing'

    # Check Npsd_min 
    for Nspd in range(int(Nspd_min), int(MAXDATASPD), int(math.ceil(Nspd_min*2))):
        # replace with proper enum
        if(wt_min == "Global"):
            wt_min = 0
        elif(wt_min == "Global_5"):
            wt_min = 1
        elif(wt_min == "Global_10"):
            wt_min = 2
        elif(wt_min == "Global_20"):
            wt_min = 3
        elif(wt_min == "Global_30"):
            wt_min = 4
        elif(wt_min == "Low_swing"):
            wt_min = 5
        elif(wt_min == "Semi_global"):
            wt_min = 6
        elif(wt_min == "Full_swing"):
            wt_min = 7
        elif(wt_min == "Transmission"):
            wt_min = 8
        elif(wt_min == "Optical"):
            wt_min = 9
        else:
            wt_min = 10

        if(wt_max == "Global"):
            wt_max = 0
        elif(wt_max == "Global_5"):
            wt_max = 1
        elif(wt_max == "Global_10"):
            wt_max = 2
        elif(wt_max == "Global_20"):
            wt_max = 3
        elif(wt_max == "Global_30"):
            wt_max = 4
        elif(wt_max == "Low_swing"):
            wt_max = 5
        elif(wt_max == "Semi_global"):
            wt_max = 6
        elif(wt_max == "Full_swing"):
            wt_max = 7
        elif(wt_max == "Transmission"):
            wt_max = 8
        elif(wt_max == "Optical"):
            wt_max = 9
        else:
            wt_max = 10

        for wr in range(wt_min, wt_max+1):
            for iter in range(tid, niter, NTHREADS):
                Ndwl = 1 << (iter // (Ndbl_niter * Ndcm_niter))
                Ndbl = 1 << ((iter // Ndcm_niter) % Ndbl_niter)
                Ndcm = 1 << (iter % Ndcm_niter)
                Ndsam_lev_1 = 1
                Ndsam_lev_2 = 1
                for Ndsam_lev_1 in range(1, MAX_COL_MUX+1, Ndsam_lev_1*2):
                    for Ndsam_lev_2 in range(1, MAX_COL_MUX+1, Ndsam_lev_2*2):
                        if g_ip.force_cache_config and not is_tag:
                            wr = g_ip.wt
                            Ndwl = g_ip.ndwl
                            Ndbl = g_ip.ndbl
                            Ndcm = g_ip.ndcm
                            if g_ip.nspd != 0:
                                Nspd = g_ip.nspd
                            if g_ip.ndsam1 != 0:
                                Ndsam_lev_1 = g_ip.ndsam1
                                Ndsam_lev_2 = g_ip.ndsam2

                        if is_tag:
                            is_valid_partition = calculate_time(is_tag, pure_ram, pure_cam, Nspd, Ndwl,
                                                                Ndbl, Ndcm, Ndsam_lev_1, Ndsam_lev_2,
                                                                tag_arr[-1], 0, None, None, wr, is_main_mem)
                        if not is_tag or g_ip.fully_assoc:
                            is_valid_partition = calculate_time(is_tag, pure_ram, pure_cam, Nspd, Ndwl,
                                                                Ndbl, Ndcm, Ndsam_lev_1, Ndsam_lev_2,
                                                                data_arr[-1], 0, None, None, wr, is_main_mem)
                            if g_ip.is_3d_mem:
                                Ndsam_lev_1 = MAX_COL_MUX+1
                                Ndsam_lev_2 = MAX_COL_MUX+1

                        if is_valid_partition:
                            if is_tag:
                                tag_arr[-1].wt = wr
                                tag_res.update_min_values_from_mem_array(tag_arr[-1])
                                tag_arr.append(MemArray())
                            if not is_tag or g_ip.fully_assoc:
                                data_arr[-1].wt = wr
                                data_res.update_min_values_from_mem_array(data_arr[-1])
                                data_arr.append(MemArray())

                        if g_ip.force_cache_config and not is_tag:
                            wr = wt_max
                            iter = niter
                            if g_ip.nspd != 0:
                                Nspd = MAXDATASPD
                            if g_ip.ndsam1 != 0:
                                Ndsam_lev_1 = MAX_COL_MUX+1
                                Ndsam_lev_2 = MAX_COL_MUX+1
                    # Ndsam_lev_1 += 1
                    # Ndsam_lev_1 += 1

    data_arr.pop()
    tag_arr.pop()

def calculate_time(
    is_tag,
    pure_ram,
    pure_cam,
    Nspd,
    Ndwl,
    Ndbl,
    Ndcm,
    Ndsam_lev_1,
    Ndsam_lev_2,
    ptr_array,
    flag_results_populate,
    ptr_results,
    ptr_fin_res,
    wt,
    is_main_mem
):
    dyn_p = DynamicParameter(is_tag, pure_ram, pure_cam, Nspd, Ndwl, Ndbl, Ndcm, Ndsam_lev_1, Ndsam_lev_2, wt, is_main_mem)

    if not dyn_p.is_valid:
        return False

    uca = UCA(dyn_p)

    if flag_results_populate:
        # For the final solution, populate the ptr_results data structure -- TODO: copy only necessary variables
        pass
    else:
        num_act_mats_hor_dir = uca.bank.dp.num_act_mats_hor_dir
        num_mats = uca.bank.dp.num_mats
        is_fa = uca.bank.dp.fully_assoc
        pure_cam = uca.bank.dp.pure_cam

        ptr_array.Ndwl = Ndwl
        ptr_array.Ndbl = Ndbl
        ptr_array.Nspd = Nspd
        ptr_array.deg_bl_muxing = dyn_p.deg_bl_muxing
        ptr_array.Ndsam_lev_1 = Ndsam_lev_1
        ptr_array.Ndsam_lev_2 = Ndsam_lev_2
        ptr_array.access_time = uca.access_time
        ptr_array.cycle_time = uca.cycle_time
        ptr_array.multisubbank_interleave_cycle_time = uca.multisubbank_interleave_cycle_time
        ptr_array.area_ram_cells = uca.area_all_dataramcells
        ptr_array.area = uca.area.get_area()

        if g_ip.is_3d_mem:
            ptr_array.area = uca.area.get_area()
            if g_ip.num_die_3d > 1:
                ptr_array.area += uca.area_TSV_tot

        ptr_array.height = uca.area.h
        ptr_array.width = uca.area.w
        ptr_array.mat_height = uca.bank.mat.area.h
        ptr_array.mat_length = uca.bank.mat.area.w
        ptr_array.subarray_height = uca.bank.mat.subarray.area.h
        ptr_array.subarray_length = uca.bank.mat.subarray.area.w
        ptr_array.power = uca.power

        #RECENT CHANGE: MAX - ignore to reduce expression size
        ptr_array.delay_senseamp_mux_decoder = symbolic_convex_max(uca.delay_array_to_sa_mux_lev_1_decoder, uca.delay_array_to_sa_mux_lev_2_decoder)
        # ptr_array.delay_senseamp_mux_decoder = uca.delay_array_to_sa_mux_lev_1_decoder

        ptr_array.delay_before_subarray_output_driver = uca.delay_before_subarray_output_driver
        ptr_array.delay_from_subarray_output_driver_to_output = uca.delay_from_subarray_out_drv_to_out
        ptr_array.delay_route_to_bank = uca.htree_in_add.delay
        ptr_array.delay_input_htree = uca.bank.htree_in_add.delay
        ptr_array.delay_row_predecode_driver_and_block = uca.bank.mat.r_predec.delay
        ptr_array.delay_row_decoder = uca.bank.mat.row_dec.delay
        ptr_array.delay_bitlines = uca.bank.mat.delay_bitline
        ptr_array.delay_matchlines = uca.bank.mat.delay_matchchline
        ptr_array.delay_sense_amp = uca.bank.mat.delay_sa
        ptr_array.delay_subarray_output_driver = uca.bank.mat.delay_subarray_out_drv_htree
        ptr_array.delay_dout_htree = uca.bank.htree_out_data.delay
        ptr_array.delay_comparator = uca.bank.mat.delay_comparator

        if g_ip.is_3d_mem:
            ptr_array.delay_row_activate_net = uca.membus_RAS.delay_bus
            ptr_array.delay_row_predecode_driver_and_block = uca.membus_RAS.delay_add_predecoder
            ptr_array.delay_row_decoder = uca.membus_RAS.delay_add_decoder
            ptr_array.delay_local_wordline = uca.membus_RAS.delay_lwl_drv
            ptr_array.delay_column_access_net = uca.membus_CAS.delay_bus
            ptr_array.delay_column_predecoder = uca.membus_CAS.delay_add_predecoder
            ptr_array.delay_column_decoder = uca.membus_CAS.delay_add_decoder
            ptr_array.delay_column_selectline = 0
            ptr_array.delay_datapath_net = uca.membus_data.delay_bus
            ptr_array.delay_global_data = uca.membus_data.delay_global_data
            ptr_array.delay_local_data_and_drv = uca.membus_data.delay_local_data
            ptr_array.delay_data_buffer = uca.membus_data.delay_data_buffer
            ptr_array.energy_row_activate_net = uca.membus_RAS.power_bus.readOp.dynamic
            ptr_array.energy_row_predecode_driver_and_block = uca.membus_RAS.power_add_predecoder.readOp.dynamic
            ptr_array.energy_row_decoder = uca.membus_RAS.power_add_decoders.readOp.dynamic
            ptr_array.energy_local_wordline = uca.membus_RAS.power_lwl_drv.readOp.dynamic
            ptr_array.energy_bitlines = dyn_p.Ndwl * uca.bank.mat.power_bitline.readOp.dynamic
            ptr_array.energy_sense_amp = dyn_p.Ndwl * uca.bank.mat.power_sa.readOp.dynamic
            ptr_array.energy_column_access_net = uca.membus_CAS.power_bus.readOp.dynamic
            ptr_array.energy_column_predecoder = uca.membus_CAS.power_add_predecoder.readOp.dynamic
            ptr_array.energy_column_decoder = uca.membus_CAS.power_add_decoders.readOp.dynamic
            ptr_array.energy_column_selectline = uca.membus_CAS.power_col_sel.readOp.dynamic
            ptr_array.energy_datapath_net = uca.membus_data.power_bus.readOp.dynamic
            ptr_array.energy_global_data = uca.membus_data.power_global_data.readOp.dynamic
            ptr_array.energy_local_data_and_drv = uca.membus_data.power_local_data.readOp.dynamic
            ptr_array.energy_subarray_output_driver = uca.bank.mat.power_subarray_out_drv.readOp.dynamic
            ptr_array.energy_data_buffer = 0
            ptr_array.area_lwl_drv = uca.area_lwl_drv
            ptr_array.area_row_predec_dec = uca.area_row_predec_dec
            ptr_array.area_col_predec_dec = uca.area_col_predec_dec
            ptr_array.area_subarray = uca.area_subarray
            ptr_array.area_bus = uca.area_bus
            ptr_array.area_address_bus = uca.area_address_bus
            ptr_array.area_data_bus = uca.area_data_bus
            ptr_array.area_data_drv = uca.area_data_drv
            ptr_array.area_IOSA = uca.area_IOSA
            ptr_array.area_sense_amp = uca.area_sense_amp

        ptr_array.all_banks_height = uca.area.h
        ptr_array.all_banks_width = uca.area.w
        ptr_array.area_efficiency = uca.area_all_dataramcells * 100 / ptr_array.area
        ptr_array.power_routing_to_bank = uca.power_routing_to_bank
        ptr_array.power_addr_input_htree = uca.bank.htree_in_add.power
        ptr_array.power_data_input_htree = uca.bank.htree_in_data.power
        ptr_array.power_data_output_htree = uca.bank.htree_out_data.power
        ptr_array.power_row_predecoder_drivers = uca.bank.mat.r_predec.driver_power
        ptr_array.power_row_predecoder_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_blocks = uca.bank.mat.r_predec.block_power
        ptr_array.power_row_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_blocks.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_blocks.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_decoders = uca.bank.mat.power_row_decoders
        ptr_array.power_row_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_drivers = uca.bank.mat.b_mux_predec.driver_power
        ptr_array.power_bit_mux_predecoder_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_blocks = uca.bank.mat.b_mux_predec.block_power
        ptr_array.power_bit_mux_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_blocks.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_blocks.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_decoders = uca.bank.mat.power_bit_mux_decoders
        ptr_array.power_bit_mux_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers = uca.bank.mat.sa_mux_lev_1_predec.driver_power
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks = uca.bank.mat.sa_mux_lev_1_predec.block_power
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_decoders = uca.bank.mat.power_sa_mux_lev_1_decoders
        ptr_array.power_senseamp_mux_lev_1_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers = uca.bank.mat.sa_mux_lev_2_predec.driver_power
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks = uca.bank.mat.sa_mux_lev_2_predec.block_power
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_decoders = uca.bank.mat.power_sa_mux_lev_2_decoders
        ptr_array.power_senseamp_mux_lev_2_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bitlines = uca.bank.mat.power_bitline
        ptr_array.power_bitlines.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bitlines.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bitlines.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_sense_amps = uca.bank.mat.power_sa
        ptr_array.power_sense_amps.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_sense_amps.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_sense_amps.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_prechg_eq_drivers = uca.bank.mat.power_bl_precharge_eq_drv
        ptr_array.power_prechg_eq_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_prechg_eq_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_prechg_eq_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_output_drivers_at_subarray = uca.bank.mat.power_subarray_out_drv
        ptr_array.power_output_drivers_at_subarray.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_output_drivers_at_subarray.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_output_drivers_at_subarray.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_comparators = uca.bank.mat.power_comparator
        ptr_array.power_comparators.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_comparators.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_comparators.searchOp.dynamic *= num_act_mats_hor_dir

        if is_fa or pure_cam:
            ptr_array.power_htree_in_search = uca.bank.htree_in_search.power
            ptr_array.power_htree_out_search = uca.bank.htree_out_search.power
            ptr_array.power_searchline = uca.bank.mat.power_searchline
            ptr_array.power_searchline.searchOp.dynamic *= num_mats
            ptr_array.power_searchline_precharge = uca.bank.mat.power_searchline_precharge
            ptr_array.power_searchline_precharge.searchOp.dynamic *= num_mats
            ptr_array.power_matchlines = uca.bank.mat.power_matchline
            ptr_array.power_matchlines.searchOp.dynamic *= num_mats
            ptr_array.power_matchline_precharge = uca.bank.mat.power_matchline_precharge
            ptr_array.power_matchline_precharge.searchOp.dynamic *= num_mats
            ptr_array.power_matchline_to_wordline_drv = uca.bank.mat.power_ml_to_ram_wl_drv

        ptr_array.activate_energy = uca.activate_energy
        ptr_array.read_energy = uca.read_energy
        ptr_array.write_energy = uca.write_energy
        ptr_array.precharge_energy = uca.precharge_energy
        ptr_array.refresh_power = uca.refresh_power
        ptr_array.leak_power_subbank_closed_page = uca.leak_power_subbank_closed_page
        ptr_array.leak_power_subbank_open_page = uca.leak_power_subbank_open_page
        ptr_array.leak_power_request_and_reply_networks = uca.leak_power_request_and_reply_networks
        ptr_array.precharge_delay = uca.precharge_delay

        if g_ip.is_3d_mem:
            ptr_array.t_RCD = uca.t_RCD
            ptr_array.t_RAS = uca.t_RAS
            ptr_array.t_RC = uca.t_RC
            ptr_array.t_CAS = uca.t_CAS
            ptr_array.t_RP = uca.t_RP
            ptr_array.t_RRD = uca.t_RRD
            ptr_array.activate_energy = uca.activate_energy
            ptr_array.read_energy = uca.read_energy
            ptr_array.write_energy = uca.write_energy
            ptr_array.precharge_energy = uca.precharge_energy
            ptr_array.activate_power = uca.activate_power
            ptr_array.read_power = uca.read_power
            ptr_array.write_power = uca.write_power
            ptr_array.peak_read_power = uca.read_energy / ((g_ip.burst_depth) / (g_ip.sys_freq_MHz * 1e6) / 2)
            ptr_array.num_row_subarray = dyn_p.num_r_subarray
            ptr_array.num_col_subarray = dyn_p.num_c_subarray
            ptr_array.delay_TSV_tot = uca.delay_TSV_tot
            ptr_array.area_TSV_tot = uca.area_TSV_tot
            ptr_array.dyn_pow_TSV_tot = uca.dyn_pow_TSV_tot
            ptr_array.dyn_pow_TSV_per_access = uca.dyn_pow_TSV_per_access
            ptr_array.num_TSV_tot = uca.num_TSV_tot

        if g_ip.power_gating:
            ptr_array.sram_sleep_tx_width = uca.bank.mat.sram_sleep_tx.width
            ptr_array.sram_sleep_tx_area = uca.bank.mat.array_sleep_tx_area
            ptr_array.sram_sleep_wakeup_latency = uca.bank.mat.array_wakeup_t
            ptr_array.sram_sleep_wakeup_energy = uca.bank.mat.array_wakeup_e.readOp.dynamic
            ptr_array.wl_sleep_tx_width = uca.bank.mat.row_dec.sleeptx.width
            ptr_array.wl_sleep_tx_area = uca.bank.mat.wl_sleep_tx_area
            ptr_array.wl_sleep_wakeup_latency = uca.bank.mat.wl_wakeup_t
            ptr_array.wl_sleep_wakeup_energy = uca.bank.mat.wl_wakeup_e.readOp.dynamic
            ptr_array.bl_floating_wakeup_latency = uca.bank.mat.blfloating_wakeup_t
            ptr_array.bl_floating_wakeup_energy = uca.bank.mat.blfloating_wakeup_e.readOp.dynamic
            ptr_array.array_leakage = uca.bank.array_leakage
            ptr_array.wl_leakage = uca.bank.wl_leakage
            ptr_array.cl_leakage = uca.bank.cl_leakage

        ptr_array.num_active_mats = uca.bank.dp.num_act_mats_hor_dir
        ptr_array.num_submarray_mats = uca.bank.mat.num_subarrays_per_mat

    return True

def check_uca_org(u, minval):
    if ((u.access_time - minval.min_delay) * 100 / minval.min_delay) > g_ip.delay_dev:
        return False
    if ((u.power.readOp.dynamic - minval.min_dyn) / minval.min_dyn) * 100 > g_ip.dynamic_power_dev:
        return False
    if ((u.power.readOp.leakage - minval.min_leakage) / minval.min_leakage) * 100 > g_ip.leakage_power_dev:
        return False
    if ((u.cycle_time - minval.min_cyc) / minval.min_cyc) * 100 > g_ip.cycle_time_dev:
        return False
    if ((u.area - minval.min_area) / minval.min_area) * 100 > g_ip.area_dev:
        return False
    return True

def check_mem_org(u, minval):
    if ((u.access_time - minval.min_delay) * 100 / minval.min_delay) > g_ip.delay_dev:
        return False
    if ((u.power.readOp.dynamic - minval.min_dyn) / minval.min_dyn) * 100 > g_ip.dynamic_power_dev:
        return False
    if ((u.power.readOp.leakage - minval.min_leakage) / minval.min_leakage) * 100 > g_ip.leakage_power_dev:
        return False
    if ((u.cycle_time - minval.min_cyc) / minval.min_cyc) * 100 > g_ip.cycle_time_dev:
        return False
    if ((u.area - minval.min_area) / minval.min_area) * 100 > g_ip.area_dev:
        return False
    return True

def find_optimal_uca(res, minval, ulist):
    cost = 0
    min_cost = BIGNUM
    dp = g_ip.dynamic_power_wt
    lp = g_ip.leakage_power_wt
    a = g_ip.area_wt
    d = g_ip.delay_wt
    c = g_ip.cycle_time_wt

    if not ulist:
        print("ERROR: no valid cache organizations found")
        exit(0)

    for niter in ulist:
        if g_ip.ed == 1:
            cost = (niter.access_time / minval.min_delay) * (niter.power.readOp.dynamic / minval.min_dyn)
            if min_cost > cost:
                min_cost = cost
                res.update(niter)
        elif g_ip.ed == 2:
            cost = ((niter.access_time / minval.min_delay) ** 2) * (niter.power.readOp.dynamic / minval.min_dyn)
            if min_cost > cost:
                min_cost = cost
                res.update(niter)
        else:
            if check_uca_org(niter, minval):
                cost = (
                    d * (niter.access_time / minval.min_delay) +
                    c * (niter.cycle_time / minval.min_cyc) +
                    dp * (niter.power.readOp.dynamic / minval.min_dyn) +
                    lp * (niter.power.readOp.leakage / minval.min_leakage) +
                    a * (niter.area / minval.min_area)
                )
                if min_cost > cost:
                    min_cost = cost
                    res.update(niter)
                    ulist.remove(niter)
            else:
                ulist.remove(niter)

    if min_cost == BIGNUM:
        print("ERROR: no cache organizations met optimization criteria")
        exit(0)

def filter_tag_arr(min_val, mem_list):
    cost = float('inf')
    cur_cost = 0.0
    wt_delay = g_ip.delay_wt
    wt_dyn = g_ip.dynamic_power_wt
    wt_leakage = g_ip.leakage_power_wt
    wt_cyc = g_ip.cycle_time_wt
    wt_area = g_ip.area_wt
    res = None

    if not mem_list:
        print("ERROR: no valid tag organizations found")
        exit(1)

    while mem_list:
        print(len(mem_list))
        v = check_mem_org(mem_list[-1], min_val)
        if v:
            cur_cost = (wt_delay * (mem_list[-1].access_time / min_val.min_delay) +
                        wt_dyn * (mem_list[-1].power.readOp.dynamic / min_val.min_dyn) +
                        wt_leakage * (mem_list[-1].power.readOp.leakage / min_val.min_leakage) +
                        wt_area * (mem_list[-1].area / min_val.min_area) +
                        wt_cyc * (mem_list[-1].cycle_time / min_val.min_cyc))
        else:
            cur_cost = float('inf')

        if cur_cost < cost:
            if res is not None:
                del res
            cost = cur_cost
            res = mem_list[-1]
        else:
            del mem_list[-1]
        
        if(len(mem_list) > 0):
            mem_list.pop()

    if not res:
        print("ERROR: no valid tag organizations found")
        exit(0)

    mem_list.append(res)

# def filter_data_arr(curr_list):
#     if not curr_list:
#         print("ERROR: no valid data array organizations found")
#         exit(1)

#     iter_list = list(curr_list)

#     for m in iter_list:
#         if m is None:
#             exit(1)

#         if (((m.access_time - m.arr_min.min_delay) / m.arr_min.min_delay > 0.5) and
#             ((m.power.readOp.dynamic - m.arr_min.min_dyn) / m.arr_min.min_dyn > 0.5)):
#             del m
#             curr_list.remove(m)

def filter_data_arr(curr_list):
    if not curr_list:
        print("ERROR: no valid data array organizations found")
        exit(1)

    iter_list = list(curr_list)

    for m in iter_list:
        if m is None:
            exit(1)

        if (math.isnan(m.access_time) or math.isnan(m.arr_min.min_delay) or
            math.isnan(m.power.readOp.dynamic) or math.isnan(m.arr_min.min_dyn)):
            continue  # Skip this iteration if any relevant value is NaN

        if (((m.access_time - m.arr_min.min_delay) / m.arr_min.min_delay > 0.5) and
            ((m.power.readOp.dynamic - m.arr_min.min_dyn) / m.arr_min.min_dyn > 0.5)):
            curr_list.remove(m)

import threading
from functools import cmp_to_key

def solve(fin_res):
    pure_ram = g_ip.pure_ram
    pure_cam = g_ip.pure_cam

    g_tp.init(g_ip.F_sz_um, False)
    g_ip.print_detail_debug = 0

    tag_arr = []
    data_arr = []
    sol_list = [uca_org_t()]

    fin_res.tag_array.access_time = 0
    fin_res.tag_array.Ndwl = 0
    fin_res.tag_array.Ndbl = 0
    fin_res.tag_array.Nspd = 0
    fin_res.tag_array.deg_bl_muxing = 0
    fin_res.tag_array.Ndsam_lev_1 = 0
    fin_res.tag_array.Ndsam_lev_2 = 0

    calc_array = [CalcTimeMtWrapperStruct() for _ in range(NTHREADS)]
    threads = [None] * NTHREADS

    for t in range(NTHREADS):
        calc_array[t].tid = t
        calc_array[t].pure_ram = pure_ram
        calc_array[t].pure_cam = pure_cam
        calc_array[t].data_res = MinValuesT()
        calc_array[t].tag_res = MinValuesT()

    if not (pure_ram or pure_cam or g_ip.fully_assoc):
        is_tag = True
        g_tp.init(g_ip.F_sz_um, is_tag)

        for t in range(NTHREADS):
            calc_array[t].is_tag = is_tag
            calc_array[t].is_main_mem = False
            calc_array[t].Nspd_min = 0.125
            threads[t] = threading.Thread(target=calc_time_mt_wrapper, args=(calc_array[t],))
            threads[t].start()

        for t in range(NTHREADS):
            threads[t].join()

        for t in range(NTHREADS):
            calc_array[t].data_arr.sort(key=cmp_to_key(MemArray.lt))
            data_arr.extend(calc_array[t].data_arr)
            calc_array[t].tag_arr.sort(key=cmp_to_key(MemArray.lt))
            tag_arr.extend(calc_array[t].tag_arr)

    is_tag = False
    g_tp.init(g_ip.F_sz_um, is_tag)

    for t in range(NTHREADS):
        calc_array[t].is_tag = is_tag
        calc_array[t].is_main_mem = g_ip.is_main_mem
        if not (pure_cam or g_ip.fully_assoc):
            calc_array[t].Nspd_min = g_ip.out_w / (g_ip.block_sz * 8)
        else:
            calc_array[t].Nspd_min = 1

        threads[t] = threading.Thread(target=calc_time_mt_wrapper, args=(calc_array[t],))
        threads[t].start()

    for t in range(NTHREADS):
        threads[t].join()

    data_arr.clear()
    for t in range(NTHREADS):
        calc_array[t].data_arr.sort(key=cmp_to_key(MemArray.lt))
        data_arr.extend(calc_array[t].data_arr)

    d_min = MinValuesT()
    t_min = MinValuesT()
    cache_min = MinValuesT()

    for t in range(NTHREADS):
        d_min.update_min_values(calc_array[t].data_res)
        t_min.update_min_values(calc_array[t].tag_res)

    for m in data_arr:
        m.arr_min = d_min

    filter_data_arr(data_arr)
    if not (pure_ram or pure_cam or g_ip.fully_assoc):
        filter_tag_arr(t_min, tag_arr)

    if pure_ram or pure_cam or g_ip.fully_assoc:
        for m in data_arr:
            curr_org = sol_list[-1]
            curr_org.tag_array2 = None
            curr_org.data_array2 = m

            curr_org.find_delay()
            curr_org.find_energy()
            curr_org.find_area()
            curr_org.find_cyc()

            cache_min.update_min_values_from_uca(curr_org)

            sol_list.append(uca_org_t())
    else:
        while tag_arr:
            arr_temp = tag_arr.pop()
            for m in data_arr:
                curr_org = sol_list[-1]
                curr_org.tag_array2 = arr_temp
                curr_org.data_array2 = m

                curr_org.find_delay()
                curr_org.find_energy()
                curr_org.find_area()
                curr_org.find_cyc()

                cache_min.update_min_values_from_uca(curr_org)

                sol_list.append(uca_org_t())

    sol_list.pop()

    find_optimal_uca(fin_res, cache_min, sol_list)

    sol_list.clear()

    for m in data_arr:
        if m != fin_res.data_array2:
            del m
    data_arr.clear()

    for t in range(NTHREADS):
        del calc_array[t].data_res
        del calc_array[t].tag_res

    del calc_array
    del cache_min
    del d_min
    del t_min

def update(fin_res):
    if fin_res.tag_array2:
        g_tp.init(g_ip.F_sz_um, True)
        tag_arr_dyn_p = DynamicParameter(
            True, g_ip.pure_ram, g_ip.pure_cam, 
            fin_res.tag_array2.Nspd, fin_res.tag_array2.Ndwl, 
            fin_res.tag_array2.Ndbl, fin_res.tag_array2.Ndcm, 
            fin_res.tag_array2.Ndsam_lev_1, fin_res.tag_array2.Ndsam_lev_2, 
            fin_res.data_array2.wt, g_ip.is_main_mem
        )
        if tag_arr_dyn_p.is_valid:
            tag_arr = UCA(tag_arr_dyn_p)
            fin_res.tag_array2.power = tag_arr.power
        else:
            print("ERROR: Cannot retrieve array structure for leakage feedback")
            exit(1)

    g_tp.init(g_ip.F_sz_um, False)
    data_arr_dyn_p = DynamicParameter(
        False, g_ip.pure_ram, g_ip.pure_cam, 
        fin_res.data_array2.Nspd, fin_res.data_array2.Ndwl, 
        fin_res.data_array2.Ndbl, fin_res.data_array2.Ndcm, 
        fin_res.data_array2.Ndsam_lev_1, fin_res.data_array2.Ndsam_lev_2, 
        fin_res.data_array2.wt, g_ip.is_main_mem
    )
    if data_arr_dyn_p.is_valid:
        data_arr = UCA(data_arr_dyn_p)
        fin_res.data_array2.power = data_arr.power
    else:
        print("ERROR: Cannot retrieve array structure for leakage feedback")
        exit(1)

    fin_res.find_energy()

##### SINGLE SOLVE



def calculate_time_single(
    is_tag,
    pure_ram,
    pure_cam,
    Nspd,
    Ndwl,
    Ndbl,
    Ndcm,
    Ndsam_lev_1,
    Ndsam_lev_2,
    ptr_array,
    flag_results_populate,
    ptr_results,
    ptr_fin_res,
    wt,
    is_main_mem
):
    dyn_p = DynamicParameter(is_tag, pure_ram, pure_cam, Nspd, Ndwl, Ndbl, Ndcm, Ndsam_lev_1, Ndsam_lev_2, wt, is_main_mem)

    # if not dyn_p.is_valid:
    #     return False
    uca = UCA(dyn_p)

    if flag_results_populate:
        # For the final solution, populate the ptr_results data structure -- TODO: copy only necessary variables
        pass
    else:
        num_act_mats_hor_dir = uca.bank.dp.num_act_mats_hor_dir
        num_mats = uca.bank.dp.num_mats
        is_fa = uca.bank.dp.fully_assoc
        pure_cam = uca.bank.dp.pure_cam

        ptr_array.Ndwl = Ndwl
        ptr_array.Ndbl = Ndbl
        ptr_array.Nspd = Nspd
        ptr_array.deg_bl_muxing = dyn_p.deg_bl_muxing
        ptr_array.Ndsam_lev_1 = Ndsam_lev_1
        ptr_array.Ndsam_lev_2 = Ndsam_lev_2
        ptr_array.access_time = uca.access_time
        ptr_array.cycle_time = uca.cycle_time
        ptr_array.multisubbank_interleave_cycle_time = uca.multisubbank_interleave_cycle_time
        ptr_array.area_ram_cells = uca.area_all_dataramcells
        ptr_array.area = uca.area.get_area()

        if g_ip.is_3d_mem:
            ptr_array.area = uca.area.get_area()
            if g_ip.num_die_3d > 1:
                ptr_array.area += uca.area_TSV_tot

        ptr_array.height = uca.area.h
        ptr_array.width = uca.area.w
        ptr_array.mat_height = uca.bank.mat.area.h
        ptr_array.mat_length = uca.bank.mat.area.w
        ptr_array.subarray_height = uca.bank.mat.subarray.area.h
        ptr_array.subarray_length = uca.bank.mat.subarray.area.w
        ptr_array.power = uca.power

        ptr_array.delay_senseamp_mux_decoder = symbolic_convex_max(uca.delay_array_to_sa_mux_lev_1_decoder, uca.delay_array_to_sa_mux_lev_2_decoder)

        ptr_array.delay_before_subarray_output_driver = uca.delay_before_subarray_output_driver
        ptr_array.delay_from_subarray_output_driver_to_output = uca.delay_from_subarray_out_drv_to_out
        ptr_array.delay_route_to_bank = uca.htree_in_add.delay
        ptr_array.delay_input_htree = uca.bank.htree_in_add.delay
        ptr_array.delay_row_predecode_driver_and_block = uca.bank.mat.r_predec.delay
        ptr_array.delay_row_decoder = uca.bank.mat.row_dec.delay
        ptr_array.delay_bitlines = uca.bank.mat.delay_bitline
        ptr_array.delay_matchlines = uca.bank.mat.delay_matchchline
        ptr_array.delay_sense_amp = uca.bank.mat.delay_sa
        ptr_array.delay_subarray_output_driver = uca.bank.mat.delay_subarray_out_drv_htree
        ptr_array.delay_dout_htree = uca.bank.htree_out_data.delay
        ptr_array.delay_comparator = uca.bank.mat.delay_comparator

        if g_ip.is_3d_mem:
            ptr_array.delay_row_activate_net = uca.membus_RAS.delay_bus
            ptr_array.delay_row_predecode_driver_and_block = uca.membus_RAS.delay_add_predecoder
            ptr_array.delay_row_decoder = uca.membus_RAS.delay_add_decoder
            ptr_array.delay_local_wordline = uca.membus_RAS.delay_lwl_drv
            ptr_array.delay_column_access_net = uca.membus_CAS.delay_bus
            ptr_array.delay_column_predecoder = uca.membus_CAS.delay_add_predecoder
            ptr_array.delay_column_decoder = uca.membus_CAS.delay_add_decoder
            ptr_array.delay_column_selectline = 0
            ptr_array.delay_datapath_net = uca.membus_data.delay_bus
            ptr_array.delay_global_data = uca.membus_data.delay_global_data
            ptr_array.delay_local_data_and_drv = uca.membus_data.delay_local_data
            ptr_array.delay_data_buffer = uca.membus_data.delay_data_buffer
            ptr_array.energy_row_activate_net = uca.membus_RAS.power_bus.readOp.dynamic
            ptr_array.energy_row_predecode_driver_and_block = uca.membus_RAS.power_add_predecoder.readOp.dynamic
            ptr_array.energy_row_decoder = uca.membus_RAS.power_add_decoders.readOp.dynamic
            ptr_array.energy_local_wordline = uca.membus_RAS.power_lwl_drv.readOp.dynamic
            ptr_array.energy_bitlines = dyn_p.Ndwl * uca.bank.mat.power_bitline.readOp.dynamic
            ptr_array.energy_sense_amp = dyn_p.Ndwl * uca.bank.mat.power_sa.readOp.dynamic
            ptr_array.energy_column_access_net = uca.membus_CAS.power_bus.readOp.dynamic
            ptr_array.energy_column_predecoder = uca.membus_CAS.power_add_predecoder.readOp.dynamic
            ptr_array.energy_column_decoder = uca.membus_CAS.power_add_decoders.readOp.dynamic
            ptr_array.energy_column_selectline = uca.membus_CAS.power_col_sel.readOp.dynamic
            ptr_array.energy_datapath_net = uca.membus_data.power_bus.readOp.dynamic
            ptr_array.energy_global_data = uca.membus_data.power_global_data.readOp.dynamic
            ptr_array.energy_local_data_and_drv = uca.membus_data.power_local_data.readOp.dynamic
            ptr_array.energy_subarray_output_driver = uca.bank.mat.power_subarray_out_drv.readOp.dynamic
            ptr_array.energy_data_buffer = 0
            ptr_array.area_lwl_drv = uca.area_lwl_drv
            ptr_array.area_row_predec_dec = uca.area_row_predec_dec
            ptr_array.area_col_predec_dec = uca.area_col_predec_dec
            ptr_array.area_subarray = uca.area_subarray
            ptr_array.area_bus = uca.area_bus
            ptr_array.area_address_bus = uca.area_address_bus
            ptr_array.area_data_bus = uca.area_data_bus
            ptr_array.area_data_drv = uca.area_data_drv
            ptr_array.area_IOSA = uca.area_IOSA
            ptr_array.area_sense_amp = uca.area_sense_amp

        ptr_array.all_banks_height = uca.area.h
        ptr_array.all_banks_width = uca.area.w
        ptr_array.area_efficiency = uca.area_all_dataramcells * 100 / ptr_array.area
        ptr_array.power_routing_to_bank = uca.power_routing_to_bank
        ptr_array.power_addr_input_htree = uca.bank.htree_in_add.power
        ptr_array.power_data_input_htree = uca.bank.htree_in_data.power
        ptr_array.power_data_output_htree = uca.bank.htree_out_data.power
        ptr_array.power_row_predecoder_drivers = uca.bank.mat.r_predec.driver_power
        ptr_array.power_row_predecoder_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_blocks = uca.bank.mat.r_predec.block_power
        ptr_array.power_row_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_blocks.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_predecoder_blocks.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_decoders = uca.bank.mat.power_row_decoders
        ptr_array.power_row_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_row_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_drivers = uca.bank.mat.b_mux_predec.driver_power
        ptr_array.power_bit_mux_predecoder_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_blocks = uca.bank.mat.b_mux_predec.block_power
        ptr_array.power_bit_mux_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_blocks.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_blocks.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_decoders = uca.bank.mat.power_bit_mux_decoders
        ptr_array.power_bit_mux_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers = uca.bank.mat.sa_mux_lev_1_predec.driver_power
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks = uca.bank.mat.sa_mux_lev_1_predec.block_power
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_decoders = uca.bank.mat.power_sa_mux_lev_1_decoders
        ptr_array.power_senseamp_mux_lev_1_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers = uca.bank.mat.sa_mux_lev_2_predec.driver_power
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks = uca.bank.mat.sa_mux_lev_2_predec.block_power
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_decoders = uca.bank.mat.power_sa_mux_lev_2_decoders
        ptr_array.power_senseamp_mux_lev_2_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_2_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bitlines = uca.bank.mat.power_bitline
        ptr_array.power_bitlines.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bitlines.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bitlines.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_sense_amps = uca.bank.mat.power_sa
        ptr_array.power_sense_amps.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_sense_amps.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_sense_amps.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_prechg_eq_drivers = uca.bank.mat.power_bl_precharge_eq_drv
        ptr_array.power_prechg_eq_drivers.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_prechg_eq_drivers.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_prechg_eq_drivers.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_output_drivers_at_subarray = uca.bank.mat.power_subarray_out_drv
        ptr_array.power_output_drivers_at_subarray.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_output_drivers_at_subarray.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_output_drivers_at_subarray.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_comparators = uca.bank.mat.power_comparator
        ptr_array.power_comparators.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_comparators.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_comparators.searchOp.dynamic *= num_act_mats_hor_dir

        if is_fa or pure_cam:
            ptr_array.power_htree_in_search = uca.bank.htree_in_search.power
            ptr_array.power_htree_out_search = uca.bank.htree_out_search.power
            ptr_array.power_searchline = uca.bank.mat.power_searchline
            ptr_array.power_searchline.searchOp.dynamic *= num_mats
            ptr_array.power_searchline_precharge = uca.bank.mat.power_searchline_precharge
            ptr_array.power_searchline_precharge.searchOp.dynamic *= num_mats
            ptr_array.power_matchlines = uca.bank.mat.power_matchline
            ptr_array.power_matchlines.searchOp.dynamic *= num_mats
            ptr_array.power_matchline_precharge = uca.bank.mat.power_matchline_precharge
            ptr_array.power_matchline_precharge.searchOp.dynamic *= num_mats
            ptr_array.power_matchline_to_wordline_drv = uca.bank.mat.power_ml_to_ram_wl_drv

        ptr_array.activate_energy = uca.activate_energy
        ptr_array.read_energy = uca.read_energy
        ptr_array.write_energy = uca.write_energy
        ptr_array.precharge_energy = uca.precharge_energy
        ptr_array.refresh_power = uca.refresh_power
        ptr_array.leak_power_subbank_closed_page = uca.leak_power_subbank_closed_page
        ptr_array.leak_power_subbank_open_page = uca.leak_power_subbank_open_page
        ptr_array.leak_power_request_and_reply_networks = uca.leak_power_request_and_reply_networks
        ptr_array.precharge_delay = uca.precharge_delay

        if g_ip.is_3d_mem:
            ptr_array.t_RCD = uca.t_RCD
            ptr_array.t_RAS = uca.t_RAS
            ptr_array.t_RC = uca.t_RC
            ptr_array.t_CAS = uca.t_CAS
            ptr_array.t_RP = uca.t_RP
            ptr_array.t_RRD = uca.t_RRD
            ptr_array.activate_energy = uca.activate_energy
            ptr_array.read_energy = uca.read_energy
            ptr_array.write_energy = uca.write_energy
            ptr_array.precharge_energy = uca.precharge_energy
            ptr_array.activate_power = uca.activate_power
            ptr_array.read_power = uca.read_power
            ptr_array.write_power = uca.write_power
            ptr_array.peak_read_power = uca.read_energy / ((g_ip.burst_depth) / (g_ip.sys_freq_MHz * 1e6) / 2)
            ptr_array.num_row_subarray = dyn_p.num_r_subarray
            ptr_array.num_col_subarray = dyn_p.num_c_subarray
            ptr_array.delay_TSV_tot = uca.delay_TSV_tot
            ptr_array.area_TSV_tot = uca.area_TSV_tot
            ptr_array.dyn_pow_TSV_tot = uca.dyn_pow_TSV_tot
            ptr_array.dyn_pow_TSV_per_access = uca.dyn_pow_TSV_per_access
            ptr_array.num_TSV_tot = uca.num_TSV_tot

        if g_ip.power_gating:
            ptr_array.sram_sleep_tx_width = uca.bank.mat.sram_sleep_tx.width
            ptr_array.sram_sleep_tx_area = uca.bank.mat.array_sleep_tx_area
            ptr_array.sram_sleep_wakeup_latency = uca.bank.mat.array_wakeup_t
            ptr_array.sram_sleep_wakeup_energy = uca.bank.mat.array_wakeup_e.readOp.dynamic
            ptr_array.wl_sleep_tx_width = uca.bank.mat.row_dec.sleeptx.width
            ptr_array.wl_sleep_tx_area = uca.bank.mat.wl_sleep_tx_area
            ptr_array.wl_sleep_wakeup_latency = uca.bank.mat.wl_wakeup_t
            ptr_array.wl_sleep_wakeup_energy = uca.bank.mat.wl_wakeup_e.readOp.dynamic
            ptr_array.bl_floating_wakeup_latency = uca.bank.mat.blfloating_wakeup_t
            ptr_array.bl_floating_wakeup_energy = uca.bank.mat.blfloating_wakeup_e.readOp.dynamic
            ptr_array.array_leakage = uca.bank.array_leakage
            ptr_array.wl_leakage = uca.bank.wl_leakage
            ptr_array.cl_leakage = uca.bank.cl_leakage

        ptr_array.num_active_mats = uca.bank.dp.num_act_mats_hor_dir
        ptr_array.num_submarray_mats = uca.bank.mat.num_subarrays_per_mat

    return ptr_array



def solve_single():
    pure_ram = g_ip.pure_ram
    pure_cam = g_ip.pure_cam

    g_tp.init(g_ip.F_sz_um, False)
    g_ip.print_detail_debug = 0

    tag_arr = MemArray()
    data_arr = MemArray()
    sol = uca_org_t()

    if not (pure_ram or pure_cam or g_ip.fully_assoc):
        is_tag = True
        g_tp.init(g_ip.F_sz_um, is_tag)
        
        calculate_time_single(is_tag, pure_ram, pure_cam, g_ip.nspd, g_ip.ndwl,
                                        g_ip.ndbl, g_ip.ndcm, g_ip.ndsam1, g_ip.ndsam2,
                                            tag_arr, 0, None, None, wr, g_ip.is_main_mem)

    is_tag = False
    g_tp.init(g_ip.F_sz_um, is_tag)

    calculate_time_single(is_tag, pure_ram, pure_cam, g_ip.nspd, g_ip.ndwl,
                                g_ip.ndbl, g_ip.ndcm, g_ip.ndsam1, g_ip.ndsam2,
                                data_arr, 0, None, None, wr, g_ip.is_main_mem)
    
    if pure_ram or pure_cam or g_ip.fully_assoc:
        curr_org = sol
        curr_org.tag_array2 = None
        curr_org.data_array2 = data_arr

        curr_org.find_delay()
        curr_org.find_energy()
        # curr_org.find_area()
        # curr_org.find_cyc()

    else:
        curr_org = sol
        curr_org.tag_array2 = tag_arr
        curr_org.data_array2 = data_arr

        curr_org.find_delay()
        curr_org.find_energy()
        # curr_org.find_area()
        # curr_org.find_cyc()

    return curr_org

