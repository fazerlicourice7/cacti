# ucache.py
#
# Python translation of Ucache.h / Ucache.cc.
# (Remember: g_tp and g_ip are passed in as parameters rather than imported as globals.)
#
import math
import sys
import threading
from typing import List

# Import other modules (assumed to have been converted already)
from .area import Area
from .router import Router
from .nuca import uca_org_t, Nuca  # assume uca_org_t and Nuca are defined
from .const import BIGNUM, NTHREADS, MAXDATAN, MAX_COL_MUX, MAXDATASPD, Global, Global_5, Global_10, Global_20, Global_30, Low_swing, Full_swing
# Also assume mem_array, results_mem_array, DynamicParameter, UCA, symbolic_convex_max, _log2
from .cacti_interface import results_mem_array, mem_array
from .parameter import DynamicParameter  # your DynamicParameter class
from .uca import UCA  # your UCA class
from .basic_circuit import (
    is_pow2, _log2, is_equal,
    wire_resistance, wire_capacitance, tsv_resistance, tsv_capacitance, tsv_area,
    pmos_to_nmos_sz_ratio, gate_C, gate_C_pass, tr_R_on, drain_C_, cmos_Ig_leakage,
    horowitz, cmos_Isub_leakage, simplified_nmos_Isat
)
from .technology import init_tech_params

def symbolic_convex_max(a, b):
    """
    An approximation to the max function that plays well with numeric
    or symbolic solvers.
    """
    return 0.5 * (a + b + abs(a - b))

###############################################
# 1. min_values_t and Solution
###############################################

class min_values_t:
    def __init__(self):
        self.min_delay   = BIGNUM
        self.min_dyn     = BIGNUM
        self.min_leakage = BIGNUM
        self.min_area    = BIGNUM
        self.min_cyc     = BIGNUM

    def update_min_values(self, val):
        """Update the minimum values with those in val.
        The argument 'val' may be:
          - an instance of min_values_t,
          - a uca_org_t,
          - a nuca_org_t (assumed to have a member nuca_pda),
          - or a mem_array.
        """
        if isinstance(val, min_values_t):
            self.min_delay   = min(self.min_delay, val.min_delay)
            self.min_dyn     = min(self.min_dyn, val.min_dyn)
            self.min_leakage = min(self.min_leakage, val.min_leakage)
            self.min_area    = min(self.min_area, val.min_area)
            self.min_cyc     = min(self.min_cyc, val.min_cyc)
        elif isinstance(val, uca_org_t):
            self.min_delay   = min(self.min_delay, val.access_time)
            self.min_dyn     = min(self.min_dyn, val.power.readOp.dynamic)
            self.min_leakage = min(self.min_leakage, val.power.readOp.leakage)
            self.min_area    = min(self.min_area, val.area)
            self.min_cyc     = min(self.min_cyc, val.cycle_time)
        elif hasattr(val, "nuca_pda"):
            # Assume it is a nuca_org_t–like object
            self.min_delay   = min(self.min_delay, val.nuca_pda.delay)
            self.min_dyn     = min(self.min_dyn, val.nuca_pda.power.readOp.dynamic)
            self.min_leakage = min(self.min_leakage, val.nuca_pda.power.readOp.leakage)
            try:
                area_val = val.nuca_pda.area.get_area()
            except AttributeError:
                area_val = val.nuca_pda.area
            self.min_area    = min(self.min_area, area_val)
            self.min_cyc     = min(self.min_cyc, val.nuca_pda.cycle_time)
        elif isinstance(val, mem_array):
            self.min_delay   = min(self.min_delay, val.access_time)
            self.min_dyn     = min(self.min_dyn, val.power.readOp.dynamic)
            self.min_leakage = min(self.min_leakage, val.power.readOp.leakage)
            self.min_area    = min(self.min_area, val.area)
            self.min_cyc     = min(self.min_cyc, val.cycle_time)
        else:
            raise TypeError("Unsupported type in update_min_values")

# A simple container for a candidate solution.
class Solution:
    def __init__(self):
        self.tag_array_index = 0
        self.data_array_index = 0
        self.tag_array_iter = None
        self.data_array_iter = None
        self.access_time = 0.0
        self.cycle_time = 0.0
        self.area = 0.0
        self.efficiency = 0.0
        self.total_power = None  # expected to be a powerDef instance

###############################################
# 2. Function calculate_time(...)
###############################################

