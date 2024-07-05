import sympy as sp
import math
import os
from const import *
import re
from get_dat import scan_dat


#Set up wrappers around
#Read cache.cfg


# lop, low oper power
# parameterize many, convert 
# hardware_symbols
# verify delay first, then energy
# param cfg
# compare the access times with the actual run and symbolic

 #check
'''
DAT PARAMS:
C_g_ideal:
C_fringe:
C_junc_sw
l_phy:
n2p_drv_rt:
nmos_effective_resistance_multiplier
Vdd
I_on_n
wire_c_per_micron

CFG PARAMS:
F_sz_um: g_tp.min_w_nmos_ uses g_ip->F_sz_um, which is just -technology of cfg file
'''

NCH = 0
PCH = 1
RISE = 1
is_dram_, is_dram = False, False
VTHFA1 = 0.452
VTHFA2 = 0.304
VTHFA3 = 0.420
VTHFA4 = 0.413
VTHFA5 = 0.405
VTHFA6 = 0.452
VSINV = 0.452
VTHCOMPINV = 0.437
VTHMUXNAND = 0.548  # TODO: this constant must be revisited
VTHEVALINV = 0.452
VTHSENSEEXTDRV = 0.438
FALL = 0

'''
cell row and subarray row added but can be decomposed further
'''
C_g_ideal, C_fringe, C_junc, C_junc_sw, l_phy, F_sz_um, \
n2p_drv_rt, nmos_effective_resistance_multiplier, Vdd, \
I_on_n, wire_c_per_micron, wire_length, wire_delay, vpp, \
cell_h, cell_w, cam_cell_h, cam_cell_w, \
subarray_num_rows, subarray_C_bl, \
RWP, ERP, EWP, SCHP, \
wire_local_R_per_um, \
dram_cell_Vdd, dram_cell_C, dram_cell_I_on, V_b_sense, \
dram_Vbitpre, dram_cell_a_w, \
sram_Vbitpre, sram_cell_Vth, sram_cell_Vdd, sram_cell_nmos_w, sram_cell_a_w, \
I_off_p, gm_sense_amp_latch, \
Ndsam_lev_1, Ndsam_lev_2, \
subarray_out_wire_repeater_size, subarray_out_wire_wire_length, subarray_out_wire_repeater_spacing, \
subarray_out_wire_delay, \
tag_assoc, tagbits, \
dram_acc_Vth, peri_global_Vth  = sp.symbols('''
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
    vpp
    cell_h
    cell_w
    cam_cell_h
    cam_cell_w  
    subarray_num_rows
    subarray_C_bl
    RWP
    ERP
    EWP        
    SCHP        
    wire_local_R_per_um   
    dram_cell_Vdd  
    dram_cell_C          
    dram_cell_I_on 
    V_b_sense         
    dram_Vbitpre 
    dram_cell_a_w
    sram_Vbitpre 
    sram_cell_Vth
    sram_cell_Vdd
    sram_cell_nmos_w
    sram_cell_a_w            
    I_off_p
    gm_sense_amp_latch
    Ndsam_lev_1
    Ndsam_lev_2
    subarray_out_wire_repeater_size
    subarray_out_wire_wire_length
    subarray_out_wire_repeater_spacing 
    subarray_out_wire_delay
    tag_assoc
    tagbits
    dram_acc_Vth
    peri_global_Vth
''')

g_tp = {
    "C_g_ideal": C_g_ideal,
    "C_fringe": C_fringe,
    "C_junc": C_junc,
    "C_junc_sw": C_junc_sw,
    "l_phy": l_phy,
    "n2p_drv_rt": n2p_drv_rt,
    "nmos_effective_resistance_multiplier": nmos_effective_resistance_multiplier,
    "Vdd": Vdd,
    "I_on_n": I_on_n,
    "wire_c_per_micron": wire_c_per_micron,
    "wire_length": wire_length,
    "wire_delay": wire_delay,

    "F_sz_um": 0.090 * 1000
}

