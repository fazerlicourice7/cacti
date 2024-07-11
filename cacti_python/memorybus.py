from .parameter import g_tp
from .decoder import *
from .component import *
from .memorybus import *
from .wire import *
from .const import *
import sympy as sp

class Memorybus(Component):
    def __init__(self, wire_model, mat_w, mat_h, subarray_w_, subarray_h_,
                 _row_add_bits, _col_add_bits, _data_bits, _ndbl, _ndwl,
                 membus_type_, dp_, dt=g_tp.peri_global):
        self.dp = dp_
        self.in_rise_time = 0
        self.out_rise_time = 0
        self.is_dram = dp_.is_dram
        self.membus_type = membus_type_
        self.mat_width = mat_w
        self.mat_height = mat_h
        self.subarray_width = subarray_w_
        self.subarray_height = subarray_h_
        self.data_bits = _data_bits
        self.ndbl = _ndbl
        self.ndwl = _ndwl
        self.wt = wire_model
        self.deviceType = dt

        if g_ip.print_detail_debug:
            print("memorybus.cc: membus_type =", membus_type_)
        self.power.readOp.dynamic = 0
        self.power.readOp.leakage = 0
        self.power.readOp.gate_leakage = 0
        self.power.searchOp.dynamic = 0
        self.delay = 0

        self.cell = Area()
        self.cell.h = g_tp.dram.b_h
        self.cell.w = g_tp.dram.b_w

        if not g_ip.is_3d_mem:
            assert self.ndbl >= 2 and self.ndwl >= 2

        if g_ip.print_detail_debug:
            print("burst length:", g_ip.burst_depth)
            print("output width:", g_ip.io_width)

        self.chip_IO_width = g_ip.io_width
        self.burst_length = g_ip.burst_depth
        self.data_bits = self.chip_IO_width * self.burst_length

        self.row_add_bits = _row_add_bits
        self.col_add_bits = _col_add_bits

        self.max_unpipelined_link_delay = 0
        self.min_w_nmos = g_tp.min_w_nmos_
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * self.min_w_nmos

        self.semi_repeated_global_line = 0
        self.ndwl = _ndwl // g_ip.num_tier_row_sprd
        self.ndbl = _ndbl // g_ip.num_tier_col_sprd
        self.num_subarray_global_IO = 16 if self.ndbl > 16 else self.ndbl

        if self.membus_type == MemorybusType.Data_path:
            self.data_bits = self.chip_IO_width * self.burst_length
            self.Network()
        elif self.membus_type == MemorybusType.Row_add_path:
            self.add_bits = _row_add_bits
            self.num_dec_signals = self.dp.num_r_subarray * self.ndbl
            self.Network()
        elif self.membus_type == MemorybusType.Col_add_path:
            self.add_bits = _col_add_bits
            self.num_dec_signals = self.dp.num_c_subarray * self.ndwl // self.data_bits
            self.Network()
        else:
            assert False

        assert self.power.readOp.dynamic >= 0
        assert self.power.readOp.leakage >= 0

    def __del__(self):
        del self.center_stripe
        del self.bank_bus
        if self.membus_type == MemorybusType.Data_path:
            del self.local_data
            del self.global_data
            del self.local_data_drv
            if self.semi_repeated_global_line:
                del self.global_data_drv
            del self.out_seg
        elif self.membus_type == MemorybusType.Row_add_path:
            del self.global_WL
            del self.add_predec
            del self.add_dec
            del self.lwl_drv
        elif self.membus_type == MemorybusType.Col_add_path:
            del self.column_sel
            del self.add_predec
            del self.add_dec
        else:
            assert False

    def Network(self):
        R_wire_dec_out = 0
        C_ld_dec_out = 0
        bank_bus_length = 0
        area_bank_vertical_peripheral_circuitry = 0
        area_bank_horizontal_peripheral_circuitry = 0

        self.area_sense_amp = (self.mat_height - self.subarray_height) * self.mat_width * self.ndbl * self.ndwl
        self.area_subarray = self.subarray_height * self.subarray_width * self.ndbl * self.ndwl

        self.subarray_height = self.mat_height
        self.subarray_width = self.mat_width

        if g_ip.partition_gran == 0:
            self.height_bank = self.subarray_height * self.ndbl + (self.col_add_bits + self.row_add_bits) * g_tp.wire_outside_mat.pitch / 2 + self.data_bits * g_tp.wire_outside_mat.pitch
            self.length_bank = self.subarray_width * self.ndwl + (self.col_add_bits + self.row_add_bits) * g_tp.wire_outside_mat.pitch / 2 + self.data_bits * g_tp.wire_outside_mat.pitch
            self.area_address_bus = (self.row_add_bits + self.col_add_bits) * g_tp.wire_outside_mat.pitch * sp.sqrt(self.length_bank * self.height_bank)
            self.area_data_bus = self.data_bits * g_tp.wire_outside_mat.pitch * sp.sqrt(self.length_bank * self.height_bank)
        elif g_ip.partition_gran == 1:
            self.height_bank = self.subarray_height * self.ndbl
            self.length_bank = self.subarray_width * self.ndwl
            self.area_address_bus = 0
            self.area_data_bus = self.data_bits * g_tp.wire_outside_mat.pitch * sp.sqrt(self.length_bank * self.height_bank)
        elif g_ip.partition_gran == 2:
            self.height_bank = self.subarray_height * self.ndbl
            self.length_bank = self.subarray_width * self.ndwl
            self.area_address_bus = 0
            self.area_data_bus = 0

        if g_ip.print_detail_debug:
            print(f"memorybus.cc: N subarrays per mat = {self.dp.num_subarrays / self.dp.num_mats}")
            print(f"memorybus.cc: g_tp.wire_local.pitch = {g_tp.wire_local.pitch / 1e3} mm")
            print(f"memorybus.cc: subarray_width = {self.subarray_width / 1e3} mm")
            print(f"memorybus.cc: subarray_height = {self.subarray_height / 1e3} mm")
            print(f"memorybus.cc: mat_height = {self.mat_height / 1e3} mm")
            print(f"memorybus.cc: mat_width = {self.mat_width / 1e3} mm")
            print(f"memorybus.cc: height_bank = {self.height_bank / 1e3} mm")
            print(f"memorybus.cc: length_bank = {self.length_bank / 1e3} mm")

        num_banks_hor_dir = 1 << sp.ceiling(math.log2(g_ip.nbanks * g_ip.num_tier_row_sprd) / 2)
        num_banks_ver_dir = 1 << sp.ceiling(math.log2(g_ip.nbanks * g_ip.num_tier_col_sprd * g_ip.num_tier_row_sprd / num_banks_hor_dir))

        if g_ip.print_detail_debug:
            print(f"horz bank #: {num_banks_hor_dir}")
            print(f"vert bank #: {num_banks_ver_dir}")
            print(f"memorybus.cc: g_ip->nbanks = {g_ip.nbanks}")
            print(f"memorybus.cc: num_banks_hor_dir = {num_banks_hor_dir}")

        center_stripe_length = 0.5 * num_banks_hor_dir * self.height_bank
        if g_ip.print_detail_debug:
            print(f"memorybus.cc: center_stripe wire length = {center_stripe_length} um")

        self.center_stripe = Wire(self.wt, center_stripe_length)
        self.area_bus = 2.0 * center_stripe_length * (self.row_add_bits + self.col_add_bits + self.data_bits) * g_tp.wire_outside_mat.pitch / g_ip.nbanks

        if self.membus_type == MemorybusType.Row_add_path:
            num_lwl_per_gwl = 4
            self.global_WL = Wire(self.wt, self.length_bank, 1, 1, 1, 'inside_mat', CU_RESISTIVITY, g_tp.peri_global)
            self.num_lwl_drv = self.ndwl

            if self.semi_repeated_global_line:
                self.C_GWL = num_lwl_per_gwl * gate_C(g_tp.min_w_nmos + self.min_w_pmos, 0) + g_tp.wire_inside_mat.C_per_um * (self.subarray_width + g_tp.wire_local.pitch)
                self.R_GWL = g_tp.wire_inside_mat.R_per_um * (self.subarray_width + g_tp.wire_local.pitch)
            else:
                self.C_GWL = self.num_lwl_drv * num_lwl_per_gwl * gate_C(g_tp.min_w_nmos + self.min_w_pmos, 0) + g_tp.wire_inside_mat.C_per_um * self.length_bank
                self.R_GWL = self.length_bank * g_tp.wire_inside_mat.R_per_um

            self.lwl_driver_c_gate_load = self.dp.num_c_subarray * gate_C_pass(g_tp.dram.cell_a_w, g_tp.dram.b_w, True, True)
            self.lwl_driver_c_wire_load = self.dp.num_c_subarray * g_tp.dram.b_w * g_tp.wire_local.C_per_um
            self.lwl_driver_r_wire_load = self.dp.num_c_subarray * g_tp.dram.b_w * g_tp.wire_local.R_per_um
            self.C_LWL = self.lwl_driver_c_gate_load + self.lwl_driver_c_wire_load

            self.lwl_drv = Driver(self.lwl_driver_c_gate_load, self.lwl_driver_c_wire_load, self.lwl_driver_r_wire_load, self.is_dram)
            self.lwl_drv.compute_area()

            if not g_ip.fine_gran_bank_lvl:
                C_ld_dec_out = self.C_GWL
                R_wire_dec_out = self.R_GWL
            else:
                C_ld_dec_out = gate_C(g_tp.min_w_nmos + self.min_w_pmos, 0)
                R_wire_dec_out = 0

            bank_bus_length = num_banks_ver_dir * 0.5 * symbolic_convex_max(self.length_bank, self.height_bank)
            self.bank_bus = Wire(self.wt, bank_bus_length)

        elif self.membus_type == MemorybusType.Col_add_path:
            self.column_sel = Wire(self.wt, sp.sqrt(self.length_bank * self.height_bank), 1, 1, 1, 'outside_mat', CU_RESISTIVITY, g_tp.peri_global)

            if self.semi_repeated_global_line:
                self.C_colsel = g_tp.wire_inside_mat.C_per_um * (self.subarray_height + g_tp.wire_local.pitch)
                self.R_colsel = g_tp.wire_inside_mat.R_per_um * (self.subarray_height + g_tp.wire_local.pitch)
            else:
                self.C_colsel = self.column_sel.repeater_size * gate_C(g_tp.min_w_nmos + self.min_w_pmos, 0) + (self.column_sel.repeater_spacing if self.column_sel.repeater_spacing < self.height_bank else self.height_bank) * g_tp.wire_outside_mat.C_per_um
                self.R_colsel = (self.column_sel.repeater_spacing if self.column_sel.repeater_spacing < self.height_bank else self.height_bank) * g_tp.wire_outside_mat.R_per_um

            if not g_ip.fine_gran_bank_lvl:
                C_ld_dec_out = self.C_colsel
                R_wire_dec_out = self.R_colsel
            else:
                C_ld_dec_out = gate_C(g_tp.min_w_nmos + self.min_w_pmos, 0)
                R_wire_dec_out = 0

            bank_bus_length = num_banks_ver_dir * 0.5 * symbolic_convex_max(self.length_bank, self.height_bank)
            self.bank_bus = Wire(self.wt, bank_bus_length)

        elif self.membus_type == MemorybusType.Data_path:
            self.local_data = Wire(self.wt, self.subarray_width, 1, 1, 1, 'inside_mat', CU_RESISTIVITY, g_tp.peri_global)
            self.global_data = Wire(self.wt, sp.sqrt(self.length_bank * self.height_bank), 1, 1, 1, 'outside_mat', CU_RESISTIVITY, g_tp.peri_global)

            if self.semi_repeated_global_line:
                self.C_global_data = g_tp.wire_inside_mat.C_per_um * (self.subarray_height + g_tp.wire_local.pitch)
                self.R_global_data = g_tp.wire_inside_mat.R_per_um * (self.subarray_height + g_tp.wire_local.pitch)
            else:
                self.C_global_data = g_tp.wire_inside_mat.C_per_um * self.height_bank / 2
                self.R_global_data = g_tp.wire_inside_mat.R_per_um * self.height_bank / 2

            self.global_data_drv = Driver(0, self.C_global_data, self.R_global_data, self.is_dram)
            self.global_data_drv.compute_delay(0)
            self.global_data_drv.compute_area()

            local_data_c_gate_load = self.dp.num_c_subarray * drain_C_(g_tp.w_nmos_sa_mux, NCH, 1, 0, self.cell.w, self.is_dram)
            local_data_c_wire_load = self.dp.num_c_subarray * g_tp.dram.b_w * g_tp.wire_inside_mat.C_per_um
            local_data_r_wire_load = self.dp.num_c_subarray * g_tp.dram.b_w * g_tp.wire_inside_mat.R_per_um
            local_data_r_gate_load = 0

            tf = (local_data_c_gate_load + local_data_c_wire_load) * (local_data_r_wire_load + local_data_r_gate_load)
            this_delay = horowitz(0, tf, 0.5, 0.5, RISE)

            data_drv_c_gate_load = local_data_c_gate_load
            data_drv_c_wire_load = local_data_c_wire_load
            data_drv_r_wire_load = local_data_r_gate_load + local_data_r_wire_load

            self.local_data_drv = Driver(data_drv_c_gate_load, data_drv_c_wire_load, data_drv_r_wire_load, self.is_dram)
            self.local_data_drv.compute_delay(0)
            self.local_data_drv.compute_area()

            bank_bus_length = num_banks_ver_dir * 0.5 * symbolic_convex_max(self.length_bank, self.height_bank)
            self.bank_bus = Wire(self.wt, bank_bus_length)
            if g_ip.print_detail_debug:
                print(f"memorybus.cc: bank_bus_length = {bank_bus_length}")

            self.out_seg = Wire(self.wt, 0.25 * num_banks_hor_dir * (self.length_bank + (self.row_add_bits + self.col_add_bits + self.data_bits) * g_tp.wire_outside_mat.pitch))
            self.area_IOSA = (875 + 500) * g_ip.F_sz_um * g_ip.F_sz_um * self.data_bits
            self.area_data_drv = self.local_data_drv.area.get_area() * self.data_bits
            if self.ndbl > 16:
                self.area_IOSA *= self.ndbl / 16.0
                self.area_data_drv *= self.ndbl / 16.0
            self.area_local_dataline = self.data_bits * self.subarray_width * g_tp.wire_local.pitch * self.ndbl

        if self.membus_type in [MemorybusType.Row_add_path, MemorybusType.Col_add_path]:
            if g_ip.print_detail_debug:
                print(f"memorybus.cc: num_dec_signals = {self.num_dec_signals}")
                print(f"memorybus.cc: C_ld_dec_out = {C_ld_dec_out}")
                print(f"memorybus.cc: R_wire_dec_out = {R_wire_dec_out}")
                print(f"memorybus.cc: is_dram = {self.is_dram}")
                print(f"memorybus.cc: cell.h = {self.cell.h}")

            self.add_dec = Decoder(
                (self.num_dec_signals > 16) and self.num_dec_signals or 16,
                False,
                C_ld_dec_out,
                R_wire_dec_out,
                False,
                self.is_dram,
                self.membus_type == MemorybusType.Row_add_path,
                self.cell
            )

            C_wire_predec_blk_out = 0
            R_wire_predec_blk_out = 0

            num_dec_per_predec = 1
            add_predec_blk1 = PredecBlk(
                self.num_dec_signals,
                self.add_dec,
                C_wire_predec_blk_out,
                R_wire_predec_blk_out,
                num_dec_per_predec,
                self.is_dram,
                True
            )

            add_predec_blk2 = PredecBlk(
                self.num_dec_signals,
                self.add_dec,
                C_wire_predec_blk_out,
                R_wire_predec_blk_out,
                num_dec_per_predec,
                self.is_dram,
                False
            )

            add_predec_blk_drv1 = PredecBlkDrv(0, add_predec_blk1, self.is_dram)
            add_predec_blk_drv2 = PredecBlkDrv(0, add_predec_blk2, self.is_dram)

            self.add_predec = Predec(add_predec_blk_drv1, add_predec_blk_drv2)

            if self.membus_type == MemorybusType.Row_add_path:
                self.area_row_predec_dec = add_predec_blk_drv1.area.get_area() + add_predec_blk_drv2.area.get_area() + add_predec_blk1.area.get_area() + add_predec_blk2.area.get_area() + self.num_dec_signals * self.add_dec.area.get_area()
                self.area_lwl_drv = self.num_lwl_drv / 2.0 * self.dp.num_r_subarray * self.ndbl * self.lwl_drv.area.get_area()

                if g_ip.print_detail_debug:
                    print(f"memorybus.cc: area_bank_vertical_peripheral_circuitry = {area_bank_vertical_peripheral_circuitry / 1e6} mm2")
                    print(f"memorybus.cc: lwl drv area = {self.lwl_drv.area.get_area() / 1e6} mm2")
                    print(f"memorybus.cc: total lwl drv area = {self.num_lwl_drv * self.dp.num_r_subarray * self.ndbl * self.lwl_drv.area.get_area() / 1e6} mm2")
            elif self.membus_type == MemorybusType.Col_add_path:
                self.area_col_predec_dec = add_predec_blk_drv1.area.get_area() + add_predec_blk_drv2.area.get_area() + add_predec_blk1.area.get_area() + add_predec_blk2.area.get_area() + self.num_dec_signals * self.add_dec.area.get_area()
                if self.ndbl > 16:
                    self.area_col_predec_dec *= self.ndbl / 16.0

            self.area_bank_vertical_peripheral_circuitry = self.area_row_predec_dec + self.area_lwl_drv + self.area_address_bus + self.area_data_bus
            self.area_bank_horizontal_peripheral_circuitry = self.area_col_predec_dec + self.area_data_drv + (self.area_bus + self.area_IOSA) / g_ip.nbanks

            if g_ip.print_detail_debug:
                print(f"memorybus.cc: add_predec_blk_drv1->area = {add_predec_blk_drv1.area.get_area() / 1e6} mm2")
                print(f"memorybus.cc: add_predec_blk_drv2->area = {add_predec_blk_drv2.area.get_area() / 1e6} mm2")
                print(f"memorybus.cc: add_predec_blk1->area = {add_predec_blk1.area.get_area() / 1e6} mm2")
                print(f"memorybus.cc: add_predec_blk2->area = {add_predec_blk2.area.get_area() / 1e6} mm2")
                print(f"memorybus.cc: total add_dec->area = {self.num_dec_signals * self.add_dec.area.get_area() / 1e6} mm2")
                print(f"wire bus width for one bank = {g_tp.wire_outside_mat.pitch * (self.add_bits + self.add_bits + self.data_bits)}")

            self.area.h = (self.height_bank + self.area_bank_horizontal_peripheral_circuitry / self.length_bank) * num_banks_ver_dir
            self.area.w = (self.length_bank + self.area_bank_vertical_peripheral_circuitry / self.height_bank) * num_banks_hor_dir

            if g_ip.partition_gran == 0:
                self.area.h += g_tp.wire_outside_mat.pitch * (self.add_bits + self.add_bits + self.data_bits)
                self.area.w += g_tp.wire_outside_mat.pitch * (self.add_bits + self.add_bits + self.data_bits)

            if g_ip.print_detail_debug:
                print(f"memorybus.cc: circuit height = {self.area_bank_horizontal_peripheral_circuitry / self.length_bank / 1e3} mm")
                print(f"memorybus.cc: circuit length = {self.area_bank_vertical_peripheral_circuitry / self.height_bank / 1e3} mm")
                print(f"memorybus.cc: area.h = {self.area.h / 1e3} mm")
                print(f"memorybus.cc: area.w = {self.area.w / 1e3} mm")
                print(f"memorybus.cc: area = {self.area.get_area() / 1e6} mm2")

        self.compute_delays(0)
        self.compute_power_energy()

    def compute_delays(self, inrisetime):
        predec_outrisetime = 0
        add_dec_outrisetime = 0
        lwl_drv_outrisetime = 0

        if self.membus_type == MemorybusType.Data_path:
            self.delay = 0
            self.delay_bus = self.center_stripe.delay + self.bank_bus.delay
            self.delay += self.delay_bus

            self.delay_global_data = (self.global_data_drv.delay * self.num_subarray_global_IO) if self.semi_repeated_global_line > 0 else (self.global_data_drv.delay + self.global_data.delay)
            if g_ip.partition_gran in [0, 1]:
                self.delay += self.delay_global_data

            self.delay_local_data = self.local_data_drv.delay
            self.delay += self.delay_local_data
            self.delay_data_buffer = 2 * 1e-6 / g_ip.sys_freq_MHz
            self.delay += self.delay_data_buffer

            if g_ip.print_detail_debug:
                print(f"memorybus.cc: data path delay = {self.delay}")
            self.out_rise_time = 0

        else:
            self.delay = 0
            self.delay_bus = self.center_stripe.delay + self.bank_bus.delay
            self.delay += self.delay_bus
            predec_outrisetime = self.add_predec.compute_delays(inrisetime)
            add_dec_outrisetime = self.add_dec.compute_delays(predec_outrisetime)
            self.delay_add_predecoder = self.add_predec.delay
            self.delay += self.delay_add_predecoder

            if self.membus_type == MemorybusType.Row_add_path:
                if self.semi_repeated_global_line:
                    self.delay_add_decoder = self.add_dec.delay * self.ndwl
                    if g_ip.page_sz_bits > 8192:
                        self.delay_add_decoder /= (g_ip.page_sz_bits / 8192)
                else:
                    self.delay_add_decoder = self.add_dec.delay
                self.delay += self.delay_add_decoder

                lwl_drv_outrisetime = self.lwl_drv.compute_delay(add_dec_outrisetime)
                self.delay_lwl_drv = self.lwl_drv.delay
                if not g_ip.fine_gran_bank_lvl:
                    self.delay += self.delay_lwl_drv

                if g_ip.print_detail_debug:
                    print(f"memorybus.cc: row add path delay = {self.delay}")

                self.out_rise_time = lwl_drv_outrisetime

            elif self.membus_type == MemorybusType.Col_add_path:
                if self.semi_repeated_global_line:
                    self.delay_add_decoder = self.add_dec.delay * self.num_subarray_global_IO
                else:
                    self.delay += self.column_sel.delay
                    self.delay_add_decoder = self.add_dec.delay
                self.delay += self.delay_add_decoder

                self.out_rise_time = 0
                if g_ip.print_detail_debug:
                    print(f"memorybus.cc: column add path delay = {self.delay}")
            else:
                raise AssertionError("Invalid membus_type")

        self.out_rise_time = self.delay / (1.0 - 0.5)

        return self.out_rise_time
  
    def compute_power_energy(self):
        coeff1 = [float(self.add_bits)] * 4
        coeff2 = [float(self.data_bits)] * 4
        coeff3 = [float(self.num_lwl_drv)] * 4
        coeff4 = [float(self.burst_length * self.chip_IO_width)] * 4
        coeff5 = [float(self.ndwl)] * 4
        coeff6 = [float(self.num_subarray_global_IO)] * 4

        if self.membus_type == MemorybusType.Data_path:
            self.power_bus = (self.center_stripe.power + self.bank_bus.power) * coeff2
            self.power_local_data = self.local_data_drv.power * coeff2
            self.power_global_data = (self.global_data_drv.power * coeff2) if self.semi_repeated_global_line > 0 else (self.global_data_drv.power + self.global_data.power)
            self.power_global_data.readOp.dynamic += 1.8 / 1e3 * self.deviceType.Vdd * 10.0 / 1e9 / 64 * self.data_bits
            self.power = self.power_bus + self.power_local_data
            if not g_ip.fine_gran_bank_lvl:
                self.power += self.power_global_data

            self.power_burst = self.out_seg.power * coeff4
            if g_ip.print_detail_debug:
                print(f"memorybus.cc: data path center stripe energy = {self.center_stripe.power.readOp.dynamic * 1e9} nJ")
                print(f"memorybus.cc: data path bank bus energy = {self.bank_bus.power.readOp.dynamic * 1e9} nJ")
                print(f"memorybus.cc: data path data driver energy = {self.local_data_drv.power.readOp.dynamic * 1e9} nJ")

        elif self.membus_type == MemorybusType.Row_add_path:
            self.power_bus = (self.center_stripe.power + self.bank_bus.power) * coeff1
            self.power_add_predecoder = self.add_predec.power
            if self.semi_repeated_global_line:
                self.power_add_decoders = self.add_dec.power * coeff5
                if g_ip.page_sz_bits > 8192:
                    self.power_add_decoders.readOp.dynamic /= (g_ip.page_sz_bits / 8192)
            else:
                self.power_add_decoders = self.add_dec.power
            self.power_lwl_drv = self.lwl_drv.power * coeff3
            self.power = self.power_bus + self.power_add_predecoder + self.power_add_decoders + self.power_lwl_drv

        elif self.membus_type == MemorybusType.Col_add_path:
            self.power_bus = (self.center_stripe.power + self.bank_bus.power) * coeff1
            self.power_add_predecoder = self.add_predec.power
            if self.semi_repeated_global_line:
                self.power_add_decoders = self.add_dec.power * coeff6
                self.power_add_decoders.readOp.dynamic = self.power_add_decoders.readOp.dynamic * g_ip.page_sz_bits / self.data_bits
                self.power_col_sel.readOp.dynamic = 0
            else:
                self.power_add_decoders = self.add_dec.power
                self.power_col_sel.readOp.dynamic = self.column_sel.power.readOp.dynamic * g_ip.page_sz_bits / self.data_bits
            self.power = self.power_bus + self.power_add_predecoder + self.power_add_decoders
            if not g_ip.fine_gran_bank_lvl:
                self.power += self.power_col_sel

        else:
            raise AssertionError("Invalid membus_type")

