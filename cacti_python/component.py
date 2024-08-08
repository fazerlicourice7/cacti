import math
from math import ceil, log, pow
import sys
from .const import *
from .parameter import g_tp
from .parameter import g_ip
from .parameter import *
from .cacti_interface import PowerDef


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

    # Change: Relational - set to one option to reduce expression size
    # total_diff_w = sp.Piecewise(
    #     (2 * spacing_poly_to_poly + num_stacked_in * w_poly + (num_stacked_in - 1) * g_tp.spacing_poly_to_poly, num_folded_tr <= 1),
    #     (2 * spacing_poly_to_poly + num_stacked_in * w_poly + (num_stacked_in - 1) * g_tp.spacing_poly_to_poly +
    #     (num_folded_tr - 2) * 2 * spacing_poly_to_poly +
    #     (num_folded_tr - 1) * num_stacked_in * w_poly +
    #     (num_folded_tr - 1) * (num_stacked_in - 1) * g_tp.spacing_poly_to_poly, num_folded_tr > 1)
    # )

    total_diff_w =  2 * spacing_poly_to_poly + num_stacked_in * w_poly + (num_stacked_in - 1) * g_tp.spacing_poly_to_poly + \
                    (num_folded_tr - 2) * 2 * spacing_poly_to_poly + \
                    (num_folded_tr - 1) * num_stacked_in * w_poly + \
                    (num_folded_tr - 1) * (num_stacked_in - 1) * g_tp.spacing_poly_to_poly
    
    # total_diff_w = 2 * spacing_poly_to_poly + num_stacked_in * w_poly + (num_stacked_in - 1) * g_tp.spacing_poly_to_poly
    # total_diff_w = (2 * spacing_poly_to_poly +  # for both source and drain
    #                 num_stacked_in * w_poly +
    #                 (num_stacked_in - 1) * g_tp.spacing_poly_to_poly)
    # if num_folded_tr > 1:
    #     total_diff_w += ((num_folded_tr - 2) * 2 * spacing_poly_to_poly +
    #                       (num_folded_tr - 1) * num_stacked_in * w_poly +
    #                       (num_folded_tr - 1) * (num_stacked_in - 1) * g_tp.spacing_poly_to_poly)

    return total_diff_w

def compute_gate_area(gate_type, num_inputs, w_pmos, w_nmos, h_gate):
    # Relational
    if w_pmos <= 0.0 or w_nmos <= 0.0:
            return 0.0

    h_tr_region = h_gate - 2 * g_tp.HPOWERRAIL  
    ratio_p_to_n = w_pmos / (w_pmos + w_nmos)

    # Relational resolved with 'result' below
    # if ratio_p_to_n >= 1 or ratio_p_to_n <= 0:
    #         return 0.0
    
    w_folded_pmos = (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS) * ratio_p_to_n
    w_folded_nmos = (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS) * (1 - ratio_p_to_n)

    # Relational
    # assert w_folded_pmos > 0
            
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

    gate_w = symbolic_convex_max(total_ndiff_w, total_pdiff_w)
 
    # Change: Relational - set to one option to reduce expression size
    # gate_h = sp.Piecewise(
    #     ((w_nmos + w_pmos + g_tp.MIN_GAP_BET_P_AND_N_DIFFS + 2 * g_tp.HPOWERRAIL), w_folded_nmos > w_nmos),
    #     (h_gate, True)  
    # )
    gate_h = (w_nmos + w_pmos + g_tp.MIN_GAP_BET_P_AND_N_DIFFS + 2 * g_tp.HPOWERRAIL)

    result = sp.Piecewise(
         (0, sp.Or(ratio_p_to_n >= 1, ratio_p_to_n <= 0)),
         (gate_w * gate_h, True )
    )

    return result

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
    # num_gates = sp.log(F) / sp.log(fopt)
    # if(F == 0):
    #     num_gates = 4
    # else:
    #     num_gates = 4

    num_gates = 4
    f = sp.Pow(F, 1.0 / num_gates)
    i = num_gates - 1
    if (f == 0):
        f = 1
    C_in = C_load / f

    w_n[i] = (1.0 / (1.0 + p_to_n_sz_ratio)) * C_in / gate_C(1, 0, is_dram_, False, is_wl_tr_)

    # RECENT CHANGE: Max - ignore to reduce expression length
    w_n[i] = symbolic_convex_max(w_n[i], g_tp.min_w_nmos_)

    w_p[i] = p_to_n_sz_ratio * w_n[i]

    # CHANGE: ARRAY LOGIC
    # #TODO IMPORTANT SINCE RELATIONAL
    # if w_n[i] > max_w_nmos:
    #     C_ld = gate_C((1 + p_to_n_sz_ratio) * max_w_nmos, 0, is_dram_, False, is_wl_tr_)
    #     F = g * C_ld / gate_C(w_n[0] + w_p[0], 0, is_dram_, False, is_wl_tr_)

    #     num_gates += 2
    #     f = sp.Pow(F, 1.0 / (num_gates - 1))
    #     i = num_gates - 1
    #     w_n[i] = max_w_nmos
    #     w_p[i] = p_to_n_sz_ratio * w_n[i]

    for i in range(num_gates - 2, 0, -1):
        w_item = w_n[i + 1] / f
        if w_item == sp.zoo:
            w_item = 0

        # RECENT CHANGE: Max - ignore to reduce expression length
        # w_n[i] = symbolic_convex_max(w_item, g_tp.min_w_nmos_)
        w_n[i] = w_item

        w_p[i] = p_to_n_sz_ratio * w_n[i]

    assert num_gates <= MAX_NUMBER_GATES_STAGE
    return num_gates


def compute_tr_width_after_folding(input_width, threshold_folding_width):
        # CHANGE: RELATIONAL: this function either returns 0 or result

        if isinstance(input_width, (int, float)):
            if input_width <= 0:
                return 0

        # CHANGE: RELATIONAL
        # num_folded_tr = sp.ceiling(input_width / threshold_folding_width)
        # spacing_poly_to_poly = g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact
        # width_poly = g_ip.F_sz_um
        # total_diff_width = (num_folded_tr * width_poly +
        #                     (num_folded_tr + 1) * spacing_poly_to_poly)
        # return total_diff_width
        
        result = sp.Piecewise(
            (0, input_width <= 0), 
            (sp.ceiling(input_width / threshold_folding_width) * g_ip.F_sz_um +
            (sp.ceiling(input_width / threshold_folding_width) + 1) * (g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact),
            True)  
        )

        return result