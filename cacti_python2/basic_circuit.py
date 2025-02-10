"""
Corresponds to basic_circuit.cc/basic_circuit.h

In C++:
  - The code references 'g_ip' (global InputParameter) and 'g_tp' (global TechnologyParameter).
  - We remove references to singletons and pass them as function parameters where needed.
"""

import math
import sympy
from math import ceil
from sympy import Basic
from const import *

# CONSTANTS
UNI_LEAK_STACK_FACTOR = 0.43

def symbolic_convex_max(a, b):
    """
    An approximation to the max function that plays well with numeric
    or symbolic solvers.
    """
    return 0.5 * (a + b + abs(a - b))

def is_pow2(val: int) -> bool:
    """Check if val is a power of two."""
    if val <= 0:
        return False
    if val == 1:
        return True
    return ((val & (val - 1)) == 0)


def _log2(num: int) -> int:
    """Return integer floor(log2(num))."""
    log2_val = 0
    temp = num
    while temp > 1:
        temp >>= 1
        log2_val += 1
    return log2_val


def logtwo(x: float) -> float:
    """Log base 2 for floating values."""
    if x <= 0:
        raise ValueError("log2(0) or negative is not defined.")
    return math.log(x, 2)


def is_equal(first: float, second: float) -> bool:
    """
    Compare two floating-point numbers for near-equality.
    (Used heavily in parameter checking.)
    """
    if abs(first - second) < 1e-12:
        return True
    relative_err = abs(first - second) / (abs(first) + 1e-15)
    return (relative_err < 1e-6)


def factorial(n: int, m: int = 1) -> int:
    """
    Returns factorial(n)/factorial(m)
    i.e. factorial from m+1 up to n.
    """
    if m > n:
        return 1
    fa = 1
    for i in range(m+1, n+1):
        fa *= i
    return fa


def combination(n: int, m: int) -> int:
    """
    Returns nCm = n! / (m!(n-m)!)
    Computed using partial factorial expansions.
    """
    # simple approach for small fanin
    # but for the typical usage in CACTI, n is small (e.g. <=16).
    return factorial(n) // (factorial(m) * factorial(n - m))


def powers(base: int, exp: int) -> int:
    """base^exp integer exponent."""
    return base**exp


############################################################
# The main transistor/wire utility functions
############################################################


def gate_C(g_ip, g_tp, width: float, wirelength: float,
           is_dram: bool = False,
           is_cell: bool = False,
           is_wl_tr: bool = False,
           is_sleep_tx: bool = False) -> float:
    """
    Returns the gate capacitance in Farads.
    Replaces gate_C() from the C++ version.
    
    In CACTI, the final expression is:
      (C_g_ideal + C_overlap + 3*C_fringe)*width + l_phy*Cpolywire
    """
    if is_dram and is_cell:
        dt = g_tp.dram_acc   # DRAM cell access transistor
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl    # DRAM wordline transistor
    elif (not is_dram) and is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif is_sleep_tx:
        dt = g_tp.sleep_tx   # Sleep transistor
    else:
        dt = g_tp.peri_global

    return (dt.C_g_ideal + dt.C_overlap + 3.0*dt.C_fringe) * width + dt.l_phy * Cpolywire


def gate_C_pass(g_ip, g_tp, width: float, wirelength: float,
                is_dram: bool = False,
                is_cell: bool = False,
                is_wl_tr: bool = False,
                is_sleep_tx: bool = False) -> float:
    """
    Returns the gate capacitance for a pass-transistor structure.
    Actually the same formula as gate_C() in modern CACTI versions.
    """
    return gate_C(g_ip, g_tp, width, wirelength,
                  is_dram, is_cell, is_wl_tr, is_sleep_tx)


