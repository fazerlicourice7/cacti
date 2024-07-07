import math
from const import *

UNI_LEAK_STACK_FACTOR = 0.43

def powers(base, n):
    p = 1
    for i in range(1, n + 1):
        p *= base
    return p

def is_pow2(val):
    if val <= 0:
        return False
    elif val == 1:
        return True
    else:
        return (_log2(val) != _log2(val - 1))

def _log2(num):
    if num == 0:
        raise ValueError("log0?")
    log2 = 0
    while num > 1:
        num >>= 1
        log2 += 1
    return log2

def factorial(n, m=1):
    fa = m
    for i in range(m + 1, n + 1):
        fa *= i
    return fa

def combination(n, m):
    return factorial(n, m + 1) // factorial(n - m)


outside_mat = "outside_mat"
inside_mat = "inside_mat"
local_wires = "local_wires"


Add_htree = "Add_htree"
Data_in_htree = "Data_in_htree"
Data_out_htree = "Data_out_htree"
Search_in_htree = "Search_in_htree"
Search_out_htree = "Search_out_htree"


Row_add_path = "Row_add_path"
Col_add_path = "Col_add_path"
Data_path = "Data_path"


nmos = "nmos"
pmos = "pmos"
inv = "inv"
nand = "nand"
nor = "nor"
tri = "tri"
tg = "tg"

parallel = "parallel"
series = "series"

class WirePlacement:
    outside_mat = "outside_mat"
    inside_mat = "inside_mat"
    local_wires = "local_wires"

class HtreeType:
    Add_htree = "Add_htree"
    Data_in_htree = "Data_in_htree"
    Data_out_htree = "Data_out_htree"
    Search_in_htree = "Search_in_htree"
    Search_out_htree = "Search_out_htree"

class MemorybusType:
    Row_add_path = "Row_add_path"
    Col_add_path = "Col_add_path"
    Data_path = "Data_path"

class GateType:
    nmos = "nmos"
    pmos = "pmos"
    inv = "inv"
    nand = "nand"
    nor = "nor"
    tri = "tri"
    tg = "tg"

class HalfNetTopology:
    parallel = "parallel"
    series = "series"

def logtwo(x):
    assert x > 0
    return math.log(x) / math.log(2.0)

