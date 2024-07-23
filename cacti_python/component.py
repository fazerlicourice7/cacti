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

    # TODO RECENTLY COMMENTED
    total_diff_w = sp.Piecewise(
        (2 * spacing_poly_to_poly + num_stacked_in * w_poly + (num_stacked_in - 1) * g_tp.spacing_poly_to_poly, num_folded_tr <= 1),
        (2 * spacing_poly_to_poly + num_stacked_in * w_poly + (num_stacked_in - 1) * g_tp.spacing_poly_to_poly +
        (num_folded_tr - 2) * 2 * spacing_poly_to_poly +
        (num_folded_tr - 1) * num_stacked_in * w_poly +
        (num_folded_tr - 1) * (num_stacked_in - 1) * g_tp.spacing_poly_to_poly, num_folded_tr > 1)
    )
    # total_diff_w = 2 * spacing_poly_to_poly + num_stacked_in * w_poly + (num_stacked_in - 1) * g_tp.spacing_poly_to_poly
    # TODO Important can't do this symbolically
    # total_diff_w = (2 * spacing_poly_to_poly +  # for both source and drain
    #                 num_stacked_in * w_poly +
    #                 (num_stacked_in - 1) * g_tp.spacing_poly_to_poly)
    # if num_folded_tr > 1:
    #     total_diff_w += ((num_folded_tr - 2) * 2 * spacing_poly_to_poly +
    #                       (num_folded_tr - 1) * num_stacked_in * w_poly +
    #                       (num_folded_tr - 1) * (num_stacked_in - 1) * g_tp.spacing_poly_to_poly)

    return total_diff_w

