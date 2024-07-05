import math
import re
from const import *
from cacti_interface import InputParameter
import sympy as sp

sympy_var = {
    'C_g_ideal': sp.symbols('C_g_ideal'),
    'C_fringe': sp.symbols('C_fringe'),
    'C_junc': sp.symbols('C_junc'),
    'C_junc_sw': sp.symbols('C_junc_sw'),
    'l_phy': sp.symbols('l_phy'),
    'l_elec': sp.symbols('l_elec'),
    'nmos_effective_resistance_multiplier': sp.symbols('nmos_effective_resistance_multiplier'),
    'Vdd': sp.symbols('Vdd'),
    'Vth': sp.symbols('Vth'),
    'Vdsat': sp.symbols('Vdsat'),
    'I_on_n': sp.symbols('I_on_n'),
    'I_on_p': sp.symbols('I_on_p'),
    'I_off_n': sp.symbols('I_off_n'),
    'I_g_on_n': sp.symbols('I_g_on_n'),
    'C_ox': sp.symbols('C_ox'),
    't_ox': sp.symbols('t_ox'),
    'n2p_drv_rt': sp.symbols('n2p_drv_rt'),
    'lch_lk_rdc': sp.symbols('lch_lk_rdc'),
    'Mobility_n': sp.symbols('Mobility_n'),
    'gmp_to_gmn_multiplier': sp.symbols('gmp_to_gmn_multiplier'),
    'vpp': sp.symbols('vpp'),
    'Wmemcella': sp.symbols('Wmemcella'),
    'Wmemcellpmos': sp.symbols('Wmemcellpmos'),
    'Wmemcellnmos': sp.symbols('Wmemcellnmos'),
    'area_cell': sp.symbols('area_cell'),
    'asp_ratio_cell': sp.symbols('asp_ratio_cell'),
    'vdd_cell': sp.symbols('vdd_cell'),
    'dram_cell_I_on': sp.symbols('dram_cell_I_on'),
    'dram_cell_Vdd': sp.symbols('dram_cell_Vdd'),
    'dram_cell_C': sp.symbols('dram_cell_C'),
    'dram_cell_I_off_worst_case_len_temp': sp.symbols('dram_cell_I_off_worst_case_len_temp'),
    'logic_scaling_co_eff': sp.symbols('logic_scaling_co_eff'),
    'core_tx_density': sp.symbols('core_tx_density'),
    'sckt_co_eff': sp.symbols('sckt_co_eff'),
    'chip_layout_overhead': sp.symbols('chip_layout_overhead'),
    'macro_layout_overhead': sp.symbols('macro_layout_overhead'),
    'sense_delay': sp.symbols('sense_delay'),
    'sense_dy_power': sp.symbols('sense_dy_power'),
    'wire_pitch': sp.symbols('wire_pitch'),
    'barrier_thickness': sp.symbols('barrier_thickness'),
    'dishing_thickness': sp.symbols('dishing_thickness'),
    'alpha_scatter': sp.symbols('alpha_scatter'),
    'aspect_ratio': sp.symbols('aspect_ratio'),
    'miller_value': sp.symbols('miller_value'),
    'horiz_dielectric_constant': sp.symbols('horiz_dielectric_constant'),
    'vert_dielectric_constant': sp.symbols('vert_dielectric_constant'),
    'ild_thickness': sp.symbols('ild_thickness'),
    'fringe_cap': sp.symbols('fringe_cap'),
    'resistivity': sp.symbols('resistivity'),
    'wire_r_per_micron': sp.symbols('wire_r_per_micron'),
    'wire_c_per_micron': sp.symbols('wire_c_per_micron'),
    'tsv_pitch': sp.symbols('tsv_pitch'),
    'tsv_diameter': sp.symbols('tsv_diameter'),
    'tsv_length': sp.symbols('tsv_length'),
    'tsv_dielec_thickness': sp.symbols('tsv_dielec_thickness'),
    'tsv_contact_resistance': sp.symbols('tsv_contact_resistance'),
    'tsv_depletion_width': sp.symbols('tsv_depletion_width'),
    'tsv_liner_dielectric_cons': sp.symbols('tsv_liner_dielectric_cons')
}