#This uses mat.cc to calcuate delays, then uca.cc to accumulate delays
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

  bitline_delay = compute_bitline_delay(g_tp, inrisetime) # check if these inrisetime should be 0
  sa_delay = compute_sa_delay(g_tp, inrisetime)
  subarray_out_drv_delay = compute_subarray_out_drv(g_tp, inrisetime)
  # sub_array_out_wire_delay = 0
  subarray_out_drv_htree_delay = subarray_out_drv_delay + subarray_out_wire_delay
  htree_out_data_delay = 0
  comparator_delay = compute_comparator_delay(g_tp, inrisetime)
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
    
'''
Find out:
where subarray.num_rows and C_bl are instantiated -> subarray.cc -> dp.num_r_subarray -> parameter.cc 1929, uses drain and gateC
cam_cell.h and cell.h instantiaed 
V_b_sense -> parameter.cc

Vbitpre

sram_Vdd -> infile low vs infile high?
wire_local.R_per_um

dram_cell_a_w
sram_cell_a_w
sram_cell_nmos_w -> this is F_sz_um in parameter.cc

g_tp.dram_acc.Vth
g_tp.sram_acc.Vdd
g_tp.dram_acc.Vth
'''
camFlag = False
deg_bl_muxing = 0 # CHECK ncdm in paramter.cc
is_3d_mem = False
def compute_bitline_delay(g_tp, inrisetime):
    V_b_pre = 0.0
    v_th_mem_cell = 0.0
    V_wl = 0.0
    tstep = 0.0
    dynRdEnergy = 0.0
    dynWriteEnergy = 0.0
    blfloating_c = 0.0
    R_cell_pull_down = 0.0
    R_cell_acc = 0.0
    r_dev = 0.0
    # deg_senseamp_muxing = dp.Ndsam_lev_1 * dp.Ndsam_lev_2

    R_b_metal = cam_cell_h if camFlag else cell_h * wire_local_R_per_um
    R_bl = subarray_num_rows * R_b_metal
    C_bl = subarray_C_bl

    # leak_power_cc_inverters_sram_cell = 0
    # gate_leak_power_cc_inverters_sram_cell = 0
    # leak_power_acc_tr_RW_or_WR_port_sram_cell = 0
    # leak_power_RD_port_sram_cell = 0
    # gate_leak_power_RD_port_sram_cell = 0

    if is_dram:
        V_b_pre = dram_Vbitpre
        v_th_mem_cell = dram_acc_Vth
        V_wl = vpp
        R_cell_acc = tr_R_on(g_tp, dram_cell_a_w, 'NCH', 1, True, True)
        r_dev = dram_cell_Vdd / dram_cell_I_on + R_bl / 2
    else:
        V_b_pre = sram_Vbitpre
        v_th_mem_cell = sram_cell_Vth
        V_wl = sram_cell_Vdd
        R_cell_pull_down = tr_R_on(g_tp, sram_cell_nmos_w, 'NCH', 1, False, True)
        R_cell_acc = tr_R_on(g_tp, sram_cell_a_w, 'NCH', 1, False, True)

        # Iport = cmos_Isub_leakage(g_tp.sram.cell_a_w, 0, 1, 'nmos', False, True)
        # Iport_erp = cmos_Isub_leakage(g_tp.sram.cell_a_w, 0, 2, 'nmos', False, True)
        # Icell = cmos_Isub_leakage(g_tp.sram.cell_nmos_w, g_tp.sram.cell_pmos_w, 1, 'inv', False, True) * 2

        # leak_power_cc_inverters_sram_cell = Icell * (g_tp.sram_cell.Vcc_min if g_ip.array_power_gated else g_tp.sram_cell.Vdd)
        # leak_power_acc_tr_RW_or_WR_port_sram_cell = Iport * (g_tp.sram.Vbitfloating if g_ip.bitline_floating else g_tp.sram_cell.Vdd)
        # leak_power_RD_port_sram_cell = Iport_erp * (g_tp.sram.Vbitfloating if g_ip.bitline_floating else g_tp.sram_cell.Vdd)

        # Ig_port_erp = cmos_Ig_leakage(g_tp.sram.cell_a_w, 0, 1, 'nmos', False, True)
        # Ig_cell = cmos_Ig_leakage(g_tp.sram.cell_nmos_w, g_tp.sram.cell_pmos_w, 1, 'inv', False, True)

        # gate_leak_power_cc_inverters_sram_cell = Ig_cell * g_tp.sram_cell.Vdd
        # gate_leak_power_RD_port_sram_cell = Ig_port_erp * g_tp.sram_cell.Vdd
    min_w_nmos_ = 3 * g_tp["F_sz_um"] / 2
    w_nmos_b_mux = 6 * min_w_nmos_
    w_iso = 12.5 * g_tp["F_sz_um"]
    w_sense_n = 3.75 * g_tp["F_sz_um"]
    w_sense_p = 7.5 * g_tp["F_sz_um"]
    w_nmos_sa_mux = 6 * min_w_nmos_

    C_drain_bit_mux = drain_C_(g_tp, w_nmos_b_mux, 'NCH', 1, 0, cam_cell_w if camFlag else cell_w / (2 * (RWP + ERP + SCHP)), is_dram)
    R_bit_mux = tr_R_on(g_tp, w_nmos_b_mux, 'NCH', 1, is_dram)
    C_drain_sense_amp_iso = drain_C_(g_tp, w_iso, 'PCH', 1, 0, cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram)
    R_sense_amp_iso = tr_R_on(g_tp, w_iso, 'PCH', 1, is_dram)
    C_sense_amp_latch = gate_C(g_tp, w_sense_p + w_sense_n, 0, is_dram) + drain_C_(g_tp, w_sense_n, 'NCH', 1, 0, cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram) + drain_C_(g_tp, w_sense_p, 'PCH', 1, 0, cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram)
    C_drain_sense_amp_mux = drain_C_(g_tp, w_nmos_sa_mux, 'NCH', 1, 0, cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram)

    if is_dram:
        fraction = V_b_sense / ((dram_cell_Vdd / 2) * dram_cell_C / (dram_cell_C + C_bl))
        tstep = fraction * r_dev * (1 if is_3d_mem == 1 else 2.3) * (dram_cell_C * (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux)) / (dram_cell_C + (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux))
        # delay_writeback = tstep
        # dynRdEnergy += (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_Vdd
        # dynWriteEnergy += (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch) * (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_Vdd * num_act_mats_hor_dir * 100
        # per_bitline_read_energy = (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_Vdd
    else:
        if deg_bl_muxing > 1:
            tau = (R_cell_pull_down + R_cell_acc) * (C_bl + 2 * C_drain_bit_mux + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) + R_bl * (C_bl / 2 + 2 * C_drain_bit_mux + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) + R_bit_mux * (C_drain_bit_mux + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) + R_sense_amp_iso * (C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux)
            # dynRdEnergy += (C_bl + 2 * C_drain_bit_mux) * 2 * dp.V_b_sense * g_tp.sram_cell.Vdd
            # blfloating_c += (C_bl + 2 * C_drain_bit_mux) * 2
            # dynRdEnergy += (2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * 2 * dp.V_b_sense * g_tp.sram_cell.Vdd / deg_bl_muxing
            # blfloating_c += (2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * 2
            # dynWriteEnergy += (1.0 / deg_bl_muxing / deg_senseamp_muxing) * num_act_mats_hor_dir * (C_bl + 2 * C_drain_bit_mux) * g_tp.sram_cell.Vdd * g_tp.sram_cell.Vdd * 2
        else:
            tau = (R_cell_pull_down + R_cell_acc) * (C_bl + C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) + R_bl * C_bl / 2 + R_sense_amp_iso * (C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux)
            # dynRdEnergy += (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * 2 * dp.V_b_sense * g_tp.sram_cell.Vdd
            # blfloating_c += (C_bl + 2 * C_drain_sense_amp_iso + C_sense_amp_latch + C_drain_sense_amp_mux) * 2
            # dynWriteEnergy += (1.0 / deg_bl_muxing / deg_senseamp_muxing) * num_act_mats_hor_dir * C_bl * g_tp.sram_cell.Vdd * g_tp.sram_cell.Vdd * 2

        tstep = tau * sp.log(V_b_pre / (V_b_pre - V_b_sense))

        # power_bitline.readOp.leakage = leak_power_cc_inverters_sram_cell + leak_power_acc_tr_RW_or_WR_port_sram_cell + leak_power_acc_tr_RW_or_WR_port_sram_cell * (RWP + EWP - 1) + leak_power_RD_port_sram_cell * ERP
        # power_bitline.readOp.gate_leakage = gate_leak_power_cc_inverters_sram_cell + gate_leak_power_RD_port_sram_cell * ERP

    m = V_wl / inrisetime

    #CHECK
    delay_bitline = sp.sqrt(2 * tstep * (V_wl - v_th_mem_cell) / m)
    # if tstep <= (0.5 * (V_wl - v_th_mem_cell) / m):
    #     delay_bitline = sp.sqrt(2 * tstep * (V_wl - v_th_mem_cell) / m)
    # else:
    #     delay_bitline = tstep + (V_wl - v_th_mem_cell) / (2 * m)

    return delay_bitline

