import math
from .component import *
from .parameter import g_tp
from .parameter import *
from .const import MAX_NUMBER_GATES_STAGE


class TSV(Component):
    def __init__(self, tsv_type, dt=None):
        if dt is None:
            dt = g_tp.peri_global
        self.deviceType = dt
        self.tsv_type = tsv_type
        
        self.num_gates = 1
        self.num_gates_min = 1
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * g_tp.min_w_nmos_
        
        if tsv_type == 'Fine':
            self.cap = g_tp.tsv_parasitic_capacitance_fine
            self.res = g_tp.tsv_parasitic_resistance_fine
            self.min_area = g_tp.tsv_minimum_area_fine
        elif tsv_type == 'Coarse':
            self.cap = g_tp.tsv_parasitic_capacitance_coarse
            self.res = g_tp.tsv_parasitic_resistance_coarse
            self.min_area = g_tp.tsv_minimum_area_coarse
        else:
            self.cap = 0
            self.res = 0
            self.min_area = 0

        self.w_TSV_n = [0] * MAX_NUMBER_GATES_STAGE
        self.w_TSV_p = [0] * MAX_NUMBER_GATES_STAGE

        first_buf_stg_coef = 5  # To tune the total buffer delay.
        self.w_TSV_n[0] = g_tp.min_w_nmos_ * first_buf_stg_coef
        self.w_TSV_p[0] = self.min_w_pmos * first_buf_stg_coef

        self.is_dram = 0
        self.is_wl_tr = 0

        self.compute_buffer_stage()
        self.compute_area()
        self.compute_delay()

    def compute_buffer_stage(self):
        p_to_n_sz_ratio = self.deviceType.n_to_p_eff_curr_drv_ratio
        self.C_load_TSV = self.cap + gate_C(g_tp.min_w_nmos_ + self.min_w_pmos, 0)

        if g_ip.print_detail_debug:
            print(f"The input cap of 1st buffer: {gate_C(self.w_TSV_n[0] + self.w_TSV_p[0], 0) * 1e15} fF")
        
        F = self.C_load_TSV / gate_C(self.w_TSV_n[0] + self.w_TSV_p[0], 0)

        if g_ip.print_detail_debug:
            print(f"F is {F}")
        
        self.num_gates = logical_effort(
            self.num_gates_min, 1, F,
            self.w_TSV_n, self.w_TSV_p,
            self.C_load_TSV, p_to_n_sz_ratio,
            self.is_dram, self.is_wl_tr,
            g_tp.max_w_nmos_
        )

    def compute_area(self):
        Vdd = self.deviceType.Vdd
        cumulative_area = 0
        cumulative_curr = 0
        cumulative_curr_Ig = 0
        self.Buffer_area = Area()
        self.Buffer_area.h = g_tp.cell_h_def

        for i in range(self.num_gates):
            cumulative_area += compute_gate_area(INV, 1, self.w_TSV_p[i], self.w_TSV_n[i], self.Buffer_area.h)
            if g_ip.print_detail_debug:
                print(f"\n\tArea up to the {i+1} stages is: {cumulative_area} um2")
            cumulative_curr += cmos_Isub_leakage(self.w_TSV_n[i], self.w_TSV_p[i], 1, inv, self.is_dram)
            cumulative_curr_Ig += cmos_Ig_leakage(self.w_TSV_n[i], self.w_TSV_p[i], 1, inv, self.is_dram)
        
        self.power = PowerDef()
        self.power.readOp.leakage = cumulative_curr * Vdd
        self.power.readOp.gate_leakage = cumulative_curr_Ig * Vdd

        self.Buffer_area.set_area(cumulative_area)
        self.Buffer_area.w = cumulative_area / self.Buffer_area.h

        self.TSV_metal_area = Area()
        self.TSV_metal_area.set_area(self.min_area * 3.1416 / 16)

        if self.Buffer_area.get_area() < self.min_area - self.TSV_metal_area.get_area():
            self.area.set_area(self.min_area)
        else:
            self.area.set_area(self.Buffer_area.get_area() + self.TSV_metal_area.get_area())

    def compute_delay(self):
        rd = tr_R_on(self.w_TSV_n[0], NCH, 1, self.is_dram, False, self.is_wl_tr)
        c_load = gate_C(self.w_TSV_n[1] + self.w_TSV_p[1], 0.0, self.is_dram, False, self.is_wl_tr)
        c_intrinsic = drain_C_(self.w_TSV_p[0], PCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr) + \
                      drain_C_(self.w_TSV_n[0], NCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr)
        tf = rd * (c_intrinsic + c_load)
        self.delay = horowitz(0, tf, 0.5, 0.5, RISE)
        inrisetime = self.delay / (1.0 - 0.5)

        Vdd = self.deviceType.Vdd
        self.power.readOp.dynamic = (c_load + c_intrinsic) * Vdd * Vdd

        for i in range(1, self.num_gates - 1):
            rd = tr_R_on(self.w_TSV_n[i], NCH, 1, self.is_dram, False, self.is_wl_tr)
            c_load = gate_C(self.w_TSV_p[i + 1] + self.w_TSV_n[i + 1], 0.0, self.is_dram, False, self.is_wl_tr)
            c_intrinsic = drain_C_(self.w_TSV_p[i], PCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr) + \
                          drain_C_(self.w_TSV_n[i], NCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr)
            tf = rd * (c_intrinsic + c_load)
            self.delay += horowitz(inrisetime, tf, 0.5, 0.5, RISE)
            inrisetime = self.delay / (1.0 - 0.5)
            self.power.readOp.dynamic += (c_load + c_intrinsic) * Vdd * Vdd

        i = self.num_gates - 1
        c_load = self.C_load_TSV
        rd = tr_R_on(self.w_TSV_n[i], NCH, 1, self.is_dram, False, self.is_wl_tr)
        c_intrinsic = drain_C_(self.w_TSV_p[i], PCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr) + \
                      drain_C_(self.w_TSV_n[i], NCH, 1, 1, self.area.h, self.is_dram, False, self.is_wl_tr)
        R_TSV_out = self.res
        tf = rd * (c_intrinsic + c_load) + R_TSV_out * c_load / 2
        self.delay += horowitz(inrisetime, tf, 0.5, 0.5, RISE)
        self.power.readOp.dynamic += (c_load + c_intrinsic) * Vdd * Vdd

    def print_TSV(self):
        print(f"\nTSV Properties:\n\n")
        print(f"  Delay Optimal - ")
        print(f" \n\tTSV Cap: {self.cap * 1e15} fF")
        print(f" \n\tTSV Res: {self.res * 1e3} mOhm")
        print(f" \n\tNumber of Buffer Chain stages - {self.num_gates}")
        print(f" \n\tDelay - {self.delay * 1e9} (ns)")
        print(f" \n\tPowerD - {self.power.readOp.dynamic * 1e9} (nJ)")
        print(f" \n\tPowerL - {self.power.readOp.leakage * 1e3} (mW)")
        print(f" \n\tPowerLgate - {self.power.readOp.gate_leakage * 1e3} (mW)\n")
        print(f" \n\tBuffer  Area: {self.Buffer_area.get_area()} um2")
        print(f" \n\tBuffer Height: {self.Buffer_area.h} um")
        print(f" \n\tBuffer Width: {self.Buffer_area.w} um")
        print(f" \n\tTSV metal area: {self.TSV_metal_area.get_area()} um2")
        print(f" \n\tTSV minimum occupied area: {self.min_area} um2")
        print(f" \n\tTotal area: {self.area.get_area()} um2")
        print(f"\n")