class TechnologyParameter:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ram_wl_stitching_overhead_ = 0
        self.min_w_nmos_ = 0
        self.max_w_nmos_ = 0
        self.max_w_nmos_dec = 0
        self.unit_len_wire_del = 0
        self.FO4 = 0
        self.kinv = 0
        self.vpp = 0
        self.w_sense_en = 0
        self.w_sense_n = 0
        self.w_sense_p = 0
        self.sense_delay = 0
        self.sense_dy_power = 0
        self.w_iso = 0
        self.w_poly_contact = 0
        self.spacing_poly_to_poly = 0
        self.spacing_poly_to_contact = 0
        self.tsv_pitch = 0
        self.tsv_diameter = 0
        self.tsv_length = 0
        self.tsv_dielec_thickness = 0
        self.tsv_contact_resistance = 0
        self.tsv_depletion_width = 0
        self.tsv_liner_dielectric_constant = 0
        self.tsv_parasitic_capacitance_fine = 0
        self.tsv_parasitic_resistance_fine = 0
        self.tsv_minimum_area_fine = 0
        self.tsv_parasitic_capacitance_coarse = 0
        self.tsv_parasitic_resistance_coarse = 0
        self.tsv_minimum_area_coarse = 0
        self.w_comp_inv_p1 = 0
        self.w_comp_inv_p2 = 0
        self.w_comp_inv_p3 = 0
        self.w_comp_inv_n1 = 0
        self.w_comp_inv_n2 = 0
        self.w_comp_inv_n3 = 0
        self.w_eval_inv_p = 0
        self.w_eval_inv_n = 0
        self.w_comp_n = 0
        self.w_comp_p = 0
        self.dram_cell_I_on = 0
        self.dram_cell_Vdd = 0
        self.dram_cell_I_off_worst_case_len_temp = 0
        self.dram_cell_C = 0
        self.gm_sense_amp_latch = 0
        self.w_nmos_b_mux = 0
        self.w_nmos_sa_mux = 0
        self.w_pmos_bl_precharge = 0
        self.w_pmos_bl_eq = 0
        self.MIN_GAP_BET_P_AND_N_DIFFS = 0
        self.MIN_GAP_BET_SAME_TYPE_DIFFS = 0
        self.HPOWERRAIL = 0
        self.cell_h_def = 0
        self.chip_layout_overhead = 0
        self.macro_layout_overhead = 0
        self.sckt_co_eff = 0
        self.fringe_cap = 0
        self.h_dec = 0
        self.sram_cell = DeviceType()
        self.dram_acc = DeviceType()
        self.dram_wl = DeviceType()
        self.peri_global = DeviceType()
        self.cam_cell = DeviceType()
        self.sleep_tx = DeviceType()
        self.wire_local = InterconnectType()
        self.wire_inside_mat = InterconnectType()
        self.wire_outside_mat = InterconnectType()
        self.scaling_factor = ScalingFactor()
        self.sram = MemoryType()
        self.dram = MemoryType()
        self.cam = MemoryType()

    def init_symbolic():
        return

    def find_upper_and_lower_tech(self, technology, tech_lo, in_file_lo, tech_hi, in_file_hi):
        print(technology)
        if 179 < technology < 181:
            tech_lo = 180
            in_file_lo = "tech_params/180nm.dat"
            tech_hi = 180
            in_file_hi = "tech_params/180nm.dat"
        elif 89 < technology < 91:
            tech_lo = 90
            in_file_lo = "tech_params/90nm.dat"
            tech_hi = 90
            in_file_hi = "tech_params/90nm.dat"
        elif 64 < technology < 66:
            tech_lo = 65
            in_file_lo = "tech_params/65nm.dat"
            tech_hi = 65
            in_file_hi = "tech_params/65nm.dat"
        elif 44 < technology < 46:
            tech_lo = 45
            in_file_lo = "tech_params/45nm.dat"
            tech_hi = 45
            in_file_hi = "tech_params/45nm.dat"
        elif 31 < technology < 33:
            tech_lo = 32
            in_file_lo = "tech_params/32nm.dat"
            tech_hi = 32
            in_file_hi = "tech_params/32nm.dat"
        elif 21 < technology < 23:
            tech_lo = 22
            in_file_lo = "tech_params/22nm.dat"
            tech_hi = 22
            in_file_hi = "tech_params/22nm.dat"
        elif 90 < technology < 180:
            tech_lo = 180
            in_file_lo = "tech_params/180nm.dat"
            tech_hi = 90
            in_file_hi = "tech_params/90nm.dat"
        elif 65 < technology < 90:
            tech_lo = 90
            in_file_lo = "tech_params/90nm.dat"
            tech_hi = 65
            in_file_hi = "tech_params/65nm.dat"
        elif 45 < technology < 65:
            tech_lo = 65
            in_file_lo = "tech_params/65nm.dat"
            tech_hi = 45
            in_file_hi = "tech_params/45nm.dat"
        elif 32 < technology < 45:
            tech_lo = 45
            in_file_lo = "tech_params/45nm.dat"
            tech_hi = 32
            in_file_hi = "tech_params/32nm.dat"
        elif 22 < technology < 32:
            tech_lo = 32
            in_file_lo = "tech_params/32nm.dat"
            tech_hi = 22
            in_file_hi = "tech_params/22nm.dat"
        else:
            print("Invalid technology nodes")
            exit(0)

        return tech_lo, in_file_lo, tech_hi, in_file_hi

    def assign_tsv(self, in_file):
        for iter in range(2):  # 0:fine 1:coarse
            tsv_type = g_ip.tsv_is_subarray_type if iter == 0 else g_ip.tsv_os_bank_type
            with open(in_file, "r") as fp:
                lines = fp.readlines()

            self.tsv_pitch = sympy_var['tsv_pitch']
            self.tsv_diameter = sympy_var['tsv_diameter']
            self.tsv_length = sympy_var['tsv_length']
            self.tsv_dielec_thickness = sympy_var['tsv_dielec_thickness']
            self.tsv_contact_resistance = sympy_var['tsv_contact_resistance']
            self.tsv_depletion_width = sympy_var['tsv_depletion_width']
            self.tsv_liner_dielectric_constant = sympy_var['tsv_liner_dielectric_cons']

            # for line in lines:
            #     if line.startswith("-tsv_pitch"):
            #         self.tsv_pitch = scan_input_double_tsv_type(line, "-tsv_pitch", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_diameter"):
            #         self.tsv_diameter = scan_input_double_tsv_type(line, "-tsv_diameter", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_length"):
            #         self.tsv_length = scan_input_double_tsv_type(line, "-tsv_length", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_dielec_thickness"):
            #         self.tsv_dielec_thickness = scan_input_double_tsv_type(line, "-tsv_dielec_thickness", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_contact_resistance"):
            #         self.tsv_contact_resistance = scan_input_double_tsv_type(line, "-tsv_contact_resistance", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_depletion_width"):
            #         self.tsv_depletion_width = scan_input_double_tsv_type(line, "-tsv_depletion_width", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            #     elif line.startswith("-tsv_liner_dielectric_cons"):
            #         self.tsv_liner_dielectric_constant = scan_input_double_tsv_type(line, "-tsv_liner_dielectric_cons", "F/um", g_ip.ic_proj_type, tsv_type, g_ip.print_detail_debug)
            
            self.tsv_length *= g_ip.num_die_3d
            if iter == 0:
                self.tsv_parasitic_resistance_fine = tsv_resistance(BULK_CU_RESISTIVITY, self.tsv_length, self.tsv_diameter, self.tsv_contact_resistance)
                self.tsv_parasitic_capacitance_fine = tsv_capacitance(self.tsv_length, self.tsv_diameter, self.tsv_pitch, self.tsv_dielec_thickness, self.tsv_liner_dielectric_constant, self.tsv_depletion_width)
                self.tsv_minimum_area_fine = tsv_area(self.tsv_pitch)
            else:
                self.tsv_parasitic_resistance_coarse = tsv_resistance(BULK_CU_RESISTIVITY, self.tsv_length, self.tsv_diameter, self.tsv_contact_resistance)
                self.tsv_parasitic_capacitance_coarse = tsv_capacitance(self.tsv_length, self.tsv_diameter, self.tsv_pitch, self.tsv_dielec_thickness, self.tsv_liner_dielectric_constant, self.tsv_depletion_width)
                self.tsv_minimum_area_coarse = tsv_area(self.tsv_pitch)

    def init(self, technology, is_tag):
        self.reset()
        ram_cell_tech_type = g_ip.tag_arr_ram_cell_tech_type if is_tag else g_ip.data_arr_ram_cell_tech_type
        peri_global_tech_type = g_ip.tag_arr_peri_global_tech_type if is_tag else g_ip.data_arr_peri_global_tech_type
        tech_lo, tech_hi = 0, 0
        in_file_lo, in_file_hi = "", ""

        technology *= 1000.0  # in the unit of nm

        tech_lo, in_file_lo, tech_hi, in_file_hi = self.find_upper_and_lower_tech(technology, tech_lo, in_file_lo, tech_hi, in_file_hi)

        if (tech_lo == 22) and (tech_hi == 22):
            if ram_cell_tech_type == 3:
                print("current version does not support eDRAM technologies at 22nm")
                exit(0)

        alpha = 1 if tech_lo == tech_hi else (technology - tech_hi) / (tech_lo - tech_hi)
        print(in_file_lo)
        with open(in_file_lo, "r") as fp:
            lines = fp.readlines()

        self.dram_cell_I_on = 0
        self.dram_cell_Vdd = 0
        self.dram_cell_C = 0
        self.dram_cell_I_off_worst_case_len_temp = 0
        self.vpp = 0
        self.macro_layout_overhead = 0
        self.chip_layout_overhead = 0
        self.sckt_co_eff = 0

        self.dram_cell_I_on = sympy_var['dram_cell_I_on']
        self.dram_cell_Vdd = sympy_var['dram_cell_Vdd']
        self.dram_cell_C = sympy_var['dram_cell_C']
        self.dram_cell_I_off_worst_case_len_temp = sympy_var['dram_cell_I_off_worst_case_len_temp']
        self.vpp = sympy_var['vpp']
        self.sckt_co_eff = sympy_var['sckt_co_eff']
        self.chip_layout_overhead = sympy_var['chip_layout_overhead']
        self.macro_layout_overhead = sympy_var['macro_layout_overhead']

        # for line in lines:
        #     if line.startswith("-dram_cell_I_on"):
        #         self.dram_cell_I_on += alpha * scan_five_input_double(line, "-dram_cell_I_on", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_Vdd"):
        #         self.dram_cell_Vdd += alpha * scan_five_input_double(line, "-dram_cell_Vdd", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_C"):
        #         self.dram_cell_C += alpha * scan_five_input_double(line, "-dram_cell_C", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_I_off_worst_case_len_temp"):
        #         self.dram_cell_I_off_worst_case_len_temp += alpha * scan_five_input_double(line, "-dram_cell_I_off_worst_case_len_temp", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-vpp"):
        #         self.vpp += alpha * scan_five_input_double(line, "-vpp", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-sckt_co_eff"):
        #         self.sckt_co_eff += alpha * scan_single_input_double(line, "-sckt_co_eff", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-chip_layout_overhead"):
        #         self.chip_layout_overhead += alpha * scan_single_input_double(line, "-chip_layout_overhead", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-macro_layout_overhead"):
        #         self.macro_layout_overhead += alpha * scan_single_input_double(line, "-macro_layout_overhead", "F/um", g_ip.print_detail_debug)

        peri_global_lo = DeviceType()
        peri_global_hi = DeviceType()
        peri_global_lo.assign(in_file_lo, peri_global_tech_type, g_ip.temp)
        print("peri lo")
        peri_global_lo.display()
        print()
        peri_global_hi.assign(in_file_hi, peri_global_tech_type, g_ip.temp)
        print("peri hi")
        peri_global_hi.display()
        print()
        
        self.peri_global.interpolate(alpha, peri_global_lo, peri_global_hi)
        print("peri_global")
        self.peri_global.display()
        print()

        sleep_tx_lo = DeviceType()
        sleep_tx_hi = DeviceType()
        sleep_tx_lo.assign(in_file_lo, 1, g_ip.temp)
        sleep_tx_hi.assign(in_file_hi, 1, g_ip.temp)
        self.sleep_tx.interpolate(alpha, sleep_tx_lo, sleep_tx_hi)

        sram_cell_lo = DeviceType()
        sram_cell_hi = DeviceType()
        sram_cell_lo.assign(in_file_lo, ram_cell_tech_type, g_ip.temp)
        sram_cell_hi.assign(in_file_hi, ram_cell_tech_type, g_ip.temp)
        self.sram_cell.interpolate(alpha, sram_cell_lo, sram_cell_hi)

        dram_acc_lo = DeviceType()
        dram_acc_hi = DeviceType()
        dram_acc_lo.assign(in_file_lo, ram_cell_tech_type if ram_cell_tech_type == comm_dram else dram_cell_tech_flavor, g_ip.temp)
        dram_acc_hi.assign(in_file_hi, ram_cell_tech_type if ram_cell_tech_type == comm_dram else dram_cell_tech_flavor, g_ip.temp)
        self.dram_acc.interpolate(alpha, dram_acc_lo, dram_acc_hi)
        if tech_lo <= 22:
            pass
        elif tech_lo <= 32:
            self.dram_acc.Vth = 0.44129 if ram_cell_tech_type == lp_dram else 1.0
        elif tech_lo <= 45:
            self.dram_acc.Vth = 0.44559 if ram_cell_tech_type == lp_dram else 1.0
        elif tech_lo <= 65:
            self.dram_acc.Vth = 0.43806 if ram_cell_tech_type == lp_dram else 1.0
        elif tech_lo <= 90:
            self.dram_acc.Vth = 0.4545 if ram_cell_tech_type == lp_dram else 1.0

        self.dram_acc.Vdd = 0.0
        self.dram_acc.I_on_p = 0.0
        self.dram_acc.I_off_n = 0.0
        self.dram_acc.I_off_p = 0.0
        self.dram_acc.C_ox = 0.0
        self.dram_acc.t_ox = 0.0
        self.dram_acc.n_to_p_eff_curr_drv_ratio = 0.0

        dram_wl_lo = DeviceType()
        dram_wl_hi = DeviceType()
        dram_wl_lo.assign(in_file_lo, ram_cell_tech_type if ram_cell_tech_type == comm_dram else dram_cell_tech_flavor, g_ip.temp)
        dram_wl_hi.assign(in_file_hi, ram_cell_tech_type if ram_cell_tech_type == comm_dram else dram_cell_tech_flavor, g_ip.temp)
        self.dram_wl.interpolate(alpha, dram_wl_lo, dram_wl_hi)

        self.dram_wl.Vdd = 0.0
        self.dram_wl.Vth = 0.0
        self.dram_wl.I_on_p = 0.0
        self.dram_wl.C_ox = 0.0
        self.dram_wl.t_ox = 0.0

        if ram_cell_tech_type < 3:
            self.dram_acc.reset()
            self.dram_wl.reset()

        cam_cell_lo = DeviceType()
        cam_cell_hi = DeviceType()
        cam_cell_lo.assign(in_file_lo, ram_cell_tech_type, g_ip.temp)
        cam_cell_hi.assign(in_file_hi, ram_cell_tech_type, g_ip.temp)
        self.cam_cell.interpolate(alpha, cam_cell_lo, cam_cell_hi)

        dram_lo = MemoryType()
        dram_hi = MemoryType()
        dram_lo.assign(in_file_lo, ram_cell_tech_type, 2)  # cell_type = dram(2)
        dram_hi.assign(in_file_hi, ram_cell_tech_type, 2)
        self.dram.interpolate(alpha, dram_lo, dram_hi)

        sram_lo = MemoryType()
        sram_hi = MemoryType()
        sram_lo.assign(in_file_lo, ram_cell_tech_type, 0)  # cell_type = sram(0)
        sram_hi.assign(in_file_hi, ram_cell_tech_type, 0)
        self.sram.interpolate(alpha, sram_lo, sram_hi)

        cam_lo = MemoryType()
        cam_hi = MemoryType()
        cam_lo.assign(in_file_lo, ram_cell_tech_type, 1)  # cell_type = sram(0)
        cam_hi.assign(in_file_hi, ram_cell_tech_type, 1)
        self.cam.interpolate(alpha, cam_lo, cam_hi)

        scaling_factor_lo = ScalingFactor()
        scaling_factor_hi = ScalingFactor()
        scaling_factor_lo.assign(in_file_lo)
        scaling_factor_hi.assign(in_file_hi)
        self.scaling_factor.interpolate(alpha, scaling_factor_lo, scaling_factor_hi)

        self.peri_global.Vcc_min += (alpha * peri_global_lo.Vdd + (1 - alpha) * peri_global_hi.Vdd) * 0.35
        self.sleep_tx.Vcc_min += alpha * sleep_tx_lo.Vdd + (1 - alpha) * sleep_tx_hi.Vdd
        self.sram_cell.Vcc_min += (alpha * sram_cell_lo.Vdd + (1 - alpha) * sram_cell_hi.Vdd) * 0.65

        with open(in_file_hi, "r") as fp:
            lines = fp.readlines()

        self.sense_delay = sympy_var['sense_delay']
        self.sense_dy_power = sympy_var['sense_dy_power']
        self.sckt_co_eff = sympy_var['sckt_co_eff']
        self.chip_layout_overhead = sympy_var['chip_layout_overhead']
        self.macro_layout_overhead = sympy_var['macro_layout_overhead']
        self.dram_cell_I_on = sympy_var['dram_cell_I_on']
        self.dram_cell_Vdd = sympy_var['dram_cell_Vdd']
        self.dram_cell_C = sympy_var['dram_cell_C']
        self.dram_cell_I_off_worst_case_len_temp = sympy_var['dram_cell_I_off_worst_case_len_temp']
        self.vpp = sympy_var['vpp']

        # for line in lines:
        #     if line.startswith("-sense_delay"):
        #         self.sense_delay = scan_single_input_double(line, "-sense_delay", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-sense_dy_power"):
        #         self.sense_dy_power = scan_single_input_double(line, "-sense_dy_power", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-sckt_co_eff"):
        #         self.sckt_co_eff += (1 - alpha) * scan_single_input_double(line, "-sckt_co_eff", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-chip_layout_overhead"):
        #         self.chip_layout_overhead += (1 - alpha) * scan_single_input_double(line, "-chip_layout_overhead", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-macro_layout_overhead"):
        #         self.macro_layout_overhead += (1 - alpha) * scan_single_input_double(line, "-macro_layout_overhead", "F/um", g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_I_on"):
        #         self.dram_cell_I_on += (1 - alpha) * scan_five_input_double(line, "-dram_cell_I_on", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_Vdd"):
        #         self.dram_cell_Vdd += (1 - alpha) * scan_five_input_double(line, "-dram_cell_Vdd", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_C"):
        #         self.dram_cell_C += (1 - alpha) * scan_five_input_double(line, "-dram_cell_C", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-dram_cell_I_off_worst_case_len_temp"):
        #         self.dram_cell_I_off_worst_case_len_temp += (1 - alpha) * scan_five_input_double(line, "-dram_cell_I_off_worst_case_len_temp", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)
        #     elif line.startswith("-vpp"):
        #         self.vpp += (1 - alpha) * scan_five_input_double(line, "-vpp", "F/um", ram_cell_tech_type, g_ip.print_detail_debug)

        self.w_comp_inv_p1 = 12.5 * g_ip.F_sz_um
        self.w_comp_inv_n1 = 7.5 * g_ip.F_sz_um
        self.w_comp_inv_p2 = 25 * g_ip.F_sz_um
        self.w_comp_inv_n2 = 15 * g_ip.F_sz_um
        self.w_comp_inv_p3 = 50 * g_ip.F_sz_um
        self.w_comp_inv_n3 = 30 * g_ip.F_sz_um
        self.w_eval_inv_p = 100 * g_ip.F_sz_um
        self.w_eval_inv_n = 50 * g_ip.F_sz_um
        self.w_comp_n = 12.5 * g_ip.F_sz_um
        self.w_comp_p = 37.5 * g_ip.F_sz_um
        self.MIN_GAP_BET_P_AND_N_DIFFS = 5 * g_ip.F_sz_um
        self.MIN_GAP_BET_SAME_TYPE_DIFFS = 1.5 * g_ip.F_sz_um
        self.HPOWERRAIL = 2 * g_ip.F_sz_um
        self.cell_h_def = 50 * g_ip.F_sz_um
        self.w_poly_contact = g_ip.F_sz_um
        self.spacing_poly_to_contact = g_ip.F_sz_um
        self.spacing_poly_to_poly = 1.5 * g_ip.F_sz_um
        self.ram_wl_stitching_overhead_ = 7.5 * g_ip.F_sz_um
        self.min_w_nmos_ = 3 * g_ip.F_sz_um / 2
        self.max_w_nmos_ = 100 * g_ip.F_sz_um
        self.w_iso = 12.5 * g_ip.F_sz_um
        self.w_sense_n = 3.75 * g_ip.F_sz_um
        self.w_sense_p = 7.5 * g_ip.F_sz_um
        self.w_sense_en = 5 * g_ip.F_sz_um
        self.w_nmos_b_mux = 6 * self.min_w_nmos_
        self.w_nmos_sa_mux = 6 * self.min_w_nmos_
        self.w_pmos_bl_precharge = 6 * pmos_to_nmos_sz_ratio() * self.min_w_nmos_
        self.w_pmos_bl_eq = pmos_to_nmos_sz_ratio() * self.min_w_nmos_

        if ram_cell_tech_type == comm_dram:
            self.max_w_nmos_dec = 8 * g_ip.F_sz_um
            self.h_dec = 8  # in the unit of memory cell height
        else:
            self.max_w_nmos_dec = self.max_w_nmos_
            self.h_dec = 4  # in the unit of memory cell height

        #TODO CHECK 388 for 180nm
        print(self.peri_global.l_elec)
        gmn_sense_amp_latch = (self.peri_global.Mobility_n / 2) * self.peri_global.C_ox * (self.w_sense_n / self.peri_global.l_elec) * self.peri_global.Vdsat
        gmp_sense_amp_latch = self.peri_global.gmp_to_gmn_multiplier * gmn_sense_amp_latch
        self.gm_sense_amp_latch = gmn_sense_amp_latch + gmp_sense_amp_latch

        wire_local_lo = InterconnectType()
        wire_local_hi = InterconnectType()
        wire_local_lo.assign(in_file_lo, g_ip.ic_proj_type, 3 if ram_cell_tech_type == comm_dram else 0)
        wire_local_hi.assign(in_file_hi, g_ip.ic_proj_type, 3 if ram_cell_tech_type == comm_dram else 0)
        self.wire_local.interpolate(alpha, wire_local_lo, wire_local_hi)

        wire_inside_mat_lo = InterconnectType()
        wire_inside_mat_hi = InterconnectType()
        wire_inside_mat_lo.assign(in_file_lo, g_ip.ic_proj_type, g_ip.wire_is_mat_type)
        wire_inside_mat_hi.assign(in_file_hi, g_ip.ic_proj_type, g_ip.wire_is_mat_type)
        self.wire_inside_mat.interpolate(alpha, wire_inside_mat_lo, wire_inside_mat_hi)

        wire_outside_mat_lo = InterconnectType()
        wire_outside_mat_hi = InterconnectType()
        wire_outside_mat_lo.assign(in_file_lo, g_ip.ic_proj_type, g_ip.wire_os_mat_type)
        wire_outside_mat_hi.assign(in_file_hi, g_ip.ic_proj_type, g_ip.wire_os_mat_type)
        self.wire_outside_mat.interpolate(alpha, wire_outside_mat_lo, wire_outside_mat_hi)

        self.unit_len_wire_del = self.wire_inside_mat.R_per_um * self.wire_inside_mat.C_per_um / 2

        self.assign_tsv(in_file_hi)

        self.fringe_cap = wire_local_hi.fringe_cap

        rd = tr_R_on(self.min_w_nmos_, NCH, 1)
        p_to_n_sizing_r = pmos_to_nmos_sz_ratio()
        c_load = gate_C(self.min_w_nmos_ * (1 + p_to_n_sizing_r), 0.0)
        tf = rd * c_load
        self.kinv = horowitz(0, tf, 0.5, 0.5, RISE)
        KLOAD = 1
        c_load = KLOAD * (drain_C_(self.min_w_nmos_, NCH, 1, 1, self.cell_h_def) +
                          drain_C_(self.min_w_nmos_ * p_to_n_sizing_r, PCH, 1, 1, self.cell_h_def) +
                          gate_C(self.min_w_nmos_ * 4 * (1 + p_to_n_sizing_r), 0.0))
        tf = rd * c_load
        self.FO4 = horowitz(0, tf, 0.5, 0.5, RISE)

    def isEqual(self, tech):
        if not is_equal(self.ram_wl_stitching_overhead_, tech.ram_wl_stitching_overhead_):
            assert False  # fs
        if not is_equal(self.min_w_nmos_, tech.min_w_nmos_):
            assert False  # fs
        if not is_equal(self.max_w_nmos_, tech.max_w_nmos_):
            assert False  # fs
        if not is_equal(self.max_w_nmos_dec, tech.max_w_nmos_dec):
            assert False  # fs + ram_cell_tech_type
        if not is_equal(self.unit_len_wire_del, tech.unit_len_wire_del):
            assert False  # wire_inside_mat
        if not is_equal(self.FO4, tech.FO4):
            assert False  # fs
        if not is_equal(self.kinv, tech.kinv):
            assert False  # fs
        if not is_equal(self.vpp, tech.vpp):
            assert False  # input 
        if not is_equal(self.w_sense_en, tech.w_sense_en):
            assert False  # fs
        if not is_equal(self.w_sense_n, tech.w_sense_n):
            assert False  # fs
        if not is_equal(self.w_sense_p, tech.w_sense_p):
            assert False  # fs
        if not is_equal(self.sense_delay, tech.sense_delay):
            PRINT("sense_delay", self.sense_delay, tech)
            assert False  # input
        if not is_equal(self.sense_dy_power, tech.sense_dy_power):
            assert False  # input
        if not is_equal(self.w_iso, tech.w_iso):
            assert False  # fs
        if not is_equal(self.w_poly_contact, tech.w_poly_contact):
            assert False  # fs
        if not is_equal(self.spacing_poly_to_poly, tech.spacing_poly_to_poly):
            assert False  # fs
        if not is_equal(self.spacing_poly_to_contact, tech.spacing_poly_to_contact):
            assert False  # fs

        # CACTI3D auxiliary variables
        # if not is_equal(self.tsv_pitch, tech.tsv_pitch):
        #     assert False
        # if not is_equal(self.tsv_diameter, tech.tsv_diameter):
        #     assert False
        # if not is_equal(self.tsv_length, tech.tsv_length):
        #     assert False
        # if not is_equal(self.tsv_dielec_thickness, tech.tsv_dielec_thickness):
        #     assert False
        # if not is_equal(self.tsv_contact_resistance, tech.tsv_contact_resistance):
        #     assert False
        # if not is_equal(self.tsv_depletion_width, tech.tsv_depletion_width):
        #     assert False
        # if not is_equal(self.tsv_liner_dielectric_constant, tech.tsv_liner_dielectric_constant):
        #     assert False

        # CACTI3DD TSV params
        if not is_equal(self.tsv_parasitic_capacitance_fine, tech.tsv_parasitic_capacitance_fine):
            PRINT("tsv_parasitic_capacitance_fine", self.tsv_parasitic_capacitance_fine, tech)
            assert False
        if not is_equal(self.tsv_parasitic_resistance_fine, tech.tsv_parasitic_resistance_fine):
            assert False
        if not is_equal(self.tsv_minimum_area_fine, tech.tsv_minimum_area_fine):
            assert False

        if not is_equal(self.tsv_parasitic_capacitance_coarse, tech.tsv_parasitic_capacitance_coarse):
            assert False
        if not is_equal(self.tsv_parasitic_resistance_coarse, tech.tsv_parasitic_resistance_coarse):
            assert False
        if not is_equal(self.tsv_minimum_area_coarse, tech.tsv_minimum_area_coarse):
            assert False

        # fs
        if not is_equal(self.w_comp_inv_p1, tech.w_comp_inv_p1):
            assert False
        if not is_equal(self.w_comp_inv_p2, tech.w_comp_inv_p2):
            assert False
        if not is_equal(self.w_comp_inv_p3, tech.w_comp_inv_p3):
            assert False
        if not is_equal(self.w_comp_inv_n1, tech.w_comp_inv_n1):
            assert False
        if not is_equal(self.w_comp_inv_n2, tech.w_comp_inv_n2):
            assert False
        if not is_equal(self.w_comp_inv_n3, tech.w_comp_inv_n3):
            assert False
        if not is_equal(self.w_eval_inv_p, tech.w_eval_inv_p):
            assert False
        if not is_equal(self.w_eval_inv_n, tech.w_eval_inv_n):
            assert False
        if not is_equal(self.w_comp_n, tech.w_comp_n):
            assert False
        if not is_equal(self.w_comp_p, tech.w_comp_p):
            assert False

        if not is_equal(self.dram_cell_I_on, tech.dram_cell_I_on):
            assert False  # ram_cell_tech_type
        if not is_equal(self.dram_cell_Vdd, tech.dram_cell_Vdd):
            assert False
        if not is_equal(self.dram_cell_I_off_worst_case_len_temp, tech.dram_cell_I_off_worst_case_len_temp):
            assert False
        if not is_equal(self.dram_cell_C, tech.dram_cell_C):
            assert False
        if not is_equal(self.gm_sense_amp_latch, tech.gm_sense_amp_latch):
            assert False  # depends on many things

        if not is_equal(self.w_nmos_b_mux, tech.w_nmos_b_mux):
            assert False  # fs
        if not is_equal(self.w_nmos_sa_mux, tech.w_nmos_sa_mux):
            assert False  # fs
        if not is_equal(self.w_pmos_bl_precharge, tech.w_pmos_bl_precharge):
            PRINT("w_pmos_bl_precharge", self.w_pmos_bl_precharge, tech)
            assert False  # fs
        if not is_equal(self.w_pmos_bl_eq, tech.w_pmos_bl_eq):
            assert False  # fs
        if not is_equal(self.MIN_GAP_BET_P_AND_N_DIFFS, tech.MIN_GAP_BET_P_AND_N_DIFFS):
            assert False  # fs
        if not is_equal(self.MIN_GAP_BET_SAME_TYPE_DIFFS, tech.MIN_GAP_BET_SAME_TYPE_DIFFS):
            assert False  # fs
        if not is_equal(self.HPOWERRAIL, tech.HPOWERRAIL):
            assert False  # fs
        if not is_equal(self.cell_h_def, tech.cell_h_def):
            assert False  # fs

        if not is_equal(self.chip_layout_overhead, tech.chip_layout_overhead):
            assert False  # input
        if not is_equal(self.macro_layout_overhead, tech.macro_layout_overhead):
            print(f"{self.macro_layout_overhead} vs. {tech.macro_layout_overhead}")
            assert False
        if not is_equal(self.sckt_co_eff, tech.sckt_co_eff):
            assert False

        if not is_equal(self.fringe_cap, tech.fringe_cap):
            PRINT("fringe_cap", self.fringe_cap, tech)
            assert False  # input

        if self.h_dec != tech.h_dec:
            assert False  # ram_cell_tech_type

        print("sram_cell")
        self.sram_cell.isEqual(tech.sram_cell)  # SRAM cell transistor
        print("dram_acc")
        self.dram_acc.isEqual(tech.dram_acc)  # DRAM access transistor
        print("dram_wl")
        self.dram_wl.isEqual(tech.dram_wl)  # DRAM wordline transistor
        print("peri_global")
        self.peri_global.isEqual(tech.peri_global)  # peripheral global
        print("cam_cell")
        self.cam_cell.isEqual(tech.cam_cell)  # SRAM cell transistor

        print("sleep_tx")
        self.sleep_tx.isEqual(tech.sleep_tx)  # Sleep transistor cell transistor

        print("wire_local")
        self.wire_local.isEqual(tech.wire_local)
        print("wire_inside_mat")
        self.wire_inside_mat.isEqual(tech.wire_inside_mat)
        print("wire_outside_mat")
        self.wire_outside_mat.isEqual(tech.wire_outside_mat)

        print("scaling_factor")
        self.scaling_factor.isEqual(tech.scaling_factor)
        print("sram:")
        self.sram.isEqual(tech.sram)
        print("dram:")
        self.dram.isEqual(tech.dram)
        print("cam:")
        self.cam.isEqual(tech.cam)

        return True

