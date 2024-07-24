import math
import enum
from .parameter import g_tp
from .component import *
from .wire import Wire

class HtreeType(enum.Enum):
    Add_htree = 1
    Data_in_htree = 2
    Data_out_htree = 3
    Search_in_htree = 4
    Search_out_htree = 5

class WireType(enum.Enum):
    Global = 1
    SemiGlobal = 2
    Local = 3

class DeviceType:
    def __init__(self, n_to_p_eff_curr_drv_ratio, Vth, Vdd):
        self.n_to_p_eff_curr_drv_ratio = n_to_p_eff_curr_drv_ratio
        self.Vth = Vth
        self.Vdd = Vdd

class Htree2(Component):
    def __init__(self, wire_model, mat_w, mat_h, a_bits, d_inbits, search_data_in, d_outbits, search_data_out, bl, wl, htree_type, uca_tree_=False, search_tree_=False, dt=None):
        super().__init__()
        if dt is None:
            dt = g_tp.peri_global
        self.in_rise_time = 0
        self.out_rise_time = 0
        self.tree_type = htree_type
        self.mat_width = mat_w
        self.mat_height = mat_h
        self.add_bits = a_bits
        self.data_in_bits = d_inbits
        self.search_data_in_bits = search_data_in
        self.data_out_bits = d_outbits
        self.search_data_out_bits = search_data_out
        self.ndbl = bl
        self.ndwl = wl
        self.uca_tree = uca_tree_
        self.search_tree = search_tree_
        self.wt = wire_model
        self.deviceType = dt

        assert self.ndbl >= 2 and self.ndwl >= 2

        self.max_unpipelined_link_delay = 0  # TODO
        self.min_w_nmos = g_tp.min_w_nmos_
        self.min_w_pmos = self.deviceType.n_to_p_eff_curr_drv_ratio * self.min_w_nmos

        # TODO have to fix the HtreeType
        self.wire_bw = self.init_wire_bw = 0
        print(f"SEE TREE TYPE! {self.tree_type}")

        if self.tree_type == "Add_htree":
            self.wire_bw = self.init_wire_bw = self.add_bits
            self.in_htree()
        elif self.tree_type == "Data_in_htree":
            self.wire_bw = self.init_wire_bw = self.data_in_bits
            self.in_htree()
        elif self.tree_type == "Data_out_htree":
            self.wire_bw = self.init_wire_bw = self.data_out_bits
            self.out_htree()
        elif self.tree_type == "Search_in_htree":
            self.wire_bw = self.init_wire_bw = self.search_data_in_bits
            self.in_htree()
        elif self.tree_type == "Search_out_htree":
            self.wire_bw = self.init_wire_bw = self.search_data_out_bits
            self.out_htree()
        else:
            print(f'Failed and the tree type is {self.tree_type}')
            assert False

        self.power_bit = self.power
        self.power.readOp.dynamic *= self.init_wire_bw

        # assert self.power.readOp.dynamic >= 0
        # assert self.power.readOp.leakage >= 0

    def input_nand(self, s1, s2, l_eff):
        w1 = Wire(self.wt, l_eff)
        pton_size = self.deviceType.n_to_p_eff_curr_drv_ratio
        nsize = s1 * (1 + pton_size) / (2 + pton_size)
        nsize = symbolic_convex_max(1, nsize)

        tc = 2 * tr_R_on(nsize * self.min_w_nmos, NCH, 1) * (
            drain_C_(nsize * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) * 2 +
            2 * gate_C(s2 * (self.min_w_nmos + self.min_w_pmos), 0)
        )
        self.delay += horowitz(w1.out_rise_time, tc,
                               self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, RISE)
        self.power.readOp.dynamic += 0.5 * (
            2 * drain_C_(pton_size * nsize * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(nsize * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) +
            2 * gate_C(s2 * (self.min_w_nmos + self.min_w_pmos), 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd

        self.power.searchOp.dynamic += 0.5 * (
            2 * drain_C_(pton_size * nsize * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(nsize * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) +
            2 * gate_C(s2 * (self.min_w_nmos + self.min_w_pmos), 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd * self.wire_bw
        self.power.readOp.leakage += (self.wire_bw * cmos_Isub_leakage(nsize * self.min_w_nmos * 2, self.min_w_pmos * nsize * 2, 2, nand)) * self.deviceType.Vdd
        self.power.readOp.gate_leakage += (self.wire_bw * cmos_Ig_leakage(nsize * self.min_w_nmos * 2, self.min_w_pmos * nsize * 2, 2, nand)) * self.deviceType.Vdd

    def output_buffer(self, s1, s2, l_eff):
        w1 = Wire(self.wt, l_eff)
        pton_size = self.deviceType.n_to_p_eff_curr_drv_ratio
        size = s1 * (1 + pton_size) / (2 + pton_size + 1 + 2 * pton_size)
        s_eff = (gate_C(s2 * (self.min_w_nmos + self.min_w_pmos), 0) + w1.wire_cap(l_eff * 1e-6, True)) / gate_C(s2 * (self.min_w_nmos + self.min_w_pmos), 0)
        tr_size = gate_C(s1 * (self.min_w_nmos + self.min_w_pmos), 0) * 1 / 2 / (s_eff * gate_C(self.min_w_pmos, 0))
        size = symbolic_convex_max(1, size)

        res_nor = 2 * tr_R_on(size * self.min_w_pmos, PCH, 1)
        res_ptrans = tr_R_on(tr_size * self.min_w_nmos, NCH, 1)
        cap_nand_out = drain_C_(size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) + drain_C_(size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) * 2 + gate_C(tr_size * self.min_w_pmos, 0)
        cap_ptrans_out = 2 * (drain_C_(tr_size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) + drain_C_(tr_size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def)) + gate_C(s1 * (self.min_w_nmos + self.min_w_pmos), 0)

        tc = res_nor * cap_nand_out + (res_nor + res_ptrans) * cap_ptrans_out

        self.delay += horowitz(w1.out_rise_time, tc,
                               self.deviceType.Vth / self.deviceType.Vdd, self.deviceType.Vth / self.deviceType.Vdd, RISE)

        self.power.readOp.dynamic += 0.5 * (
            2 * drain_C_(size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) +
            gate_C(tr_size * self.min_w_pmos, 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd

        self.power.searchOp.dynamic += 0.5 * (
            2 * drain_C_(size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) +
            gate_C(tr_size * self.min_w_pmos, 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd * self.init_wire_bw

        self.power.readOp.dynamic += 0.5 * (
            drain_C_(size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) +
            gate_C(size * (self.min_w_nmos + self.min_w_pmos), 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd

        self.power.searchOp.dynamic += 0.5 * (
            drain_C_(size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) +
            gate_C(size * (self.min_w_nmos + self.min_w_pmos), 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd * self.init_wire_bw

        self.power.readOp.dynamic += 0.5 * (
            drain_C_(size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            2 * drain_C_(size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) +
            gate_C(tr_size * (self.min_w_nmos + self.min_w_pmos), 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd

        self.power.searchOp.dynamic += 0.5 * (
            drain_C_(size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            2 * drain_C_(size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) +
            gate_C(tr_size * (self.min_w_nmos + self.min_w_pmos), 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd * self.init_wire_bw

        self.power.readOp.dynamic += 0.5 * (
            drain_C_(tr_size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(tr_size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) * 2 +
            gate_C(s1 * (self.min_w_nmos + self.min_w_pmos), 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd

        self.power.searchOp.dynamic += 0.5 * (
            drain_C_(tr_size * self.min_w_pmos, PCH, 1, 1, g_tp.cell_h_def) +
            drain_C_(tr_size * self.min_w_nmos, NCH, 1, 1, g_tp.cell_h_def) * 2 +
            gate_C(s1 * (self.min_w_nmos + self.min_w_pmos), 0)
        ) * self.deviceType.Vdd * self.deviceType.Vdd * self.init_wire_bw

        if self.uca_tree:
            self.power.readOp.leakage += cmos_Isub_leakage(self.min_w_nmos * tr_size * 2, self.min_w_pmos * tr_size * 2, 1, inv) * self.deviceType.Vdd * self.wire_bw
            self.power.readOp.leakage += cmos_Isub_leakage(self.min_w_nmos * size * 3, self.min_w_pmos * size * 3, 2, nand) * self.deviceType.Vdd * self.wire_bw
            self.power.readOp.leakage += cmos_Isub_leakage(self.min_w_nmos * size * 3, self.min_w_pmos * size * 3, 2, nor) * self.deviceType.Vdd * self.wire_bw

            self.power.readOp.gate_leakage += cmos_Ig_leakage(self.min_w_nmos * tr_size * 2, self.min_w_pmos * tr_size * 2, 1, inv) * self.deviceType.Vdd * self.wire_bw
            self.power.readOp.gate_leakage += cmos_Ig_leakage(self.min_w_nmos * size * 3, self.min_w_pmos * size * 3, 2, nand) * self.deviceType.Vdd * self.wire_bw
            self.power.readOp.gate_leakage += cmos_Ig_leakage(self.min_w_nmos * size * 3, self.min_w_pmos * size * 3, 2, nor) * self.deviceType.Vdd * self.wire_bw
        else:
            self.power.readOp.leakage += cmos_Isub_leakage(self.min_w_nmos * tr_size * 2, self.min_w_pmos * tr_size * 2, 1, inv) * self.deviceType.Vdd * self.wire_bw
            self.power.readOp.leakage += cmos_Isub_leakage(self.min_w_nmos * size * 3, self.min_w_pmos * size * 3, 2, nand) * self.deviceType.Vdd * self.wire_bw
            self.power.readOp.leakage += cmos_Isub_leakage(self.min_w_nmos * size * 3, self.min_w_pmos * size * 3, 2, nor) * self.deviceType.Vdd * self.wire_bw

            self.power.readOp.gate_leakage += cmos_Ig_leakage(self.min_w_nmos * tr_size * 2, self.min_w_pmos * tr_size * 2, 1, inv) * self.deviceType.Vdd * self.wire_bw
            self.power.readOp.gate_leakage += cmos_Ig_leakage(self.min_w_nmos * size * 3, self.min_w_pmos * size * 3, 2, nand) * self.deviceType.Vdd * self.wire_bw
            self.power.readOp.gate_leakage += cmos_Ig_leakage(self.min_w_nmos * size * 3, self.min_w_pmos * size * 3, 2, nor) * self.deviceType.Vdd * self.wire_bw

    def in_htree(self):
        # temp var
        s1, s2, s3 = 0, 0, 0
        l_eff = 0
        wtemp1, wtemp2, wtemp3 = None, None, None
        len_temp, ht_temp = 0, 0
        option = 0

        #TODO deleted ints
        h = math.log2(self.ndwl / 2)  # horizontal nodes
        v = math.log2(self.ndbl / 2)  # vertical nodes

        if self.uca_tree:
            # this computation does not consider the wires that route from edge to middle
            ht_temp = (self.mat_height * self.ndbl / 2 +
                       ((self.add_bits + self.data_in_bits + self.data_out_bits + (self.search_data_in_bits + self.search_data_out_bits)) * g_tp.wire_outside_mat.pitch *
                        2 * (1 - pow(0.5, h)))) / 2
            len_temp = (self.mat_width * self.ndwl / 2 +
                        ((self.add_bits + self.data_in_bits + self.data_out_bits + (self.search_data_in_bits + self.search_data_out_bits)) * g_tp.wire_outside_mat.pitch *
                         2 * (1 - pow(0.5, v)))) / 2
        else:
            if self.ndwl == self.ndbl:
                ht_temp = ((self.mat_height * self.ndbl / 2) +
                           ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * (self.ndbl / 2 - 1) * g_tp.wire_outside_mat.pitch) +
                           ((self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * h)) / 2
                len_temp = (self.mat_width * self.ndwl / 2 +
                            ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * (self.ndwl / 2 - 1) * g_tp.wire_outside_mat.pitch) +
                            ((self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * v)) / 2
            elif self.ndwl > self.ndbl:
                excess_part = (math.log2(self.ndwl / 2) - math.log2(self.ndbl / 2))
                ht_temp = ((self.mat_height * self.ndbl / 2) +
                           ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * ((self.ndbl / 2 - 1) + excess_part) * g_tp.wire_outside_mat.pitch) +
                           (self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch *
                           (2 * (1 - pow(0.5, h - v)) + pow(0.5, v - h) * v)) / 2
                len_temp = (self.mat_width * self.ndwl / 2 +
                            ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * (self.ndwl / 2 - 1) * g_tp.wire_outside_mat.pitch) +
                            ((self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * v)) / 2
            else:
                excess_part = (math.log2(self.ndbl / 2) - math.log2(self.ndwl / 2))
                ht_temp = ((self.mat_height * self.ndbl / 2) +
                           ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * ((self.ndwl / 2 - 1) + excess_part) * g_tp.wire_outside_mat.pitch) +
                           ((self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * h)) / 2
                len_temp = (self.mat_width * self.ndwl / 2 +
                            ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * ((self.ndwl / 2 - 1) + excess_part) * g_tp.wire_outside_mat.pitch) +
                            (self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * (h + 2 * (1 - pow(0.5, v - h)))) / 2

        self.area.h = ht_temp * 2
        self.area.w = len_temp * 2
        self.delay = 0
        self.power.readOp.dynamic = 0
        self.power.readOp.leakage = 0
        self.power.searchOp.dynamic = 0
        len = len_temp
        ht = ht_temp / 2

        while v > 0 or h > 0:
            if wtemp1:
                del wtemp1
            if wtemp2:
                del wtemp2
            if wtemp3:
                del wtemp3

            if h > v:
                # the iteration considers only one horizontal link
                wtemp1 = Wire(self.wt, len)  # hor
                wtemp2 = Wire(self.wt, len / 2)  # ver
                len_temp = len
                len /= 2
                wtemp3 = None
                h -= 1
                option = 0
            elif v > 0 and h > 0:
                # considers one horizontal link and one vertical link
                wtemp1 = Wire(self.wt, len)  # hor
                wtemp2 = Wire(self.wt, ht)  # ver
                wtemp3 = Wire(self.wt, len / 2)  # next hor
                len_temp = len
                ht_temp = ht
                len /= 2
                ht /= 2
                v -= 1
                h -= 1
                option = 1
            else:
                # considers only one vertical link
                assert h == 0
                wtemp1 = Wire(self.wt, ht)  # ver
                wtemp2 = Wire(self.wt, ht / 2)  # hor
                ht_temp = ht
                ht /= 2
                wtemp3 = None
                v -= 1
                option = 2

            self.delay += wtemp1.delay
            self.power.readOp.dynamic += wtemp1.power.readOp.dynamic
            self.power.searchOp.dynamic += wtemp1.power.readOp.dynamic * self.wire_bw
            self.power.readOp.leakage += wtemp1.power.readOp.leakage * self.wire_bw
            self.power.readOp.gate_leakage += wtemp1.power.readOp.gate_leakage * self.wire_bw
            if not self.uca_tree and option == 2 or self.search_tree:
                self.wire_bw *= 2  # wire bandwidth doubles only for vertical branches

            if not self.uca_tree:
                # TODO important relational cannot handle
                # if len_temp > wtemp1.repeater_spacing:
                #     s1 = wtemp1.repeater_size
                #     l_eff = wtemp1.repeater_spacing
                # else:
                #     s1 = (len_temp / wtemp1.repeater_spacing) * wtemp1.repeater_size
                #     l_eff = len_temp

                s1 = sp.Piecewise(
                    (wtemp1.repeater_size, len_temp > wtemp1.repeater_spacing),
                    ((len_temp / wtemp1.repeater_spacing) * wtemp1.repeater_size, True)
                )

                l_eff = sp.Piecewise(
                    (wtemp1.repeater_spacing, len_temp > wtemp1.repeater_spacing),
                    (len_temp, True)
                )

                # TODO important relational cannot handle
                # if ht_temp > wtemp2.repeater_spacing:
                #     s2 = wtemp2.repeater_size
                # else:
                #     s2 = (len_temp / wtemp2.repeater_spacing) * wtemp2.repeater_size

                s2 = sp.Piecewise(
                    (wtemp2.repeater_size, ht_temp > wtemp2.repeater_spacing),
                    ((len_temp / wtemp2.repeater_spacing) * wtemp2.repeater_size, True)
                )

                # first level
                self.input_nand(s1, s2, l_eff)

            if option != 1:
                continue

            # second level
            self.delay += wtemp2.delay
            self.power.readOp.dynamic += wtemp2.power.readOp.dynamic
            self.power.searchOp.dynamic += wtemp2.power.readOp.dynamic * self.wire_bw
            self.power.readOp.leakage += wtemp2.power.readOp.leakage * self.wire_bw
            self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage * self.wire_bw

            if self.uca_tree:
                self.power.readOp.leakage += (wtemp2.power.readOp.leakage * self.wire_bw)
                self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage * self.wire_bw
            else:
                self.power.readOp.leakage += (wtemp2.power.readOp.leakage * self.wire_bw)
                self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage * self.wire_bw
                self.wire_bw *= 2

                # TODO RELATIONAL
                # if ht_temp > wtemp3.repeater_spacing:
                # s3 = wtemp3.repeater_size
                # l_eff = wtemp3.repeater_spacing
                # else:
                #     s3 = (len_temp / wtemp3.repeater_spacing) * wtemp3.repeater_size
                #     l_eff = ht_temp

                s3 = sp.Piecewise(
                    (wtemp3.repeater_size, ht_temp > wtemp3.repeater_spacing),
                    ((len_temp / wtemp3.repeater_spacing) * wtemp3.repeater_size, True)
                )

                l_eff = sp.Piecewise(
                    (wtemp3.repeater_spacing, ht_temp > wtemp3.repeater_spacing),
                    (ht_temp, True)
                )

                self.input_nand(s2, s3, l_eff)

        if wtemp1:
            del wtemp1
        if wtemp2:
            del wtemp2
        if wtemp3:
            del wtemp3

    def out_htree(self):
        # temp var
        s1, s2, s3 = 0, 0, 0
        l_eff = 0
        wtemp1, wtemp2, wtemp3 = None, None, None
        len_temp, ht_temp = 0, 0
        option = 0

        #TODO deleted int
        h = math.log2(self.ndwl / 2)
        v = math.log2(self.ndbl / 2)

        if self.uca_tree:
            ht_temp = (self.mat_height * self.ndbl / 2 +
                       ((self.add_bits + self.data_in_bits + self.data_out_bits + (self.search_data_in_bits + self.search_data_out_bits)) * g_tp.wire_outside_mat.pitch *
                        2 * (1 - pow(0.5, h)))) / 2
            len_temp = (self.mat_width * self.ndwl / 2 +
                        ((self.add_bits + self.data_in_bits + self.data_out_bits + (self.search_data_in_bits + self.search_data_out_bits)) * g_tp.wire_outside_mat.pitch *
                         2 * (1 - pow(0.5, v)))) / 2
        else:
            if self.ndwl == self.ndbl:
                ht_temp = ((self.mat_height * self.ndbl / 2) +
                           ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * (self.ndbl / 2 - 1) * g_tp.wire_outside_mat.pitch) +
                           ((self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * h)) / 2
                len_temp = (self.mat_width * self.ndwl / 2 +
                            ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * (self.ndwl / 2 - 1) * g_tp.wire_outside_mat.pitch) +
                            ((self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * v)) / 2
            elif self.ndwl > self.ndbl:
                excess_part = (math.log2(self.ndwl / 2) - math.log2(self.ndbl / 2))
                ht_temp = ((self.mat_height * self.ndbl / 2) +
                           ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * ((self.ndbl / 2 - 1) + excess_part) * g_tp.wire_outside_mat.pitch) +
                           (self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch *
                           (2 * (1 - pow(0.5, h - v)) + pow(0.5, v - h) * v)) / 2
                len_temp = (self.mat_width * self.ndwl / 2 +
                            ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * (self.ndwl / 2 - 1) * g_tp.wire_outside_mat.pitch) +
                            ((self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * v)) / 2
            else:
                excess_part = (math.log2(self.ndbl / 2) - math.log2(self.ndwl / 2))
                ht_temp = ((self.mat_height * self.ndbl / 2) +
                           ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * ((self.ndwl / 2 - 1) + excess_part) * g_tp.wire_outside_mat.pitch) +
                           ((self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * h)) / 2
                len_temp = (self.mat_width * self.ndwl / 2 +
                            ((self.add_bits + (self.search_data_in_bits + self.search_data_out_bits)) * ((self.ndwl / 2 - 1) + excess_part) * g_tp.wire_outside_mat.pitch) +
                            (self.data_in_bits + self.data_out_bits) * g_tp.wire_outside_mat.pitch * (h + 2 * (1 - pow(0.5, v - h)))) / 2

        self.area.h = ht_temp * 2
        self.area.w = len_temp * 2
        self.delay = 0
        self.power.readOp.dynamic = 0
        self.power.readOp.leakage = 0
        self.power.readOp.gate_leakage = 0
        len = len_temp
        ht = ht_temp / 2

        while v > 0 or h > 0:
            if wtemp1:
                del wtemp1
            if wtemp2:
                del wtemp2
            if wtemp3:
                del wtemp3

            if h > v:
                # the iteration considers only one horizontal link
                wtemp1 = Wire(self.wt, len)  # hor
                wtemp2 = Wire(self.wt, len / 2)  # ver
                len_temp = len
                len /= 2
                wtemp3 = None
                h -= 1
                option = 0
            elif v > 0 and h > 0:
                # considers one horizontal link and one vertical link
                wtemp1 = Wire(self.wt, len)  # hor
                wtemp2 = Wire(self.wt, ht)  # ver
                wtemp3 = Wire(self.wt, len / 2)  # next hor
                len_temp = len
                ht_temp = ht
                len /= 2
                ht /= 2
                v -= 1
                h -= 1
                option = 1
            else:
                # considers only one vertical link
                assert h == 0
                wtemp1 = Wire(self.wt, ht)  # hor
                wtemp2 = Wire(self.wt, ht / 2)  # ver
                ht_temp = ht
                ht /= 2
                wtemp3 = None
                v -= 1
                option = 2

            self.delay += wtemp1.delay
            self.power.readOp.dynamic += wtemp1.power.readOp.dynamic
            self.power.searchOp.dynamic += wtemp1.power.readOp.dynamic * self.init_wire_bw
            self.power.readOp.leakage += wtemp1.power.readOp.leakage * self.wire_bw
            self.power.readOp.gate_leakage += wtemp1.power.readOp.gate_leakage * self.wire_bw

            if not self.uca_tree and option == 2 or self.search_tree:
                self.wire_bw *= 2

            if not self.uca_tree:
                # TODO relational
                # if len_temp > wtemp1.repeater_spacing:
                #     s1 = wtemp1.repeater_size
                #     l_eff = wtemp1.repeater_spacing
                # else:
                #     s1 = (len_temp / wtemp1.repeater_spacing) * wtemp1.repeater_size
                #     l_eff = len_temp

                # # TODO relational
                # if ht_temp > wtemp2.repeater_spacing:
                #     s2 = wtemp2.repeater_size
                # else:
                #     s2 = (len_temp / wtemp2.repeater_spacing) * wtemp2.repeater_size

                s1 = sp.Piecewise(
                    (wtemp1.repeater_size, len_temp > wtemp1.repeater_spacing),
                    ((len_temp / wtemp1.repeater_spacing) * wtemp1.repeater_size, True)
                )

                l_eff = sp.Piecewise(
                    (wtemp1.repeater_spacing, len_temp > wtemp1.repeater_spacing),
                    (len_temp, True)
                )

                s2 = sp.Piecewise(
                    (wtemp2.repeater_size, ht_temp > wtemp2.repeater_spacing),
                    ((len_temp / wtemp2.repeater_spacing) * wtemp2.repeater_size, True)
                )

                # first level
                self.output_buffer(s1, s2, l_eff)

            if option != 1:
                continue

            # second level
            self.delay += wtemp2.delay
            self.power.readOp.dynamic += wtemp2.power.readOp.dynamic
            self.power.searchOp.dynamic += wtemp2.power.readOp.dynamic * self.init_wire_bw
            self.power.readOp.leakage += wtemp2.power.readOp.leakage * self.wire_bw
            self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage * self.wire_bw

            if self.uca_tree:
                self.power.readOp.leakage += (wtemp2.power.readOp.leakage * self.wire_bw)
                self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage * self.wire_bw
            else:
                self.power.readOp.leakage += (wtemp2.power.readOp.leakage * self.wire_bw)
                self.power.readOp.gate_leakage += wtemp2.power.readOp.gate_leakage * self.wire_bw
                self.wire_bw *= 2

                # TODO RELATONAL
                # if ht_temp > wtemp3.repeater_spacing:
                #     s3 = wtemp3.repeater_size
                #     l_eff = wtemp3.repeater_spacing
                # else:
                #     s3 = (len_temp / wtemp3.repeater_spacing) * wtemp3.repeater_size
                #     l_eff = ht_temp

                s3 = sp.Piecewise(
                    (wtemp3.repeater_size, ht_temp > wtemp3.repeater_spacing),
                    ((len_temp / wtemp3.repeater_spacing) * wtemp3.repeater_size, True)
                )

                l_eff = sp.Piecewise(
                    (wtemp3.repeater_spacing, ht_temp > wtemp3.repeater_spacing),
                    (ht_temp, True)
                )

                self.output_buffer(s2, s3, l_eff)

        if wtemp1:
            del wtemp1
        if wtemp2:
            del wtemp2
        if wtemp3:
            del wtemp3