import sympy as sp
import math
import os

'''
Consts
'''
NCH = 0
PCH = 1
RISE = 1
is_dram_, is_dram = False, False

'''
Input parameters to dat file
'''
C_g_ideal, C_fringe, C_junc, C_junc_sw, l_phy, F_sz_um, \
n2p_drv_rt, nmos_effective_resistance_multiplier, Vdd, \
I_on_n, wire_c_per_micron, wire_length, wire_delay = sp.symbols('''
    C_g_ideal
    C_fringe
    C_junc
    C_junc_sw
    l_phy
    F_sz_um
    n2p_drv_rt
    nmos_effective_resistance_multiplier
    Vdd
    I_on_n
    wire_c_per_micron
    wire_length
    wire_delay
''')

g_tp = {
    "C_g_ideal": C_g_ideal,
    "C_fringe": C_fringe,
    "C_junc": C_junc,
    "C_junc_sw": C_junc_sw,
    "l_phy": l_phy,
    "F_sz_um": F_sz_um,
    "n2p_drv_rt": n2p_drv_rt,
    "nmos_effective_resistance_multiplier": nmos_effective_resistance_multiplier,
    "Vdd": Vdd,
    "I_on_n": I_on_n,
    "wire_c_per_micron": wire_c_per_micron,
    "wire_length": wire_length,
    "wire_delay": wire_delay
}

'''
Main/overall function
This uses mat.cc to calcuate delays, then uca.cc to accumulate delays
Returns acess_time
'''
def get_access_time(g_tp, inrisetime):
  # Compute Delays: for order of calculations look at mat.cc
  r_predec_delay = get_predec_delay(g_tp, inrisetime)
  row_dec_delay = get_dec_delay(g_tp, r_predec_delay)

  b_mux_predec_delay = get_predec_delay(g_tp, inrisetime)
  bit_mux_dec_delay = get_dec_delay(g_tp, b_mux_predec_delay)

  sa_mux_lev_1_predec_delay = get_predec_delay(g_tp, inrisetime)
  sa_mux_lev_1_dec_delay = get_dec_delay(g_tp, sa_mux_lev_1_predec_delay)

  sa_mux_lev_2_predec_delay = get_predec_delay(g_tp, inrisetime)
  sa_mux_lev_2_dec_delay = get_dec_delay(g_tp, sa_mux_lev_2_predec_delay)

  bitline_delay = 0
  sa_delay = 0
  sub_array_out_drv_delay = 0
  sub_array_out_wire_delay = 0
  subarray_out_drv_htree_delay = sub_array_out_drv_delay + sub_array_out_wire_delay
  htree_out_data_delay = 0
  comparator_delay = 0
  matchchline_delay = 0

  # Accumulate Delays uca.cc
  # delay_array_to_mat = htree_in_add.delay + bank.htree_in_add.delay 
  delay_array_to_mat = get_htree_in_add_delay(g_tp) # (Need to check wire of this)
  max_delay_before_row_decoder = delay_array_to_mat + r_predec_delay
  delay_array_to_sa_mux_lev_1_decoder = delay_array_to_mat + sa_mux_lev_1_predec_delay + sa_mux_lev_1_dec_delay
  delay_array_to_sa_mux_lev_2_decoder = delay_array_to_mat + sa_mux_lev_2_predec_delay + sa_mux_lev_2_dec_delay
  delay_inside_mat = row_dec_delay + bitline_delay + sa_delay

  delay_before_subarray_output_driver = sp.Max(
      sp.Max(max_delay_before_row_decoder + delay_inside_mat,
          delay_array_to_mat + b_mux_predec_delay+ bit_mux_dec_delay + sa_delay),
      sp.Max(delay_array_to_sa_mux_lev_1_decoder,
          delay_array_to_sa_mux_lev_2_decoder)
  )

  #delay_from_subarray_out_drv_to_out = subarray_out_drv_htree_delay + bank.htree_out_data.delay + htree_out_data.delay
  delay_from_subarray_out_drv_to_out = subarray_out_drv_htree_delay + htree_out_data_delay
  access_time = comparator_delay

  fully_assoc = False # CHECK this needs to be input
  if fully_assoc:
      ram_delay_inside_mat = bitline_delay + matchchline_delay
      #access_time = htree_in_add.delay + bank.htree_in_add.delay
      access_time = get_htree_in_add_delay(g_tp)
      access_time += ram_delay_inside_mat + delay_from_subarray_out_drv_to_out
  else:
      access_time = delay_before_subarray_output_driver + delay_from_subarray_out_drv_to_out

  is_main_mem = False # CHECK this needs to be input
  if is_main_mem:
      t_rcd = max_delay_before_row_decoder + delay_inside_mat
      cas_latency = max(delay_array_to_sa_mux_lev_1_decoder, delay_array_to_sa_mux_lev_2_decoder) + delay_from_subarray_out_drv_to_out
      access_time = t_rcd + cas_latency

  return access_time