def is_equal(first, second):
    if first == 0 and second == 0:
        return True

    if second == 0 or sp.isnan(second):
        return True

    if sp.isnan(first) or sp.isnan(second):
        return True

    if first == 0:
        if abs(first - second) < (second * 0.000001):
            return True
    else:
        if abs(first - second) < (first * 0.000001):
            return True

    return False

class DeviceType:
    def __init__(self):
        self.C_g_ideal = 0
        self.C_fringe = 0
        self.C_overlap = 0
        self.C_junc = 0  # C_junc_area
        self.C_junc_sidewall = 0
        self.l_phy = 0
        self.l_elec = 0
        self.R_nch_on = 0
        self.R_pch_on = 0
        self.Vdd = 0
        self.Vth = 0
        self.Vcc_min = 0  # allowed min vcc; for memory cell it is the lowest vcc for data retention. for logic it is the vcc to balance the leakage reduction and wakeup latency
        self.I_on_n = 0
        self.I_on_p = 0
        self.I_off_n = 0
        self.I_off_p = 0
        self.I_g_on_n = 0
        self.I_g_on_p = 0
        self.C_ox = 0
        self.t_ox = 0
        self.n_to_p_eff_curr_drv_ratio = 0
        self.long_channel_leakage_reduction = 0
        self.Mobility_n = 0

        # auxiliary parameters
        self.Vdsat = 0
        self.gmp_to_gmn_multiplier = 0

    def reset(self):
        self.C_g_ideal = 0
        self.C_fringe = 0
        self.C_overlap = 0
        self.C_junc = 0  # C_junc_area
        self.C_junc_sidewall = 0
        self.l_phy = 0
        self.l_elec = 0
        self.R_nch_on = 0
        self.R_pch_on = 0
        self.Vdd = 0
        self.Vth = 0
        self.Vcc_min = 0  # allowed min vcc; for memory cell it is the lowest vcc for data retention. for logic it is the vcc to balance the leakage reduction and wakeup latency
        self.I_on_n = 0
        self.I_on_p = 0
        self.I_off_n = 0
        self.I_off_p = 0
        self.I_g_on_n = 0
        self.I_g_on_p = 0
        self.C_ox = 0
        self.t_ox = 0
        self.n_to_p_eff_curr_drv_ratio = 0
        self.long_channel_leakage_reduction = 0
        self.Mobility_n = 0

        # auxiliary parameters
        self.Vdsat = 0
        self.gmp_to_gmn_multiplier = 0

    def display(self, indent=0):
        indent_str = ' ' * indent
        print(f"{indent_str}C_g_ideal = {self.C_g_ideal} F/um")
        print(f"{indent_str}C_fringe  = {self.C_fringe} F/um")
        print(f"{indent_str}C_overlap = {self.C_overlap} F/um")
        print(f"{indent_str}C_junc    = {self.C_junc} F/um^2")
        print(f"{indent_str}C_junc_sw = {self.C_junc_sidewall} F/um^2")
        print(f"{indent_str}l_phy     = {self.l_phy} um")
        print(f"{indent_str}l_elec    = {self.l_elec} um")
        print(f"{indent_str}R_nch_on  = {self.R_nch_on} ohm-um")
        print(f"{indent_str}R_pch_on  = {self.R_pch_on} ohm-um")
        print(f"{indent_str}Vdd       = {self.Vdd} V")
        print(f"{indent_str}Vth       = {self.Vth} V")
        print(f"{indent_str}I_on_n    = {self.I_on_n} A/um")
        print(f"{indent_str}I_on_p    = {self.I_on_p} A/um")
        print(f"{indent_str}I_off_n   = {self.I_off_n} A/um")
        print(f"{indent_str}I_off_p   = {self.I_off_p} A/um")
        print(f"{indent_str}C_ox      = {self.C_ox} F/um^2")
        print(f"{indent_str}t_ox      = {self.t_ox} um")
        print(f"{indent_str}n_to_p_eff_curr_drv_ratio = {self.n_to_p_eff_curr_drv_ratio}")

    def isEqual(self, dev):
        if not is_equal(self.C_g_ideal, dev.C_g_ideal): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_fringe, dev.C_fringe): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_overlap, dev.C_overlap): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_junc, dev.C_junc): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_junc_sidewall, dev.C_junc_sidewall): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.l_phy, dev.l_phy): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.l_elec, dev.l_elec): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.R_nch_on, dev.R_nch_on): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.R_pch_on, dev.R_pch_on): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.Vdd, dev.Vdd): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.Vth, dev.Vth): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_on_n, dev.I_on_n): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_on_p, dev.I_on_p): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_off_n, dev.I_off_n): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_off_p, dev.I_off_p): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_g_on_n, dev.I_g_on_n): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.I_g_on_p, dev.I_g_on_p): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.C_ox, dev.C_ox): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.t_ox, dev.t_ox): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.n_to_p_eff_curr_drv_ratio, dev.n_to_p_eff_curr_drv_ratio): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.long_channel_leakage_reduction, dev.long_channel_leakage_reduction): self.display(); print("\n\n\n"); dev.display(); assert False
        if not is_equal(self.Mobility_n, dev.Mobility_n): self.display(); print("\n\n\n"); dev.display(); assert False
        return True

    def assign(self, in_file, tech_flavor, temperature):
        with open(in_file, 'r') as fp:
            lines = fp.readlines()

        nmos_effective_resistance_multiplier = 0

        self.C_g_ideal = sympy_var['C_g_ideal']
        self.C_fringe = sympy_var['C_fringe']
        self.C_junc_sidewall = sympy_var['C_junc_sw']
        self.C_junc = sympy_var['C_junc']
        self.l_phy = sympy_var['l_phy']
        self.l_elec = sympy_var['l_elec']
        self.nmos_effective_resistance_multiplier = sympy_var['nmos_effective_resistance_multiplier']
        self.Vdd = sympy_var['Vdd']
        self.Vth = sympy_var['Vth']
        self.Vdsat = sympy_var['Vdsat']
        self.I_on_n = sympy_var['I_on_n']
        self.I_on_p = sympy_var['I_on_p']
        self.I_off_n = sympy_var['I_off_n']
        self.I_g_on_n = sympy_var['I_g_on_n']
        self.C_ox = sympy_var['C_ox']
        self.t_ox = sympy_var['t_ox']
        self.n_to_p_eff_curr_drv_ratio = sympy_var['n2p_drv_rt']
        self.long_channel_leakage_reduction = sympy_var['lch_lk_rdc']
        self.Mobility_n = sympy_var['Mobility_n']
        self.gmp_to_gmn_multiplier = sympy_var['gmp_to_gmn_multiplier']

        # for line in lines:
        #     if line.startswith("-C_g_ideal"):
        #         self.C_g_ideal = scan_five_input_double(line, "-C_g_ideal", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-C_fringe"):
        #         self.C_fringe = scan_five_input_double(line, "-C_fringe", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-C_junc_sw"):
        #         self.C_junc_sidewall = scan_five_input_double(line, "-C_junc_sw", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-C_junc"):
        #         self.C_junc = scan_five_input_double(line, "-C_junc", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-l_phy"):
        #         self.l_phy = scan_five_input_double(line, "-l_phy", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-l_elec"):
        #         print("HERE!")
        #         self.l_elec = scan_five_input_double(line, "-l_elec", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         print(self.l_elec)
        #         print()
        #         continue
        #     if line.startswith("-nmos_effective_resistance_multiplier"):
        #         nmos_effective_resistance_multiplier = scan_five_input_double(line, "-nmos_effective_resistance_multiplier", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-Vdd"):
        #         self.Vdd = scan_five_input_double(line, "-Vdd", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-Vth"):
        #         self.Vth = scan_five_input_double(line, "-Vth", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-Vdsat"):
        #         self.Vdsat = scan_five_input_double(line, "-Vdsat", "V", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-I_on_n"):
        #         self.I_on_n = scan_five_input_double(line, "-I_on_n", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-I_on_p"):
        #         self.I_on_p = scan_five_input_double(line, "-I_on_p", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-I_off_n"):
        #         scan_five_input_double_temperature(line, "-I_off_n", "F/um", tech_flavor, temperature, g_ip.print_detail_debug, self.I_off_n)
        #         continue
        #     if line.startswith("-I_g_on_n"):
        #         scan_five_input_double_temperature(line, "-I_g_on_n", "F/um", tech_flavor, temperature, g_ip.print_detail_debug, self.I_g_on_n)
        #         continue
        #     if line.startswith("-C_ox"):
        #         self.C_ox = scan_five_input_double(line, "-C_ox", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-t_ox"):
        #         self.t_ox = scan_five_input_double(line, "-t_ox", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-n2p_drv_rt"):
        #         self.n_to_p_eff_curr_drv_ratio = scan_five_input_double(line, "-n2p_drv_rt", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-lch_lk_rdc"):
        #         self.long_channel_leakage_reduction = scan_five_input_double(line, "-lch_lk_rdc", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-Mobility_n"):
        #         self.Mobility_n = scan_five_input_double(line, "-Mobility_n", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-gmp_to_gmn_multiplier"):
        #         self.gmp_to_gmn_multiplier = scan_five_input_double(line, "-gmp_to_gmn_multiplier", "F/um", tech_flavor, g_ip.print_detail_debug)
        #         continue

        self.C_overlap = 0.2 * self.C_g_ideal
        if tech_flavor >= 3:
            if(self.I_on_n):
                self.R_nch_on = nmos_effective_resistance_multiplier * g_tp.vpp / self.I_on_n
        else:
            if(self.I_on_n):
                self.R_nch_on = nmos_effective_resistance_multiplier * self.Vdd / self.I_on_n
        self.R_pch_on = self.n_to_p_eff_curr_drv_ratio * self.R_nch_on
        self.I_off_p = self.I_off_n
        self.I_g_on_p = self.I_g_on_n
        if g_ip.print_detail_debug:
            print(f"C_overlap: {self.C_overlap} F/um")
            print(f"R_nch_on: {self.R_nch_on} ohm-micron")
            print(f"R_pch_on: {self.R_pch_on} ohm-micron")

    def interpolate(self, alpha, dev1, dev2):
        result = DeviceType()
        self.C_g_ideal = alpha * dev1.C_g_ideal + (1 - alpha) * dev2.C_g_ideal
        print(f'GLOBAL result {self.C_g_ideal}')
        self.C_fringe = alpha * dev1.C_fringe + (1 - alpha) * dev2.C_fringe
        self.C_overlap = alpha * dev1.C_overlap + (1 - alpha) * dev2.C_overlap
        self.C_junc = alpha * dev1.C_junc + (1 - alpha) * dev2.C_junc
        self.l_phy = alpha * dev1.l_phy + (1 - alpha) * dev2.l_phy
        self.l_elec = alpha * dev1.l_elec + (1 - alpha) * dev2.l_elec
        self.R_nch_on = alpha * dev1.R_nch_on + (1 - alpha) * dev2.R_nch_on
        self.R_pch_on = alpha * dev1.R_pch_on + (1 - alpha) * dev2.R_pch_on
        self.Vdd = alpha * dev1.Vdd + (1 - alpha) * dev2.Vdd
        self.Vth = alpha * dev1.Vth + (1 - alpha) * dev2.Vth
        self.Vcc_min = alpha * dev1.Vcc_min + (1 - alpha) * dev2.Vcc_min
        self.I_on_n = alpha * dev1.I_on_n + (1 - alpha) * dev2.I_on_n
        self.I_on_p = alpha * dev1.I_on_p + (1 - alpha) * dev2.I_on_p
        self.I_off_n = alpha * dev1.I_off_n + (1 - alpha) * dev2.I_off_n
        self.I_off_p = alpha * dev1.I_off_p + (1 - alpha) * dev2.I_off_p
        self.I_g_on_n = alpha * dev1.I_g_on_n + (1 - alpha) * dev2.I_g_on_n
        self.I_g_on_p = alpha * dev1.I_g_on_p + (1 - alpha) * dev2.I_g_on_p
        self.C_ox = alpha * dev1.C_ox + (1 - alpha) * dev2.C_ox
        self.t_ox = alpha * dev1.t_ox + (1 - alpha) * dev2.t_ox
        self.n_to_p_eff_curr_drv_ratio = alpha * dev1.n_to_p_eff_curr_drv_ratio + (1 - alpha) * dev2.n_to_p_eff_curr_drv_ratio
        self.long_channel_leakage_reduction = alpha * dev1.long_channel_leakage_reduction + (1 - alpha) * dev2.long_channel_leakage_reduction
        self.Mobility_n = alpha * dev1.Mobility_n + (1 - alpha) * dev2.Mobility_n
        self.Vdsat = alpha * dev1.Vdsat + (1 - alpha) * dev2.Vdsat
        self.gmp_to_gmn_multiplier = alpha * dev1.gmp_to_gmn_multiplier + (1 - alpha) * dev2.gmp_to_gmn_multiplier
        self.C_junc_sidewall = dev1.C_junc_sidewall
    
