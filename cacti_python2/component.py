import math
import sympy as sp
from sympy import Basic
from .area import Area
from .cacti_interface import powerDef
from .const import *

# If you have your own definitions, or you can define them here:
# from .area import Area
# from .cacti_interface import PowerDef
# from .parameter import gate_C    # or something similar
# from .const import MAX_NUMBER_GATES_STAGE, fopt, ...

##############################################################################
# Symbolic convex max (approx. version of the standard max)
##############################################################################

def symbolic_convex_max(a, b):
    """
    An approximation to the max function that plays well with numeric/ symbolic solvers.
    """
    return 0.5 * (a + b + abs(a - b))

def is_symbolic(var):
    """
    Check if a variable is symbolic (Sympy expression).
    """
    return isinstance(var, Basic)

##############################################################################
# The main Component class, as in component.h
##############################################################################

class Component:
    def __init__(self):
        self.area       = Area()
        self.power      = powerDef()
        self.rt_power   = powerDef()
        self.delay      = 0
        self.cycle_time = 0

##############################################################################
# Functions that mirror component.cc, but in Python, passing g_ip/g_tp
##############################################################################

def compute_diffusion_width(g_ip, g_tp, num_stacked_in, num_folded_tr):
    w_poly = g_ip.F_sz_um
    spacing_poly_to_poly = g_tp.w_poly_contact + 2*g_tp.spacing_poly_to_contact

    total_diff_w = (2 * spacing_poly_to_poly
                    + num_stacked_in * w_poly
                    + (num_stacked_in - 1) * g_tp.spacing_poly_to_poly)

    # We handle piecewise: if num_folded_tr > 1 => add more. 
    # If symbolic, we pick the "likely" path that num_folded_tr>1:
    if (not is_symbolic(num_folded_tr) and (num_folded_tr > 1)):
        total_diff_w += ((num_folded_tr - 2)*2*spacing_poly_to_poly
                         + (num_folded_tr - 1)*num_stacked_in*w_poly
                         + (num_folded_tr - 1)*(num_stacked_in - 1)*g_tp.spacing_poly_to_poly)
    
    # ERROR PATH_APPROX
    # elif is_symbolic(num_folded_tr):
    #     # Choose path "most likely" => folded:
    #     total_diff_w += ((num_folded_tr - 2)*2*spacing_poly_to_poly
    #                      + (num_folded_tr - 1)*num_stacked_in*w_poly
    #                      + (num_folded_tr - 1)*(num_stacked_in - 1)*g_tp.spacing_poly_to_poly)

    return total_diff_w


def compute_gate_area(g_ip, g_tp,
                      gate_type,
                      num_inputs,
                      w_pmos,
                      w_nmos,
                      h_gate):
    # Return 0 if the widths are non-positive
    if (not is_symbolic(w_pmos) and w_pmos <= 0) or (not is_symbolic(w_nmos) and w_nmos <= 0):
        return 0

    gate = Area()
    h_tr_region = h_gate - 2*g_tp.HPOWERRAIL

    # ratio p to n
    if (is_symbolic(w_pmos) or is_symbolic(w_nmos)):
        ratio_p_to_n = w_pmos / (w_pmos + w_nmos)
        # CHECK PATH_APPROX
        # ratio_p_to_n = 0.5   # fallback if symbolic
    else:
        ratio_p_to_n = w_pmos / (w_pmos + w_nmos)
        # if ratio invalid, area=0
        if ratio_p_to_n >= 1 or ratio_p_to_n <= 0:
            return 0

    # folded widths
    w_folded_pmos = (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)*ratio_p_to_n
    w_folded_nmos = (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)*(1 - ratio_p_to_n)

    if not is_symbolic(w_folded_pmos):
        assert(w_folded_pmos > 0)

    # CHECK PATH_APPROX
    # number of folds
    # if not is_symbolic(w_pmos):
    #     num_folded_pmos = sp.ceiling(w_pmos / w_folded_pmos)
    # else:
    #     num_folded_pmos = 1
    # if not is_symbolic(w_nmos):
    #     num_folded_nmos = sp.ceiling(w_nmos / w_folded_nmos)
    # else:
    #     num_folded_nmos = 1

    num_folded_pmos = sp.ceiling(w_pmos / w_folded_pmos)
    num_folded_nmos = sp.ceiling(w_nmos / w_folded_nmos)

    # CHECK NAND
    # total diffusion widths based on gate_type:
    if gate_type == INV: # in ["INV", "inv"]:
        total_ndiff_w = compute_diffusion_width(g_ip, g_tp, 1, num_folded_nmos)
        total_pdiff_w = compute_diffusion_width(g_ip, g_tp, 1, num_folded_pmos)
    elif gate_type == NOR: # in ["NOR", "nor"]:
        total_ndiff_w = compute_diffusion_width(g_ip, g_tp, 1, num_inputs*num_folded_nmos)
        total_pdiff_w = compute_diffusion_width(g_ip, g_tp, num_inputs, num_folded_pmos)
    elif gate_type == NAND: # in ["NAND", "nand"]:
        total_ndiff_w = compute_diffusion_width(g_ip, g_tp, num_inputs, num_folded_nmos)
        total_pdiff_w = compute_diffusion_width(g_ip, g_tp, 1, num_inputs*num_folded_pmos)
    else:
        raise ValueError(f"Unknown gate type {gate_type} in compute_gate_area")

    # gate width = symbolic_convex_max
    gate.w = symbolic_convex_max(total_ndiff_w, total_pdiff_w)

    # ERROR PATH_APPROX
    # gate height
    # If we have a purely numeric scenario and w_folded_nmos > w_nmos => smaller gate
    # else => h_gate.
    # We'll pick "most likely" path if symbolic. 
    if (not is_symbolic(w_folded_nmos)
        and not is_symbolic(w_nmos)
        and (w_folded_nmos > w_nmos)):
        gate.h = (w_nmos + w_pmos
                  + g_tp.MIN_GAP_BET_P_AND_N_DIFFS
                  + 2*g_tp.HPOWERRAIL)
    else:
        gate.h = h_gate

    return gate.get_area()