'''
The following are the helper functions in order
to compute delays of the various components
'''
# htree.[cc/h]
def get_htree_in_add_delay(g_tp):
    # CHECK delay of wire and whether to blackbox it
    return g_tp["wire_length"] * g_tp["wire_delay"] #SYMBOLIC

# decoder.[cc/h]
def get_predec_delay(g_tp, inrisetime):
    return get_predec_blk_delay(g_tp, inrisetime, inrisetime)

def get_predec_blk_delay(g_tp, inrisetime_nand2_path, inrisetime_nand3_path):
    # Init Predec
    width_nand2_path_n, width_nand2_path_p = [0] * 20, [0] * 20
    for i in range (20):
        width_nand2_path_n[i] = 0
        width_nand2_path_p[i] = 0

    min_w_nmos_ = 3 * g_tp["F_sz_um"] / 2 # paramter.cc
    max_w_nmos_ = 100 * g_tp["F_sz_um"];
    width_nand2_path_n[0] = min_w_nmos_
    p_to_n_sz_ratio = g_tp["n2p_drv_rt"]

    # decoder.[cc/h]
    w_dec_n_0 = 3 * min_w_nmos_ # check the if/else statement
    w_dec_p_0 = p_to_n_sz_ratio * min_w_nmos_
    # c_load_nand2_path_out = gate_C(dec->w_dec_n[0] + dec->w_dec_p[0], 0, is_dram_)
    c_load_nand2_path_out = gate_C(g_tp, w_dec_n_0 + w_dec_p_0, 0, is_dram_)

    F = c_load_nand2_path_out / gate_C(g_tp, width_nand2_path_n[0] + width_nand2_path_p[0], 0, is_dram_)
    
    number_gates_nand2_path = logical_effort(
          g_tp,
          2,
          1,
          F,
          width_nand2_path_n,
          width_nand2_path_p,
          c_load_nand2_path_out,
          p_to_n_sz_ratio,
          is_dram_, False, max_w_nmos_)
    
    # Calculate Delay
    ret_val = 0
    flag_driver_exists = True
    if flag_driver_exists:
        PCH = 0
        NCH = 1
        RISE = 1
        cell_h_def = 50 * g_tp["F_sz_um"];
        for i in range(number_gates_nand2_path - 1):
            rd = tr_R_on(g_tp, width_nand2_path_n[i], NCH, 1, is_dram_)
            c_gate_load = gate_C(g_tp, width_nand2_path_p[i+1] + width_nand2_path_n[i+1], 0.0, is_dram_)
            c_intrinsic = (drain_C_(g_tp, width_nand2_path_p[i], PCH, 1, 1, cell_h_def, is_dram_) +
                           drain_C_(g_tp, width_nand2_path_n[i], NCH, 1, 1, cell_h_def, is_dram_))
            tf = rd * (c_intrinsic + c_gate_load)
            this_delay = horowitz(inrisetime_nand2_path, tf, 0.5, 0.5, RISE)
            # delay_nand2_path += this_delay
            inrisetime_nand2_path = this_delay / (1.0 - 0.5)
            #power_nand2_path.readOp.dynamic += (c_gate_load + c_intrinsic) * 0.5 * Vdd * Vdd

        if number_gates_nand2_path != 0:
            i = number_gates_nand2_path - 1
            rd = tr_R_on(g_tp, width_nand2_path_n[i], NCH, 1, is_dram_)
            c_intrinsic = (drain_C_(g_tp, width_nand2_path_p[i], PCH, 1, 1, cell_h_def, is_dram_) +
                           drain_C_(g_tp, width_nand2_path_n[i], NCH, 1, 1, cell_h_def, is_dram_))
            c_load = c_load_nand2_path_out
            r_load_nand2_path_out = 0 # CHECK Decoder.cc/h
            tf = rd * (c_intrinsic + c_load) + r_load_nand2_path_out * c_load / 2
            this_delay = horowitz(inrisetime_nand2_path, tf, 0.5, 0.5, RISE)
            # delay_nand2_path += this_delay
            ret_val = this_delay / (1.0 - 0.5)
            #power_nand2_path.readOp.dynamic += (c_intrinsic + c_load) * 0.5 * Vdd * Vdd

    return ret_val
    
    #figure out width_nand2_path_p and width_nand2_pathn