class InterconnectType:
    def __init__(self):
        self.pitch = 0
        self.R_per_um = 0
        self.C_per_um = 0
        self.horiz_dielectric_constant = 0
        self.vert_dielectric_constant = 0
        self.aspect_ratio = 0
        self.miller_value = 0
        self.ild_thickness = 0

        # auxiliary parameters
        self.wire_width = 0
        self.wire_thickness = 0
        self.wire_spacing = 0
        self.barrier_thickness = 0
        self.dishing_thickness = 0
        self.alpha_scatter = 0
        self.fringe_cap = 0

        self.reset()

    def reset(self):
        self.pitch = 0
        self.R_per_um = 0
        self.C_per_um = 0
        self.horiz_dielectric_constant = 0
        self.vert_dielectric_constant = 0
        self.aspect_ratio = 0
        self.miller_value = 0
        self.ild_thickness = 0

        # auxiliary parameters
        self.wire_width = 0
        self.wire_thickness = 0
        self.wire_spacing = 0
        self.barrier_thickness = 0
        self.dishing_thickness = 0
        self.alpha_scatter = 0
        self.fringe_cap = 0

    def is_equal(self, inter):
        if not is_equal(self.pitch, inter.pitch): return False
        if not is_equal(self.R_per_um, inter.R_per_um): return False
        if not is_equal(self.C_per_um, inter.C_per_um): return False
        if not is_equal(self.horiz_dielectric_constant, inter.horiz_dielectric_constant): return False
        if not is_equal(self.vert_dielectric_constant, inter.vert_dielectric_constant): return False
        if not is_equal(self.aspect_ratio, inter.aspect_ratio): return False
        if not is_equal(self.miller_value, inter.miller_value): return False
        if not is_equal(self.ild_thickness, inter.ild_thickness): return False
        return True

    def display(self, indent=0):
        indent_str = ' ' * indent
        print(f"{indent_str}pitch = {self.pitch} um")
        print(f"{indent_str}R_per_um = {self.R_per_um} ohm/um")
        print(f"{indent_str}C_per_um = {self.C_per_um} F/um")
        print(f"{indent_str}horiz_dielectric_constant = {self.horiz_dielectric_constant}")
        print(f"{indent_str}vert_dielectric_constant = {self.vert_dielectric_constant}")
        print(f"{indent_str}aspect_ratio = {self.aspect_ratio}")
        print(f"{indent_str}miller_value = {self.miller_value}")
        print(f"{indent_str}ild_thickness = {self.ild_thickness} um")

    def assign(self, in_file, projection_type, tech_flavor):
        with open(in_file, 'r') as fp:
            lines = fp.readlines()

        resistivity = 0
        print_debug = g_ip.print_detail_debug

        self.pitch = sympy_var['wire_pitch']
        self.barrier_thickness = sympy_var['barrier_thickness']
        self.dishing_thickness = sympy_var['dishing_thickness']
        self.alpha_scatter = sympy_var['alpha_scatter']
        self.aspect_ratio = sympy_var['aspect_ratio']
        self.miller_value = sympy_var['miller_value']
        self.horiz_dielectric_constant = sympy_var['horiz_dielectric_constant']
        self.vert_dielectric_constant = sympy_var['vert_dielectric_constant']
        self.ild_thickness = sympy_var['ild_thickness']
        self.fringe_cap = sympy_var['fringe_cap']
        self.R_per_um = sympy_var['wire_r_per_micron']
        self.C_per_um = sympy_var['wire_c_per_micron']
        self.resistivity = sympy_var['resistivity']

        # for line in lines:
        #     if line.startswith("-wire_pitch"):
        #         self.pitch = scan_input_double_inter_type(line, "-wire_pitch", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-barrier_thickness"):
        #         self.barrier_thickness = scan_input_double_inter_type(line, "-barrier_thickness", "ohm", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-dishing_thickness"):
        #         self.dishing_thickness = scan_input_double_inter_type(line, "-dishing_thickness", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-alpha_scatter"):
        #         self.alpha_scatter = scan_input_double_inter_type(line, "-alpha_scatter", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-aspect_ratio"):
        #         self.aspect_ratio = scan_input_double_inter_type(line, "-aspect_ratio", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-miller_value"):
        #         self.miller_value = scan_input_double_inter_type(line, "-miller_value", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-horiz_dielectric_constant"):
        #         self.horiz_dielectric_constant = scan_input_double_inter_type(line, "-horiz_dielectric_constant", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-vert_dielectric_constant"):
        #         self.vert_dielectric_constant = scan_input_double_inter_type(line, "-vert_dielectric_constant", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-ild_thickness"):
        #         self.ild_thickness = scan_input_double_inter_type(line, "-ild_thickness", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-fringe_cap"):
        #         self.fringe_cap = scan_input_double_inter_type(line, "-fringe_cap", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-wire_r_per_micron"):
        #         self.R_per_um = scan_input_double_inter_type(line, "-wire_r_per_micron", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-wire_c_per_micron"):
        #         self.C_per_um = scan_input_double_inter_type(line, "-wire_c_per_micron", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue
        #     if line.startswith("-resistivity"):
        #         resistivity = scan_input_double_inter_type(line, "-resistivity", "um", g_ip.ic_proj_type, tech_flavor, print_debug)
        #         continue

        self.pitch *= g_ip.F_sz_um
        self.wire_width = self.pitch / 2  # micron
        self.wire_thickness = self.aspect_ratio * self.wire_width  # micron
        self.wire_spacing = self.pitch - self.wire_width  # micron

        if projection_type != 1 or tech_flavor != 3:
            self.R_per_um = wire_resistance(resistivity, self.wire_width,
                                            self.wire_thickness, self.barrier_thickness, self.dishing_thickness, self.alpha_scatter)  # ohm/micron
            if print_debug:
                print(f"{self.R_per_um} = wire_resistance({resistivity}, {self.wire_width}, {self.wire_thickness}, {self.barrier_thickness}, {self.dishing_thickness}, {self.alpha_scatter})")

            self.C_per_um = wire_capacitance(self.wire_width, self.wire_thickness, self.wire_spacing,
                                             self.ild_thickness, self.miller_value, self.horiz_dielectric_constant,
                                             self.vert_dielectric_constant, self.fringe_cap)  # F/micron
            if print_debug:
                print(f"{self.C_per_um} = wire_capacitance({self.wire_width}, {self.wire_thickness}, {self.wire_spacing}, {self.ild_thickness}, {self.miller_value}, {self.horiz_dielectric_constant}, {self.vert_dielectric_constant}, {self.fringe_cap})")

    def interpolate(self, alpha, inter1, inter2):
        self.pitch = alpha * inter1.pitch + (1 - alpha) * inter2.pitch
        self.R_per_um = alpha * inter1.R_per_um + (1 - alpha) * inter2.R_per_um
        self.C_per_um = alpha * inter1.C_per_um + (1 - alpha) * inter2.C_per_um
        self.horiz_dielectric_constant = alpha * inter1.horiz_dielectric_constant + (1 - alpha) * inter2.horiz_dielectric_constant
        self.vert_dielectric_constant = alpha * inter1.vert_dielectric_constant + (1 - alpha) * inter2.vert_dielectric_constant
        self.aspect_ratio = alpha * inter1.aspect_ratio + (1 - alpha) * inter2.aspect_ratio
        self.miller_value = alpha * inter1.miller_value + (1 - alpha) * inter2.miller_value
        self.ild_thickness = alpha * inter1.ild_thickness + (1 - alpha) * inter2.ild_thickness

