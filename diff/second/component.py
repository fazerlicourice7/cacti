import math
from math import ceil, log, pow
import sys
from const import *
from parameter import g_tp
from parameter import g_ip
from parameter import *
from cacti_interface import PowerDef


# Assuming g_ip and g_tp are global configurations provided elsewhere in the code
# You will need to provide these global configurations or import them as necessary

class Component:
    def __init__(self):
        self.area = Area()  # Define appropriate default values or constructors
        self.power = PowerDef()
        self.rt_power = PowerDef()
        self.delay = 0
        self.cycle_time = 0

def compute_diffusion_width(num_stacked_in, num_folded_tr):
    w_poly = g_ip.F_sz_um
    spacing_poly_to_poly = g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact
    total_diff_w = (2 * spacing_poly_to_poly +  # for both source and drain
                    num_stacked_in * w_poly +
                    (num_stacked_in - 1) * g_tp.spacing_poly_to_poly)

    # TODO Important can't do this symbolically
    # if num_folded_tr > 1:
    #     total_diff_w += ((num_folded_tr - 2) * 2 * spacing_poly_to_poly +
    #                       (num_folded_tr - 1) * num_stacked_in * w_poly +
    #                       (num_folded_tr - 1) * (num_stacked_in - 1) * g_tp.spacing_poly_to_poly)

    return total_diff_w

def compute_gate_area(gate_type, num_inputs, w_pmos, w_nmos, h_gate):
    #TODO IMPORTANT this can't be done synbolically
    # if w_pmos <= 0.0 or w_nmos <= 0.0:
    #     return 0.0

    h_tr_region = h_gate - 2 * g_tp.HPOWERRAIL
    # TODO important w_pmos + w_nmos shortcut
    if (w_pmos + w_nmos) == 0:
        ratio_p_to_n = 0
    else:
        ratio_p_to_n = w_pmos / (w_pmos + w_nmos)

    # TODO IMPORTANT this can't be done synbolically
    # if ratio_p_to_n >= 1 or ratio_p_to_n <= 0:
    #     return 0.0

    w_folded_pmos = (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS) * ratio_p_to_n
    w_folded_nmos = (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS) * (1 - ratio_p_to_n)

    # TODO IMPORTANT this can't be done synbolically
    # assert w_folded_pmos > 0
    if(w_folded_pmos == 0):
        return 0
    num_folded_pmos = sp.ceiling(w_pmos / w_folded_pmos)
    num_folded_nmos = sp.ceiling(w_nmos / w_folded_nmos)

    if gate_type == "INV" or gate_type == "inv":
        total_ndiff_w = compute_diffusion_width(1, num_folded_nmos)
        total_pdiff_w = compute_diffusion_width(1, num_folded_pmos)
    elif gate_type == "NOR" or gate_type == "nor":
        total_ndiff_w = compute_diffusion_width(1, num_inputs * num_folded_nmos)
        total_pdiff_w = compute_diffusion_width(num_inputs, num_folded_pmos)
    elif gate_type == "NAND" or gate_type == "nand":
        total_ndiff_w = compute_diffusion_width(num_inputs, num_folded_nmos)
        total_pdiff_w = compute_diffusion_width(1, num_inputs * num_folded_pmos)
    else:
        print(f"Unknown gate type: {gate_type}")
        sys.exit(1)

    gate_w = sp.Max(total_ndiff_w, total_pdiff_w)

    # TODO Important can't do this symbolically
    # if w_folded_nmos > w_nmos:
    gate_h = (w_nmos + w_pmos + g_tp.MIN_GAP_BET_P_AND_N_DIFFS + 2 * g_tp.HPOWERRAIL)
    # else:
    #     gate_h = h_gate

    return gate_w * gate_h  # Assuming area is width * height

def compute_tr_width_after_folding(input_width, threshold_folding_width):
    if input_width <= 0:
        return 0

    num_folded_tr = ceil(input_width / threshold_folding_width)
    spacing_poly_to_poly = g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact
    width_poly = g_ip.F_sz_um
    total_diff_width = (num_folded_tr * width_poly +
                        (num_folded_tr + 1) * spacing_poly_to_poly)

    return total_diff_width