def drain_C_(g_ip, g_tp,
             width: float,
             nchannel: int,
             stack: int,
             fold_parameter: int,   # If 0, interpret fold_dimension as threshold
             fold_dimension: float, # or if 1 interpret as cell height
             is_dram: bool = False,
             is_cell: bool = False,
             is_wl_tr: bool = False,
             is_sleep_tx: bool = False) -> float:
    """
    Returns the drain diffusion capacitance.

    - fold_parameter = 0  => fold_dimension is the maximum transistor width allowed before folding
    - fold_parameter = 1  => fold_dimension is the cell height we can use to fold the transistor

    For modern CACTI code, we typically pass fold_parameter=1 and fold_dimension=<cell_height>.
    """
    # pick device flavor
    if is_dram and is_cell:
        dt = g_tp.dram_acc   # DRAM cell access transistor
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl    # DRAM wordline transistor
    elif (not is_dram) and is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif is_sleep_tx:
        dt = g_tp.sleep_tx   # Sleep transistor
    else:
        dt = g_tp.peri_global

    c_junc_area     = dt.C_junc
    c_junc_sidewall = dt.C_junc_sidewall
    c_fringe        = 2.0 * dt.C_fringe
    c_overlap       = 2.0 * dt.C_overlap

    # Figure out how the transistor is folded
    if fold_parameter == 0:
        # interpret fold_dimension as nmos_folding_width_threshold
        w_fold_threshold = fold_dimension
    else:
        # interpret fold_dimension as the cell height we have
        # minus rails and spacing
        h_tr_region = fold_dimension - 2.0 * g_tp.HPOWERRAIL
        ratio_p_to_n = 2.0 / 3.0  # (2 p parts / (2 p + 1 n)) if we assume ratio?
        if nchannel == NCH:
            w_fold_threshold = (1.0 - ratio_p_to_n) * (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)
        else:
            w_fold_threshold = ratio_p_to_n * (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)

    if w_fold_threshold < 1e-15:
        w_fold_threshold = 1e-15  # avoid division by zero

    num_folded_tr = int(math.ceil(width / w_fold_threshold))

    # If no folding actually happens => just one transistor
    if num_folded_tr < 2:
        w_fold_threshold = width
        num_folded_tr = 1

    # The effective drain width in the layout
    # One transistor => we have just one drain region
    # If multiple folded => multiple drain contacts + spacing
    total_drain_w = (g_tp.w_poly_contact + 2*g_tp.spacing_poly_to_contact) \
                    + (stack - 1)*g_tp.spacing_poly_to_poly

    drain_h_for_sidewall = w_fold_threshold
    total_drain_height_for_cap_wrt_gate = w_fold_threshold + 2.0*w_fold_threshold*(stack - 1)
    drain_C_metal_connecting_folded_tr = 0.0

    if num_folded_tr > 1:
        # Additional contacts
        total_drain_w += (num_folded_tr - 2)*(g_tp.w_poly_contact + 2*g_tp.spacing_poly_to_contact) \
                         + (num_folded_tr - 1)*((stack - 1)*g_tp.spacing_poly_to_poly)

        # If we have an even number of folds, we might get two drains
        if (num_folded_tr % 2 == 0):
            drain_h_for_sidewall = 0.0

        total_drain_height_for_cap_wrt_gate *= num_folded_tr

        # The local interconnect that merges these folded segments
        drain_C_metal_connecting_folded_tr = g_tp.wire_local.C_per_um * total_drain_w

    # Now compute diffusion area, sidewall, fringe, overhead from local wire, etc.
    drain_C_area     = c_junc_area * total_drain_w * w_fold_threshold
    drain_C_sidewall = c_junc_sidewall * (drain_h_for_sidewall + 2.0*total_drain_w)
    drain_C_wrt_gate = (c_fringe + c_overlap) * total_drain_height_for_cap_wrt_gate

    return (drain_C_area + drain_C_sidewall + drain_C_wrt_gate + drain_C_metal_connecting_folded_tr)


def tr_R_on(g_tp, width: float, nchannel: int, stack: int,
            is_dram: bool = False,
            is_cell: bool = False,
            is_wl_tr: bool = False,
            is_sleep_tx: bool = False) -> float:
    """
    Return R_on (Ohms) of a transistor of given width.  Gains a factor of 'stack.'
    """
    if is_dram and is_cell:
        dt = g_tp.dram_acc
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    r_on = dt.R_nch_on if nchannel == NCH else dt.R_pch_on
    return stack * r_on / width


def R_to_w(g_tp, res: float, nchannel: int,
           is_dram: bool = False,
           is_cell: bool = False,
           is_wl_tr: bool = False,
           is_sleep_tx: bool = False) -> float:
    """
    Inverse of tr_R_on().  Return transistor width that yields a given R_on.
    """
    if is_dram and is_cell:
        dt = g_tp.dram_acc
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    r_on = dt.R_nch_on if (nchannel == NCH) else dt.R_pch_on
    width = r_on / res
    return width