class MemoryType:
    def __init__(self):
        self.reset()

    def reset(self):
        self.b_w = 0
        self.b_h = 0
        self.cell_a_w = 0
        self.cell_pmos_w = 0
        self.cell_nmos_w = 0
        self.Vbitpre = 0
        self.Vbitfloating = 0
        self.area_cell = 0
        self.asp_ratio_cell = 0

    def assign(self, in_file, tech_flavor, cell_type):
        try:
            with open(in_file, "r") as fp:
                lines = fp.readlines()
        except FileNotFoundError:
            print(f"{in_file} is missing!")
            exit(-1)

        vdd_cell = 0
        vdd = 0

        print(f'tech_flavor {tech_flavor}')

        vdd = sympy_var['Vdd']
        vdd_cell = sympy_var['vdd_cell']
        self.cell_a_w = sympy_var['Wmemcella']
        self.cell_pmos_w = sympy_var['Wmemcellpmos']
        self.cell_nmos_w = sympy_var['Wmemcellnmos']
        self.area_cell = sympy_var['area_cell']
        self.asp_ratio_cell = sympy_var['asp_ratio_cell']
        
        # for line in lines:
        #     if line.startswith("-Vdd"):
        #         vdd = scan_five_input_double(line, "-Vdd", "V", tech_flavor, g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-vdd_cell"):
        #         scan_res = scan_five_input_double_mem_type(line, "-vdd_cell", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         vdd_cell = scan_res if scan_res != None else vdd_cell
        #         continue
        #     if line.startswith("-Wmemcella"):
        #         scan_res = scan_five_input_double_mem_type(line, "-Wmemcella", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.cell_a_w = scan_res if scan_res != None else self.cell_a_w
        #         continue
        #     if line.startswith("-Wmemcellpmos"):
        #         scan_res = scan_five_input_double_mem_type(line, "-Wmemcellpmos", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.cell_pmos_w = scan_res if scan_res != None else self.cell_pmos_w
        #         continue
        #     if line.startswith("-Wmemcellnmos"):
        #         scan_res = scan_five_input_double_mem_type(line, "-Wmemcellnmos", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.cell_nmos_w = scan_res if scan_res != None else self.cell_nmos_w
        #         continue
        #     if line.startswith("-area_cell"):
        #         scan_res = scan_five_input_double_mem_type(line, "-area_cell", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.area_cell = scan_res if scan_res != None else self.area_cell
        #         continue
        #     if line.startswith("-asp_ratio_cell"):
        #         scan_res = scan_five_input_double_mem_type(line, "-asp_ratio_cell", "V", tech_flavor, cell_type, g_ip.print_detail_debug)
        #         self.asp_ratio_cell = scan_res if scan_res != None else self.asp_ratio_cell
        #         continue

        # print(g_ip.F_sz_um)
        # print(self.cell_pmos_w)
        if cell_type != 2:
            print(self.cell_a_w)
            self.cell_a_w *= g_ip.F_sz_um
        self.cell_pmos_w *= g_ip.F_sz_um
        self.cell_nmos_w *= g_ip.F_sz_um
        if cell_type != 2:
            self.area_cell *= (g_ip.F_sz_um * g_ip.F_sz_um)

        #TODO 1028-1030
        self.b_w = sp.sqrt(self.area_cell / self.asp_ratio_cell)
        self.b_h = self.asp_ratio_cell * self.b_w
        if cell_type == 2:
            self.Vbitpre = vdd_cell
        else:
            self.Vbitpre = vdd

        self.Vbitfloating = self.Vbitpre * 0.7

    def interpolate(self, alpha, mem1, mem2):
        self.cell_a_w = alpha * mem1.cell_a_w + (1 - alpha) * mem2.cell_a_w
        self.cell_pmos_w = alpha * mem1.cell_pmos_w + (1 - alpha) * mem2.cell_pmos_w
        self.cell_nmos_w = alpha * mem1.cell_nmos_w + (1 - alpha) * mem2.cell_nmos_w
        self.area_cell = alpha * mem1.area_cell + (1 - alpha) * mem2.area_cell
        self.asp_ratio_cell = alpha * mem1.asp_ratio_cell + (1 - alpha) * mem2.asp_ratio_cell
        self.Vbitpre = mem2.Vbitpre
        self.Vbitfloating = self.Vbitpre * 0.7

        #TODO 1028-1030
        self.b_w = sp.sqrt(self.area_cell / self.asp_ratio_cell)
        self.b_h = self.asp_ratio_cell * self.b_w

    def isEqual(self, mem):
        if not self.is_equal(self.b_w, mem.b_w): return False
        if not self.is_equal(self.b_h, mem.b_h): return False
        if not self.is_equal(self.cell_a_w, mem.cell_a_w): return False
        if not self.is_equal(self.cell_pmos_w, mem.cell_pmos_w): return False
        if not self.is_equal(self.cell_nmos_w, mem.cell_nmos_w): return False
        if not self.is_equal(self.Vbitpre, mem.Vbitpre): return False
        return True

    def is_equal(self, first, second):
        if (first == 0) and (second == 0):
            return True
        if (second == 0) or (second != second):
            return True
        if (first != first) or (second != second):  # both are NaNs
            return True
        if first == 0:
            if abs(first - second) < (second * 0.000001):
                return True
        else:
            if abs(first - second) < (first * 0.000001):
                return True
        return False

    def scan_five_input_double(self, line, name, unit_name, flavor, print_flag):
        temp = [0] * 5
        unit = ''

        pattern = re.compile(rf"{name}\s+(\S+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)")
        match = pattern.search(line)
        print(f'{line},  {match}')

        if match:
            unit = match.group(1)
            temp[0] = float(match.group(2))
            temp[1] = float(match.group(3))
            temp[2] = float(match.group(4))
            temp[3] = float(match.group(5))
            temp[4] = float(match.group(6))

            if print_flag:
                print(f"{name}[{flavor}]: {temp[flavor]} {unit}")
            return temp[flavor]
        return None

class ScalingFactor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.logic_scaling_co_eff = 0
        self.core_tx_density = 0
        self.long_channel_leakage_reduction = 0

    def assign(self, in_file):
        try:
            with open(in_file, "r") as fp:
                lines = fp.readlines()
        except FileNotFoundError:
            print(f"{in_file} is missing!")
            exit(-1)

        self.logic_scaling_co_eff = sympy_var['logic_scaling_co_eff']
        self.core_tx_density = sympy_var['core_tx_density']

        # for line in lines:
        #     if line.startswith("-logic_scaling_co_eff"):
        #         self.logic_scaling_co_eff = scan_single_input_double(line, "-logic_scaling_co_eff", "F/um", g_ip.print_detail_debug)
        #         continue
        #     if line.startswith("-core_tx_density"):
        #         self.core_tx_density = scan_single_input_double(line, "-core_tx_density", "F/um", g_ip.print_detail_debug)
        #         continue

    def interpolate(self, alpha, dev1, dev2):
        self.logic_scaling_co_eff = alpha * dev1.logic_scaling_co_eff + (1 - alpha) * dev2.logic_scaling_co_eff
        self.core_tx_density = alpha * dev1.core_tx_density + (1 - alpha) * dev2.core_tx_density

    def isEqual(self, scal):
        if not is_equal(self.logic_scaling_co_eff, scal.logic_scaling_co_eff):
            self.display(0)
            assert False
        if not is_equal(self.core_tx_density, scal.core_tx_density):
            self.display(0)
            assert False
        if not is_equal(self.long_channel_leakage_reduction, scal.long_channel_leakage_reduction):
            self.display(0)
            assert False
        return True

    def display(self, indent=0):
        indent_str = ' ' * indent
        print(f"{indent_str}logic_scaling_co_eff = {self.logic_scaling_co_eff}")
        print(f"{indent_str}core_tx_density = {self.core_tx_density}")
        print(f"{indent_str}long_channel_leakage_reduction = {self.long_channel_leakage_reduction}")

class Area:
    h: float = 0.0
    w: float = 0.0