def compute_gate_area(gate_type, num_inputs, w_pmos, w_nmos, h_gate):
    #TODO IMPORTANT this can't be done synbolically

    # TODO inverstiage Why is w_pmos and w_nmos 0
    # Traceback (most recent call last):
    #     File "/Users/dw/Documents/codesign/cacti/diff/second/main.py", line 44, in <module>
    #         mat = Mat(dyn_p)
    #             ^^^^^^^^^^
    #     File "/Users/dw/Documents/codesign/cacti/diff/second/mat.py", line 164, in __init__
    #         self.r_predec_blk1 = PredecBlk(num_dec_signals, self.row_dec, C_wire_predec_blk_out, R_wire_predec_blk_out, self.num_subarrays_per_mat, self.is_dram, True)
    #                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #     File "/Users/dw/Documents/codesign/cacti/diff/second/decoder.py", line 271, in __init__
    #         self.compute_area()
    #     File "/Users/dw/Documents/codesign/cacti/diff/second/decoder.py", line 396, in compute_area
    #         tot_area_L1_nand2 = compute_gate_area(NAND, 2, self.w_L1_nand2_p[0], self.w_L1_nand2_n[0], g_tp.cell_h_def)
    #                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #     File "/Users/dw/Documents/codesign/cacti/diff/second/component.py", line 39, in compute_gate_area
    #         if w_pmos <= 0.0 or w_nmos <= 0.0:
    #         ^^^^^^^^^^^^^
    #     File "/Users/dw/miniconda3/lib/python3.11/site-packages/sympy/core/relational.py", line 510, in __bool__
    #         raise TypeError("cannot determine truth value of Relational")

    # if w_pmos <= 0.0 or w_nmos <= 0.0:
    #     return 0.0

    if isinstance(w_pmos, (int, float)) and isinstance(w_nmos, (int, float)):
        if w_pmos <= 0.0 or w_nmos <= 0.0:
            return 0.0
    
    print("compute_gate_area CHECKPINT 0")
    # TODO RELATIONAL
    # simplify_w_pmos = sp.simplify(w_pmos)
    # simplify_w_nmos = sp.simplify(w_nmos)
    # if simplify_w_pmos.is_zero or simplify_w_pmos.is_negative or simplify_w_nmos.is_zero or simplify_w_nmos.is_negative:
    #     return 0.0
    
    print("compute_gate_area CHECKPINT 1")

    # print(f"w_pmos {w_pmos} and w_nmos {w_nmos}")

    h_tr_region = h_gate - 2 * g_tp.HPOWERRAIL  
    ratio_p_to_n = w_pmos / (w_pmos + w_nmos)

    # TODO IMPORTANT this can't be done synbolically
    # simplify_ratio_p_to_n = sp.simplify(ratio_p_to_n)
    # if ratio_p_to_n >= 1 or ratio_p_to_n <= 0:
    #     return 0.0
    # if sp.Or(ratio_p_to_n >= 1 or ratio_p_to_n <= 0):
    #     return 0.0
    # if simplify_ratio_p_to_n.is_integer and (simplify_ratio_p_to_n >= 1 or simplify_ratio_p_to_n <= 0):
    #     return 0.0
    if isinstance(ratio_p_to_n, (int, float)):
        if ratio_p_to_n <= 0 or ratio_p_to_n >= 1:
            return 0.0

    
    
    print("compute_gate_area CHECKPINT 2")
    

    w_folded_pmos = (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS) * ratio_p_to_n
    w_folded_nmos = (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS) * (1 - ratio_p_to_n)

    # TODO IMPORTANT this can't be done synbolically
    # assert w_folded_pmos > 0
    if(w_folded_pmos == 0):
        return 0
    if isinstance(w_folded_pmos, (int, float)):
        if w_folded_pmos <= 0:
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

    gate_w = symbolic_convex_max(total_ndiff_w, total_pdiff_w)

    # TODO Important can't do this symbolically
    # if w_folded_nmos > w_nmos:
    #     gate_h = (w_nmos + w_pmos + g_tp.MIN_GAP_BET_P_AND_N_DIFFS + 2 * g_tp.HPOWERRAIL)
    # else:
    #     gate_h = h_gate

    # TODO RECENTLY COMMENTED
    gate_h = sp.Piecewise(
        ((w_nmos + w_pmos + g_tp.MIN_GAP_BET_P_AND_N_DIFFS + 2 * g_tp.HPOWERRAIL), w_folded_nmos > w_nmos),
        (h_gate, True)  # TODO CHECK Else case
    )
    # gate_h = (w_nmos + w_pmos + g_tp.MIN_GAP_BET_P_AND_N_DIFFS + 2 * g_tp.HPOWERRAIL)

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
    # print(f'F is this {fopt}')
    num_gates = sp.log(F) / sp.log(fopt)
    if(F == 0):
        num_gates = 2
    # print(f'num_gates is this {num_gates}')
    # print("End")
    # print("")

    # TODO MOD Important
    # num_gates += (num_gates % 2)
    num_gates += (num_gates + 2)
    num_gates = symbolic_convex_max(num_gates, num_gates_min)

    f = sp.Pow(F, 1.0 / num_gates)
    num_gates = 4 # TODO IMPORTANT this can't be done synbolically
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
    w_n[i] = symbolic_convex_max(w_n[i], g_tp.min_w_nmos_)
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
    #     num_gates = symbolic_convex_max(num_gates, num_gates_min)
    #     f = sp.Pow(F, 1.0 / (num_gates - 1))
    #     i = num_gates - 1
    #     w_n[i] = max_w_nmos
    #     w_p[i] = p_to_n_sz_ratio * w_n[i]

    for i in range(num_gates - 2, 0, -1):
        #TODO important zoo shortcut
        w_item = w_n[i + 1] / f
        if w_item == sp.zoo:
            w_item = 0
        
        w_n[i] = symbolic_convex_max(w_item, g_tp.min_w_nmos_)
        w_p[i] = p_to_n_sz_ratio * w_n[i]

    assert num_gates <= MAX_NUMBER_GATES_STAGE
    return num_gates


def compute_tr_width_after_folding(input_width, threshold_folding_width):
        # TODO can't do relational
        # if input_width <= 0:
        #     return 0

        if isinstance(input_width, (int, float)):
            if input_width <= 0:
                return 0

        # print(f"input_widht {input_width}")
        # print(f"thresh {threshold_folding_width}")
        # num_folded_tr = sp.ceiling(input_width / threshold_folding_width)
        # spacing_poly_to_poly = g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact
        # width_poly = g_ip.F_sz_um
        # total_diff_width = (num_folded_tr * width_poly +
        #                     (num_folded_tr + 1) * spacing_poly_to_poly)
        # return total_diff_width
        
        result = sp.Piecewise(
            (0, input_width <= 0),  # Return 0 if input_width <= 0
            (sp.ceiling(input_width / threshold_folding_width) * g_ip.F_sz_um +
            (sp.ceiling(input_width / threshold_folding_width) + 1) * (g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact),
            True)  # TODO CHECKCalculate total_diff_width otherwise
        )

        return result