import math

def compute_sa_delay(g_tp, inrisetime):
    min_w_nmos_ = 3 * g_tp["F_sz_um"] / 2
    w_nmos_b_mux = 6 * min_w_nmos_
    w_iso = 12.5 * g_tp["F_sz_um"]
    w_sense_n = 3.75 * g_tp["F_sz_um"]
    w_sense_p = 7.5 * g_tp["F_sz_um"]
    w_nmos_sa_mux = 6 * min_w_nmos_

    # Bitline circuitry leakage.
    # Iiso = simplified_pmos_leakage(g_tp.w_iso, is_dram)
    # IsenseEn = simplified_nmos_leakage(g_tp.w_sense_en, is_dram)
    # IsenseN = simplified_nmos_leakage(g_tp.w_sense_n, is_dram)
    # IsenseP = simplified_pmos_leakage(g_tp.w_sense_p, is_dram)

    # lkgIdlePh = IsenseEn
    # lkgReadPh = Iiso + IsenseN + IsenseP
    # lkgIdle = lkgIdlePh
    # leak_power_sense_amps_closed_page_state = lkgIdlePh * g_tp.peri_global.Vdd
    # leak_power_sense_amps_open_page_state = lkgReadPh * g_tp.peri_global.Vdd

    # Sense amplifier load.
    C_ld = (gate_C(g_tp, w_sense_p + w_sense_n, 0, is_dram) +
            drain_C_(g_tp, w_sense_n, 'NCH', 1, 0, cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram) +
            drain_C_(g_tp, w_sense_p, 'PCH', 1, 0, cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram) +
            drain_C_(g_tp, w_iso, 'PCH', 1, 0, cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram) +
            drain_C_(g_tp, w_nmos_sa_mux, 'NCH', 1, 0, cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram))
    
    tau = C_ld / gm_sense_amp_latch
    #delay_sa = tau * math.log(g_tp.peri_global.Vdd / dp.V_b_sense)
    delay_sa = tau * sp.log(Vdd / V_b_sense)
    # power_sa.readOp.dynamic = C_ld * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
    # power_sa.readOp.leakage = lkgIdle * g_tp.peri_global.Vdd

    # outrisetime = 0
    return delay_sa