def get_dec_delay(g_tp, inrisetime):
    #Init Decoder
    num_in_signals = 0
    num_gates_min = 2

    p_to_n_sz_ratio = g_tp["n2p_drv_rt"]
    gnand2 = (2 + p_to_n_sz_ratio) / (1 + p_to_n_sz_ratio)
    gnand3 = (3 + p_to_n_sz_ratio) / (1 + p_to_n_sz_ratio)
    #check these decoder.cc based on FA and num_in_signals
    w_dec_n, w_dec_p = [0] * 20, [0] * 20
    for i in range (20):
        w_dec_n[i] = 0
        w_dec_p[i] = 0
    # remove redundancy of min_w_nmos
    min_w_nmos_ = 3 * g_tp["F_sz_um"] / 2 # paramter.cc
    min_w_pmos_ = p_to_n_sz_ratio * min_w_nmos_
    w_dec_n[0] = 3 * min_w_nmos_
    w_dec_p[0] = p_to_n_sz_ratio * min_w_nmos_
    F = gnand3
    is_wl_tr = False # default false in TSV.cc
    #check C_ld and R_wire in memorybus.cc
    C_ld_dec_out = gate_C(g_tp, min_w_nmos_+min_w_pmos_,0)
    R_wire_dec_out = 0
    F *= C_ld_dec_out / (gate_C(g_tp, w_dec_n[0], 0, is_dram, False, is_wl_tr) +
                         gate_C(g_tp, w_dec_p[0], 0, is_dram, False, is_wl_tr))
    
    max_w_nmos_dec = 8 * F_sz_um

    num_gates = logical_effort(
        g_tp,
        num_gates_min, 
        gnand2 if num_in_signals == 2 else gnand3,
        F,
        w_dec_n,
        w_dec_p,
        C_ld_dec_out,
        p_to_n_sz_ratio,
        is_dram,
        is_wl_tr,
        max_w_nmos_dec)
    
    h_dec = 4 # 8 if comm_ram see parameter.cc
    cell_h = 100 # CHECK need to fix this
    area_h = h_dec * cell_h
      
    # Caclulate Delay
    exist = True
    if exist:
        ret_val = 0  # outrisetime
        Vdd = g_tp["Vdd"]

        # bypass for now
        # if is_wl_tr and is_dram:
        #     Vpp = g_tp['vpp']
        # elif is_wl_tr:
        #     Vpp = g_tp['sram_cell']['Vdd']
        # else:
        #     Vpp = g_tp['peri_global']['Vdd']
        Vpp = g_tp["Vdd"]
        
        # First check whether a decoder is required at all
        rd = tr_R_on(g_tp, w_dec_n[0], NCH, num_in_signals, is_dram, False, is_wl_tr)
        c_load = gate_C(g_tp, w_dec_n[1] + w_dec_p[1], 0.0, is_dram, False, is_wl_tr)
        c_intrinsic = (
            drain_C_(g_tp, w_dec_p[0], PCH, 1, 1, area_h, is_dram, False, is_wl_tr) * num_in_signals +
            drain_C_(g_tp, w_dec_n[0], NCH, num_in_signals, 1, area_h, is_dram, False, is_wl_tr)
        )
        tf = rd * (c_intrinsic + c_load)
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        delay = this_delay
        inrisetime = this_delay / (1.0 - 0.5)
        # comment out for now
        # power['readOp']['dynamic'] += (c_load + c_intrinsic) * Vdd * Vdd 

        for i in range(1, num_gates - 1):
            rd = tr_R_on(g_tp, w_dec_n[i], NCH, 1, is_dram, False, is_wl_tr)
            c_load = gate_C(g_tp, w_dec_p[i + 1] + w_dec_n[i + 1], 0.0, is_dram, False, is_wl_tr)
            c_intrinsic = (
                drain_C_(g_tp, w_dec_p[i], PCH, 1, 1, area_h, is_dram, False, is_wl_tr) +
                drain_C_(g_tp, w_dec_n[i], NCH, 1, 1, area_h, is_dram, False, is_wl_tr)
            )
            tf = rd * (c_intrinsic + c_load)
            this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
            delay += this_delay
            inrisetime = this_delay / (1.0 - 0.5)
            # comment out for now
            # power['readOp']['dynamic'] += (c_load + c_intrinsic) * Vdd * Vdd

        # Add delay of final inverter that drives the wordline
        i = num_gates - 1
        c_load = C_ld_dec_out
        rd = tr_R_on(g_tp, w_dec_n[i], NCH, 1, is_dram, False, is_wl_tr)
        c_intrinsic = (
            drain_C_(g_tp, w_dec_p[i], PCH, 1, 1, area_h, is_dram, False, is_wl_tr) +
            drain_C_(g_tp, w_dec_n[i], NCH, 1, 1, area_h, is_dram, False, is_wl_tr)
        )
        tf = rd * (c_intrinsic + c_load) + R_wire_dec_out * c_load / 2
        this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        delay += this_delay
        ret_val = this_delay / (1.0 - 0.5)
        # comment out for now
        #power['readOp']['dynamic'] += c_load * Vpp * Vpp + c_intrinsic * Vdd * Vdd

        # CHECK comment out for now
        #compute_power_gating()
        return ret_val
    else:
        return 0.0