def calculate_time(is_tag: bool,
                   pure_ram: int,
                   pure_cam: bool,
                   Nspd: float,
                   Ndwl: int,
                   Ndbl: int,
                   Ndcm: int,
                   Ndsam_lev_1: int,
                   Ndsam_lev_2: int,
                   ptr_array: mem_array,
                   flag_results_populate: int,
                   ptr_results: results_mem_array,
                   ptr_fin_res: uca_org_t,
                   wtype,  # Wire_type
                   is_main_mem: bool,
                   g_tp, g_ip) -> bool:
    """
    Mimics the C++ function:
      bool calculate_time( ... )
    It instantiates a DynamicParameter (for tag or data),
    then creates a UCA object and populates ptr_array.
    """
    dyn_p = DynamicParameter(is_tag, pure_ram, pure_cam, Nspd,
                               Ndwl, Ndbl, Ndcm,
                               Ndsam_lev_1, Ndsam_lev_2,
                               wtype, is_main_mem)
    if not dyn_p.is_valid:
        return False
    uca_obj = UCA(dyn_p)
    if flag_results_populate:
        # Populate ptr_results if desired (not implemented in detail here)
        pass
    else:
        ptr_array.Ndwl = Ndwl
        ptr_array.Ndbl = Ndbl
        ptr_array.Nspd = Nspd
        # (Other parameters such as deg_bl_muxing, power, area, etc.)
        ptr_array.access_time = uca_obj.access_time
        ptr_array.cycle_time  = uca_obj.cycle_time
        if hasattr(uca_obj.area, "get_area"):
            ptr_array.area = uca_obj.area.get_area()
        else:
            ptr_array.area = 0.0
        ptr_array.power = uca_obj.power
        # (Many additional fields are set in the C++ version; these are omitted here for brevity.)
    return True

###############################################
# 3. Multithread wrapper: CalcTimeMTWrapperStruct and calc_time_mt_wrapper
###############################################

class CalcTimeMTWrapperStruct:
    def __init__(self, tid: int, is_tag: bool, pure_ram: bool, pure_cam: bool,
                 is_main_mem: bool, Nspd_min: float, g_ip):
        self.tid = tid
        self.is_tag = is_tag
        self.pure_ram = pure_ram
        self.pure_cam = pure_cam
        self.is_main_mem = is_main_mem
        self.Nspd_min = Nspd_min
        self.data_res = min_values_t()
        self.tag_res  = min_values_t()
        self.data_arr: List[mem_array] = []
        self.tag_arr: List[mem_array] = []
        self.g_ip = g_ip  # include g_ip reference

