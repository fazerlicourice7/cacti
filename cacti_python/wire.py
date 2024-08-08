from .decoder import *
from .parameter import g_tp
from .parameter import *
from .const import *
from .component import Component
from .cacti_interface import *

import math

class Wire(Component):
    global_ = Component()
    global_5 = Component()
    global_10 = Component()
    global_20 = Component()
    global_30 = Component()
    low_swing = Component()
    initialized = 0
    wire_width_init = None
    wire_spacing_init = None

    def __init__(self, wire_model=0, wl=1, n=1, w_s=1, s_s=1, wp=outside_mat, resistivity=CU_RESISTIVITY, dt=g_tp.peri_global):
        super().__init__()
        self.wt = wire_model
        self.wire_length = wl * 1e-6
        self.nsense = n
        self.w_scale = w_s
        self.s_scale = s_s
        self.resistivity = resistivity
        self.deviceType = dt
        self.wire_placement = wp
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * g_tp.min_w_nmos_
        self.in_rise_time = 0
        self.out_rise_time = 0
        self.repeated_wire = []

        self.transmitter = Component()
        self.l_wire = Component()
        self.sense_amp = Component()

        # CHECK
        self.repeater_spacing = 0
        self.wire_width = 0
        self.wire_spacing = 0
        self.repeater_size = 0 

        if Wire.initialized != 1:
            print("Initializing Wire")
            self.__init_wire_simple(w_s, s_s, wp, resistivity, dt)

        self.calculate_wire_stats()

        self.repeater_spacing *= 1e6
        self.wire_length *= 1e6
        self.wire_width *= 1e6
        self.wire_spacing *= 1e6
        
        # assert self.wire_length > 0
        # assert self.power.readOp.dynamic > 0
        # assert self.power.readOp.leakage > 0
        # assert self.power.readOp.gate_leakage > 0

    def __init_wire_simple(self, w_s, s_s, wp, resis, dt):
        if self.wire_placement == outside_mat:
            self.wire_width = g_tp.wire_outside_mat.pitch / 2
        elif self.wire_placement == inside_mat:
            self.wire_width = g_tp.wire_inside_mat.pitch / 2
        else:
            self.wire_width = g_tp.wire_local.pitch / 2

        self.wire_spacing = self.wire_width

        self.wire_width *= (self.w_scale * 1e-6 / 2)
        self.wire_spacing *= (self.s_scale * 1e-6 / 2)

        Wire.initialized = 1
        self.init_wire()
        Wire.wire_width_init = self.wire_width
        Wire.wire_spacing_init = self.wire_spacing

        # assert self.power.readOp.dynamic > 0
        # assert self.power.readOp.leakage > 0
        # assert self.power.readOp.gate_leakage > 0

    def __del__(self):
        pass

    def calculate_wire_stats(self):
        if self.wire_placement == outside_mat:
            self.wire_width = g_tp.wire_outside_mat.pitch / 2
        elif self.wire_placement == inside_mat:
            self.wire_width = g_tp.wire_inside_mat.pitch / 2
        else:
            self.wire_width = g_tp.wire_local.pitch / 2

        self.wire_spacing = self.wire_width

        self.wire_width *= (self.w_scale * 1e-6 / 2)
        self.wire_spacing *= (self.s_scale * 1e-6 / 2)

        if self.wt != 'Low_swing':
            if self.wt == 'Global':
                self.delay = Wire.global_.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_.area.w
                self.repeater_size = Wire.global_.area.h

                self.area.set_area((self.wire_length / self.repeater_spacing) * compute_gate_area(INV, 1, self.min_w_pmos * self.repeater_size, g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            elif self.wt == 'Global_5':
                self.delay = Wire.global_5.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_5.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_5.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_5.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_5.area.w
                self.repeater_size = Wire.global_5.area.h

                self.area.set_area((self.wire_length / self.repeater_spacing) * compute_gate_area('INV', 1, self.min_w_pmos * self.repeater_size, g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            elif self.wt == 'Global_10':
                self.delay = Wire.global_10.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_10.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_10.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_10.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_10.area.w
                self.repeater_size = Wire.global_10.area.h

                self.area.set_area((self.wire_length / self.repeater_spacing) * compute_gate_area('INV', 1, self.min_w_pmos * self.repeater_size, g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            elif self.wt == 'Global_20':
                self.delay = Wire.global_20.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_20.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_20.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_20.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_20.area.w
                self.repeater_size = Wire.global_20.area.h

                self.area.set_area((self.wire_length / self.repeater_spacing) * compute_gate_area('INV', 1, self.min_w_pmos * self.repeater_size, g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            elif self.wt == 'Global_30':
                self.delay = Wire.global_30.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_30.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_30.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_30.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_30.area.w
                self.repeater_size = Wire.global_30.area.h

                self.area.set_area((self.wire_length / self.repeater_spacing) * compute_gate_area('INV', 1, self.min_w_pmos * self.repeater_size, g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            else: # Check wr wire type
                self.delay = Wire.global_.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_.area.w
                self.repeater_size = Wire.global_.area.h

                self.area.set_area((self.wire_length / self.repeater_spacing) * compute_gate_area(INV, 1, self.min_w_pmos * self.repeater_size, g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            self.out_rise_time = self.delay * self.repeater_spacing / self.deviceType.Vth
        elif self.wt == 'Low_swing':
            self.low_swing_model()
            self.repeater_spacing = self.wire_length
            self.repeater_size = 1
        else:
            raise AssertionError()

    def signal_fall_time(self):
        timeconst = (drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                     drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                     gate_C(self.min_w_pmos + g_tp.min_w_nmos_, 0)) * \
                    tr_R_on(self.min_w_pmos, PCH, 1)
        rt = horowitz(0, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, FALL) / (self.deviceType.Vdd - self.deviceType.Vth)
        timeconst = (drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                     drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                     gate_C(self.min_w_pmos + g_tp.min_w_nmos_, 0)) * \
                    tr_R_on(g_tp.min_w_nmos_, NCH, 1)
        ft = horowitz(rt, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, RISE) / self.deviceType.Vth
        return ft

    def signal_rise_time(self):
        timeconst = (drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                     drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                     gate_C(self.min_w_pmos + g_tp.min_w_nmos_, 0)) * \
                    tr_R_on(g_tp.min_w_nmos_, NCH, 1)
        rt = horowitz(0, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, RISE) / self.deviceType.Vth
        timeconst = (drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                     drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                     gate_C(self.min_w_pmos + g_tp.min_w_nmos_, 0)) * \
                    tr_R_on(self.min_w_pmos, PCH, 1)
        ft = horowitz(rt, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, FALL) / (self.deviceType.Vdd - self.deviceType.Vth)
        return ft

    def wire_cap(self, length, call_from_outside=False):
        epsilon0 = 8.8542e-12
        if self.wire_placement == 'outside_mat':
            aspect_ratio = g_tp.wire_outside_mat.aspect_ratio
            horiz_dielectric_constant = g_tp.wire_outside_mat.horiz_dielectric_constant
            vert_dielectric_constant = g_tp.wire_outside_mat.vert_dielectric_constant
            miller_value = g_tp.wire_outside_mat.miller_value
            ild_thickness = g_tp.wire_outside_mat.ild_thickness
        elif self.wire_placement == 'inside_mat':
            aspect_ratio = g_tp.wire_inside_mat.aspect_ratio
            horiz_dielectric_constant = g_tp.wire_inside_mat.horiz_dielectric_constant
            vert_dielectric_constant = g_tp.wire_inside_mat.vert_dielectric_constant
            miller_value = g_tp.wire_inside_mat.miller_value
            ild_thickness = g_tp.wire_inside_mat.ild_thickness
        else:
            aspect_ratio = g_tp.wire_local.aspect_ratio
            horiz_dielectric_constant = g_tp.wire_local.horiz_dielectric_constant
            vert_dielectric_constant = g_tp.wire_local.vert_dielectric_constant
            miller_value = g_tp.wire_local.miller_value
            ild_thickness = g_tp.wire_local.ild_thickness

        if call_from_outside:
            self.wire_width *= 1e-6
            self.wire_spacing *= 1e-6

        wire_height = self.wire_width / self.w_scale * aspect_ratio
        sidewall = miller_value * horiz_dielectric_constant * (wire_height / self.wire_spacing) * epsilon0
        adj = miller_value * vert_dielectric_constant * self.wire_width / (ild_thickness * 1e-6) * epsilon0
        tot_cap = (sidewall + adj + (g_tp.fringe_cap * 1e6))

        if call_from_outside:
            self.wire_width *= 1e6
            self.wire_spacing *= 1e6

        return tot_cap * length
    
    def wire_res(self, length):
        alpha_scatter = 1.05
        dishing_thickness = 0
        barrier_thickness = 0

        if self.wire_placement == 'outside_mat':
            aspect_ratio = g_tp.wire_outside_mat.aspect_ratio
        elif self.wire_placement == 'inside_mat':
            aspect_ratio = g_tp.wire_inside_mat.aspect_ratio
        else:
            aspect_ratio = g_tp.wire_local.aspect_ratio

        return (alpha_scatter * self.resistivity * 1e-6 * length /
                ((aspect_ratio * self.wire_width / self.w_scale - dishing_thickness - barrier_thickness) *
                 (self.wire_width - 2 * barrier_thickness)))

    def low_swing_model(self):
        len_ = self.wire_length
        beta = pmos_to_nmos_sz_ratio()

        inputrise = self.in_rise_time if self.in_rise_time != 0 else self.signal_rise_time()

        cwire = self.wire_cap(len_)
        rwire = self.wire_res(len_)

        RES_ADJ = 8.6
        driver_res = (-8 * g_tp.FO4 / (math.log(0.5) * cwire)) / RES_ADJ
        nsize = R_to_w(driver_res, NCH)

        # RECENT CHANGE: MAX - ignore to reduce expression length
        # nsize = sp.Min(nsize, g_tp.max_w_nmos_)
        # nsize = symbolic_convex_max(nsize, g_tp.min_w_nmos_)

        # CHANGE: RELATIONAL
        # if rwire * cwire > 8 * g_tp.FO4:
        #     nsize = g_tp.max_w_nmos_

        nsize = sp.Piecewise(
            (g_tp.max_w_nmos_, rwire * cwire > 8 * g_tp.FO4),
            (nsize, True)
        )

        st_eff = sp.sqrt((2 + beta / 1 + beta) * gate_C(nsize, 0) / 
                           (gate_C(2 * g_tp.min_w_nmos_, 0) + gate_C(2 * self.min_w_pmos, 0)))
        req_cin = ((2 + beta / 1 + beta) * gate_C(nsize, 0)) / st_eff
        inv_size = req_cin / (gate_C(self.min_w_pmos, 0) + gate_C(g_tp.min_w_nmos_, 0))

        # RECENT CHANGE: MAX - ignore to reduce expression size
        inv_size = symbolic_convex_max(inv_size, 1)

        res_eq = 2 * tr_R_on(g_tp.min_w_nmos_, NCH, 1)
        cap_eq = 2 * drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) + \
                 drain_C_(2 * g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) + \
                 gate_C(inv_size * g_tp.min_w_nmos_, 0) + \
                 gate_C(inv_size * self.min_w_pmos, 0)

        timeconst = res_eq * cap_eq
        self.delay = horowitz(inputrise, timeconst, self.deviceType.Vth / self.deviceType.Vdd,
                              self.deviceType.Vth / self.deviceType.Vdd, RISE)
        temp_power = cap_eq * self.deviceType.Vdd * self.deviceType.Vdd

        inputrise = self.delay / (self.deviceType.Vdd - self.deviceType.Vth)

        res_eq = tr_R_on(inv_size * self.min_w_pmos, PCH, 1)
        cap_eq = drain_C_(inv_size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) + \
                 drain_C_(inv_size * g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) + \
                 gate_C(nsize, 0)
        timeconst = res_eq * cap_eq

        self.delay += horowitz(inputrise, timeconst, self.deviceType.Vth / self.deviceType.Vdd,
                               self.deviceType.Vth / self.deviceType.Vdd, FALL)
        temp_power += cap_eq * self.deviceType.Vdd * self.deviceType.Vdd

        self.transmitter.delay = self.delay
        self.transmitter.power.readOp.dynamic = temp_power * 2
        self.transmitter.power.readOp.leakage = self.deviceType.Vdd * \
            (4 * cmos_Isub_leakage(g_tp.min_w_nmos_, self.min_w_pmos, 2, 'nand') +
             4 * cmos_Isub_leakage(g_tp.min_w_nmos_, self.min_w_pmos, 1, 'inv'))

        self.transmitter.power.readOp.gate_leakage = self.deviceType.Vdd * \
            (4 * cmos_Ig_leakage(g_tp.min_w_nmos_, self.min_w_pmos, 2, 'nand') +
             4 * cmos_Ig_leakage(g_tp.min_w_nmos_, self.min_w_pmos, 1, 'inv'))

        inputrise = self.delay / self.deviceType.Vth

        cap_eq = cwire + 2 * drain_C_(nsize, NCH, 1, 1, g_tp.cell_h_def) + \
                 self.nsense * self.sense_amp_input_cap()
        timeconst = (tr_R_on(nsize, NCH, 1) * RES_ADJ) * (cwire + 2 * drain_C_(nsize, NCH, 1, 1, g_tp.cell_h_def)) + \
                    rwire * cwire / 2 + \
                    (tr_R_on(nsize, NCH, 1) * RES_ADJ + rwire) * \
                    self.nsense * self.sense_amp_input_cap()

        self.delay += horowitz(inputrise, timeconst, self.deviceType.Vth / self.deviceType.Vdd, 0.25, 0)
        VOL_SWING = 0.1
        temp_power += cap_eq * VOL_SWING * 0.400
        temp_power *= 2

        self.l_wire.delay = self.delay - self.transmitter.delay
        self.l_wire.power.readOp.dynamic = temp_power - self.transmitter.power.readOp.dynamic
        self.l_wire.power.readOp.leakage = self.deviceType.Vdd * \
            (4 * cmos_Isub_leakage(nsize, 0, 1, nmos))

        self.l_wire.power.readOp.gate_leakage = self.deviceType.Vdd * \
            (4 * cmos_Ig_leakage(nsize, 0, 1, nmos))

        self.delay += g_tp.sense_delay

        self.sense_amp.delay = g_tp.sense_delay
        self.out_rise_time = g_tp.sense_delay / self.deviceType.Vth
        self.sense_amp.power.readOp.dynamic = g_tp.sense_dy_power
        self.sense_amp.power.readOp.leakage = 0
        self.sense_amp.power.readOp.gate_leakage = 0

        self.power.readOp.dynamic = temp_power + self.sense_amp.power.readOp.dynamic
        self.power.readOp.leakage = self.transmitter.power.readOp.leakage + \
                                    self.l_wire.power.readOp.leakage + \
                                    self.sense_amp.power.readOp.leakage
        self.power.readOp.gate_leakage = self.transmitter.power.readOp.gate_leakage + \
                                         self.l_wire.power.readOp.gate_leakage + \
                                         self.sense_amp.power.readOp.gate_leakage
        
    def sense_amp_input_cap(self):
        return (
            drain_C_(g_tp.w_iso, PCH, 1, 1, g_tp.cell_h_def) +
            gate_C(g_tp.w_sense_en + g_tp.w_sense_n, 0) +
            drain_C_(g_tp.w_sense_n, NCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(g_tp.w_sense_p, PCH, 1, 1, g_tp.cell_h_def)
        )

    def delay_optimal_wire(self):
        len_ = self.wire_length
        beta = pmos_to_nmos_sz_ratio()
        switching = 0
        short_ckt = 0
        tc = 0
        input_cap = gate_C(g_tp.min_w_nmos_ + self.min_w_pmos, 0)
        out_cap = (
            drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def)
        )
        out_res = (
            tr_R_on(g_tp.min_w_nmos_, NCH, 1) +
            tr_R_on(self.min_w_pmos, PCH, 1)
        ) / 2
        wr = self.wire_res(len_)
        wc = self.wire_cap(len_)
        repeater_scaling = sp.sqrt(out_res * wc / (wr * input_cap))
        self.repeater_spacing = sp.sqrt(2 * out_res * (out_cap + input_cap) / ((wr / len_) * (wc / len_)))
        self.repeater_size = repeater_scaling

        switching = (
            (repeater_scaling * (input_cap + out_cap) +
            self.repeater_spacing * (wc / len_)) *
            self.deviceType.Vdd * self.deviceType.Vdd
        )

        tc = (
            out_res * (input_cap + out_cap) +
            out_res * wc / len_ * self.repeater_spacing / repeater_scaling +
            wr / len_ * self.repeater_spacing * input_cap * repeater_scaling +
            0.5 * (wr / len_) * (wc / len_) * self.repeater_spacing * self.repeater_spacing
        )

        self.delay = 0.693 * tc * len_ / self.repeater_spacing

        Ishort_ckt = 65e-6
        short_ckt = (
            self.deviceType.Vdd * g_tp.min_w_nmos_ * Ishort_ckt * 1.0986 *
            repeater_scaling * tc
        )

        self.area.set_area(
            (len_ / self.repeater_spacing) *
            compute_gate_area(
                INV, 1, self.min_w_pmos * repeater_scaling,
                g_tp.min_w_nmos_ * repeater_scaling, g_tp.cell_h_def
            )
        )

        self.power.readOp.dynamic = (len_ / self.repeater_spacing) * (switching + short_ckt)
        self.power.readOp.leakage = (
            (len_ / self.repeater_spacing) *
            self.deviceType.Vdd *
            cmos_Isub_leakage(
                g_tp.min_w_nmos_ * repeater_scaling, beta * g_tp.min_w_nmos_ * repeater_scaling, 1, inv
            )
        )
        self.power.readOp.gate_leakage = (
            (len_ / self.repeater_spacing) *
            self.deviceType.Vdd *
            cmos_Ig_leakage(
                g_tp.min_w_nmos_ * repeater_scaling, beta * g_tp.min_w_nmos_ * repeater_scaling, 1, inv
            )
        )

    def init_wire(self):
        self.wire_length = 1
        self.delay_optimal_wire()
        # sp = self.repeater_spacing * 1e6  # in microns
        sp = int(g_ip.repeater_spacing)  # CHANGE: ARRAY LOGIC

        # si = self.repeater_size
        si = int(g_ip.repeater_size) # CHANGE: ARRAY LOGIC
        # si = 85.6553


        # CHANGE: ARRAY LOGIC - cannot index with symbolic expression, so we have to use value
        self.repeated_wire.append(Component())
        for j in range(int(sp), int(4 * sp), 100):
            for i in range(int(si), 1, -1):
                pow_, del_ = self.wire_model(j * 1e-6, i)
                
                if j == int(sp) and i == int(si):
                    Wire.global_.delay = del_
                    Wire.global_.power = pow_
                    Wire.global_.area.h = si
                    Wire.global_.area.w = sp * 1e-6  # m

                self.repeated_wire[-1].delay = del_
                self.repeated_wire[-1].power.readOp = pow_.readOp
                self.repeated_wire[-1].area.w = j * 1e-6  # m
                self.repeated_wire[-1].area.h = i
                self.repeated_wire.append(Component())

        self.repeated_wire.pop()
        self.update_fullswing()

        # CHANGE: SET LOGIC - just set global_ to be spacing and size
        Wire.global_.area.h = si
        Wire.global_.area.w = sp * 1e-6  # m

        l_wire = Wire('Low_swing', 0.001, 1)
        Wire.low_swing.delay = l_wire.delay
        Wire.low_swing.power = l_wire.power
        del l_wire

    def update_fullswing(self):
        deltas = [
            self.global_.delay + self.global_.delay * 0.05,
            self.global_.delay + self.global_.delay * 0.1,
            self.global_.delay + self.global_.delay * 0.2,
            self.global_.delay + self.global_.delay * 0.3
        ]

        i = 4
        while i > 0:
            threshold = deltas[i - 1]
            cost = float('inf')
            for citer in list(self.repeated_wire):
                # CHANGE: RELATIONAL LOGIC
                # if citer.delay > threshold:
                #     self.repeated_wire.remove(citer)
                # else:
                ncost = citer.power.readOp.dynamic / self.global_.power.readOp.dynamic + \
                        citer.power.readOp.leakage / self.global_.power.readOp.leakage
                
                # CHANGE: RELATIONAL LOGIC
                # if ncost < cost:
                cost = ncost
                if i == 4:
                    Wire.global_30.delay = citer.delay
                    Wire.global_30.power = citer.power
                    Wire.global_30.area = citer.area
                elif i == 3:
                    Wire.global_20.delay = citer.delay
                    Wire.global_20.power = citer.power
                    Wire.global_20.area = citer.area
                elif i == 2:
                    Wire.global_10.delay = citer.delay
                    Wire.global_10.power = citer.power
                    Wire.global_10.area = citer.area
                elif i == 1:
                    Wire.global_5.delay = citer.delay
                    Wire.global_5.power = citer.power
                    Wire.global_5.area = citer.area
            i -= 1

    def wire_model(self, space, size):
        ptemp = PowerDef()
        len_ = 1
        beta = pmos_to_nmos_sz_ratio()
        switching = 0
        short_ckt = 0
        tc = 0
        input_cap = gate_C(g_tp.min_w_nmos_ + self.min_w_pmos, 0)
        out_cap = drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) + \
                  drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def)
        out_res = (tr_R_on(g_tp.min_w_nmos_, NCH, 1) +
                   tr_R_on(self.min_w_pmos, PCH, 1)) / 2
        wr = self.wire_res(len_)
        wc = self.wire_cap(len_)

        self.repeater_spacing = space
        self.repeater_size = size

        switching = (self.repeater_size * (input_cap + out_cap) +
                     self.repeater_spacing * (wc / len_)) * self.deviceType.Vdd * self.deviceType.Vdd

        tc = out_res * (input_cap + out_cap) + \
             out_res * wc / len_ * self.repeater_spacing / self.repeater_size + \
             wr / len_ * self.repeater_spacing * out_cap * self.repeater_size + \
             0.5 * (wr / len_) * (wc / len_) * self.repeater_spacing * self.repeater_spacing

        delay = 0.693 * tc * len_ / self.repeater_spacing

        Ishort_ckt = 65e-6
        short_ckt = self.deviceType.Vdd * g_tp.min_w_nmos_ * Ishort_ckt * 1.0986 * \
                    self.repeater_size * tc

        ptemp.readOp.dynamic = (len_ / self.repeater_spacing) * (switching + short_ckt)
        ptemp.readOp.leakage = (len_ / self.repeater_spacing) * \
                               self.deviceType.Vdd * \
                               cmos_Isub_leakage(g_tp.min_w_nmos_ * self.repeater_size,
                                                      beta * g_tp.min_w_nmos_ * self.repeater_size, 1, inv)

        ptemp.readOp.gate_leakage = (len_ / self.repeater_spacing) * \
                                    self.deviceType.Vdd * \
                                    cmos_Ig_leakage(g_tp.min_w_nmos_ * self.repeater_size,
                                                         beta * g_tp.min_w_nmos_ * self.repeater_size, 1, inv)

        return ptemp, delay

    def print_wire(self):
        print("\nWire Properties:\n")
        print(f"  Delay Optimal\n\tRepeater size - {self.global_.area.h}"
              f" \n\tRepeater spacing - {self.global_.area.w * 1e3} (mm)"
              f" \n\tDelay - {self.global_.delay * 1e6} (ns/mm)"
              f" \n\tPowerD - {self.global_.power.readOp.dynamic * 1e6} (nJ/mm)"
              f" \n\tPowerL - {self.global_.power.readOp.leakage} (mW/mm)"
              f" \n\tPowerLgate - {self.global_.power.readOp.gate_leakage} (mW/mm)")
        print(f"\tWire width - {self.wire_width_init * 1e6} microns")
        print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        for overhead, global_comp in zip(["5%", "10%", "20%", "30%"],
                                         [self.global_5, self.global_10, self.global_20, self.global_30]):
            print(f"  {overhead} Overhead\n\tRepeater size - {global_comp.area.h}"
                  f" \n\tRepeater spacing - {global_comp.area.w * 1e3} (mm)"
                  f" \n\tDelay - {global_comp.delay * 1e6} (ns/mm)"
                  f" \n\tPowerD - {global_comp.power.readOp.dynamic * 1e6} (nJ/mm)"
                  f" \n\tPowerL - {global_comp.power.readOp.leakage} (mW/mm)"
                  f" \n\tPowerLgate - {global_comp.power.readOp.gate_leakage} (mW/mm)")
            print(f"\tWire width - {self.wire_width_init * 1e6} microns")
            print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        print("  Low-swing wire (1 mm) - Note: Unlike repeated wires, \n\tdelay and power "
              "values of low-swing wires do not\n\thave a linear relationship with length."
              f" \n\tdelay - {self.low_swing.delay * 1e9} (ns)"
              f" \n\tpowerD - {self.low_swing.power.readOp.dynamic * 1e9} (nJ)"
              f" \n\tPowerL - {self.low_swing.power.readOp.leakage} (mW)"
              f" \n\tPowerLgate - {self.low_swing.power.readOp.gate_leakage} (mW)")
        print(f"\tWire width - {self.wire_width_init * 2} microns")
        print(f"\tWire spacing - {self.wire_spacing_init * 2} microns\n\n")

    def set_in_rise_time(self, rt):
        self.in_rise_time = rt