# logical_effort in components.[cc/h]
def logical_effort(g_tp, num_gates_min, g, F, w_n, w_p, C_load, p_to_n_sz_ratio, is_dram_, is_wl_tr_, max_w_nmos):
    fopt = 4.0 # const.h
    #num_gates = int(math.log(F) / math.log(fopt))
    # print(F)
    # print(fopt)
    num_gates = sp.log(F) / math.log(fopt)

    # Check if num_gates is odd. If so, add 1 to make it even
    num_gates += 1 if num_gates % 2 else 0
    num_gates = sp.Max(num_gates, num_gates_min)

    # Recalculate the effective fanout of each stage
    f = pow(F, 1.0 / num_gates)
    num_gates = 5 # CHECK since symbolic, we just have to approx since we don't know exact
    i = num_gates - 1
    C_in = C_load / f
    w_n[i] = (1.0 / (1.0 + p_to_n_sz_ratio)) * C_in / gate_C(g_tp, 1, 0, is_dram_, False, is_wl_tr_)
    min_w_nmos_ = 3 * g_tp["F_sz_um"] / 2 # paramter.cc
    w_n[i] = sp.Max(w_n[i], min_w_nmos_)
    w_p[i] = p_to_n_sz_ratio * w_n[i]

    # Check ignore this for now...
    # if w_n[i] > max_w_nmos:
    #     C_ld = gate_C(g_tp, (1 + p_to_n_sz_ratio) * max_w_nmos, 0, is_dram_, False, is_wl_tr_)
    #     F = g * C_ld / gate_C(g_tp, w_n[0] + w_p[0], 0, is_dram_, False, is_wl_tr_)
    #     num_gates = int(sp.log(F) / sp.log(fopt)) + 1
    #     num_gates += 1 if num_gates % 2 else 0
    #     num_gates = sp.Max(num_gates, num_gates_min)
    #     num_gates = 5 # CHECK since symbolic, we just have to approx since we don't know exact
    #     f = pow(F, 1.0 / (num_gates - 1))
    #     i = num_gates - 1
    #     w_n[i] = max_w_nmos
    #     w_p[i] = p_to_n_sz_ratio * w_n[i]

    for i in range(num_gates - 2, 0, -1):
        w_n[i] = sp.Max(w_n[i+1] / f, min_w_nmos_)
        w_p[i] = p_to_n_sz_ratio * w_n[i]

    MAX_NUMBER_GATES_STAGE = 20
    assert num_gates <= MAX_NUMBER_GATES_STAGE
    return num_gates

# basic_circuit.[cc/h]
# ASK about diferent configs
def gate_C (g_tp, width, wirelength, _is_dram = False, _is_cell = False, 
            _is_wl_tr = False, _is_sleep_tx = False):
    Cpolywire = 0 # const.h
    return (g_tp["C_g_ideal"] + 0.2 * g_tp["C_g_ideal"] + 3 * g_tp["C_fringe"]) * width + g_tp["l_phy"] * Cpolywire

def tr_R_on(g_tp, width, nchannel, stack, _is_dram = False, _is_cell = False, _is_wl_tr = False, _is_sleep_tx = False):
    # parameter.cc
    R_nch_on = g_tp["nmos_effective_resistance_multiplier"] * g_tp["Vdd"] /g_tp["I_on_n"] # all dat inputs
    R_pch_on = g_tp["n2p_drv_rt"] * R_nch_on # dat input
    restrans = R_nch_on if nchannel else R_pch_on
    return stack * restrans / width