class DynamicParameter:
    def __init__(self, is_tag_=False, pure_ram_=0, pure_cam_=0, Nspd_=1.0, Ndwl_=1, Ndbl_=1, Ndcm_=1, Ndsam_lev_1_=1, Ndsam_lev_2_=1, wt=None, is_main_mem_=False):
        self.is_tag = is_tag_
        self.pure_ram = pure_ram_
        self.pure_cam = pure_cam_
        self.fully_assoc = False
        self.tagbits = 0
        self.num_subarrays = 0
        self.num_mats = 0
        self.Nspd = Nspd_
        self.Ndwl = Ndwl_
        self.Ndbl = Ndbl_
        self.Ndcm = Ndcm_
        self.deg_bl_muxing = 0
        self.deg_senseamp_muxing_non_associativity = 0
        self.Ndsam_lev_1 = Ndsam_lev_1_
        self.Ndsam_lev_2 = Ndsam_lev_2_
        self.wtype = wt
        self.number_addr_bits_mat = 0
        self.number_subbanks_decode = 0
        self.num_di_b_bank_per_port = 0
        self.num_do_b_bank_per_port = 0
        self.num_di_b_mat = 0
        self.num_do_b_mat = 0
        self.num_di_b_subbank = 0
        self.num_do_b_subbank = 0
        self.num_si_b_mat = 0
        self.num_so_b_mat = 0
        self.num_si_b_subbank = 0
        self.num_so_b_subbank = 0
        self.num_si_b_bank_per_port = 0
        self.num_so_b_bank_per_port = 0
        self.number_way_select_signals_mat = 0
        self.num_act_mats_hor_dir = 0
        self.num_act_mats_hor_dir_sl = 0
        self.is_dram = False
        self.V_b_sense = 0.0
        self.num_r_subarray = 0
        self.num_c_subarray = 0
        self.tag_num_r_subarray = 0
        self.tag_num_c_subarray = 0
        self.data_num_r_subarray = 0
        self.data_num_c_subarray = 0
        self.num_mats_h_dir = 0
        self.num_mats_v_dir = 0
        self.ram_cell_tech_type = 0
        self.dram_refresh_period = 0.0
        self.use_inp_params = 0
        self.num_rw_ports = 0
        self.num_rd_ports = 0
        self.num_wr_ports = 0
        self.num_se_rd_ports = 0
        self.num_search_ports = 0
        self.out_w = 0
        self.is_main_mem = is_main_mem_
        self.cell = Area()
        self.cam_cell = Area()
        self.is_valid = False
        self.init_parameters()

    def init_parameters(self):
        if self.is_tag:
            self.ram_cell_tech_type = g_ip.tag_arr_ram_cell_tech_type
        else:
            self.ram_cell_tech_type = g_ip.data_arr_ram_cell_tech_type
        
        self.is_dram = (self.ram_cell_tech_type == lp_dram or self.ram_cell_tech_type == comm_dram)
        self.fully_assoc = bool(g_ip.fully_assoc)
        capacity_per_die = g_ip.cache_sz / NUMBER_STACKED_DIE_LAYERS
        wire_local = g_tp.wire_local
        
        if self.pure_cam:
            self.init_CAM()
            return

        if self.fully_assoc:
            self.init_FA()
            return

        if not self.calc_subarr_rc(capacity_per_die):
            return

        if self.is_tag:
            self.cell.h = g_tp.sram.b_h + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports)
            self.cell.w = g_tp.sram.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_wr_ports + (g_ip.num_rd_ports - g_ip.num_se_rd_ports)) + wire_local.pitch * g_ip.num_se_rd_ports
        else:
            if self.is_dram:
                self.cell.h = g_tp.dram.b_h
                self.cell.w = g_tp.dram.b_w
            else:
                self.cell.h = g_tp.sram.b_h + 2 * wire_local.pitch * (g_ip.num_wr_ports + g_ip.num_rw_ports - 1 + g_ip.num_rd_ports)
                self.cell.w = g_tp.sram.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + (g_ip.num_rd_ports - g_ip.num_se_rd_ports) + g_ip.num_wr_ports) + g_tp.wire_local.pitch * g_ip.num_se_rd_ports

        c_b_metal = self.cell.h * wire_local.C_per_um

        if self.is_dram:
            self.deg_bl_muxing = 1
            if self.ram_cell_tech_type == comm_dram:
                Cbitrow_drain_cap = drain_C_(g_tp.dram.cell_a_w, NCH, 1, 0, self.cell.w, True, True) / 2.0
                C_bl = self.num_r_subarray * (Cbitrow_drain_cap + c_b_metal)
                self.V_b_sense = (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_C / (g_tp.dram_cell_C + C_bl)
                if self.V_b_sense < VBITSENSEMIN and not (g_ip.is_3d_mem and g_ip.force_cache_config):
                    return
                self.dram_refresh_period = 64e-3
            else:
                Cbitrow_drain_cap = drain_C_(g_tp.dram.cell_a_w, NCH, 1, 0, self.cell.w, True, True) / 2.0
                C_bl = self.num_r_subarray * (Cbitrow_drain_cap + c_b_metal)
                self.V_b_sense = (g_tp.dram_cell_Vdd / 2) * g_tp.dram_cell_C / (g_tp.dram_cell_C + C_bl)
                if self.V_b_sense < VBITSENSEMIN:
                    return
                self.V_b_sense = VBITSENSEMIN
                self.dram_refresh_period = 0.9 * g_tp.dram_cell_C * VDD_STORAGE_LOSS_FRACTION_WORST * g_tp.dram_cell_Vdd / g_tp.dram_cell_I_off_worst_case_len_temp
        else:
            self.V_b_sense = max(0.05 * g_tp.sram_cell.Vdd, VBITSENSEMIN)
            self.deg_bl_muxing = self.Ndcm
            Cbitrow_drain_cap = drain_C_(g_tp.sram.cell_a_w, NCH, 1, 0, self.cell.w, False, True) / 2.0
            C_bl = self.num_r_subarray * (Cbitrow_drain_cap + c_b_metal)
            self.dram_refresh_period = 0

        self.num_mats_h_dir = max(self.Ndwl // 2, 1)
        self.num_mats_v_dir = max(self.Ndbl // 2, 1)
        self.num_mats = self.num_mats_h_dir * self.num_mats_v_dir
        self.num_do_b_mat = max((self.num_subarrays / self.num_mats) * self.num_c_subarray / (self.deg_bl_muxing * self.Ndsam_lev_1 * self.Ndsam_lev_2), 1)

        if not (self.fully_assoc or self.pure_cam) and self.num_do_b_mat < (self.num_subarrays / self.num_mats):
            return

        if not self.is_tag:
            if self.is_main_mem:
                self.num_do_b_subbank = g_ip.int_prefetch_w * g_ip.out_w
                if g_ip.is_3d_mem:
                    self.num_do_b_subbank = g_ip.page_sz_bits
                deg_sa_mux_l1_non_assoc = self.Ndsam_lev_1
            else:
                if g_ip.fast_access:
                    self.num_do_b_subbank = g_ip.out_w * g_ip.data_assoc
                    deg_sa_mux_l1_non_assoc = self.Ndsam_lev_1
                else:
                    self.num_do_b_subbank = g_ip.out_w
                    deg_sa_mux_l1_non_assoc = self.Ndsam_lev_1 / g_ip.data_assoc
                    if deg_sa_mux_l1_non_assoc < 1:
                        return
        else:
            self.num_do_b_subbank = self.tagbits * g_ip.tag_assoc
            if self.num_do_b_mat < self.tagbits:
                return
            deg_sa_mux_l1_non_assoc = self.Ndsam_lev_1

        self.deg_senseamp_muxing_non_associativity = deg_sa_mux_l1_non_assoc
        self.num_act_mats_hor_dir = self.num_do_b_subbank // self.num_do_b_mat
        if g_ip.is_3d_mem and self.num_act_mats_hor_dir == 0:
            self.num_act_mats_hor_dir = 1
        if self.num_act_mats_hor_dir == 0:
            return

        if self.is_tag:
            if not (self.fully_assoc or self.pure_cam):
                self.num_do_b_mat = g_ip.tag_assoc // self.num_act_mats_hor_dir
                self.num_do_b_subbank = self.num_act_mats_hor_dir * self.num_do_b_mat

        if (not g_ip.is_cache and self.is_main_mem) or (PAGE_MODE == 1 and self.is_dram):
            if self.num_act_mats_hor_dir * self.num_do_b_mat * self.Ndsam_lev_1 * self.Ndsam_lev_2 != int(g_ip.page_sz_bits):
                return

        if (not self.is_tag) and (g_ip.is_main_mem) and (self.num_act_mats_hor_dir * self.num_do_b_mat * self.Ndsam_lev_1 * self.Ndsam_lev_2 < int(g_ip.out_w * g_ip.burst_len * g_ip.data_assoc)):
            return

        if self.num_act_mats_hor_dir > self.num_mats_h_dir:
            return

        if not self.is_tag:
            if g_ip.fast_access:
                self.num_di_b_mat = self.num_do_b_mat // g_ip.data_assoc
            else:
                self.num_di_b_mat = self.num_do_b_mat
        else:
            self.num_di_b_mat = self.tagbits

        self.num_di_b_subbank = self.num_di_b_mat * self.num_act_mats_hor_dir
        self.num_si_b_subbank = self.num_si_b_mat

        num_addr_b_row_dec = _log2(self.num_r_subarray)
        if self.fully_assoc or self.pure_cam:
            num_addr_b_row_dec += _log2(self.num_subarrays // self.num_mats)
        number_subbanks = self.num_mats // self.num_act_mats_hor_dir
        self.number_subbanks_decode = _log2(number_subbanks)

        self.num_rw_ports = g_ip.num_rw_ports
        self.num_rd_ports = g_ip.num_rd_ports
        self.num_wr_ports = g_ip.num_wr_ports
        self.num_se_rd_ports = g_ip.num_se_rd_ports
        self.num_search_ports = g_ip.num_search_ports

        if self.is_dram and self.is_main_mem:
            self.number_addr_bits_mat = max(num_addr_b_row_dec, _log2(self.deg_bl_muxing) + _log2(self.deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2))
            if g_ip.print_detail_debug:
                print(f"parameter.cc: number_addr_bits_mat = {num_addr_b_row_dec}")
                print(f"parameter.cc: num_addr_b_row_dec = {num_addr_b_row_dec}")
                print(f"parameter.cc: num_addr_b_mux_sel = {_log2(self.deg_bl_muxing) + _log2(self.deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2)}")
        else:
            self.number_addr_bits_mat = num_addr_b_row_dec + _log2(self.deg_bl_muxing) + _log2(self.deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2)

        if self.is_tag:
            self.num_di_b_bank_per_port = self.tagbits
            self.num_do_b_bank_per_port = g_ip.data_assoc
        else:
            self.num_di_b_bank_per_port = g_ip.out_w + g_ip.data_assoc
            self.num_do_b_bank_per_port = g_ip.out_w

        if not self.is_tag and g_ip.data_assoc > 1 and not g_ip.fast_access:
            self.number_way_select_signals_mat = g_ip.data_assoc

        if g_ip.add_ecc_b_:
            self.ECC_adjustment()

        self.is_valid = True

    def init_CAM(self):
        wire_local = g_tp.wire_local
        capacity_per_die = g_ip.cache_sz / NUMBER_STACKED_DIE_LAYERS

        if self.Ndwl != 1 or self.Ndcm != 1 or self.Nspd < 1 or self.Nspd > 1 or self.Ndsam_lev_1 != 1 or self.Ndsam_lev_2 != 1 or self.Ndbl < 2:
            return

        if g_ip.specific_tag:
            self.tagbits = int(sp.ceiling(g_ip.tag_w / 8.0) * 8)
        else:
            self.tagbits = int(sp.ceiling((ADDRESS_BITS + EXTRA_TAG_BITS) / 8.0) * 8)

        self.tag_num_r_subarray = int(sp.ceiling(capacity_per_die / (g_ip.nbanks * self.tagbits / 8.0 * self.Ndbl)))
        self.tag_num_c_subarray = self.tagbits

        if self.tag_num_r_subarray == 0:
            return
        if self.tag_num_r_subarray > MAXSUBARRAYROWS:
            return
        if self.tag_num_c_subarray < MINSUBARRAYCOLS:
            return
        if self.tag_num_c_subarray > MAXSUBARRAYCOLS:
            return
        self.num_r_subarray = self.tag_num_r_subarray

        self.num_subarrays = self.Ndwl * self.Ndbl

        self.cam_cell.h = g_tp.cam.b_h + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1) + wire_local.pitch * g_ip.num_se_rd_ports
        self.cam_cell.w = g_tp.cam.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1) + wire_local.pitch * g_ip.num_se_rd_ports

        self.cell.h = g_tp.sram.b_h + 2 * wire_local.pitch * (g_ip.num_wr_ports + g_ip.num_rw_ports - 1 + g_ip.num_rd_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1)
        self.cell.w = g_tp.sram.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + (g_ip.num_rd_ports - g_ip.num_se_rd_ports) + g_ip.num_wr_ports) + g_tp.wire_local.pitch * g_ip.num_se_rd_ports + 2 * wire_local.pitch * (g_ip.num_search_ports - 1)

        c_b_metal = self.cell.h * wire_local.C_per_um
        c_b_metal = self.cam_cell.h * wire_local.C_per_um
        self.V_b_sense = max(0.05 * g_tp.sram_cell.Vdd, VBITSENSEMIN)
        self.deg_bl_muxing = 1

        Cbitrow_drain_cap = drain_C_(g_tp.cam.cell_a_w, NCH, 1, 0, self.cam_cell.w, False, True) / 2.0
        self.dram_refresh_period = 0

        if self.Ndbl == 0:
            print("   Invalid Ndbl \n")
            exit(0)
        elif self.Ndbl == 1:
            self.num_mats_h_dir = 1
            self.num_mats_v_dir = 1
        elif self.Ndbl == 2:
            self.num_mats_h_dir = 1
            self.num_mats_v_dir = 1
        else:
            self.num_mats_h_dir = int(sp.floor(sp.sqrt(self.Ndbl / 4.0)))
            self.num_mats_v_dir = int(self.Ndbl / 4.0 / self.num_mats_h_dir)

        self.num_mats = self.num_mats_h_dir * self.num_mats_v_dir

        self.num_so_b_mat = int(sp.ceiling(_log2(self.num_r_subarray)) + sp.ceiling(_log2(self.num_subarrays)))
        self.num_do_b_mat = self.tagbits

        deg_sa_mux_l1_non_assoc = 1

        self.num_so_b_subbank = int(sp.ceiling(_log2(self.num_r_subarray)) + sp.ceiling(_log2(self.num_subarrays)))
        self.num_do_b_subbank = self.tag_num_c_subarray

        self.deg_senseamp_muxing_non_associativity = deg_sa_mux_l1_non_assoc

        self.num_act_mats_hor_dir = 1
        self.num_act_mats_hor_dir_sl = self.num_mats_h_dir

        if self.num_act_mats_hor_dir > self.num_mats_h_dir:
            return

        self.num_di_b_mat = self.tagbits
        self.num_si_b_mat = self.tagbits

        self.num_di_b_subbank = self.num_di_b_mat * self.num_act_mats_hor_dir
        self.num_si_b_subbank = self.num_si_b_mat

        num_addr_b_row_dec = _log2(self.num_r_subarray)
        num_addr_b_row_dec += _log2(self.num_subarrays / self.num_mats)
        number_subbanks = self.num_mats / self.num_act_mats_hor_dir
        self.number_subbanks_decode = _log2(number_subbanks)

        self.num_rw_ports = g_ip.num_rw_ports
        self.num_rd_ports = g_ip.num_rd_ports
        self.num_wr_ports = g_ip.num_wr_ports
        self.num_se_rd_ports = g_ip.num_se_rd_ports
        self.num_search_ports = g_ip.num_search_ports

        self.number_addr_bits_mat = num_addr_b_row_dec + _log2(self.deg_bl_muxing) + _log2(deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2)

        self.num_di_b_bank_per_port = self.tagbits
        self.num_si_b_bank_per_port = self.tagbits
        self.num_do_b_bank_per_port = self.tagbits
        self.num_so_b_bank_per_port = int(sp.ceiling(_log2(self.num_r_subarray)) + sp.ceiling(_log2(self.num_subarrays)))

        if not self.is_tag and g_ip.data_assoc > 1 and not g_ip.fast_access:
            self.number_way_select_signals_mat = g_ip.data_assoc

        if g_ip.add_ecc_b_:
            self.ECC_adjustment()

        self.is_valid = True

    def init_FA(self):
        wire_local = g_tp.wire_local
        assert NUMBER_STACKED_DIE_LAYERS == 1
        capacity_per_die = g_ip.cache_sz

        if self.Ndwl != 1 or self.Ndcm != 1 or self.Nspd < 1 or self.Nspd > 1 or self.Ndsam_lev_1 != 1 or self.Ndsam_lev_2 != 1 or self.Ndbl < 2:
            return

        if g_ip.specific_tag:
            self.tagbits = g_ip.tag_w
        else:
            self.tagbits = ADDRESS_BITS + EXTRA_TAG_BITS - _log2(g_ip.block_sz)
        self.tagbits = (((self.tagbits + 3) >> 2) << 2)

        self.tag_num_r_subarray = int(capacity_per_die / (g_ip.nbanks * g_ip.block_sz * self.Ndbl))
        self.tag_num_c_subarray = int(sp.ceiling((self.tagbits * self.Nspd / self.Ndwl)))
        if self.tag_num_r_subarray == 0:
            return
        if self.tag_num_r_subarray > MAXSUBARRAYROWS:
            return
        if self.tag_num_c_subarray < MINSUBARRAYCOLS:
            return
        if self.tag_num_c_subarray > MAXSUBARRAYCOLS:
            return

        self.data_num_r_subarray = self.tag_num_r_subarray
        self.data_num_c_subarray = 8 * g_ip.block_sz
        if self.data_num_r_subarray == 0:
            return
        if self.data_num_r_subarray > MAXSUBARRAYROWS:
            return
        if self.data_num_c_subarray < MINSUBARRAYCOLS:
            return
        if self.data_num_c_subarray > MAXSUBARRAYCOLS:
            return
        self.num_r_subarray = self.tag_num_r_subarray

        self.num_subarrays = self.Ndwl * self.Ndbl

        self.cam_cell.h = g_tp.cam.b_h + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1) + wire_local.pitch * g_ip.num_se_rd_ports
        self.cam_cell.w = g_tp.cam.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + g_ip.num_rd_ports + g_ip.num_wr_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1) + wire_local.pitch * g_ip.num_se_rd_ports

        self.cell.h = g_tp.sram.b_h + 2 * wire_local.pitch * (g_ip.num_wr_ports + g_ip.num_rw_ports - 1 + g_ip.num_rd_ports) + 2 * wire_local.pitch * (g_ip.num_search_ports - 1)
        self.cell.w = g_tp.sram.b_w + 2 * wire_local.pitch * (g_ip.num_rw_ports - 1 + (g_ip.num_rd_ports - g_ip.num_se_rd_ports) + g_ip.num_wr_ports) + g_tp.wire_local.pitch * g_ip.num_se_rd_ports + 2 * wire_local.pitch * (g_ip.num_search_ports - 1)

        c_b_metal = self.cell.h * wire_local.C_per_um
        c_b_metal = self.cam_cell.h * wire_local.C_per_um
        self.V_b_sense = max(0.05 * g_tp.sram_cell.Vdd, VBITSENSEMIN)
        self.deg_bl_muxing = 1

        Cbitrow_drain_cap = drain_C_(g_tp.cam.cell_a_w, NCH, 1, 0, self.cam_cell.w, False, True) / 2.0
        self.dram_refresh_period = 0

        if self.Ndbl == 0:
            print("   Invalid Ndbl \n")
            exit(0)
        elif self.Ndbl == 1:
            self.num_mats_h_dir = 1
            self.num_mats_v_dir = 1
        elif self.Ndbl == 2:
            self.num_mats_h_dir = 1
            self.num_mats_v_dir = 1
        else:
            self.num_mats_h_dir = int(sp.floor(sp.sqrt(self.Ndbl / 4.0)))
            self.num_mats_v_dir = int(self.Ndbl / 4.0 / self.num_mats_h_dir)

        self.num_mats = self.num_mats_h_dir * self.num_mats_v_dir

        self.num_so_b_mat = self.data_num_c_subarray
        self.num_do_b_mat = self.data_num_c_subarray + self.tagbits

        deg_sa_mux_l1_non_assoc = 1
        self.num_so_b_subbank = 8 * g_ip.block_sz
        self.num_do_b_subbank = self.num_so_b_subbank + self.tag_num_c_subarray

        self.deg_senseamp_muxing_non_associativity = deg_sa_mux_l1_non_assoc
        self.num_act_mats_hor_dir = 1
        self.num_act_mats_hor_dir_sl = self.num_mats_h_dir

        if self.num_act_mats_hor_dir > self.num_mats_h_dir:
            return

        if self.fully_assoc:
            self.num_di_b_mat = self.num_do_b_mat
            self.num_si_b_mat = self.tagbits
        self.num_di_b_subbank = self.num_di_b_mat * self.num_act_mats_hor_dir
        self.num_si_b_subbank = self.num_si_b_mat

        num_addr_b_row_dec = _log2(self.num_r_subarray)
        num_addr_b_row_dec += _log2(self.num_subarrays / self.num_mats)
        number_subbanks = self.num_mats / self.num_act_mats_hor_dir
        self.number_subbanks_decode = _log2(number_subbanks)

        self.num_rw_ports = g_ip.num_rw_ports
        self.num_rd_ports = g_ip.num_rd_ports
        self.num_wr_ports = g_ip.num_wr_ports
        self.num_se_rd_ports = g_ip.num_se_rd_ports
        self.num_search_ports = g_ip.num_search_ports

        self.number_addr_bits_mat = num_addr_b_row_dec + _log2(self.deg_bl_muxing) + _log2(deg_sa_mux_l1_non_assoc) + _log2(self.Ndsam_lev_2)

        self.num_di_b_bank_per_port = g_ip.out_w + self.tagbits
        self.num_si_b_bank_per_port = self.tagbits
        self.num_do_b_bank_per_port = g_ip.out_w + self.tagbits
        self.num_so_b_bank_per_port = g_ip.out_w

        if not self.is_tag and g_ip.data_assoc > 1 and not g_ip.fast_access:
            self.number_way_select_signals_mat = g_ip.data_assoc

        if g_ip.add_ecc_b_:
            self.ECC_adjustment()

        self.is_valid = True

    def ECC_adjustment(self):
        self.num_do_b_mat += int(sp.ceiling(self.num_do_b_mat / self.num_bits_per_ecc_b_))
        self.num_di_b_mat += int(sp.ceiling(self.num_di_b_mat / self.num_bits_per_ecc_b_))
        self.num_di_b_subbank += int(sp.ceiling(self.num_di_b_subbank / self.num_bits_per_ecc_b_))
        self.num_do_b_subbank += int(sp.ceiling(self.num_do_b_subbank / self.num_bits_per_ecc_b_))
        self.num_di_b_bank_per_port += int(sp.ceiling(self.num_di_b_bank_per_port / self.num_bits_per_ecc_b_))
        self.num_do_b_bank_per_port += int(sp.ceiling(self.num_do_b_bank_per_port / self.num_bits_per_ecc_b_))

        self.num_so_b_mat += int(sp.ceiling(self.num_so_b_mat / self.num_bits_per_ecc_b_))
        self.num_si_b_mat += int(sp.ceiling(self.num_si_b_mat / self.num_bits_per_ecc_b_))
        self.num_si_b_subbank += int(sp.ceiling(self.num_si_b_subbank / self.num_bits_per_ecc_b_))
        self.num_so_b_subbank += int(sp.ceiling(self.num_so_b_subbank / self.num_bits_per_ecc_b_))
        self.num_si_b_bank_per_port += int(sp.ceiling(self.num_si_b_bank_per_port / self.num_bits_per_ecc_b_))
        self.num_so_b_bank_per_port += int(sp.ceiling(self.num_so_b_bank_per_port / self.num_bits_per_ecc_b_))

    def calc_subarr_rc(self, capacity_per_die):
        if self.Ndwl < 2 or self.Ndbl < 2:
            return False

        if self.is_dram and not self.is_tag and self.Ndcm > 1:
            return False

        if self.is_tag:
            if g_ip.specific_tag:
                self.tagbits = g_ip.tag_w
            else:
                self.tagbits = ADDRESS_BITS + EXTRA_TAG_BITS - _log2(capacity_per_die) + _log2(g_ip.tag_assoc * 2 - 1)

            self.num_r_subarray = int(sp.ceiling(capacity_per_die / (g_ip.nbanks * g_ip.block_sz * g_ip.tag_assoc * self.Ndbl * self.Nspd)))
            self.num_c_subarray = int(sp.ceiling((self.tagbits * g_ip.tag_assoc * self.Nspd / self.Ndwl)))
        else:
            self.num_r_subarray = int(sp.ceiling(capacity_per_die / (g_ip.nbanks * g_ip.block_sz * g_ip.data_assoc * self.Ndbl * self.Nspd)))
            self.num_c_subarray = int(sp.ceiling((8 * g_ip.block_sz * g_ip.data_assoc * self.Nspd / self.Ndwl)))
            if g_ip.is_3d_mem:
                capacity_per_die_double = float(g_ip.cache_sz) / g_ip.num_die_3d
                self.num_c_subarray = g_ip.page_sz_bits / self.Ndwl
                self.num_r_subarray = 1 << int(sp.floor(_log2(float(g_ip.cache_sz) / g_ip.num_die_3d / self.num_c_subarray / g_ip.nbanks / self.Ndbl / self.Ndwl * 1024 * 1024 * 1024) + 0.5))
                if g_ip.print_detail_debug:
                    print(f"parameter.cc: capacity_per_die_double = {capacity_per_die_double} Gbit")
                    print(f"parameter.cc: g_ip.nbanks * Ndbl * Ndwl = {g_ip.nbanks * self.Ndbl * self.Ndwl}")
                    print(f"parameter.cc: num_r_subarray = {self.num_r_subarray}")
                    print(f"parameter.cc: num_c_subarray = {self.num_c_subarray}")

        if self.num_r_subarray < MINSUBARRAYROWS or self.num_r_subarray == 0 or self.num_r_subarray > MAXSUBARRAYROWS:
            return False
        if self.num_c_subarray < MINSUBARRAYCOLS or self.num_c_subarray > MAXSUBARRAYCOLS:
            return False

        self.num_subarrays = self.Ndwl * self.Ndbl
        return True
    