def height_sense_amplifier(pitch_sense_amp):
    h_pmos_tr = (compute_tr_width_after_folding(g_tp.w_sense_p, pitch_sense_amp) * 2 +
                  compute_tr_width_after_folding(g_tp.w_iso, pitch_sense_amp) +
                  2 * g_tp.MIN_GAP_BET_SAME_TYPE_DIFFS)

    h_nmos_tr = (compute_tr_width_after_folding(g_tp.w_sense_n, pitch_sense_amp) * 2 +
                  compute_tr_width_after_folding(g_tp.w_sense_en, pitch_sense_amp) +
                  2 * g_tp.MIN_GAP_BET_SAME_TYPE_DIFFS)

    return h_pmos_tr + h_nmos_tr + g_tp.MIN_GAP_BET_P_AND_N_DIFFS

def logical_effort(num_gates_min, g, F, w_n, w_p, C_load, p_to_n_sz_ratio, is_dram_, is_wl_tr_, max_w_nmos):
    #TODO deleted int
    # print(f'F is this {F}')
    num_gates = sp.log(F) / sp.log(fopt)
    if(F == 0):
        num_gates = 2
    # print(f'num_gates is this {num_gates}')
    # print("End")
    # print("")

    num_gates += (num_gates % 2)
    num_gates = sp.Max(num_gates, num_gates_min)

    f = sp.Pow(F, 1.0 / num_gates)
    num_gates = 3 # TODO IMPORTANT this can't be done synbolically
    i = num_gates - 1
    #TODO IMPORTANT this can't be done synbolically
    # i = 2
    #print(f'OH NOES! {i}')
    C_in = C_load / f
    # print(f'I is {i}')
    w_n[i] = (1.0 / (1.0 + p_to_n_sz_ratio)) * C_in / gate_C(1, 0, is_dram_, False, is_wl_tr_)
    # print(f'w_n[i] is this {w_n[i]}')
    # print(f'min_w_nmos_ is this {g_tp.min_w_nmos_}')
    # print("End")
    # print("")
    #TODO important nan shortcut
    if not contains_any_symbol(w_n[i]) and math.isnan(w_n[i]):
        w_n[i] = 0
    w_n[i] = sp.Max(w_n[i], g_tp.min_w_nmos_)
    w_p[i] = p_to_n_sz_ratio * w_n[i]

    #TODO IMPORTANT SINCE RELATIONAL
    # if w_n[i] > max_w_nmos:
    #     print(f'OH NOES p_to_n_sz_ratio! {p_to_n_sz_ratio}')
    #     print(f'OH NOES max_w_nmos! {max_w_nmos}')
    #     C_ld = gate_C((1 + p_to_n_sz_ratio) * max_w_nmos, 0, is_dram_, False, is_wl_tr_)
    #     print(f'OH NOES C_ld! {C_ld}')
    #     F = g * C_ld / gate_C(w_n[0] + w_p[0], 0, is_dram_, False, is_wl_tr_)
    #     print(f'OH NOES F! {F}')
    #     #TODO deleted int
    #     num_gates = sp.log(F) / sp.log(fopt) + 1
    #     num_gates += (num_gates % 2)
    #     print(f'OH NOES num_gates! {num_gates}')
    #     num_gates = sp.Max(num_gates, num_gates_min)
    #     f = sp.Pow(F, 1.0 / (num_gates - 1))
    #     i = num_gates - 1
    #     w_n[i] = max_w_nmos
    #     w_p[i] = p_to_n_sz_ratio * w_n[i]

    for i in range(num_gates - 2, 0, -1):
        #TODO important zoo shortcut
        w_item = w_n[i + 1] / f
        if w_item == sp.zoo:
            w_item = 0
        
        w_n[i] = sp.Max(w_item, g_tp.min_w_nmos_)
        w_p[i] = p_to_n_sz_ratio * w_n[i]

    assert num_gates <= MAX_NUMBER_GATES_STAGE
    return num_gates


def compute_tr_width_after_folding(input_width, threshold_folding_width):
        # TODO can't do relational
        # if input_width <= 0:
        #     return 0

        # TODO zero
        if (threshold_folding_width == 0):
            num_folded_tr = sp.ceiling(input_width)
        else:
            num_folded_tr = sp.ceiling(input_width / threshold_folding_width)
        spacing_poly_to_poly = g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact
        width_poly = g_ip.F_sz_um
        total_diff_width = (num_folded_tr * width_poly +
                            (num_folded_tr + 1) * spacing_poly_to_poly)

        return total_diff_width