def calc_time_mt_wrapper_func(wrapper: CalcTimeMTWrapperStruct, g_tp, g_ip):
    """
    Thread worker equivalent to:
      void *calc_time_mt_wrapper(void * void_obj)
    in C++.
    """
    # Clear and initialize the lists
    wrapper.data_arr.clear()
    wrapper.data_arr.append(mem_array())
    wrapper.tag_arr.clear()
    wrapper.tag_arr.append(mem_array())

    Ndwl_niter = _log2(MAXDATAN) + 1
    Ndbl_niter = _log2(MAXDATAN) + 1
    Ndcm_niter = _log2(MAX_COL_MUX) + 1
    niter = Ndwl_niter * Ndbl_niter * Ndcm_niter

    # Determine wire type range
    if g_ip.force_wiretype:
        if g_ip.wt == Full_swing:
            wt_min = Global
            wt_max = Low_swing - 1
        else:
            if g_ip.wt == Global:
                wt_min = wt_max = Global
            elif g_ip.wt == Global_5:
                wt_min = wt_max = Global_5
            elif g_ip.wt == Global_10:
                wt_min = wt_max = Global_10
            elif g_ip.wt == Global_20:
                wt_min = wt_max = Global_20
            elif g_ip.wt == Global_30:
                wt_min = wt_max = Global_30
            elif g_ip.wt == Low_swing:
                wt_min = wt_max = Low_swing
            else:
                sys.stderr.write("Unknown wire type!\n")
                sys.exit(1)
    else:
        wt_min = Global
        wt_max = Low_swing

    # Loop over Nspd, wire type (wr), iterations, and then over Ndsam_lev_1 and Ndsam_lev_2.
    Nspd = wrapper.Nspd_min
    while Nspd <= MAXDATASPD:
        for wr in range(wt_min, wt_max + 1):
            for iter in range(wrapper.tid, niter, NTHREADS):
                Ndwl = 1 << (iter // (Ndbl_niter * Ndcm_niter))
                Ndbl = 1 << ((iter // Ndcm_niter) % Ndbl_niter)
                Ndcm = 1 << (iter % Ndcm_niter)
                Ndsam_lev_1 = 1
                while Ndsam_lev_1 <= MAX_COL_MUX:
                    Ndsam_lev_2 = 1
                    while Ndsam_lev_2 <= MAX_COL_MUX:
                        # If forced cache config and not tag array, override parameters.
                        if g_ip.force_cache_config and (not wrapper.is_tag):
                            wr   = g_ip.wt
                            Ndwl = g_ip.ndwl
                            Ndbl = g_ip.ndbl
                            Ndcm = g_ip.ndcm
                            if g_ip.nspd != 0:
                                Nspd = g_ip.nspd
                            if g_ip.ndsam1 != 0:
                                Ndsam_lev_1 = g_ip.ndsam1
                                Ndsam_lev_2 = g_ip.ndsam2
                        if wrapper.is_tag:
                            valid = calculate_time(True, wrapper.pure_ram, wrapper.pure_cam, Nspd,
                                                   Ndwl, Ndbl, Ndcm, Ndsam_lev_1, Ndsam_lev_2,
                                                   wrapper.tag_arr[-1], 0, None, None, wr,
                                                   wrapper.is_main_mem, g_tp, g_ip)
                        else:
                            valid = calculate_time(False, wrapper.pure_ram, wrapper.pure_cam, Nspd,
                                                   Ndwl, Ndbl, Ndcm, Ndsam_lev_1, Ndsam_lev_2,
                                                   wrapper.data_arr[-1], 0, None, None, wr,
                                                   wrapper.is_main_mem, g_tp, g_ip)
                            if g_ip.is_3d_mem:
                                Ndsam_lev_1 = MAX_COL_MUX + 1
                                Ndsam_lev_2 = MAX_COL_MUX + 1
                        if valid:
                            if wrapper.is_tag:
                                wrapper.tag_arr[-1].wt = wr
                                wrapper.tag_res.update_min_values(wrapper.tag_arr[-1])
                                wrapper.tag_arr.append(mem_array())
                            if (not wrapper.is_tag) or g_ip.fully_assoc:
                                wrapper.data_arr[-1].wt = wr
                                wrapper.data_res.update_min_values(wrapper.data_arr[-1])
                                wrapper.data_arr.append(mem_array())
                        if g_ip.force_cache_config and (not wrapper.is_tag):
                            wr   = wt_max
                            iter = niter
                            if g_ip.nspd != 0:
                                Nspd = MAXDATASPD
                            if g_ip.ndsam1 != 0:
                                Ndsam_lev_1 = MAX_COL_MUX + 1
                                Ndsam_lev_2 = MAX_COL_MUX + 1
                        Ndsam_lev_2 *= 2
                    Ndsam_lev_1 *= 2
                # end for iter
            # end for wr
        Nspd *= 2
    # End of thread; in Python simply return.
    return

###############################################
# 4. Check functions and filtering
###############################################

def check_uca_org(u: uca_org_t, minval: min_values_t, g_ip) -> bool:
    if ((u.access_time - minval.min_delay)*100/minval.min_delay) > g_ip.delay_dev:
        return False
    if ((u.power.readOp.dynamic - minval.min_dyn)/minval.min_dyn)*100 > g_ip.dynamic_power_dev:
        return False
    if ((u.power.readOp.leakage - minval.min_leakage)/minval.min_leakage)*100 > g_ip.leakage_power_dev:
        return False
    if ((u.cycle_time - minval.min_cyc)/minval.min_cyc)*100 > g_ip.cycle_time_dev:
        return False
    if ((u.area - minval.min_area)/minval.min_area)*100 > g_ip.area_dev:
        return False
    return True

def check_mem_org(u: mem_array, minval: min_values_t, g_ip) -> bool:
    if ((u.access_time - minval.min_delay)*100/minval.min_delay) > g_ip.delay_dev:
        return False
    if ((u.power.readOp.dynamic - minval.min_dyn)/minval.min_dyn)*100 > g_ip.dynamic_power_dev:
        return False
    if ((u.power.readOp.leakage - minval.min_leakage)/minval.min_leakage)*100 > g_ip.leakage_power_dev:
        return False
    if ((u.cycle_time - minval.min_cyc)/minval.min_cyc)*100 > g_ip.cycle_time_dev:
        return False
    if ((u.area - minval.min_area)/minval.min_area)*100 > g_ip.area_dev:
        return False
    return True

def find_optimal_uca(ulist: List[uca_org_t], minval: min_values_t, g_ip) -> uca_org_t:
    dp = g_ip.dynamic_power_wt_nuca
    lp = g_ip.leakage_power_wt_nuca
    a  = g_ip.area_wt_nuca
    d  = g_ip.delay_wt_nuca
    c  = g_ip.cycle_time_wt_nuca

    min_cost = BIGNUM
    res = None

    for u in ulist:
        print("-----------------------------")
        print(f"NUCA___stats bank_count: {u.bank_count}, lat = {u.nuca_pda.delay}, dynP = {u.nuca_pda.power.readOp.dynamic}, wt = {u.h_wire.wt},"
              f" bank_dpower = {u.bank_pda.power.readOp.dynamic}, leak = {u.nuca_pda.power.readOp.leakage}, cycle = {u.nuca_pda.cycle_time}")
        if g_ip.ed == 1:
            cost = (u.access_time/minval.min_delay) * (u.power.readOp.dynamic/minval.min_dyn)
            if cost < min_cost:
                min_cost = cost
                res = u
        elif g_ip.ed == 2:
            cost = (u.access_time/minval.min_delay)**2 * (u.power.readOp.dynamic/minval.min_dyn)
            if cost < min_cost:
                min_cost = cost
                res = u
        else:
            if check_uca_org(u, minval, g_ip):
                cost = (d * (u.access_time/minval.min_delay) +
                        c * (u.cycle_time/minval.min_cyc) +
                        dp * (u.power.readOp.dynamic/minval.min_dyn) +
                        lp * (u.power.readOp.leakage/minval.min_leakage) +
                        a * (u.area/minval.min_area))
                print(f"cost = {cost}")
                if cost < min_cost:
                    min_cost = cost
                    res = u
            else:
                # In C++ the candidate is erased; here we simply ignore it.
                pass
    if res is None:
        print("ERROR: no cache organizations met optimization criteria")
        sys.exit(1)
    return res

def filter_tag_arr(min_val: min_values_t, arr_list: List[mem_array], g_ip):
    cost = BIGNUM
    res = None
    if not arr_list:
        print("ERROR: no valid tag organizations found")
        sys.exit(1)
    while arr_list:
        candidate = arr_list.pop()
        if check_mem_org(candidate, min_val, g_ip):
            cur_cost = (g_ip.delay_wt * (candidate.access_time/min_val.min_delay) +
                        g_ip.dynamic_power_wt * (candidate.power.readOp.dynamic/min_val.min_dyn) +
                        g_ip.leakage_power_wt * (candidate.power.readOp.leakage/min_val.min_leakage) +
                        g_ip.area_wt * (candidate.area/min_val.min_area) +
                        g_ip.cycle_time_wt * (candidate.cycle_time/min_val.min_cyc))
        else:
            cur_cost = BIGNUM
        if cur_cost < cost:
            cost = cur_cost
            res = candidate
        else:
            # Candidate is discarded.
            pass
    if res is None:
        print("ERROR: no valid tag organizations found")
        sys.exit(1)
    arr_list.append(res)

def filter_data_arr(curr_list: List[mem_array], g_ip):
    if not curr_list:
        print("ERROR: no valid data array organizations found")
        sys.exit(1)
    filtered = []
    for m in curr_list:
        if check_mem_org(m, m.arr_min, g_ip):
            filtered.append(m)
    curr_list.clear()
    curr_list.extend(filtered)

###############################################
# 5. solve(fin_res) and update(fin_res)
###############################################

def solve(fin_res: uca_org_t, g_tp, g_ip):
    """
    Python equivalent of:
      void solve(uca_org_t *fin_res)
    Performs an exhaustive search across different sub-array sizes,
    wire types and aspect ratios to find an optimal UCA organization.
    (Many details are omitted; here we outline the overall structure.)
    """
    pure_ram = g_ip.pure_ram
    pure_cam = g_ip.pure_cam

    init_tech_params(g_tp, g_ip.F_sz_um, False)
    g_ip.print_detail_debug = False

    tag_arr: List[mem_array] = []
    data_arr: List[mem_array] = []
    sol_list: List[uca_org_t] = []

    # (In the C++ code the uca_org_t structure "ures" is used to compute bank organization.)
    ures = uca_org_t()
    # Assume that solve(ures) sets ures.access_time, cycle_time, area, etc.
    solve(ures)  # call the imported (or previously defined) solve function
    bank_count = int(g_ip.nuca_cache_sz / g_ip.cache_sz)
    print(f"==== {g_ip.cache_sz}\n")

    # Multithreading: distribute calculate_time() calls to nthreads.
    calc_array = []
    threads = []
    for t in range(NTHREADS):
        wrapper = CalcTimeMTWrapperStruct(t, True, pure_ram, pure_cam, g_ip.is_main_mem, 0.125, g_ip)
        calc_array.append(wrapper)
        thread = threading.Thread(target=calc_time_mt_wrapper_func, args=(wrapper, g_tp, g_ip))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    # Merge results from all threads:
    for wrapper in calc_array:
        wrapper.data_arr.sort(key=lambda m: m.access_time)
        data_arr.extend(wrapper.data_arr)
        wrapper.tag_arr.sort(key=lambda m: m.access_time)
        tag_arr.extend(wrapper.tag_arr)

    d_min = min_values_t()
    t_min = min_values_t()
    for wrapper in calc_array:
        d_min.update_min_values(wrapper.data_res)
        t_min.update_min_values(wrapper.tag_res)

    for m in data_arr:
        m.arr_min = d_min

    filter_data_arr(data_arr, g_ip)
    if not (pure_ram or pure_cam or g_ip.fully_assoc):
        filter_tag_arr(t_min, tag_arr, g_ip)

    # Now build the solution list.
    if pure_ram or pure_cam or g_ip.fully_assoc:
        for m in data_arr:
            curr_org = uca_org_t()
            curr_org.tag_array2 = None
            curr_org.data_array2 = m
            curr_org.find_delay()
            curr_org.find_energy()
            curr_org.find_area()
            curr_org.find_cyc()
            d_min.update_min_values(curr_org)
            sol_list.append(curr_org)
    else:
        for tag_obj in tag_arr:
            for m in data_arr:
                curr_org = uca_org_t()
                curr_org.tag_array2 = tag_obj
                curr_org.data_array2 = m
                curr_org.find_delay()
                curr_org.find_energy()
                curr_org.find_area()
                curr_org.find_cyc()
                d_min.update_min_values(curr_org)
                sol_list.append(curr_org)
    if sol_list:
        sol_list.pop()  # remove extra element as in C++
    else:
        print("No valid solution found!")
        sys.exit(1)
    optimal = find_optimal_uca(sol_list, d_min, g_ip)
    fin_res.__dict__.update(optimal.__dict__)  # copy optimal solution into fin_res

    # Clean up temporary lists (in Python, deletion is automatic)
    for m in data_arr:
        if m != fin_res.data_array2:
            del m
    data_arr.clear()
    for wrapper in calc_array:
        del wrapper.data_res
        del wrapper.tag_res
    calc_array.clear()
    for _ in range(len(sol_list)):
        del _
    sol_list.clear()
    # End of solve.

def update(fin_res: uca_org_t, g_tp, g_ip):
    """
    Python equivalent of:
      void update(uca_org_t *fin_res)
    Updates the leakage feedback of the tag and data arrays.
    """
    if fin_res.tag_array2 is not None:
        init_tech_params(g_tp, g_ip.F_sz_um, True)
        tag_arr_dyn_p = DynamicParameter(True, g_ip.pure_ram, g_ip.pure_cam,
                                          fin_res.tag_array2.Nspd,
                                          fin_res.tag_array2.Ndwl,
                                          fin_res.tag_array2.Ndbl,
                                          fin_res.tag_array2.Ndcm,
                                          fin_res.tag_array2.Ndsam_lev_1,
                                          fin_res.tag_array2.Ndsam_lev_2,
                                          fin_res.data_array2.wt,
                                          g_ip.is_main_mem)
        if tag_arr_dyn_p.is_valid:
            tag_arr = UCA(tag_arr_dyn_p)
            fin_res.tag_array2.power = tag_arr.power
        else:
            print("ERROR: Cannot retrieve array structure for leakage feedback")
            sys.exit(1)
    init_tech_params(g_tp, g_ip.F_sz_um, False)
    data_arr_dyn_p = DynamicParameter(False, g_ip.pure_ram, g_ip.pure_cam,
                                       fin_res.data_array2.Nspd,
                                       fin_res.data_array2.Ndwl,
                                       fin_res.data_array2.Ndbl,
                                       fin_res.data_array2.Ndcm,
                                       fin_res.data_array2.Ndsam_lev_1,
                                       fin_res.data_array2.Ndsam_lev_2,
                                       fin_res.data_array2.wt,
                                       g_ip.is_main_mem)
    if data_arr_dyn_p.is_valid:
        data_arr = UCA(data_arr_dyn_p)
        fin_res.data_array2.power = data_arr.power
    else:
        print("ERROR: Cannot retrieve array structure for leakage feedback")
        sys.exit(1)
    fin_res.find_energy()

def check_uca_org_wrapper(uca_obj: uca_org_t, minval: min_values_t, g_ip) -> bool:
    return check_uca_org(uca_obj, minval, g_ip)

def check_mem_org_wrapper(mem_obj: mem_array, minval: min_values_t, g_ip) -> bool:
    return check_mem_org(mem_obj, minval, g_ip)


# SINGLE VERSION - SOURCE OF ERROR

##### SINGLE SOLVE


def calculate_all_results_single(
    g_ip,
    g_tp,
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
    is_main_mem,
):
    """"
    All the bulk of the calculation happens here. 
    """
    dyn_p = DynamicParameter(
        g_ip,
        g_tp,
        is_tag,
        pure_ram,
        pure_cam,
        Nspd,
        Ndwl,
        Ndbl,
        Ndcm,
        Ndsam_lev_1,
        Ndsam_lev_2,
        wt,
        is_main_mem,
    )

    # if not dyn_p.is_valid:
    #     return False
    uca = UCA(dyn_p, g_ip, g_tp)

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
        ptr_array.multisubbank_interleave_cycle_time = (
            uca.multisubbank_interleave_cycle_time
        )
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

        ptr_array.delay_senseamp_mux_decoder = symbolic_convex_max(
            uca.delay_array_to_sa_mux_lev_1_decoder,
            uca.delay_array_to_sa_mux_lev_2_decoder,
        )

        ptr_array.delay_before_subarray_output_driver = (
            uca.delay_before_subarray_output_driver
        )
        ptr_array.delay_from_subarray_output_driver_to_output = (
            uca.delay_from_subarray_out_drv_to_out
        )
        ptr_array.delay_route_to_bank = uca.htree_in_add.delay
        ptr_array.delay_input_htree = uca.bank.htree_in_add.delay
        ptr_array.delay_row_predecode_driver_and_block = uca.bank.mat.r_predec.delay
        ptr_array.delay_row_decoder = uca.bank.mat.row_dec.delay
        ptr_array.delay_bitlines = uca.bank.mat.delay_bitline
        ptr_array.delay_matchlines = uca.bank.mat.delay_matchchline
        ptr_array.delay_sense_amp = uca.bank.mat.delay_sa
        ptr_array.delay_subarray_output_driver = (
            uca.bank.mat.delay_subarray_out_drv_htree
        )
        ptr_array.delay_dout_htree = uca.bank.htree_out_data.delay
        ptr_array.delay_comparator = uca.bank.mat.delay_comparator

        if g_ip.is_3d_mem:
            ptr_array.delay_row_activate_net = uca.membus_RAS.delay_bus
            ptr_array.delay_row_predecode_driver_and_block = (
                uca.membus_RAS.delay_add_predecoder
            )
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
            ptr_array.energy_row_predecode_driver_and_block = (
                uca.membus_RAS.power_add_predecoder.readOp.dynamic
            )
            ptr_array.energy_row_decoder = (
                uca.membus_RAS.power_add_decoders.readOp.dynamic
            )
            ptr_array.energy_local_wordline = (
                uca.membus_RAS.power_lwl_drv.readOp.dynamic
            )
            ptr_array.energy_bitlines = (
                dyn_p.Ndwl * uca.bank.mat.power_bitline.readOp.dynamic
            )
            ptr_array.energy_sense_amp = (
                dyn_p.Ndwl * uca.bank.mat.power_sa.readOp.dynamic
            )
            ptr_array.energy_column_access_net = uca.membus_CAS.power_bus.readOp.dynamic
            ptr_array.energy_column_predecoder = (
                uca.membus_CAS.power_add_predecoder.readOp.dynamic
            )
            ptr_array.energy_column_decoder = (
                uca.membus_CAS.power_add_decoders.readOp.dynamic
            )
            ptr_array.energy_column_selectline = (
                uca.membus_CAS.power_col_sel.readOp.dynamic
            )
            ptr_array.energy_datapath_net = uca.membus_data.power_bus.readOp.dynamic
            ptr_array.energy_global_data = (
                uca.membus_data.power_global_data.readOp.dynamic
            )
            ptr_array.energy_local_data_and_drv = (
                uca.membus_data.power_local_data.readOp.dynamic
            )
            ptr_array.energy_subarray_output_driver = (
                uca.bank.mat.power_subarray_out_drv.readOp.dynamic
            )
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
        ptr_array.power_bit_mux_predecoder_drivers = (
            uca.bank.mat.b_mux_predec.driver_power
        )
        ptr_array.power_bit_mux_predecoder_drivers.readOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_bit_mux_predecoder_drivers.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_bit_mux_predecoder_drivers.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_bit_mux_predecoder_blocks = (
            uca.bank.mat.b_mux_predec.block_power
        )
        ptr_array.power_bit_mux_predecoder_blocks.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_predecoder_blocks.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_bit_mux_predecoder_blocks.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_bit_mux_decoders = uca.bank.mat.power_bit_mux_decoders
        ptr_array.power_bit_mux_decoders.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_decoders.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_bit_mux_decoders.searchOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers = (
            uca.bank.mat.sa_mux_lev_1_predec.driver_power
        )
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.readOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_1_predecoder_drivers.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks = (
            uca.bank.mat.sa_mux_lev_1_predec.block_power
        )
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.readOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_1_predecoder_blocks.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_1_decoders = (
            uca.bank.mat.power_sa_mux_lev_1_decoders
        )
        ptr_array.power_senseamp_mux_lev_1_decoders.readOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_1_decoders.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_1_decoders.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers = (
            uca.bank.mat.sa_mux_lev_2_predec.driver_power
        )
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.readOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_predecoder_drivers.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks = (
            uca.bank.mat.sa_mux_lev_2_predec.block_power
        )
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.readOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_predecoder_blocks.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_decoders = (
            uca.bank.mat.power_sa_mux_lev_2_decoders
        )
        ptr_array.power_senseamp_mux_lev_2_decoders.readOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_decoders.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_senseamp_mux_lev_2_decoders.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
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
        ptr_array.power_output_drivers_at_subarray.readOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_output_drivers_at_subarray.writeOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_output_drivers_at_subarray.searchOp.dynamic *= (
            num_act_mats_hor_dir
        )
        ptr_array.power_comparators = uca.bank.mat.power_comparator
        ptr_array.power_comparators.readOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_comparators.writeOp.dynamic *= num_act_mats_hor_dir
        ptr_array.power_comparators.searchOp.dynamic *= num_act_mats_hor_dir

        if is_fa or pure_cam:
            ptr_array.power_htree_in_search = uca.bank.htree_in_search.power
            ptr_array.power_htree_out_search = uca.bank.htree_out_search.power
            ptr_array.power_searchline = uca.bank.mat.power_searchline
            ptr_array.power_searchline.searchOp.dynamic *= num_mats
            ptr_array.power_searchline_precharge = (
                uca.bank.mat.power_searchline_precharge
            )
            ptr_array.power_searchline_precharge.searchOp.dynamic *= num_mats
            ptr_array.power_matchlines = uca.bank.mat.power_matchline
            ptr_array.power_matchlines.searchOp.dynamic *= num_mats
            ptr_array.power_matchline_precharge = uca.bank.mat.power_matchline_precharge
            ptr_array.power_matchline_precharge.searchOp.dynamic *= num_mats
            ptr_array.power_matchline_to_wordline_drv = (
                uca.bank.mat.power_ml_to_ram_wl_drv
            )

        ptr_array.activate_energy = uca.activate_energy
        ptr_array.read_energy = uca.read_energy
        ptr_array.write_energy = uca.write_energy
        ptr_array.precharge_energy = uca.precharge_energy
        ptr_array.refresh_power = uca.refresh_power
        ptr_array.leak_power_subbank_closed_page = uca.leak_power_subbank_closed_page
        ptr_array.leak_power_subbank_open_page = uca.leak_power_subbank_open_page
        ptr_array.leak_power_request_and_reply_networks = (
            uca.leak_power_request_and_reply_networks
        )
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
            ptr_array.peak_read_power = uca.read_energy / (
                (g_ip.burst_depth) / (g_ip.sys_freq_MHz * 1e6) / 2
            )
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
            ptr_array.sram_sleep_wakeup_energy = (
                uca.bank.mat.array_wakeup_e.readOp.dynamic
            )
            ptr_array.wl_sleep_tx_width = uca.bank.mat.row_dec.sleeptx.width
            ptr_array.wl_sleep_tx_area = uca.bank.mat.wl_sleep_tx_area
            ptr_array.wl_sleep_wakeup_latency = uca.bank.mat.wl_wakeup_t
            ptr_array.wl_sleep_wakeup_energy = uca.bank.mat.wl_wakeup_e.readOp.dynamic
            ptr_array.bl_floating_wakeup_latency = uca.bank.mat.blfloating_wakeup_t
            ptr_array.bl_floating_wakeup_energy = (
                uca.bank.mat.blfloating_wakeup_e.readOp.dynamic
            )
            ptr_array.array_leakage = uca.bank.array_leakage
            ptr_array.wl_leakage = uca.bank.wl_leakage
            ptr_array.cl_leakage = uca.bank.cl_leakage

        ptr_array.num_active_mats = uca.bank.dp.num_act_mats_hor_dir
        ptr_array.num_submarray_mats = uca.bank.mat.num_subarrays_per_mat

    return ptr_array

from .cacti_interface import InputParameter, MemArray
from .parameter import TechnologyParameter
def solve_single(g_ip: InputParameter):
    pure_ram = g_ip.pure_ram
    pure_cam = g_ip.pure_cam

    g_tp = TechnologyParameter(g_ip)
    g_tp.init(g_ip, g_ip.F_sz_um, False)
    g_ip.print_detail_debug = False

    tag_arr = MemArray()
    data_arr = MemArray()
    sol = uca_org_t(g_ip)

    # if not (pure_ram or pure_cam or g_ip.fully_assoc):
    #     is_tag = True
    #     g_tp.init(g_ip, g_ip.F_sz_um, is_tag)

    #     calculate_all_results_single(
    #         g_ip,
    #         g_tp,
    #         is_tag,
    #         pure_ram,
    #         pure_cam,
    #         g_ip.nspd,
    #         g_ip.ndwl,
    #         g_ip.ndbl,
    #         g_ip.ndcm,
    #         g_ip.ndsam1,
    #         g_ip.ndsam2,
    #         tag_arr,
    #         0,
    #         None,
    #         None,
    #         wr,
    #         g_ip.is_main_mem,
    #     )

    is_tag = False
    g_tp.init(g_ip, g_ip.F_sz_um, is_tag)

    wr = g_ip.data_wire_type
    data_arr = calculate_all_results_single(
        g_ip,
        g_tp,
        is_tag,
        pure_ram,
        pure_cam,
        g_ip.nspd,
        g_ip.ndwl,
        g_ip.ndbl,
        g_ip.ndcm,
        g_ip.ndsam1,
        g_ip.ndsam2,
        data_arr,
        0,
        None,
        None,
        wr,
        g_ip.is_main_mem,
    )

    if pure_ram or pure_cam or g_ip.fully_assoc:
        curr_org = sol
        curr_org.tag_array2 = None
        curr_org.data_array2 = data_arr
    else:
        curr_org = sol
        curr_org.tag_array2 = tag_arr
        curr_org.data_array2 = data_arr

    # curr_org is of type uca_org_t
    curr_org.find_delay()
    curr_org.find_energy()
    # curr_org.find_area()
    # curr_org.find_cyc()

    curr_org.find_IO()
    # print("PRINTING IO")
    # # time.sleep(7)
    # print(f"io_area: {curr_org.io_area}")
    # print(f"io_timing_margin: {curr_org.io_timing_margin}")
    # print(f"io_dynamic_power: {curr_org.io_dynamic_power}")
    # print(f"io_phy_power: {curr_org.io_phy_power}")
    # print(f"io_termination_power: {curr_org.io_termination_power}")
    # time.sleep(60)

    return curr_org