'''
Find Ndsam_lev_1, Ndsam_lev_2
pmos_to_nmos_sz_ratio(is_dram)
subarray_out_wire.repeater_size * (subarray_out_wire.wire_length / subarray_out_wire.repeater_spacing

'''
def compute_subarray_out_drv(g_tp, inrisetime):
    # Initialization of variables
   #p_to_n_sz_r = pmos_to_nmos_sz_ratio(is_dram)
    p_to_n_sz_r = g_tp["n2p_drv_rt"]
    min_w_nmos = 3 * g_tp["F_sz_um"] / 2
    w_nmos_sa_mux = 6 * min_w_nmos
    cell_h_def = 50 * g_tp["F_sz_um"]

    # Delay through pass-transistor of first level of sense-amp mux to input of inverter-buffer
    rd = tr_R_on(g_tp, w_nmos_sa_mux, NCH, 1, is_dram)
    C_ld = (Ndsam_lev_1 * drain_C_(g_tp, w_nmos_sa_mux, NCH, 1, 0, camFlag * cam_cell_w if camFlag else cell_w * deg_bl_muxing / (RWP + ERP + SCHP), is_dram) +
            gate_C(g_tp, min_w_nmos + p_to_n_sz_r * min_w_nmos, 0.0, is_dram))
    tf = rd * C_ld
    this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
    # global delay_subarray_out_drv
    delay_subarray_out_drv = 0
    delay_subarray_out_drv += this_delay
    inrisetime = this_delay / (1.0 - 0.5)
    global power_subarray_out_drv
    # power_subarray_out_drv.readOp.dynamic += C_ld * 0.5 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
    # power_subarray_out_drv.readOp.leakage += 0  # Assuming leakage of the pass transistor is 0 for now
    # power_subarray_out_drv.readOp.gate_leakage += cmos_Ig_leakage(g_tp.w_nmos_sa_mux, 0, 1, nmos) * g_tp.peri_global.Vdd

    # Delay through inverter-buffer to second level of sense-amp mux
    rd = tr_R_on(g_tp, min_w_nmos, NCH, 1, is_dram)
    C_ld = (drain_C_(g_tp, min_w_nmos, NCH, 1, 1, cell_h_def, is_dram) +
            drain_C_(g_tp, p_to_n_sz_r * min_w_nmos, PCH, 1, 1, cell_h_def, is_dram) +
            gate_C(g_tp, min_w_nmos + p_to_n_sz_r * min_w_nmos, 0.0, is_dram))
    tf = rd * C_ld
    this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
    delay_subarray_out_drv += this_delay
    inrisetime = this_delay / (1.0 - 0.5)
    # power_subarray_out_drv.readOp.dynamic += C_ld * 0.5 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
    # power_subarray_out_drv.readOp.leakage += cmos_Isub_leakage(g_tp.min_w_nmos, p_to_n_sz_r * g_tp.min_w_nmos, 1, inv, is_dram) * g_tp.peri_global.Vdd
    # power_subarray_out_drv.readOp.gate_leakage += cmos_Ig_leakage(g_tp.min_w_nmos, p_to_n_sz_r * g_tp.min_w_nmos, 1, inv) * g_tp.peri_global.Vdd

    # Delay of signal through pass-transistor to input of subarray output driver
    rd = tr_R_on(g_tp, w_nmos_sa_mux, NCH, 1, is_dram)
    C_ld = (Ndsam_lev_2 * drain_C_(g_tp, w_nmos_sa_mux, NCH, 1, 0, camFlag * cam_cell_w if camFlag else cell_w * deg_bl_muxing * Ndsam_lev_1 / (RWP + ERP + SCHP), is_dram) +
            gate_C(g_tp, subarray_out_wire_repeater_size * (subarray_out_wire_wire_length / subarray_out_wire_repeater_spacing) * min_w_nmos * (1 + p_to_n_sz_r), 0.0, is_dram))
    tf = rd * C_ld
    this_delay = horowitz(inrisetime, tf, 0.5, 0.5, RISE)
    delay_subarray_out_drv += this_delay
    inrisetime = this_delay / (1.0 - 0.5)
    # power_subarray_out_drv.readOp.dynamic += C_ld * 0.5 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd
    # power_subarray_out_drv.readOp.leakage += 0  # Assuming leakage of the pass transistor is 0 for now
    # power_subarray_out_drv.readOp.gate_leakage += cmos_Ig_leakage(g_tp.w_nmos_sa_mux, 0, 1, nmos) * g_tp.peri_global.Vdd

    return delay_subarray_out_drv

