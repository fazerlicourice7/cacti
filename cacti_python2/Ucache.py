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