# HELPERS
# CHECK THESE
def PRINT(A, X, tech):
    print(f"{A}: {X} , {tech.X}")

def scan_single_input_double(line, name, unit_name, print_output):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = float(match.group(2))
        if print_output:
            print(f"{name}: {temp} {unit}")
        return temp
    return 0.0

def scan_five_input_double(line, name, unit_name, flavor, print_output):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = [float(match.group(i)) for i in range(2, 7)]
        if print_output:
            print(f"{name}[{flavor}]: {temp[flavor]} {unit}")
        return temp[flavor]
    return 0.0

def scan_five_input_double_temperature(line, name, unit_name, flavor, temperature, print_output, result):
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        thermal_temp = int(match.group(2))
        temp = [float(match.group(i)) for i in range(3, 8)]
        if thermal_temp == (temperature - 300):
            if print_output:
                print(f"{name}: {temp[flavor]} {unit}")
            result = temp[flavor]

def scan_input_double_inter_type(line, name, unit_name, proj_type, tech_flavor, print_output):
    assert proj_type < NUMBER_INTERCONNECT_PROJECTION_TYPES
    index = proj_type * NUMBER_WIRE_TYPES + tech_flavor
    match = re.search(f"{name}\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", line)
    if match:
        unit = match.group(1)
        temp = [float(match.group(i)) for i in range(2, 10)]
        if print_output:
            print(f"{name} {temp[index]} {unit}")
        return temp[index]
    return 0.0

def scan_five_input_double_mem_type(line, name, unit_name, flavor, cell_type, print_flag):
    temp = [0.0] * 5
    unit = ""
    
    # Extract the relevant part of the line
    relevant_line = line[len(name):].strip()

    # print(line)
    # print(relevant_line)
    
    # Scan the input line and extract values
    parts = relevant_line.split()
    # print(parts)
    # print(cell_type)
    
    unit = parts[0]
    cell_type_temp = int(parts[1])
    temp[0] = float(parts[2])
    temp[1] = float(parts[3])
    temp[2] = float(parts[4])
    temp[3] = float(parts[5])
    temp[4] = float(parts[6])
    
    result = None
    if cell_type_temp == cell_type:
        if print_flag:
            print(f"{name}: {temp[flavor]} {unit}")
        result = temp[flavor]
    
    return result

def scan_input_double_tsv_type(line, name, unit_name, proj_type, tsv_type, print_flag):
    assert proj_type < NUMBER_INTERCONNECT_PROJECTION_TYPES
    index = proj_type * NUMBER_TSV_TYPES + tsv_type
    temp = [0.0] * 6
    unit = ""
    
    # Extracting the values using regular expressions
    match = re.search(rf"{name}\s+(\S+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)", line)
    
    if match:
        unit = match.group(1)
        temp[0] = float(match.group(2))
        temp[1] = float(match.group(3))
        temp[2] = float(match.group(4))
        temp[3] = float(match.group(5))
        temp[4] = float(match.group(6))
        temp[5] = float(match.group(7))
        
        if print_flag:
            print(f"{name}: {temp[index]} {unit}")
            
        return temp[index]
    else:
        raise ValueError("Line does not match the expected format")





#### TO AVOID CIRCULAR DEPENDNCY
UNI_LEAK_STACK_FACTOR = 0.43

def powers(base, n):
    p = 1
    for i in range(1, n + 1):
        p *= base
    return p

def is_pow2(val):
    if val <= 0:
        return False
    elif val == 1:
        return True
    else:
        return (_log2(val) != _log2(val - 1))

def _log2(num):
    if num == 0:
        raise ValueError("log0?")
    log2 = 0
    while num > 1:
        num >>= 1
        log2 += 1
    return log2

def factorial(n, m=1):
    fa = m
    for i in range(m + 1, n + 1):
        fa *= i
    return fa

def combination(n, m):
    return factorial(n, m + 1) // factorial(n - m)


outside_mat = "outside_mat"
inside_mat = "inside_mat"
local_wires = "local_wires"


Add_htree = "Add_htree"
Data_in_htree = "Data_in_htree"
Data_out_htree = "Data_out_htree"
Search_in_htree = "Search_in_htree"
Search_out_htree = "Search_out_htree"


Row_add_path = "Row_add_path"
Col_add_path = "Col_add_path"
Data_path = "Data_path"


nmos = "nmos"
pmos = "pmos"
inv = "inv"
nand = "nand"
nor = "nor"
tri = "tri"
tg = "tg"

parallel = "parallel"
series = "series"

# class WirePlacement:
#     outside_mat = "outside_mat"
#     inside_mat = "inside_mat"
#     local_wires = "local_wires"

# class HtreeType:
#     Add_htree = "Add_htree"
#     Data_in_htree = "Data_in_htree"
#     Data_out_htree = "Data_out_htree"
#     Search_in_htree = "Search_in_htree"
#     Search_out_htree = "Search_out_htree"

# class MemorybusType:
#     Row_add_path = "Row_add_path"
#     Col_add_path = "Col_add_path"
#     Data_path = "Data_path"

# class GateType:
#     nmos = "nmos"
#     pmos = "pmos"
#     inv = "inv"
#     nand = "nand"
#     nor = "nor"
#     tri = "tri"
#     tg = "tg"

# class HalfNetTopology:
#     parallel = "parallel"
#     series = "series"

# def logtwo(x):
#     assert x > 0
#     return sp.log(x) / sp.log(2.0)

