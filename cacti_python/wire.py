from .decoder import *
from .parameter import g_tp
from .parameter import *
from .const import *
from .component import Component
from .cacti_interface import *

class Wire(Component):
    global_comp = Component()
    global_5 = Component()
    global_10 = Component()
    global_20 = Component()
    global_30 = Component()
    low_swing = Component()
    initialized = 0
    wire_width_init = 0
    wire_spacing_init = 0

    def __init__(self, wire_model = 0, length = 1, nsense=1, width_scaling=1, spacing_scaling=1, wire_placement=outside_mat, resistivity=CU_RESISTIVITY, dt=g_tp.peri_global):
        super().__init__()
        self.wt = wire_model
        self.wire_length = length * 1e-6
        self.nsense = nsense
        self.w_scale = width_scaling
        self.s_scale = spacing_scaling
        self.resistivity = resistivity
        self.deviceType = dt if dt else g_tp.peri_global # TODO check this
        self.wire_placement = wire_placement
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * g_tp.min_w_nmos_
        self.in_rise_time = 0
        self.out_rise_time = 0
        self.repeater_spacing = 1
        # TODO set arbitrary for now
        self.repeater_size = 0

        print("WRIE CHECKPINT 0")
        
        self.calculate_wire_stats()
        print("WRIE CHECKPINT 0")
        self.repeater_spacing *= 1e6
        self.wire_length *= 1e6
        self.wire_width *= 1e6
        self.wire_spacing *= 1e6

        self.transmitter = Component()
        self.l_wire = Component()
        self.sense_amp = Component()
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * g_tp.min_w_nmos_
        
        # assert self.wire_length > 0
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
        self.wire_width *= self.w_scale * 1e-6 / 2
        self.wire_spacing *= self.s_scale * 1e-6 / 2

        if self.wt != Low_swing:
            if self.wt == Global:
                self.delay = self.global_comp.delay * self.wire_length
                self.power.readOp.dynamic = self.global_comp.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = self.global_comp.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = self.global_comp.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = self.global_comp.area.w
                self.repeater_size = self.global_comp.area.h
                self.area.set_area((self.wire_length / self.repeater_spacing) *
                                   compute_gate_area(INV, 1, self.min_w_pmos * self.repeater_size,
                                                     g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            elif self.wt == Global_5:
                self.delay = Wire.global_5.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_5.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_5.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_5.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_5.area.w
                self.repeater_size = Wire.global_5.area.h
                self.area.set_area((self.wire_length / self.repeater_spacing) *
                                   compute_gate_area(INV, 1, self.min_w_pmos * self.repeater_size,
                                                     g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            elif self.wt == Global_10:
                self.delay = Wire.global_10.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_10.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_10.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_10.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_10.area.w
                self.repeater_size = Wire.global_10.area.h
                self.area.set_area((self.wire_length / self.repeater_spacing) *
                                   compute_gate_area(INV, 1, self.min_w_pmos * self.repeater_size,
                                                     g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            elif self.wt == Global_20:
                self.delay = Wire.global_20.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_20.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_20.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_20.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_20.area.w
                self.repeater_size = Wire.global_20.area.h
                self.area.set_area((self.wire_length / self.repeater_spacing) *
                                   compute_gate_area(INV, 1, self.min_w_pmos * self.repeater_size,
                                                     g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            elif self.wt == Global_30:
                self.delay = Wire.global_30.delay * self.wire_length
                self.power.readOp.dynamic = Wire.global_30.power.readOp.dynamic * self.wire_length
                self.power.readOp.leakage = Wire.global_30.power.readOp.leakage * self.wire_length
                self.power.readOp.gate_leakage = Wire.global_30.power.readOp.gate_leakage * self.wire_length
                self.repeater_spacing = Wire.global_30.area.w
                self.repeater_size = Wire.global_30.area.h
                self.area.set_area((self.wire_length / self.repeater_spacing) *
                                   compute_gate_area(INV, 1, self.min_w_pmos * self.repeater_size,
                                                     g_tp.min_w_nmos_ * self.repeater_size, g_tp.cell_h_def))
            print("HOTSPOT")
            print(self.deviceType.Vth)
            #TODO important self.deviceType.Vth is not symbolic for some reason
            if(self.deviceType.Vth == 0):
                self.deviceType.Vth = 1
            self.out_rise_time = self.delay * self.repeater_spacing / self.deviceType.Vth
        elif self.wt == Low_swing:
            self.low_swing_model()
            self.repeater_spacing = self.wire_length
            self.repeater_size = 1
        else:
            assert False

    def signal_fall_time(self):
        timeconst = (drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                     drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                     gate_C(self.min_w_pmos + g_tp.min_w_nmos_, 0)) * tr_R_on(self.min_w_pmos, PCH, 1)
        rt = horowitz(0, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, FALL) / (self.deviceType.Vdd - self.deviceType.Vth)
        timeconst = (drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                     drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                     gate_C(self.min_w_pmos + g_tp.min_w_nmos_, 0)) * tr_R_on(g_tp.min_w_nmos_, NCH, 1)
        ft = horowitz(rt, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, RISE) / self.deviceType.Vth
        return ft

    def signal_rise_time(self):
        timeconst = (drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                     drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                     gate_C(self.min_w_pmos + g_tp.min_w_nmos_, 0)) * tr_R_on(g_tp.min_w_nmos_, NCH, 1)
        # TODO need to check why deviceType
        if (self.deviceType.Vdd == 0):
            self.deviceType.Vdd = 1
        rt = horowitz(0, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, RISE) / self.deviceType.Vth
        timeconst = (drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                     drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                     gate_C(self.min_w_pmos + g_tp.min_w_nmos_, 0)) * tr_R_on(self.min_w_pmos, PCH, 1)
        ft = horowitz(rt, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, FALL) / (self.deviceType.Vdd - self.deviceType.Vth)
        return ft

    def set_in_rise_time(self, rt):
        self.in_rise_time = rt

    def print_wire(self):
        pass
    
    def wire_cap(self, length, call_from_outside=False):
        epsilon0 = 8.8542e-12

        if self.wire_placement == outside_mat:
            aspect_ratio = g_tp.wire_outside_mat.aspect_ratio
            horiz_dielectric_constant = g_tp.wire_outside_mat.horiz_dielectric_constant
            vert_dielectric_constant = g_tp.wire_outside_mat.vert_dielectric_constant
            miller_value = g_tp.wire_outside_mat.miller_value
            ild_thickness = g_tp.wire_outside_mat.ild_thickness
        elif self.wire_placement == inside_mat:
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
        tot_cap = sidewall + adj + g_tp.fringe_cap * 1e6

        if call_from_outside:
            self.wire_width *= 1e6
            self.wire_spacing *= 1e6

        return tot_cap * length

    def wire_res(self, length):
        alpha_scatter = 1.05
        dishing_thickness = 0
        barrier_thickness = 0

        if self.wire_placement == outside_mat:
            aspect_ratio = g_tp.wire_outside_mat.aspect_ratio
        elif self.wire_placement == inside_mat:
            aspect_ratio = g_tp.wire_inside_mat.aspect_ratio
        else:
            aspect_ratio = g_tp.wire_local.aspect_ratio

        return (alpha_scatter * self.resistivity * 1e-6 * length) / (
                (aspect_ratio * self.wire_width / self.w_scale - dishing_thickness - barrier_thickness) *
                (self.wire_width - 2 * barrier_thickness))

    def low_swing_model(self):
        length = self.wire_length
        beta = pmos_to_nmos_sz_ratio()
        inputrise = self.signal_rise_time() if self.in_rise_time == 0 else self.in_rise_time

        cwire = self.wire_cap(length)
        rwire = self.wire_res(length)

        RES_ADJ = 8.6

        driver_res = (-8 * g_tp.FO4 / (math.log(0.5) * cwire)) / RES_ADJ
        nsize = R_to_w(driver_res, NCH)

        nsize = min(nsize, g_tp.max_w_nmos_)
        nsize = symbolic_convex_max(nsize, g_tp.min_w_nmos_)

        if rwire * cwire > 8 * g_tp.FO4:
            nsize = g_tp.max_w_nmos_

        st_eff = sp.sqrt((2 + beta / 1 + beta) * gate_C(nsize, 0) / (
                    gate_C(2 * g_tp.min_w_nmos_, 0) + gate_C(2 * self.min_w_pmos, 0)))
        req_cin = ((2 + beta / 1 + beta) * gate_C(nsize, 0)) / st_eff
        inv_size = req_cin / (gate_C(self.min_w_pmos, 0) + gate_C(g_tp.min_w_nmos_, 0))
        inv_size = symbolic_convex_max(inv_size, 1)

        res_eq = 2 * tr_R_on(g_tp.min_w_nmos_, NCH, 1)
        cap_eq = (2 * drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                  drain_C_(2 * g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                  gate_C(inv_size * g_tp.min_w_nmos_, 0) +
                  gate_C(inv_size * self.min_w_pmos, 0))

        timeconst = res_eq * cap_eq
        self.delay = horowitz(inputrise, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, RISE)
        temp_power = cap_eq * self.deviceType.Vdd * self.deviceType.Vdd

        inputrise = self.delay / (self.deviceType.Vdd - self.deviceType.Vth)

        res_eq = tr_R_on(inv_size * self.min_w_pmos, PCH, 1)
        cap_eq = (drain_C_(inv_size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                  drain_C_(inv_size * g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def) +
                  gate_C(nsize, 0))

        timeconst = res_eq * cap_eq
        self.delay += horowitz(inputrise, timeconst, self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, FALL)
        temp_power += cap_eq * self.deviceType.Vdd * self.deviceType.Vdd

        self.transmitter.delay = self.delay
        self.transmitter.power.readOp.dynamic = temp_power * 2
        self.transmitter.power.readOp.leakage = self.deviceType.Vdd * (
                    4 * cmos_Isub_leakage(g_tp.min_w_nmos_, self.min_w_pmos, 2, nand) +
                    4 * cmos_Isub_leakage(g_tp.min_w_nmos_, self.min_w_pmos, 1, inv))
        self.transmitter.power.readOp.gate_leakage = self.deviceType.Vdd * (
                    4 * cmos_Ig_leakage(g_tp.min_w_nmos_, self.min_w_pmos, 2, nand) +
                    4 * cmos_Ig_leakage(g_tp.min_w_nmos_, self.min_w_pmos, 1, inv))

        inputrise = self.delay / self.deviceType.Vth

        cap_eq = cwire + drain_C_(nsize, NCH, 1, 1, g_tp.cell_h_def) * 2 + self.nsense * self.sense_amp_input_cap()
        timeconst = (tr_R_on(nsize, NCH, 1) * RES_ADJ) * (cwire + drain_C_(nsize, NCH, 1, 1, g_tp.cell_h_def) * 2) + rwire * cwire / 2 + (
                    tr_R_on(nsize, NCH, 1) * RES_ADJ + rwire) * self.nsense * self.sense_amp_input_cap()

        self.delay += horowitz(inputrise, timeconst, self.deviceType.Vth / self.deviceType.Vdd, 0.25, 0)
        VOL_SWING = 0.1
        temp_power += cap_eq * VOL_SWING * 0.400
        temp_power *= 2

        self.l_wire.delay = self.delay - self.transmitter.delay
        self.l_wire.power.readOp.dynamic = temp_power - self.transmitter.power.readOp.dynamic
        self.l_wire.power.readOp.leakage = self.deviceType.Vdd * (4 * cmos_Isub_leakage(nsize, 0, 1, nmos))
        self.l_wire.power.readOp.gate_leakage = self.deviceType.Vdd * (4 * cmos_Ig_leakage(nsize, 0, 1, nmos))

        self.delay += g_tp.sense_delay

        self.sense_amp.delay = g_tp.sense_delay
        self.out_rise_time = g_tp.sense_delay / self.deviceType.Vth
        self.sense_amp.power.readOp.dynamic = g_tp.sense_dy_power
        self.sense_amp.power.readOp.leakage = 0
        self.sense_amp.power.readOp.gate_leakage = 0

        self.power.readOp.dynamic = temp_power + self.sense_amp.power.readOp.dynamic
        self.power.readOp.leakage = self.transmitter.power.readOp.leakage + self.l_wire.power.readOp.leakage + self.sense_amp.power.readOp.leakage
        self.power.readOp.gate_leakage = self.transmitter.power.readOp.gate_leakage + self.l_wire.power.readOp.gate_leakage + self.sense_amp.power.readOp.gate_leakage

    def sense_amp_input_cap(self):
        return (drain_C_(g_tp.w_iso, PCH, 1, 1, g_tp.cell_h_def) +
                gate_C(g_tp.w_sense_en + g_tp.w_sense_n, 0) +
                drain_C_(g_tp.w_sense_n, NCH, 1, 1, g_tp.cell_h_def) +
                drain_C_(g_tp.w_sense_p, PCH, 1, 1, g_tp.cell_h_def))

    def delay_optimal_wire(self):
        len = self.wire_length
        beta = pmos_to_nmos_sz_ratio()
        switching = 0
        short_ckt = 0
        tc = 0
        input_cap = gate_C(g_tp.min_w_nmos_ + self.min_w_pmos, 0)
        out_cap = (drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                   drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def))
        out_res = (tr_R_on(g_tp.min_w_nmos_, NCH, 1) +
                   tr_R_on(self.min_w_pmos, PCH, 1)) / 2
        wr = self.wire_res(len)
        wc = self.wire_cap(len)
        repeater_scaling = sp.sqrt(out_res * wc / (wr * input_cap))
        self.repeater_spacing = sp.sqrt(2 * out_res * (out_cap + input_cap) /
                                          ((wr / len) * (wc / len)))
        self.repeater_size = repeater_scaling
        switching = (repeater_scaling * (input_cap + out_cap) +
                     self.repeater_spacing * (wc / len)) * self.deviceType.Vdd * self.deviceType.Vdd
        tc = (out_res * (input_cap + out_cap) +
              out_res * wc / len * self.repeater_spacing / repeater_scaling +
              wr / len * self.repeater_spacing * input_cap * repeater_scaling +
              0.5 * (wr / len) * (wc / len) * self.repeater_spacing * self.repeater_spacing)
        self.delay = 0.693 * tc * len / self.repeater_spacing
        Ishort_ckt = 65e-6
        short_ckt = (self.deviceType.Vdd * g_tp.min_w_nmos_ * Ishort_ckt * 1.0986 *
                     repeater_scaling * tc)
        self.area.set_area((len / self.repeater_spacing) *
                           compute_gate_area(INV, 1, self.min_w_pmos * repeater_scaling,
                                             g_tp.min_w_nmos_ * repeater_scaling, g_tp.cell_h_def))
        self.power.readOp.dynamic = (len / self.repeater_spacing) * (switching + short_ckt)
        self.power.readOp.leakage = ((len / self.repeater_spacing) *
                                     self.deviceType.Vdd *
                                     cmos_Isub_leakage(g_tp.min_w_nmos_ * repeater_scaling,
                                                       beta * g_tp.min_w_nmos_ * repeater_scaling, 1, inv))
        self.power.readOp.gate_leakage = ((len / self.repeater_spacing) *
                                          self.deviceType.Vdd *
                                          cmos_Ig_leakage(g_tp.min_w_nmos_ * repeater_scaling,
                                                          beta * g_tp.min_w_nmos_ * repeater_scaling, 1, inv))

    def init_wire(self):
        self.wire_length = 1
        self.delay_optimal_wire()
        sp = self.repeater_spacing * 1e6
        si = self.repeater_size
        self.repeated_wire.append(Component())
        for j in range(int(sp), int(4 * sp), 100):
            for i in range(int(si), 1, -1):
                pow = self.wire_model(j * 1e-6, i)
                if j == sp and i == si:
                    self.global_comp.delay = self.delay
                    self.global_comp.power = pow
                    self.global_comp.area.h = si
                    self.global_comp.area.w = sp * 1e-6
                self.repeated_wire[-1].delay = self.delay
                self.repeated_wire[-1].power.readOp = pow.readOp
                self.repeated_wire[-1].area.w = j * 1e-6
                self.repeated_wire[-1].area.h = i
                self.repeated_wire.append(Component())
        self.repeated_wire.pop()
        self.update_fullswing()
        l_wire = Wire(Low_swing, 0.001, 1)
        self.low_swing.delay = l_wire.delay
        self.low_swing.power = l_wire.power
        del l_wire

    def update_fullswing(self):
        del_values = [self.global_comp.delay * (1 + 0.3), self.global_comp.delay * (1 + 0.2),
                      self.global_comp.delay * (1 + 0.1), self.global_comp.delay * (1 + 0.05)]
        i = 4
        while i > 0:
            threshold = del_values[i - 1]
            cost = BIGNUM
            for component in self.repeated_wire:
                if component.delay > threshold:
                    self.repeated_wire.remove(component)
                else:
                    ncost = (component.power.readOp.dynamic / self.global_comp.power.readOp.dynamic +
                             component.power.readOp.leakage / self.global_comp.power.readOp.leakage)
                    if ncost < cost:
                        cost = ncost
                        if i == 4:
                            self.global_30 = component
                        elif i == 3:
                            self.global_20 = component
                        elif i == 2:
                            self.global_10 = component
                        elif i == 1:
                            self.global_5 = component
            i -= 1

    def wire_model(self, space, size):
        len = 1
        beta = pmos_to_nmos_sz_ratio()
        switching = 0
        short_ckt = 0
        tc = 0
        input_cap = gate_C(g_tp.min_w_nmos_ + self.min_w_pmos, 0)
        out_cap = (drain_C_(self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
                   drain_C_(g_tp.min_w_nmos_, NCH, 1, 1, g_tp.cell_h_def))
        out_res = (tr_R_on(g_tp.min_w_nmos_, NCH, 1) +
                   tr_R_on(self.min_w_pmos, PCH, 1)) / 2
        wr = self.wire_res(len)
        wc = self.wire_cap(len)
        self.repeater_spacing = space
        self.repeater_size = size
        switching = (self.repeater_size * (input_cap + out_cap) +
                     self.repeater_spacing * (wc / len)) * self.deviceType.Vdd * self.deviceType.Vdd
        tc = (out_res * (input_cap + out_cap) +
              out_res * wc / len * self.repeater_spacing / self.repeater_size +
              wr / len * self.repeater_spacing * out_cap * self.repeater_size +
              0.5 * (wr / len) * (wc / len) * self.repeater_spacing * self.repeater_spacing)
        self.delay = 0.693 * tc * len / self.repeater_spacing
        Ishort_ckt = 65e-6
        short_ckt = (self.deviceType.Vdd * g_tp.min_w_nmos_ * Ishort_ckt * 1.0986 *
                     self.repeater_size * tc)
        ptemp = PowerDef()
        ptemp.readOp.dynamic = ((len / self.repeater_spacing) * (switching + short_ckt))
        ptemp.readOp.leakage = ((len / self.repeater_spacing) *
                                self.deviceType.Vdd *
                                cmos_Isub_leakage(g_tp.min_w_nmos_ * self.repeater_size,
                                                  beta * g_tp.min_w_nmos_ * self.repeater_size, 1, inv))
        ptemp.readOp.gate_leakage = ((len / self.repeater_spacing) *
                                     self.deviceType.Vdd *
                                     cmos_Ig_leakage(g_tp.min_w_nmos_ * self.repeater_size,
                                                     beta * g_tp.min_w_nmos_ * self.repeater_size, 1, inv))
        return ptemp

    def print_wire(self):
        print("\nWire Properties:\n\n")
        print(f"  Delay Optimal\n\tRepeater size - {self.global_comp.area.h} "
              f"\n\tRepeater spacing - {self.global_comp.area.w * 1e3} (mm)"
              f"\n\tDelay - {self.global_comp.delay * 1e6} (ns/mm)"
              f"\n\tPowerD - {self.global_comp.power.readOp.dynamic * 1e6} (nJ/mm)"
              f"\n\tPowerL - {self.global_comp.power.readOp.leakage} (mW/mm)"
              f"\n\tPowerLgate - {self.global_comp.power.readOp.gate_leakage} (mW/mm)\n")
        print(f"\tWire width - {self.wire_width_init * 1e6} microns\n")
        print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        print(f"  5% Overhead\n\tRepeater size - {self.global_5.area.h} "
              f"\n\tRepeater spacing - {self.global_5.area.w * 1e3} (mm)"
              f"\n\tDelay - {self.global_5.delay * 1e6} (ns/mm)"
              f"\n\tPowerD - {self.global_5.power.readOp.dynamic * 1e6} (nJ/mm)"
              f"\n\tPowerL - {self.global_5.power.readOp.leakage} (mW/mm)"
              f"\n\tPowerLgate - {self.global_5.power.readOp.gate_leakage} (mW/mm)\n")
        print(f"\tWire width - {self.wire_width_init * 1e6} microns\n")
        print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        print(f"  10% Overhead\n\tRepeater size - {self.global_10.area.h} "
              f"\n\tRepeater spacing - {self.global_10.area.w * 1e3} (mm)"
              f"\n\tDelay - {self.global_10.delay * 1e6} (ns/mm)"
              f"\n\tPowerD - {self.global_10.power.readOp.dynamic * 1e6} (nJ/mm)"
              f"\n\tPowerL - {self.global_10.power.readOp.leakage} (mW/mm)"
              f"\n\tPowerLgate - {self.global_10.power.readOp.gate_leakage} (mW/mm)\n")
        print(f"\tWire width - {self.wire_width_init * 1e6} microns\n")
        print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        print(f"  20% Overhead\n\tRepeater size - {self.global_20.area.h} "
              f"\n\tRepeater spacing - {self.global_20.area.w * 1e3} (mm)"
              f"\n\tDelay - {self.global_20.delay * 1e6} (ns/mm)"
              f"\n\tPowerD - {self.global_20.power.readOp.dynamic * 1e6} (nJ/mm)"
              f"\n\tPowerL - {self.global_20.power.readOp.leakage} (mW/mm)"
              f"\n\tPowerLgate - {self.global_20.power.readOp.gate_leakage} (mW/mm)\n")
        print(f"\tWire width - {self.wire_width_init * 1e6} microns\n")
        print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        print(f"  30% Overhead\n\tRepeater size - {self.global_30.area.h} "
              f"\n\tRepeater spacing - {self.global_30.area.w * 1e3} (mm)"
              f"\n\tDelay - {self.global_30.delay * 1e6} (ns/mm)"
              f"\n\tPowerD - {self.global_30.power.readOp.dynamic * 1e6} (nJ/mm)"
              f"\n\tPowerL - {self.global_30.power.readOp.leakage} (mW/mm)"
              f"\n\tPowerLgate - {self.global_30.power.readOp.gate_leakage} (mW/mm)\n")
        print(f"\tWire width - {self.wire_width_init * 1e6} microns\n")
        print(f"\tWire spacing - {self.wire_spacing_init * 1e6} microns\n")

        print("  Low-swing wire (1 mm) - Note: Unlike repeated wires, \n\tdelay and power "
              "values of low-swing wires do not\n\thave a linear relationship with length."
              f" \n\tdelay - {self.low_swing.delay * 1e9} (ns)"
              f" \n\tpowerD - {self.low_swing.power.readOp.dynamic * 1e9} (nJ)"
              f" \n\tPowerL - {self.low_swing.power.readOp.leakage} (mW)"
              f" \n\tPowerLgate - {self.low_swing.power.readOp.gate_leakage} (mW)\n")
        print(f"\tWire width - {self.wire_width_init * 2} microns\n")
        print(f"\tWire spacing - {self.wire_spacing_init * 2} microns\n")
        print()