def gate_C(width, wirelength, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global
    return (dt.C_g_ideal + dt.C_overlap + 3 * dt.C_fringe) * width + dt.l_phy * Cpolywire

def gate_C_pass(width, wirelength, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    return gate_C(width, wirelength, _is_dram, _is_sram, _is_wl_tr, _is_sleep_tx)

def drain_C_(width, nchannel, stack, next_arg_thresh_folding_width_or_height_cell, fold_dimension, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    c_junc_area = dt.C_junc
    c_junc_sidewall = dt.C_junc_sidewall
    c_fringe = 2 * dt.C_fringe
    c_overlap = 2 * dt.C_overlap
    drain_C_metal_connecting_folded_tr = 0

    if next_arg_thresh_folding_width_or_height_cell == 0:
        w_folded_tr = fold_dimension
    else:
        h_tr_region = fold_dimension - 2 * g_tp.HPOWERRAIL
        ratio_p_to_n = 2.0 / (2.0 + 1.0)
        if nchannel:
            w_folded_tr = (1 - ratio_p_to_n) * (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)
        else:
            w_folded_tr = ratio_p_to_n * (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)

    num_folded_tr = int(sp.ceiling(width / w_folded_tr))
    if num_folded_tr < 2:
        w_folded_tr = width

    total_drain_w = (g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact) + (stack - 1) * g_tp.spacing_poly_to_poly
    drain_h_for_sidewall = w_folded_tr
    total_drain_height_for_cap_wrt_gate = w_folded_tr + 2 * w_folded_tr * (stack - 1)
    if num_folded_tr > 1:
        total_drain_w += (num_folded_tr - 2) * (g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact) + (num_folded_tr - 1) * ((stack - 1) * g_tp.spacing_poly_to_poly)
        if num_folded_tr % 2 == 0:
            drain_h_for_sidewall = 0
        total_drain_height_for_cap_wrt_gate *= num_folded_tr
        drain_C_metal_connecting_folded_tr = g_tp.wire_local.C_per_um * total_drain_w

    drain_C_area = c_junc_area * total_drain_w * w_folded_tr
    drain_C_sidewall = c_junc_sidewall * (drain_h_for_sidewall + 2 * total_drain_w)
    drain_C_wrt_gate = (c_fringe + c_overlap) * total_drain_height_for_cap_wrt_gate

    return drain_C_area + drain_C_sidewall + drain_C_wrt_gate + drain_C_metal_connecting_folded_tr

def tr_R_on(width, nchannel, stack, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    restrans = dt.R_nch_on if nchannel else dt.R_pch_on
    return stack * restrans / width

def R_to_w(res, nchannel, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    restrans = dt.R_nch_on if nchannel else dt.R_pch_on
    return restrans / res

def pmos_to_nmos_sz_ratio(_is_dram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_wl_tr:
        return g_tp.dram_wl.n_to_p_eff_curr_drv_ratio
    elif _is_sleep_tx:
        return g_tp.sleep_tx.n_to_p_eff_curr_drv_ratio
    else:
        return g_tp.peri_global.n_to_p_eff_curr_drv_ratio

def horowitz(inputramptime, tf, vs1, vs2, rise):
    if inputramptime == 0 and vs1 == vs2:
        return tf * (-math.log(vs1) if vs1 < 1 else math.log(vs1))

    a = inputramptime / tf
    if rise == RISE:
        b = 0.5
        td = tf * math.sqrt(math.log(vs1) ** 2 + 2 * a * b * (1.0 - vs1)) + tf * (math.log(vs1) - math.log(vs2))
    else:
        b = 0.4
        td = tf * math.sqrt(math.log(1.0 - vs1) ** 2 + 2 * a * b * vs1) + tf * (math.log(1.0 - vs1) - math.log(1.0 - vs2))
    return td

def cmos_Ileak(nWidth, pWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nWidth * dt.I_off_n + pWidth * dt.I_off_p

def simplified_nmos_Isat(nwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nwidth * dt.I_on_n

def simplified_pmos_Isat(pwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pwidth * dt.I_on_n / dt.n_to_p_eff_curr_drv_ratio

def simplified_nmos_leakage(nwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nwidth * dt.I_off_n

def simplified_pmos_leakage(pwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pwidth * dt.I_off_p

def cmos_Ig_n(nWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nWidth * dt.I_g_on_n

def cmos_Ig_p(pWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pWidth * dt.I_g_on_p

def cmos_Isub_leakage(nWidth, pWidth, fanin, g_type, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False, topo=series):
    assert fanin >= 1
    nmos_leak = simplified_nmos_leakage(nWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    pmos_leak = simplified_pmos_leakage(pWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    Isub = 0
    num_states = int(math.pow(2.0, fanin))

    if g_type == nmos:
        if fanin == 1:
            Isub = nmos_leak / num_states
        else:
            if topo == parallel:
                Isub = nmos_leak * fanin / num_states
            else:
                for num_off_tx in range(1, fanin + 1):
                    Isub += nmos_leak * math.pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
                Isub /= num_states

    elif g_type == pmos:
        if fanin == 1:
            Isub = pmos_leak / num_states
        else:
            if topo == parallel:
                Isub = pmos_leak * fanin / num_states
            else:
                for num_off_tx in range(1, fanin + 1):
                    Isub += pmos_leak * math.pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
                Isub /= num_states

    elif g_type == inv:
        Isub = (nmos_leak + pmos_leak) / 2

    elif g_type == nand:
        Isub += fanin * pmos_leak
        for num_off_tx in range(1, fanin + 1):
            Isub += nmos_leak * math.pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
        Isub /= num_states

    elif g_type == nor:
        for num_off_tx in range(1, fanin + 1):
            Isub += pmos_leak * math.pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
        Isub += fanin * nmos_leak
        Isub /= num_states

    elif g_type == tri:
        Isub += (nmos_leak + pmos_leak) / 2
        Isub += nmos_leak * UNI_LEAK_STACK_FACTOR
        Isub /= 2

    elif g_type == tg:
        Isub = (nmos_leak + pmos_leak) / 2

    else:
        raise ValueError("Invalid gate type")

    return Isub

def cmos_Ig_leakage(nWidth, pWidth, fanin, g_type, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False, topo=series):
    assert fanin >= 1
    nmos_leak = cmos_Ig_n(nWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    pmos_leak = cmos_Ig_p(pWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    Ig_on = 0
    num_states = int(math.pow(2.0, fanin))

    if g_type == nmos:
        if fanin == 1:
            Ig_on = nmos_leak / num_states
        else:
            if topo == parallel:
                for num_on_tx in range(1, fanin + 1):
                    Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx
            else:
                Ig_on += nmos_leak * fanin
                for num_on_tx in range(1, fanin):
                    Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
                Ig_on /= num_states

    elif g_type == pmos:
        if fanin == 1:
            Ig_on = pmos_leak / num_states
        else:
            if topo == parallel:
                for num_on_tx in range(1, fanin + 1):
                    Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx
            else:
                Ig_on += pmos_leak * fanin
                for num_on_tx in range(1, fanin):
                    Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
                Ig_on /= num_states

    elif g_type == inv:
        Ig_on = (nmos_leak + pmos_leak) / 2

    elif g_type == nand:
        for num_on_tx in range(1, fanin + 1):
            Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx
        Ig_on += nmos_leak * fanin
        for num_on_tx in range(1, fanin):
            Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
        Ig_on /= num_states

    elif g_type == nor:
        Ig_on += pmos_leak * fanin
        for num_on_tx in range(1, fanin):
            Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
        for num_on_tx in range(1, fanin + 1):
            Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx
        Ig_on /= num_states

    elif g_type == tri:
        Ig_on += (2 * nmos_leak + 2 * pmos_leak) / 2
        Ig_on += (nmos_leak + pmos_leak) / 2
        Ig_on /= 2

    elif g_type == tg:
        Ig_on = (nmos_leak + pmos_leak) / 2

    else:
        raise ValueError("Invalid gate type")

    return Ig_on

def shortcircuit_simple(vt, velocity_index, c_in, c_out, w_nmos, w_pmos, i_on_n, i_on_p, i_on_n_in, i_on_p_in, vdd):
    fo_n = i_on_n / i_on_n_in
    fo_p = i_on_p / i_on_p_in
    fanout = c_out / c_in
    beta_ratio = i_on_p / i_on_n
    vt_to_vdd_ratio = vt / vdd

    p_short_circuit_discharge_low = (10 / 3) * (pow((vdd - vt) - vt_to_vdd_ratio, 3.0) / pow(velocity_index, 2.0) / pow(2.0, 3 * vt_to_vdd_ratio * vt_to_vdd_ratio)) * c_in * vdd * vdd * fo_p * fo_p / fanout / beta_ratio
    p_short_circuit_charge_low = (10 / 3) * (pow((vdd - vt) - vt_to_vdd_ratio, 3.0) / pow(velocity_index, 2.0) / pow(2.0, 3 * vt_to_vdd_ratio * vt_to_vdd_ratio)) * c_in * vdd * vdd * fo_n * fo_n / fanout * beta_ratio

    p_short_circuit_discharge = p_short_circuit_discharge_low
    p_short_circuit_charge = p_short_circuit_charge_low
    p_short_circuit = (p_short_circuit_discharge + p_short_circuit_charge) / 2

    return p_short_circuit

def shortcircuit(vt, velocity_index, c_in, c_out, w_nmos, w_pmos, i_on_n, i_on_p, i_on_n_in, i_on_p_in, vdd):
    fo_p = i_on_p / i_on_p_in
    fanout = 1
    beta_ratio = i_on_p / i_on_n
    e = 2.71828
    f_alpha = 1 / (velocity_index + 2) - velocity_index / (2 * (velocity_index + 3)) + velocity_index / (velocity_index + 4) * (velocity_index / 2 - 1)
    k_v = 0.9 / 0.8 + (vdd - vt) / 0.8 * math.log(10 * (vdd - vt) / e)
    g_v_alpha = (velocity_index + 1) * pow((1 - velocity_index), velocity_index) * pow((1 - velocity_index), velocity_index / 2) / f_alpha / pow((1 - velocity_index - velocity_index), (velocity_index / 2 + velocity_index + 2))
    h_v_alpha = pow(2, velocity_index) * (velocity_index + 1) * pow((1 - velocity_index), velocity_index) / pow((1 - velocity_index - velocity_index), (velocity_index + 1))

    p_short_circuit_discharge = k_v * vdd * vdd * c_in * fo_p * fo_p / ((vdd - vt) * g_v_alpha * fanout * beta_ratio / 2 / k_v + h_v_alpha * fo_p)
    return p_short_circuit_discharge

def wire_resistance(resistivity, wire_width, wire_thickness, barrier_thickness, dishing_thickness, alpha_scatter):
    resistance = alpha_scatter * resistivity / ((wire_thickness - barrier_thickness - dishing_thickness) * (wire_width - 2 * barrier_thickness))
    return resistance

def wire_capacitance(wire_width, wire_thickness, wire_spacing, ild_thickness, miller_value, horiz_dielectric_constant, vert_dielectric_constant, fringe_cap):
    vertical_cap = 2 * PERMITTIVITY_FREE_SPACE * vert_dielectric_constant * wire_width / ild_thickness
    sidewall_cap = 2 * PERMITTIVITY_FREE_SPACE * miller_value * horiz_dielectric_constant * wire_thickness / wire_spacing
    total_cap = vertical_cap + sidewall_cap + fringe_cap
    return total_cap

def tsv_resistance(resistivity, tsv_len, tsv_diam, tsv_contact_resistance):
    resistance = resistivity * tsv_len / (math.pi * (tsv_diam / 2) ** 2) + tsv_contact_resistance
    return resistance

def tsv_capacitance(tsv_len, tsv_diam, tsv_pitch, dielec_thickness, liner_dielectric_constant, depletion_width):
    e_si = PERMITTIVITY_FREE_SPACE * 11.9
    PI = math.pi
    lateral_coupling_constant = 4.1
    diagonal_coupling_constant = 5.3

    liner_cap = 2 * PI * PERMITTIVITY_FREE_SPACE * liner_dielectric_constant * tsv_len / math.log(1 + dielec_thickness / (tsv_diam / 2))
    depletion_cap = 2 * PI * e_si * tsv_len / math.log(1 + depletion_width / (dielec_thickness + tsv_diam / 2))
    self_cap = 1 / (1 / liner_cap + 1 / depletion_cap)

    lateral_coupling_cap = 0.4 * (0.225 * math.log(0.97 * tsv_len / tsv_diam) + 0.53) * e_si / (tsv_pitch - tsv_diam) * PI * tsv_diam * tsv_len
    diagonal_coupling_cap = 0.4 * (0.225 * math.log(0.97 * tsv_len / tsv_diam) + 0.53) * e_si / (1.414 * tsv_pitch - tsv_diam) * PI * tsv_diam * tsv_len

    total_cap = self_cap + lateral_coupling_constant * lateral_coupling_cap + diagonal_coupling_constant * diagonal_coupling_cap
    return total_cap

def tsv_area(tsv_pitch):
    return tsv_pitch ** 2