def gate_C(width, wirelength, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global
    return (dt.C_g_ideal + dt.C_overlap + 3 * dt.C_fringe) * width + dt.l_phy * Cpolywire

def gate_C_pass(width, wirelength, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    return gate_C(width, wirelength, _is_dram, _is_sram, _is_wl_tr, _is_sleep_tx)

def drain_C_(width, nchannel, stack, next_arg_thresh_folding_width_or_height_cell, fold_dimension, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    c_junc_area = dt.C_junc
    c_junc_sidewall = dt.C_junc_sidewall
    c_fringe = 2 * dt.C_fringe
    c_overlap = 2 * dt.C_overlap
    drain_C_metal_connecting_folded_tr = 0

    if next_arg_thresh_folding_width_or_height_cell == 0:
        w_folded_tr = fold_dimension
    else:
        h_tr_region = fold_dimension - 2 * g_tp.HPOWERRAIL
        ratio_p_to_n = 2.0 / (2.0 + 1.0)
        if nchannel:
            w_folded_tr = (1 - ratio_p_to_n) * (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)
        else:
            w_folded_tr = ratio_p_to_n * (h_tr_region - g_tp.MIN_GAP_BET_P_AND_N_DIFFS)

    num_folded_tr = int(sp.ceiling(width / w_folded_tr))
    if num_folded_tr < 2:
        w_folded_tr = width

    total_drain_w = (g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact) + (stack - 1) * g_tp.spacing_poly_to_poly
    drain_h_for_sidewall = w_folded_tr
    total_drain_height_for_cap_wrt_gate = w_folded_tr + 2 * w_folded_tr * (stack - 1)
    if num_folded_tr > 1:
        total_drain_w += (num_folded_tr - 2) * (g_tp.w_poly_contact + 2 * g_tp.spacing_poly_to_contact) + (num_folded_tr - 1) * ((stack - 1) * g_tp.spacing_poly_to_poly)
        if num_folded_tr % 2 == 0:
            drain_h_for_sidewall = 0
        total_drain_height_for_cap_wrt_gate *= num_folded_tr
        drain_C_metal_connecting_folded_tr = g_tp.wire_local.C_per_um * total_drain_w

    drain_C_area = c_junc_area * total_drain_w * w_folded_tr
    drain_C_sidewall = c_junc_sidewall * (drain_h_for_sidewall + 2 * total_drain_w)
    drain_C_wrt_gate = (c_fringe + c_overlap) * total_drain_height_for_cap_wrt_gate

    return drain_C_area + drain_C_sidewall + drain_C_wrt_gate + drain_C_metal_connecting_folded_tr

def tr_R_on(width, nchannel, stack, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    restrans = dt.R_nch_on if nchannel else dt.R_pch_on
    return stack * restrans / width

def R_to_w(res, nchannel, _is_dram=False, _is_sram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_sram:
        dt = g_tp.dram_acc  # DRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif not _is_dram and _is_sram:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global

    restrans = dt.R_nch_on if nchannel else dt.R_pch_on
    return restrans / res

def pmos_to_nmos_sz_ratio(_is_dram=False, _is_wl_tr=False, _is_sleep_tx=False):
    if _is_dram and _is_wl_tr:
        return g_tp.dram_wl.n_to_p_eff_curr_drv_ratio
    elif _is_sleep_tx:
        return g_tp.sleep_tx.n_to_p_eff_curr_drv_ratio
    else:
        return g_tp.peri_global.n_to_p_eff_curr_drv_ratio

def horowitz(inputramptime, tf, vs1, vs2, rise):
    if inputramptime == 0 and vs1 == vs2:
        return tf * (-sp.log(vs1) if vs1 < 1 else sp.log(vs1))

    a = inputramptime / tf
    if rise == RISE:
        b = 0.5
        td = tf * sp.sqrt(sp.log(vs1) ** 2 + 2 * a * b * (1.0 - vs1)) + tf * (sp.log(vs1) - sp.log(vs2))
    else:
        b = 0.4
        td = tf * sp.sqrt(sp.log(1.0 - vs1) ** 2 + 2 * a * b * vs1) + tf * (sp.log(1.0 - vs1) - sp.log(1.0 - vs2))
    return td

def cmos_Ileak(nWidth, pWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nWidth * dt.I_off_n + pWidth * dt.I_off_p

def simplified_nmos_Isat(nwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nwidth * dt.I_on_n

def simplified_pmos_Isat(pwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pwidth * dt.I_on_n / dt.n_to_p_eff_curr_drv_ratio

def simplified_nmos_leakage(nwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nwidth * dt.I_off_n

def simplified_pmos_leakage(pwidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pwidth * dt.I_off_p

def cmos_Ig_n(nWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return nWidth * dt.I_g_on_n

def cmos_Ig_p(pWidth, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False):
    if not _is_dram and _is_cell:
        dt = g_tp.sram_cell  # SRAM cell access transistor
    elif _is_dram and _is_wl_tr:
        dt = g_tp.dram_wl  # DRAM wordline transistor
    elif _is_sleep_tx:
        dt = g_tp.sleep_tx  # Sleep transistor
    else:
        dt = g_tp.peri_global  # DRAM or SRAM all other transistors

    return pWidth * dt.I_g_on_p

def cmos_Isub_leakage(nWidth, pWidth, fanin, g_type, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False, topo=series):
    assert fanin >= 1
    nmos_leak = simplified_nmos_leakage(nWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    pmos_leak = simplified_pmos_leakage(pWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    Isub = 0
    num_states = int(sp.Pow(2.0, fanin))

    if g_type == nmos:
        if fanin == 1:
            Isub = nmos_leak / num_states
        else:
            if topo == parallel:
                Isub = nmos_leak * fanin / num_states
            else:
                for num_off_tx in range(1, fanin + 1):
                    Isub += nmos_leak * sp.Pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
                Isub /= num_states

    elif g_type == pmos:
        if fanin == 1:
            Isub = pmos_leak / num_states
        else:
            if topo == parallel:
                Isub = pmos_leak * fanin / num_states
            else:
                for num_off_tx in range(1, fanin + 1):
                    Isub += pmos_leak * sp.Pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
                Isub /= num_states

    elif g_type == inv:
        Isub = (nmos_leak + pmos_leak) / 2

    elif g_type == nand:
        Isub += fanin * pmos_leak
        for num_off_tx in range(1, fanin + 1):
            Isub += nmos_leak * sp.Pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
        Isub /= num_states

    elif g_type == nor:
        for num_off_tx in range(1, fanin + 1):
            Isub += pmos_leak * sp.Pow(UNI_LEAK_STACK_FACTOR, (num_off_tx - 1)) * combination(fanin, num_off_tx)
        Isub += fanin * nmos_leak
        Isub /= num_states

    elif g_type == tri:
        Isub += (nmos_leak + pmos_leak) / 2
        Isub += nmos_leak * UNI_LEAK_STACK_FACTOR
        Isub /= 2

    elif g_type == tg:
        Isub = (nmos_leak + pmos_leak) / 2

    else:
        raise ValueError("Invalid gate type")

    return Isub

def cmos_Ig_leakage(nWidth, pWidth, fanin, g_type, _is_dram=False, _is_cell=False, _is_wl_tr=False, _is_sleep_tx=False, topo=series):
    assert fanin >= 1
    nmos_leak = cmos_Ig_n(nWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    pmos_leak = cmos_Ig_p(pWidth, _is_dram, _is_cell, _is_wl_tr, _is_sleep_tx)
    Ig_on = 0
    num_states = int(sp.Pow(2.0, fanin))

    if g_type == nmos:
        if fanin == 1:
            Ig_on = nmos_leak / num_states
        else:
            if topo == parallel:
                for num_on_tx in range(1, fanin + 1):
                    Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx
            else:
                Ig_on += nmos_leak * fanin
                for num_on_tx in range(1, fanin):
                    Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
                Ig_on /= num_states

    elif g_type == pmos:
        if fanin == 1:
            Ig_on = pmos_leak / num_states
        else:
            if topo == parallel:
                for num_on_tx in range(1, fanin + 1):
                    Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx
            else:
                Ig_on += pmos_leak * fanin
                for num_on_tx in range(1, fanin):
                    Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
                Ig_on /= num_states

    elif g_type == inv:
        Ig_on = (nmos_leak + pmos_leak) / 2

    elif g_type == nand:
        for num_on_tx in range(1, fanin + 1):
            Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx
        Ig_on += nmos_leak * fanin
        for num_on_tx in range(1, fanin):
            Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
        Ig_on /= num_states

    elif g_type == nor:
        Ig_on += pmos_leak * fanin
        for num_on_tx in range(1, fanin):
            Ig_on += pmos_leak * combination(fanin, num_on_tx) * num_on_tx / 2
        for num_on_tx in range(1, fanin + 1):
            Ig_on += nmos_leak * combination(fanin, num_on_tx) * num_on_tx
        Ig_on /= num_states

    elif g_type == tri:
        Ig_on += (2 * nmos_leak + 2 * pmos_leak) / 2
        Ig_on += (nmos_leak + pmos_leak) / 2
        Ig_on /= 2

    elif g_type == tg:
        Ig_on = (nmos_leak + pmos_leak) / 2

    else:
        raise ValueError("Invalid gate type")

    return Ig_on

def shortcircuit_simple(vt, velocity_index, c_in, c_out, w_nmos, w_pmos, i_on_n, i_on_p, i_on_n_in, i_on_p_in, vdd):
    fo_n = i_on_n / i_on_n_in
    fo_p = i_on_p / i_on_p_in
    fanout = c_out / c_in
    beta_ratio = i_on_p / i_on_n
    vt_to_vdd_ratio = vt / vdd

    p_short_circuit_discharge_low = (10 / 3) * (pow((vdd - vt) - vt_to_vdd_ratio, 3.0) / pow(velocity_index, 2.0) / pow(2.0, 3 * vt_to_vdd_ratio * vt_to_vdd_ratio)) * c_in * vdd * vdd * fo_p * fo_p / fanout / beta_ratio
    p_short_circuit_charge_low = (10 / 3) * (pow((vdd - vt) - vt_to_vdd_ratio, 3.0) / pow(velocity_index, 2.0) / pow(2.0, 3 * vt_to_vdd_ratio * vt_to_vdd_ratio)) * c_in * vdd * vdd * fo_n * fo_n / fanout * beta_ratio

    p_short_circuit_discharge = p_short_circuit_discharge_low
    p_short_circuit_charge = p_short_circuit_charge_low
    p_short_circuit = (p_short_circuit_discharge + p_short_circuit_charge) / 2

    return p_short_circuit

def shortcircuit(vt, velocity_index, c_in, c_out, w_nmos, w_pmos, i_on_n, i_on_p, i_on_n_in, i_on_p_in, vdd):
    fo_p = i_on_p / i_on_p_in
    fanout = 1
    beta_ratio = i_on_p / i_on_n
    e = 2.71828
    f_alpha = 1 / (velocity_index + 2) - velocity_index / (2 * (velocity_index + 3)) + velocity_index / (velocity_index + 4) * (velocity_index / 2 - 1)
    k_v = 0.9 / 0.8 + (vdd - vt) / 0.8 * sp.log(10 * (vdd - vt) / e)
    g_v_alpha = (velocity_index + 1) * pow((1 - velocity_index), velocity_index) * pow((1 - velocity_index), velocity_index / 2) / f_alpha / pow((1 - velocity_index - velocity_index), (velocity_index / 2 + velocity_index + 2))
    h_v_alpha = pow(2, velocity_index) * (velocity_index + 1) * pow((1 - velocity_index), velocity_index) / pow((1 - velocity_index - velocity_index), (velocity_index + 1))

    p_short_circuit_discharge = k_v * vdd * vdd * c_in * fo_p * fo_p / ((vdd - vt) * g_v_alpha * fanout * beta_ratio / 2 / k_v + h_v_alpha * fo_p)
    return p_short_circuit_discharge

def wire_resistance(resistivity, wire_width, wire_thickness, barrier_thickness, dishing_thickness, alpha_scatter):
    resistance = alpha_scatter * resistivity / ((wire_thickness - barrier_thickness - dishing_thickness) * (wire_width - 2 * barrier_thickness))
    return resistance

def wire_capacitance(wire_width, wire_thickness, wire_spacing, ild_thickness, miller_value, horiz_dielectric_constant, vert_dielectric_constant, fringe_cap):
    vertical_cap = 2 * PERMITTIVITY_FREE_SPACE * vert_dielectric_constant * wire_width / ild_thickness
    sidewall_cap = 2 * PERMITTIVITY_FREE_SPACE * miller_value * horiz_dielectric_constant * wire_thickness / wire_spacing
    total_cap = vertical_cap + sidewall_cap + fringe_cap
    return total_cap

def tsv_resistance(resistivity, tsv_len, tsv_diam, tsv_contact_resistance):
    resistance = resistivity * tsv_len / (math.pi * (tsv_diam / 2) ** 2) + tsv_contact_resistance
    return resistance

def tsv_capacitance(tsv_len, tsv_diam, tsv_pitch, dielec_thickness, liner_dielectric_constant, depletion_width):
    e_si = PERMITTIVITY_FREE_SPACE * 11.9
    PI = math.pi
    lateral_coupling_constant = 4.1
    diagonal_coupling_constant = 5.3

    liner_cap = 2 * PI * PERMITTIVITY_FREE_SPACE * liner_dielectric_constant * tsv_len / sp.log(1 + dielec_thickness / (tsv_diam / 2))
    depletion_cap = 2 * PI * e_si * tsv_len / sp.log(1 + depletion_width / (dielec_thickness + tsv_diam / 2))
    self_cap = 1 / (1 / liner_cap + 1 / depletion_cap)

    lateral_coupling_cap = 0.4 * (0.225 * sp.log(0.97 * tsv_len / tsv_diam) + 0.53) * e_si / (tsv_pitch - tsv_diam) * PI * tsv_diam * tsv_len
    diagonal_coupling_cap = 0.4 * (0.225 * sp.log(0.97 * tsv_len / tsv_diam) + 0.53) * e_si / (1.414 * tsv_pitch - tsv_diam) * PI * tsv_diam * tsv_len

    total_cap = self_cap + lateral_coupling_constant * lateral_coupling_cap + diagonal_coupling_constant * diagonal_coupling_cap
    return total_cap

def tsv_area(tsv_pitch):
    return tsv_pitch ** 2


g_ip = InputParameter()
g_tp = TechnologyParameter()