def drain_C_(g_tp, width, nchannel, stack, next_arg_thresh_folding_width_or_height_cell, fold_dimension, 
             _is_dram, _is_cell = False, _is_wl_tr = False, _is_sleep_tx = False):
    c_junc_area = g_tp["C_junc"]
    c_junc_sidewall = g_tp["C_junc_sw"]
    c_fringe = 2 * g_tp["C_fringe"]
    #c_overlap = 2 * dt.C_overlap
    c_overlap = 2 * 0.2 * g_tp["C_g_ideal"]
    drain_C_metal_connecting_folded_tr = 0

    HPOWERRAIL = 2 * g_tp["F_sz_um"]
    MIN_GAP_BET_P_AND_N_DIFFS = 5 * g_tp["F_sz_um"]

    # Determine the width of the transistor after folding (if it is getting folded)
    if next_arg_thresh_folding_width_or_height_cell == 0:
        w_folded_tr = fold_dimension
    else:
        h_tr_region = fold_dimension - 2 * HPOWERRAIL
        ratio_p_to_n = 2.0 / (2.0 + 1.0)
        if nchannel:
            w_folded_tr = (1 - ratio_p_to_n) * (h_tr_region - MIN_GAP_BET_P_AND_N_DIFFS)
        else:
            w_folded_tr = ratio_p_to_n * (h_tr_region - MIN_GAP_BET_P_AND_N_DIFFS)

    num_folded_tr = sp.ceiling(width / w_folded_tr)
    num_folded_tr = 2 #CHECK set since symbolic

    if num_folded_tr < 2:
        w_folded_tr = width

    w_poly_contact = g_tp["F_sz_um"]
    spacing_poly_to_contact = g_tp["F_sz_um"]
    spacing_poly_to_poly = 1.5 * g_tp["F_sz_um"]

    total_drain_w = (w_poly_contact + 2 * spacing_poly_to_contact) + (stack - 1) * spacing_poly_to_poly
    drain_h_for_sidewall = w_folded_tr
    total_drain_height_for_cap_wrt_gate = w_folded_tr + 2 * w_folded_tr * (stack - 1)

    if num_folded_tr > 1:
        total_drain_w += (num_folded_tr - 2) * (w_poly_contact + 2 * spacing_poly_to_contact) + (num_folded_tr - 1) * ((stack - 1) * spacing_poly_to_poly)

        if num_folded_tr % 2 == 0:
            drain_h_for_sidewall = 0

        total_drain_height_for_cap_wrt_gate *= num_folded_tr
        wire_local_C_per_um = wire_c_per_micron
        drain_C_metal_connecting_folded_tr = wire_local_C_per_um * total_drain_w

    drain_C_area = c_junc_area * total_drain_w * w_folded_tr
    drain_C_sidewall = c_junc_sidewall * (drain_h_for_sidewall + 2 * total_drain_w)
    drain_C_wrt_gate = (c_fringe + c_overlap) * total_drain_height_for_cap_wrt_gate

    return drain_C_area + drain_C_sidewall + drain_C_wrt_gate + drain_C_metal_connecting_folded_tr
  
def horowitz(inputramptime, tf, vs1, vs2, rise):
    if inputramptime == 0 and vs1 == vs2:
        return tf * (-math.log(vs1) if vs1 < 1 else math.log(vs1))
    
    a = inputramptime / tf
    RISE = 1
    if rise == RISE:
        b = 0.5
        td = tf * sp.sqrt(sp.log(vs1)**2 + 2 * a * b * (1.0 - vs1)) + tf * (sp.log(vs1) - sp.log(vs2))
    else:
        b = 0.4
        td = tf * sp.sqrt(sp.log(1.0 - vs1)**2 + 2 * a * b * (vs1)) + tf * (sp.log(1.0 - vs1) - sp.log(1.0 - vs2))
    
    return td

'''
Sympy differentiation
'''
if __name__ == "__main__" :
    inrisetime = sp.symbols('inrisetime')
    access_time_expr = get_access_time(g_tp, inrisetime)
    diff_access_time_C_g_ideal = sp.diff(access_time_expr, g_tp["C_g_ideal"])
    #print(f"The derivative of the function is: {diff_access_time_C_g_ideal}")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = current_dir + "/diff_result.txt"
    try:
        with open(filename, 'w') as file:
            file.write(f"The derivative of the function is: {diff_access_time_C_g_ideal}\n")
        print(f"Output has been written to {filename}")
    except Exception as e:
        print(f"Error writing to file: {e}")