def pmos_to_nmos_sz_ratio(g_tp,
                          is_dram: bool = False,
                          is_wl_tr: bool = False,
                          is_sleep_tx: bool = False) -> float:
    """
    Return the typical ratio p/n for device sizing.  E.g. ~2.0 in older processes.
    """
    if is_dram and is_wl_tr:
        return g_tp.dram_wl.n_to_p_eff_curr_drv_ratio
    elif is_sleep_tx:
        return g_tp.sleep_tx.n_to_p_eff_curr_drv_ratio
    else:
        return g_tp.peri_global.n_to_p_eff_curr_drv_ratio


def horowitz(in_rise_time: float,
             tf: float,
             vs1: float,
             vs2: float,
             rise: int) -> float:
    """
    The Horowitz delay model:  See "Timing Models for MOS Circuits" by M. Horowitz, 1984.
    inputramptime => in_rise_time
    tf => time constant of gate
    vs1, vs2 => threshold voltages
    rise => RISE or FALL
    """
    if in_rise_time == 0 and abs(vs1 - vs2) < 1e-12:
        # If there's no input slope, then just use a simple approximation
        # half-plane check
        if vs1 < 1.0:
            return tf * (-math.log(vs1))
        else:
            return tf * ( math.log(vs1))

    a = in_rise_time / tf
    if rise == RISE:
        b = 0.5
        # eqn from the cacti code
        tmp = (math.log(vs1))**2.0 + 2.0*a*b*(1.0 - vs1)
        if tmp < 0.0:
            tmp = 0.0
        delay = tf*math.sqrt(tmp) + tf*(math.log(vs1) - math.log(vs2))
    else:
        b = 0.4
        tmp = (math.log(1.0-vs1))**2.0 + 2.0*a*b*(vs1)
        if tmp < 0.0:
            tmp = 0.0
        delay = tf*math.sqrt(tmp) + tf*(math.log(1.0-vs1) - math.log(1.0-vs2))
    return delay