'''
Check 
peri_global_Vdd = g_tp["Vdd"]
peri_global_Vth = g_tp["Vth"]
'''
def compute_comparator_delay(g_tp, inrisetime):

    w_comp_inv_p1 = 12.5 * g_tp["F_sz_um"]
    w_comp_inv_n1 = 7.5 * g_tp["F_sz_um"]
    w_comp_inv_p2 = 25 * g_tp["F_sz_um"]
    w_comp_inv_n2 = 15 * g_tp["F_sz_um"]
    w_comp_inv_p3 = 50 * g_tp["F_sz_um"]
    w_comp_inv_n3 = 30 * g_tp["F_sz_um"]
    cell_h_def = 50 * g_tp["F_sz_um"]
    w_eval_inv_p = 100 * g_tp["F_sz_um"]
    w_eval_inv_n = 50 * g_tp["F_sz_um"]
    w_comp_n = 12.5 * g_tp["F_sz_um"]
    w_comp_p = 37.5 * g_tp["F_sz_um"]


    A = tag_assoc

    tagbits_ = tagbits // 4  # Assuming there are 4 quarter comparators. input tagbits is already a multiple of 4.

    # First Inverter
    Ceq = gate_C(g_tp, w_comp_inv_n2 + w_comp_inv_p2, 0, is_dram) + \
          drain_C_(g_tp, w_comp_inv_p1, PCH, 1, 1, cell_h_def, is_dram) + \
          drain_C_(g_tp, w_comp_inv_n1, NCH, 1, 1, cell_h_def, is_dram)
    Req = tr_R_on(g_tp, w_comp_inv_p1, PCH, 1, is_dram)
    tf = Req * Ceq
    st1del = horowitz(inrisetime, tf, VTHCOMPINV, VTHCOMPINV, FALL)
    nextinputtime = st1del / VTHCOMPINV
    # power_comparator.readOp.dynamic += 0.5 * Ceq * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 4 * A

    # For each degree of associativity there are 4 such quarter comparators
    # lkgCurrent = cmos_Isub_leakage(g_tp.w_comp_inv_n1, g_tp.w_comp_inv_p1, 1, inv, is_dram) * 4 * A
    # gatelkgCurrent = cmos_Ig_leakage(g_tp.w_comp_inv_n1, g_tp.w_comp_inv_p1, 1, inv, is_dram) * 4 * A

    # Second Inverter
    Ceq = gate_C(g_tp, w_comp_inv_n3 + w_comp_inv_p3, 0, is_dram) + \
          drain_C_(g_tp, w_comp_inv_p2, PCH, 1, 1, cell_h_def, is_dram) + \
          drain_C_(g_tp, w_comp_inv_n2, NCH, 1, 1, cell_h_def, is_dram)
    Req = tr_R_on(g_tp, w_comp_inv_n2, NCH, 1, is_dram)
    tf = Req * Ceq
    st2del = horowitz(nextinputtime, tf, VTHCOMPINV, VTHCOMPINV, RISE)
    nextinputtime = st2del / (1.0 - VTHCOMPINV)
    # power_comparator.readOp.dynamic += 0.5 * Ceq * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 4 * A
    # lkgCurrent += cmos_Isub_leakage(g_tp.w_comp_inv_n2, g_tp.w_comp_inv_p2, 1, inv, is_dram) * 4 * A
    # gatelkgCurrent += cmos_Ig_leakage(g_tp.w_comp_inv_n2, g_tp.w_comp_inv_p2, 1, inv, is_dram) * 4 * A

    # Third Inverter
    Ceq = gate_C(g_tp, w_eval_inv_n + w_eval_inv_p, 0, is_dram) + \
          drain_C_(g_tp, w_comp_inv_p3, PCH, 1, 1, cell_h_def, is_dram) + \
          drain_C_(g_tp, w_comp_inv_n3, NCH, 1, 1, cell_h_def, is_dram)
    Req = tr_R_on(g_tp, w_comp_inv_p3, PCH, 1, is_dram)
    tf = Req * Ceq
    st3del = horowitz(nextinputtime, tf, VTHCOMPINV, VTHEVALINV, FALL)
    nextinputtime = st3del / (VTHEVALINV)
    # power_comparator.readOp.dynamic += 0.5 * Ceq * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 4 * A
    # lkgCurrent += cmos_Isub_leakage(g_tp.w_comp_inv_n3, g_tp.w_comp_inv_p3, 1, inv, is_dram) * 4 * A
    # gatelkgCurrent += cmos_Ig_leakage(g_tp.w_comp_inv_n3, g_tp.w_comp_inv_p3, 1, inv, is_dram) * 4 * A

    # Final Inverter (virtual ground driver) discharging compare part
    r1 = tr_R_on(g_tp, w_comp_n, NCH, 2, is_dram)
    r2 = tr_R_on(g_tp, w_eval_inv_n, NCH, 1, is_dram)  # was switch
    c2 = (tagbits_) * (drain_C_(g_tp, w_comp_n, NCH, 1, 1, cell_h_def, is_dram) +
                       drain_C_(g_tp, w_comp_n, NCH, 2, 1, cell_h_def, is_dram)) + \
         drain_C_(g_tp, w_eval_inv_p, PCH, 1, 1, cell_h_def, is_dram) + \
         drain_C_(g_tp, w_eval_inv_n, NCH, 1, 1, cell_h_def, is_dram)
    c1 = (tagbits_) * (drain_C_(g_tp, w_comp_n, NCH, 1, 1, cell_h_def, is_dram) +
                       drain_C_(g_tp, w_comp_n, NCH, 2, 1, cell_h_def, is_dram)) + \
         drain_C_(g_tp, w_comp_p, PCH, 1, 1, cell_h_def, is_dram) + \
         gate_C(g_tp, 0, 0, is_dram)
    # power_comparator.readOp.dynamic += 0.5 * c2 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * 4 * A
    # power_comparator.readOp.dynamic += c1 * g_tp.peri_global.Vdd * g_tp.peri_global.Vdd * (A - 1)
    # lkgCurrent += cmos_Isub_leakage(g_tp.w_eval_inv_n, g_tp.w_eval_inv_p, 1, inv, is_dram) * 4 * A
    # lkgCurrent += cmos_Isub_leakage(g_tp.w_comp_n, g_tp.w_comp_n, 1, inv, is_dram) * 4 * A  # stack factor of 0.2

    # gatelkgCurrent += cmos_Ig_leakage(g_tp.w_eval_inv_n, g_tp.w_eval_inv_p, 1, inv, is_dram) * 4 * A
    # gatelkgCurrent += cmos_Ig_leakage(g_tp.w_comp_n, g_tp.w_comp_n, 1, inv, is_dram) * 4 * A  # for gate leakage this equals to a inverter

    # Time to go to threshold of mux driver
    tstep = (r2 * c2 + (r1 + r2) * c1) * math.log(1.0 / VTHMUXNAND)
    # Take into account non-zero input rise time
    peri_global_Vdd = g_tp["Vdd"]
    m = peri_global_Vdd / nextinputtime
    Tcomparatorni = 0.0

    # Check Relational!
    a = m
    b = 2 * ((peri_global_Vdd * VTHEVALINV) - peri_global_Vth)
    c = -2 * (tstep) * (peri_global_Vdd - peri_global_Vth) + \
        1 / m * ((peri_global_Vdd * VTHEVALINV) - peri_global_Vth) * \
        ((peri_global_Vdd * VTHEVALINV) - peri_global_Vth)
    Tcomparatorni = (-b + sp.sqrt(b * b - 4 * a * c)) / (2 * a)
    # if (tstep) <= (0.5 * (peri_global_Vdd - peri_global_Vth) / m):
    #     a = m
    #     b = 2 * ((peri_global_Vdd * VTHEVALINV) - peri_global_Vth)
    #     c = -2 * (tstep) * (peri_global_Vdd - peri_global_Vth) + \
    #         1 / m * ((peri_global_Vdd * VTHEVALINV) - peri_global_Vth) * \
    #         ((peri_global_Vdd * VTHEVALINV) - peri_global_Vth)
    #     Tcomparatorni = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
    # else:
    #     Tcomparatorni = (tstep) + (peri_global_Vdd + peri_global_Vth) / (2 * m) - \
    #                     (peri_global_Vdd * VTHEVALINV) / m

    delay_comparator = Tcomparatorni + st1del + st2del + st3del
    # power_comparator.readOp.leakage = lkgCurrent * g_tp.peri_global.Vdd
    # power_comparator.readOp.gate_leakage = gatelkgCurrent * g_tp.peri_global.Vdd

    return Tcomparatorni / (1.0 - VTHMUXNAND)