def compute_tr_width_after_folding(g_ip, g_tp, input_width, threshold_folding_width):
    if (not is_symbolic(input_width) and input_width <= 0):
        return 0

    num_folded_tr = sp.ceiling(input_width / threshold_folding_width)
    spacing_poly_to_poly = g_tp.w_poly_contact + 2*g_tp.spacing_poly_to_contact
    width_poly = g_ip.F_sz_um

    total_diff_width = (num_folded_tr*width_poly
                        + (num_folded_tr + 1)*spacing_poly_to_poly)
    return total_diff_width


def height_sense_amplifier(g_ip, g_tp, pitch_sense_amp):
    h_pmos_tr = ( compute_tr_width_after_folding(g_ip, g_tp, g_tp.w_sense_p, pitch_sense_amp)*2
                  + compute_tr_width_after_folding(g_ip, g_tp, g_tp.w_iso, pitch_sense_amp)
                  + 2*g_tp.MIN_GAP_BET_SAME_TYPE_DIFFS )

    h_nmos_tr = ( compute_tr_width_after_folding(g_ip, g_tp, g_tp.w_sense_n, pitch_sense_amp)*2
                  + compute_tr_width_after_folding(g_ip, g_tp, g_tp.w_sense_en, pitch_sense_amp)
                  + 2*g_tp.MIN_GAP_BET_SAME_TYPE_DIFFS )

    return h_pmos_tr + h_nmos_tr + g_tp.MIN_GAP_BET_P_AND_N_DIFFS


def logical_effort(g_tp,
                   num_gates_min,
                   g,
                   F,
                   w_n,   # e.g. a list or array of stage widths for NMOS
                   w_p,   # e.g. a list or array of stage widths for PMOS
                   C_load,
                   p_to_n_sz_ratio,
                   is_dram_,
                   is_wl_tr_,
                   max_w_nmos):
    """
    Python version of:
      int Component::logical_effort(...)
    that handles the possibility that F is symbolic.

    We pick a single "likely" path: 
      - We do not do the re-calc if final stage w_n > max_w_nmos, 
        we just comment it out to remove piecewise branching.
    """
    # If F can be symbolic, let's do a safe approach:
    #  1) compute num_gates = floor(log(F)/log(fopt)).
    # But log(...) is tricky if F can be symbolic => use sp.log
    # We'll pick 4 stages as a "common path," ignoring adjustments.
    # ERROR MAIN_GATES
    num_gates = 4

    # fanout per stage
    # If F=0 => f->∞? We'll clamp or pick f=1 if F=0:
    # We assume F>1 typical scenario. If symbolic, we do sp.Pow(F, 1.0/num_gates).
    if is_symbolic(F):
        f = sp.Pow(F, 1.0/sp.Integer(num_gates))
    else:
        if F <= 0:
            # fallback
            f = 1
        else:
            f = (F)**(1.0/num_gates)

    i_final = num_gates - 1

    # compute final stage input size
    # clamp f=1 if symbolic or zero
    if (not is_symbolic(f)) and (f == 0):
        f = 1
    C_in = C_load / f

    # final stage nmos width
    # calls gate_C(...) with is_dram_, is_wl_tr_ etc. 
    # you must define or pass in your gate_C function:
    from .basic_circuit import gate_C

    wn_i = (1.0/(1.0+p_to_n_sz_ratio)) * C_in / gate_C(None, g_tp, 1, 0, is_dram_, False, is_wl_tr_)

    # use symbolic_convex_max for the clamp with min_w_nmos
    wn_i = symbolic_convex_max(wn_i, g_tp.min_w_nmos_)
    wp_i = p_to_n_sz_ratio*wn_i

    # store them:
    w_n[i_final] = wn_i
    w_p[i_final] = wp_i

    # We omit the piecewise logic for w_n[i] > max_w_nmos; just comment out:

    # for the earlier stages:
    for stage_idx in range(num_gates - 2, 0, -1):
        # f might be symbolic, so we do w_n[i+1]/f:
        wn_candidate = w_n[stage_idx + 1]/f
        # clamp:
        wn_candidate = symbolic_convex_max(wn_candidate, g_tp.min_w_nmos_)
        w_n[stage_idx] = wn_candidate
        w_p[stage_idx] = p_to_n_sz_ratio*wn_candidate

    # no check for num_gates <= MAX_NUMBER_GATES_STAGE in symbolic code
    return num_gates