def cmos_Ileak(g_tp,
               nWidth: float, pWidth: float,
               is_dram: bool = False,
               is_cell: bool = False,
               is_wl_tr: bool = False,
               is_sleep_tx: bool = False) -> float:
    """
    Sum of the subthreshold leakage for an n/p pair.
    """
    if (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    return nWidth*dt.I_off_n + pWidth*dt.I_off_p


def combination_fanin(n: int, r: int) -> int:
    return combination(n, r)


def simplified_nmos_Isat(g_tp, nwidth: float,
                        is_dram: bool = False,
                        is_cell: bool = False,
                        is_wl_tr: bool = False,
                        is_sleep_tx: bool = False) -> float:
    """
    Return I_on for an NMOS of width = nwidth.
    """
    if (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    return nwidth * dt.I_on_n


def simplified_pmos_Isat(g_tp, pwidth: float,
                        is_dram: bool = False,
                        is_cell: bool = False,
                        is_wl_tr: bool = False,
                        is_sleep_tx: bool = False) -> float:
    """
    Return I_on for a PMOS of width = pwidth.
    """
    if (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    # pmos I_on is scaled by (n_to_p_eff_curr_drv_ratio)
    return pwidth * dt.I_on_n / dt.n_to_p_eff_curr_drv_ratio


def simplified_nmos_leakage(g_tp,
                            nwidth: float,
                            is_dram: bool = False,
                            is_cell: bool = False,
                            is_wl_tr: bool = False,
                            is_sleep_tx: bool = False) -> float:
    """
    Return the subthreshold leakage for an nmos of given width.
    """
    if (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    return nwidth * dt.I_off_n


def simplified_pmos_leakage(g_tp,
                            pwidth: float,
                            is_dram: bool = False,
                            is_cell: bool = False,
                            is_wl_tr: bool = False,
                            is_sleep_tx: bool = False) -> float:
    """
    Return the subthreshold leakage for a pmos of given width.
    """
    if (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    return pwidth * dt.I_off_p


def cmos_Ig_n(g_tp,
              nWidth: float,
              is_dram: bool = False,
              is_cell: bool = False,
              is_wl_tr: bool = False,
              is_sleep_tx: bool = False) -> float:
    """
    Gate leakage for an nmos of given width.
    """
    if (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    return nWidth * dt.I_g_on_n


def cmos_Ig_p(g_tp,
              pWidth: float,
              is_dram: bool = False,
              is_cell: bool = False,
              is_wl_tr: bool = False,
              is_sleep_tx: bool = False) -> float:
    """
    Gate leakage for a pmos of given width.
    """
    if (not is_dram) and is_cell:
        dt = g_tp.sram_cell
    elif is_dram and is_wl_tr:
        dt = g_tp.dram_wl
    elif is_sleep_tx:
        dt = g_tp.sleep_tx
    else:
        dt = g_tp.peri_global

    return pWidth * dt.I_g_on_p


def cmos_Isub_leakage(g_tp,
                      nWidth: float,
                      pWidth: float,
                      fanin: int,
                      gate_type: str,
                      is_dram: bool = False,
                      is_cell: bool = False,
                      is_wl_tr: bool = False,
                      is_sleep_tx: bool = False,
                      topology: str = "series") -> float:
    """
    Compute subthreshold leakage for a logic gate with 'fanin' inputs.
    gate_type = ["nmos", "pmos", "inv", "nand", "nor", "tri", "tg"].
    topology  = ["parallel", "series"] for half_net_topology in CACTI
    """
    # usage in cacti: gate_type=inv, fanin=1, ...
    if fanin < 1:
        return 0.0

    n_leak = simplified_nmos_leakage(g_tp, nWidth, is_dram, is_cell, is_wl_tr, is_sleep_tx)
    p_leak = simplified_pmos_leakage(g_tp, pWidth, is_dram, is_cell, is_wl_tr, is_sleep_tx)
    Isub   = 0.0
    num_states = float(2**fanin)

    def leak_stack_factor(k: int) -> float:
        return (UNI_LEAK_STACK_FACTOR ** (k - 1))

    # CHECK NAND
    if gate_type == nmos or gate_type == "nmos":
        if fanin == 1:
            Isub = n_leak / num_states
        else:
            if topology == "parallel":
                # all off => 1 / num_states
                Isub = (n_leak * fanin) / num_states
            else:
                # series
                for off_cnt in range(1, fanin+1):
                    # combination => choose off trans count
                    Isub += n_leak * leak_stack_factor(off_cnt) * combination_fanin(fanin, off_cnt)
                Isub /= num_states

    elif gate_type == pmos or gate_type == "pmos":
        if fanin == 1:
            Isub = p_leak / num_states
        else:
            if topology == "parallel":
                Isub = (p_leak * fanin) / num_states
            else:
                for off_cnt in range(1, fanin+1):
                    Isub += p_leak * leak_stack_factor(off_cnt) * combination_fanin(fanin, off_cnt)
                Isub /= num_states

    elif gate_type == inv or gate_type == "inv":
        Isub = (n_leak + p_leak) / 2.0

    elif gate_type == nand or gate_type == "nand":
        # pull up => pmos in parallel
        Isub += fanin * p_leak
        # pull down => nmos in series
        for off_cnt in range(1, fanin+1):
            Isub += n_leak * leak_stack_factor(off_cnt) * combination_fanin(fanin, off_cnt)
        Isub /= num_states

    elif gate_type == nor or gate_type == "nor":
        # pull up => pmos in series
        for off_cnt in range(1, fanin+1):
            Isub += p_leak * leak_stack_factor(off_cnt) * combination_fanin(fanin, off_cnt)
        # pull down => nmos in parallel
        Isub += fanin * n_leak
        Isub /= num_states

    elif gate_type == tri or gate_type == "tri":
        # tri-state
        # approximate
        Isub = (n_leak + p_leak)*0.5
        Isub += n_leak*UNI_LEAK_STACK_FACTOR
        Isub *= 0.5

    elif gate_type == tg or gate_type == "tg":
        # pass gate
        Isub = (n_leak + p_leak)*0.5

    else:
        # invalid gate
        pass

    return Isub


def cmos_Ig_leakage(g_tp,
                    nWidth: float,
                    pWidth: float,
                    fanin: int,
                    gate_type: str,
                    is_dram: bool = False,
                    is_cell: bool = False,
                    is_wl_tr: bool = False,
                    is_sleep_tx: bool = False,
                    topology: str = "series") -> float:
    """
    Gate leakage for a logic gate with 'fanin' inputs.
    """
    if fanin < 1:
        return 0.0

    n_leak = cmos_Ig_n(g_tp, nWidth, is_dram, is_cell, is_wl_tr, is_sleep_tx)
    p_leak = cmos_Ig_p(g_tp, pWidth, is_dram, is_cell, is_wl_tr, is_sleep_tx)

    Ig_on  = 0.0
    num_states = float(2**fanin)

    if gate_type == nmos or gate_type == "nmos":
        if fanin == 1:
            Ig_on = n_leak / num_states
        else:
            if topology == "parallel":
                # each input can be on => sum up
                # for typical usage, though, we do an approximate method
                for on_cnt in range(1, fanin+1):
                    Ig_on += n_leak * combination_fanin(fanin, on_cnt)*on_cnt
            else:
                # series
                Ig_on += n_leak * fanin
                for on_cnt in range(1, fanin):
                    Ig_on += n_leak * combination_fanin(fanin, on_cnt)*on_cnt*0.5
                Ig_on /= num_states

    elif gate_type == pmos or gate_type == "pmos":
        if fanin == 1:
            Ig_on = p_leak / num_states
        else:
            if topology == "parallel":
                for on_cnt in range(1, fanin+1):
                    Ig_on += p_leak * combination_fanin(fanin, on_cnt)*on_cnt
            else:
                Ig_on += p_leak * fanin
                for on_cnt in range(1, fanin):
                    Ig_on += p_leak * combination_fanin(fanin, on_cnt)*on_cnt*0.5
                Ig_on /= num_states

    elif gate_type == inv or gate_type == "inv":
        Ig_on = (n_leak + p_leak)*0.5

    elif gate_type == nand or gate_type == "nand":
        # pull up => pmos are in parallel
        for on_cnt in range(1, fanin+1):
            Ig_on += p_leak * combination_fanin(fanin, on_cnt)*on_cnt
        # pull down => nmos in series
        Ig_on += n_leak * fanin
        for on_cnt in range(1, fanin):
            Ig_on += n_leak * combination_fanin(fanin, on_cnt)*on_cnt*0.5
        Ig_on /= num_states

    elif gate_type == nor or gate_type == "nor":
        # pull up => pmos in series
        Ig_on += p_leak * fanin
        for on_cnt in range(1, fanin):
            Ig_on += p_leak * combination_fanin(fanin, on_cnt)*on_cnt*0.5
        # pull down => nmos in parallel
        for on_cnt in range(1, fanin+1):
            Ig_on += n_leak * combination_fanin(fanin, on_cnt)*on_cnt
        Ig_on /= num_states

    elif gate_type == tri or gate_type == "tri":
        Ig_on += (2*n_leak + 2*p_leak)*0.5
        Ig_on += (n_leak + p_leak)*0.5
        Ig_on *= 0.5

    elif gate_type == tg or gate_type == "tg":
        Ig_on = (n_leak + p_leak)*0.5

    return Ig_on


def shortcircuit_simple(vt: float,
                        velocity_index: float,
                        c_in: float,
                        c_out: float,
                        w_nmos: float,
                        w_pmos: float,
                        i_on_n: float,
                        i_on_p: float,
                        i_on_n_in: float,
                        i_on_p_in: float,
                        vdd: float) -> float:
    """
    A simplified short-circuit energy model for an inverter switching event.
    """
    fo_n = i_on_n / i_on_n_in
    fo_p = i_on_p / i_on_p_in
    fanout = c_out / c_in if c_in > 1e-15 else 1.0
    beta_ratio = i_on_p / (i_on_n + 1e-15)
    vt_to_vdd_ratio = vt / (vdd + 1e-15)

    # simplified version
    tmp_factor = pow((vdd - vt) - vt_to_vdd_ratio, 3.0) / (pow(velocity_index, 2.0)* pow(2.0, 3.0*vt_to_vdd_ratio*vt_to_vdd_ratio)+1e-15)
    p_short_circuit_dis_low  = (10.0/3.0) * tmp_factor * c_in * vdd*vdd * fo_p*fo_p/(fanout+1e-15)/(beta_ratio+1e-15)
    p_short_circuit_cha_low  = (10.0/3.0) * tmp_factor * c_in * vdd*vdd * fo_n*fo_n/(fanout+1e-15)*(beta_ratio+1e-15)

    return 0.5*(p_short_circuit_dis_low + p_short_circuit_cha_low)


def shortcircuit(vt: float,
                 velocity_index: float,
                 c_in: float,
                 c_out: float,
                 w_nmos: float,
                 w_pmos: float,
                 i_on_n: float,
                 i_on_p: float,
                 i_on_n_in: float,
                 i_on_p_in: float,
                 vdd: float) -> float:
    """
    A more complicated short-circuit model for advanced usage.
    """
    fo_p   = i_on_p / (i_on_p_in+1e-15)
    beta_ratio = i_on_p/(i_on_n+1e-15)
    # Some partial modeling from older code, no perfect match
    # Usually shortcircuit_simple is enough in CACTI.
    return shortcircuit_simple(vt, velocity_index, c_in, c_out, w_nmos, w_pmos,
                               i_on_n, i_on_p, i_on_n_in, i_on_p_in, vdd)


############################################################
# Wire calculations for local, semi-global, global wires
############################################################

def wire_resistance(resistivity: float,
                    wire_width: float,
                    wire_thickness: float,
                    barrier_thickness: float,
                    dishing_thickness: float,
                    alpha_scatter: float) -> float:
    """
    Return wire R per micron (ohms/micron).
    """
    # cross sectional area ~ (wire_thickness - barrier - dishing)*(wire_width - 2*barrier)
    area = symbolic_convex_max(1e-15, (wire_thickness - barrier_thickness - dishing_thickness)*
                         (wire_width - 2.0*barrier_thickness))
    return alpha_scatter * resistivity / area


def wire_capacitance(wire_width: float,
                     wire_thickness: float,
                     wire_spacing: float,
                     ild_thickness: float,
                     miller_value: float,
                     horiz_dielectric_constant: float,
                     vert_dielectric_constant: float,
                     fringe_cap: float) -> float:
    """
    Return wire C per micron (F/micron).
    """
    # vertical parallel plate
    vertical_cap = 2.0 * PERMITTIVITY_FREE_SPACE * vert_dielectric_constant * wire_width / ild_thickness
    # sidewall parallel plate
    sidewall_cap = 2.0 * PERMITTIVITY_FREE_SPACE * miller_value * horiz_dielectric_constant * wire_thickness / wire_spacing
    return (vertical_cap + sidewall_cap + fringe_cap)


def tsv_resistance(resistivity: float,
                   tsv_len: float,
                   tsv_diam: float,
                   tsv_contact_resistance: float) -> float:
    """
    Resistivity-based TSV R = resistivity*length / area + contact
    """
    area = math.pi*(0.5*tsv_diam)*(0.5*tsv_diam)
    if area < 1e-30:
        return 1e30
    return resistivity * tsv_len / area + tsv_contact_resistance


def tsv_capacitance(tsv_len: float,
                    tsv_diam: float,
                    tsv_pitch: float,
                    tsv_dielec_thickness: float,
                    tsv_liner_dielectric_constant: float,
                    tsv_depletion_width: float) -> float:
    """
    Approx. TSV self + coupling cap.
    """
    # typical approach from CACTI 3DD references
    # laterally
    e_si = PERMITTIVITY_FREE_SPACE*11.9
    # 1. Liner cap
    radius = 0.5 * tsv_diam
    if radius < 1e-15:
        return 0.0

    # mechanical disclaimers
    # Approx formula:
    #   C_liner = 2*pi*eps*(length)/ln( (R+thickness)/R )
    #   similarly for depletion
    import math
    # clamp for log domain
    if tsv_dielec_thickness < 1e-15:
        tsv_dielec_thickness = 1e-15

    liner_cap = 2.0*math.pi*PERMITTIVITY_FREE_SPACE*tsv_liner_dielectric_constant*tsv_len \
                / math.log(1.0 + tsv_dielec_thickness/radius)
    depletion_cap = 2.0*math.pi*e_si*tsv_len \
                    / math.log(1.0 + tsv_depletion_width/(tsv_dielec_thickness+radius))

    if (liner_cap<1e-30) or (depletion_cap<1e-30):
        return 0.0

    self_cap = 1.0/(1.0/liner_cap + 1.0/depletion_cap)

    # Coupling with neighbor
    # For simplicity:
    lateral_coupling_constant = 4.1
    diagonal_coupling_constant= 5.3

    if (tsv_pitch - tsv_diam)<1e-15:
        lateral_coupling_cap = 0.0
        diagonal_coupling_cap= 0.0
    else:
        partial_factor = 0.4 * (0.225*math.log( symbolic_convex_max(1.0, 0.97*tsv_len/tsv_diam ))+0.53)* e_si
        lateral_coupling_cap  = partial_factor/(tsv_pitch - tsv_diam)* math.pi*tsv_diam*tsv_len
        diagonal_coupling_cap = partial_factor/(1.414*tsv_pitch - tsv_diam)* math.pi*tsv_diam*tsv_len

    total_cap = self_cap + lateral_coupling_constant*lateral_coupling_cap \
                         + diagonal_coupling_constant*diagonal_coupling_cap
    return total_cap


def tsv_area(tsv_pitch: float) -> float:
    """
    The minimum area a TSV takes up in the layout is pitch^2.
    """
    return tsv_pitch*tsv_pitch