# wire.[cc/h]
# TODO -> replace subarray_out_wire.repeater_size etc in compute_subarray_out_drv and compute_htree

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
    R_nch_on = g_tp["nmos_effective_resistance_multiplier"] * g_tp["Vdd"] / g_tp["I_on_n"] # all dat inputs
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

def simplified_pmos_leakage(
    pwidth,
    _is_dram,
    _is_cell,
    _is_wl_tr,
    _is_sleep_tx):
    return pwidth * I_off_p
    
if __name__ == "__main__" :
    inrisetime = 0

    # point to text file with sympy expression
    # validate (expr_file, cfg_file, dat_file)
    # return sympy.out, cacti.out
    # save as mem_access_time.txt and buf_access_time.txt -> save in src/cacti for now
    #codeisng calls sympfiy.cacti 
    substitutions = {
        C_g_ideal: 5.34e-16,
        C_fringe: 4e-17,
        C_junc: 1e-15,
        C_junc_sw: 2.5e-16,
        l_phy: 0.013,
        F_sz_um: 0,
        n2p_drv_rt: 2.41,
        nmos_effective_resistance_multiplier: 1.49,
        Vdd: 0.9,
        I_on_n: 0.0022117,
        wire_c_per_micron: 1.89209e-15,
        wire_length: 1,
        wire_delay: 0,
        vpp: 0,
        cell_h: 1,
        cell_w: 1,
        cam_cell_h: 1,
        cam_cell_w: 1,
        subarray_num_rows: 5,
        subarray_C_bl: 5,
        RWP: 1,
        ERP: 1,
        EWP: 1,
        SCHP: 1,
        wire_local_R_per_um: 4,
        dram_cell_Vdd: 4,
        dram_cell_C: 4,
        dram_cell_I_on: 4,
        V_b_sense: 4,
        dram_Vbitpre: 3,
        dram_cell_a_w: 3,
        sram_Vbitpre: 3,
        sram_cell_Vth: 0.21835,
        sram_cell_Vdd: 0.9,
        sram_cell_nmos_w: 1,
        sram_cell_a_w: 1,
        I_off_p: 1,
        gm_sense_amp_latch: 4,
        Ndsam_lev_1: 1,
        Ndsam_lev_2: 1,
        subarray_out_wire_repeater_size: 1,
        subarray_out_wire_wire_length: 1,
        subarray_out_wire_repeater_spacing: 1,
        subarray_out_wire_delay: 1,
        tag_assoc: 4,
        tagbits: 4,
        dram_acc_Vth: 4,
        peri_global_Vth: 4
    }
    file = "../tech_params/180nm.dat"
    scan_dat(substitutions, file, 0, 0, 360)
    print(substitutions)

    access_time_expr = get_access_time(g_tp, inrisetime)
    result = access_time_expr.subs(substitutions)
    print(result)
    # diff_access_time_C_g_ideal = sp.diff(access_time_expr, g_tp["C_g_ideal"])
    # #print(f"The derivative of the function is: {diff_access_time_C_g_ideal}")

    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # filename = current_dir + "/diff_result.txt"
    # try:
    #     with open(filename, 'w') as file:
    #         file.write("HELLO!\n")
    #         file.write(f"The derivative of the function is: {diff_access_time_C_g_ideal}\n")
    #     print(f"Output has been written to {filename}")
    # except Exception as e:
    #     print(f"Error writing to file: {e}")