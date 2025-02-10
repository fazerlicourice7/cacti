# subarray.py

from .component import Component
from .area import Area
from const import *

from .basic_circuit import (
    is_pow2, _log2, is_equal,
    wire_resistance, wire_capacitance, tsv_resistance, tsv_capacitance, tsv_area,
    pmos_to_nmos_sz_ratio, gate_C, gate_C_pass, tr_R_on, drain_C_, cmos_Ig_leakage,
    horowitz, cmos_Isub_leakage, simplified_nmos_Isat
)

import math
import sys

class Subarray(Component):
    def __init__(self, dp, is_fa_):
        """
        Python version of Subarray::Subarray(const DynamicParameter & dp_, bool is_fa_)
        """
        super().__init__()  # Initialize base Component
        self.dp = dp
        self.is_fa = is_fa_

        # Mirror the C++ members:
        self.num_rows        = dp.num_r_subarray
        self.num_cols        = dp.num_c_subarray
        self.num_cols_fa_cam = dp.tag_num_c_subarray
        self.num_cols_fa_ram = dp.data_num_c_subarray
        self.cell            = dp.cell         # Typically an Area instance or similar
        self.cam_cell        = dp.cam_cell     # Also an Area instance
        self.C_wl            = 0.0
        self.C_wl_cam        = 0.0
        self.C_wl_ram        = 0.0
        self.R_wl            = 0.0
        self.R_wl_cam        = 0.0
        self.R_wl_ram        = 0.0
        self.C_bl            = 0.0
        self.C_bl_cam        = 0.0

        # CEHCK THIS DOESN't INTERFERE
        g_ip = self.dp.g_ip
        g_tp = self.dp.g_tp

        # Now replicate the logic in subarray.cc constructor:
        # "if (!(is_fa || dp.pure_cam)) { ... } else { ... }"
        if not (self.is_fa or dp.pure_cam):
            # ECC overhead
            if g_ip.add_ecc_b_:
                self.num_cols += math.ceil(self.num_cols / num_bits_per_ecc_b_)

            # For stitching overhead, pick the relevant ram_num_cells_wl_stitching
            if dp.ram_cell_tech_type == lp_dram:
                ram_num_cells_wl_stitching = dram_num_cells_wl_stitching_
            elif dp.ram_cell_tech_type == comm_dram:
                ram_num_cells_wl_stitching = comm_dram_num_cells_wl_stitching_
            else:
                ram_num_cells_wl_stitching = sram_num_cells_wl_stitching_

            # area.h = cell.h * num_rows
            self.area.h = self.cell.h * self.num_rows

            # area.w = cell.w * num_cols + overhead
            # ERROR CHECK MATH.CEIL
            overhead = math.ceil(self.num_cols / ram_num_cells_wl_stitching) * g_tp.ram_wl_stitching_overhead_
            self.area.w = self.cell.w * self.num_cols + overhead

            # Debug if needed:
            # if g_ip.print_detail_debug:
            #     print("subarray.cc: ram_num_cells_wl_stitching =", ram_num_cells_wl_stitching)
            #     print("subarray.cc: g_tp.ram_wl_stitching_overhead_ =", g_tp.ram_wl_stitching_overhead_, "um")

        else:
            # cam or fully-associative
            # "if (is_fa) { ... } else { ... }"
            if self.is_fa:
                if g_ip.add_ecc_b_:
                    self.num_cols_fa_cam += math.ceil(self.num_cols_fa_cam / num_bits_per_ecc_b_)
                    self.num_cols_fa_ram += math.ceil(self.num_cols_fa_ram / num_bits_per_ecc_b_)
                self.num_cols = self.num_cols_fa_cam + self.num_cols_fa_ram
            else:
                # pure CAM but not FA
                if g_ip.add_ecc_b_:
                    self.num_cols_fa_cam += math.ceil(self.num_cols_fa_cam / num_bits_per_ecc_b_)
                self.num_cols_fa_ram = 0
                self.num_cols        = self.num_cols_fa_cam

            # area.h => cam_cell.h * (num_rows + 1)
            # area.w => cam_cell.w * num_cols_fa_cam + cell.w * num_cols_fa_ram ...
            self.area.h = self.cam_cell.h * (self.num_rows + 1)

            overhead_stitching = math.ceil((self.num_cols_fa_cam + self.num_cols_fa_ram) / sram_num_cells_wl_stitching_) \
                                 * g_tp.ram_wl_stitching_overhead_

            # overhead for NAND gate to connect two halves => 16*g_tp.wire_local.pitch
            # overhead for the drivers from matchline to RAM => 128*g_tp.wire_local.pitch
            other_overhead = (16 + 128) * g_tp.wire_local.pitch

            self.area.w = (self.cam_cell.w * self.num_cols_fa_cam
                           + self.cell.w * self.num_cols_fa_ram
                           + overhead_stitching
                           + other_overhead)

        # Basic checks:
        assert self.area.h > 0, "area.h must be > 0"
        assert self.area.w > 0, "area.w must be > 0"

        # Finally, call compute_C to compute bitline/wordline caps
        self.compute_C()


    def compute_C(self):
        """
        Python version of Subarray::compute_C().
        Fills in C_wl, R_wl, C_bl, etc. based on DP.
        """
        # We'll need to reference the global technology parameters, e.g. g_tp, g_ip
        # In your C++ code, you do:
        #   double c_w_metal = cell.w * g_tp.wire_local.C_per_um;
        #   ...
        # Let’s replicate that logic:

        g_ip = self.dp.g_ip
        g_tp = self.dp.g_tp

        c_w_metal = self.cell.w * g_tp.wire_local.C_per_um
        r_w_metal = self.cell.w * g_tp.wire_local.R_per_um
        C_b_metal = self.cell.h * g_tp.wire_local.C_per_um  # for bitline

        if self.dp.is_dram:
            # DRAM path
            # Wordline cap
            self.C_wl = ( gate_C_pass(g_tp.dram.cell_a_w, g_tp.dram.b_w, True, True ) + c_w_metal ) * self.num_cols

            # Bitline cap depends on comm_dram vs. others
            if self.dp.ram_cell_tech_type == comm_dram:
                self.C_bl = self.num_rows * C_b_metal
            else:
                # shared contact => factor of 1/2
                C_b_row_drain_C = drain_C_(g_tp.dram.cell_a_w, NCH, 1, 0, self.cell.w, True, True)/2.0
                self.C_bl = self.num_rows * (C_b_row_drain_C + C_b_metal)
        else:
            # SRAM or CAM/FA
            if not (self.is_fa or self.dp.pure_cam):
                # normal SRAM subarray
                self.C_wl = (
                    gate_C_pass(
                        g_tp.sram.cell_a_w,
                        (g_tp.sram.b_w - 2*g_tp.sram.cell_a_w)/2.0,
                        False, True
                    )*2
                    + c_w_metal
                ) * self.num_cols

                # bitline
                C_b_row_drain_C = drain_C_(
                    g_tp.sram.cell_a_w, NCH, 1, 0, self.cell.w, False, True
                ) / 2.0
                self.C_bl = self.num_rows * (C_b_row_drain_C + C_b_metal)

            else:
                # CAM / fully assoc
                # --- CAM portion:
                c_w_metal_cam  = self.cam_cell.w * g_tp.wire_local.C_per_um
                r_w_metal_cam  = self.cam_cell.w * g_tp.wire_local.R_per_um
                self.C_wl_cam  = (
                    gate_C_pass(
                        g_tp.cam.cell_a_w,
                        (g_tp.cam.b_w - 2*g_tp.cam.cell_a_w)/2.0,
                        False, True
                    )*2
                    + c_w_metal_cam
                ) * self.num_cols_fa_cam

                self.R_wl_cam  = r_w_metal_cam * self.num_cols_fa_cam

                if not self.dp.pure_cam:
                    # RAM portion in FA
                    c_w_metal_ram = self.cell.w * g_tp.wire_local.C_per_um
                    r_w_metal_ram = self.cell.w * g_tp.wire_local.R_per_um

                    self.C_wl_ram = (
                        gate_C_pass(
                            g_tp.sram.cell_a_w,
                            (g_tp.sram.b_w - 2*g_tp.sram.cell_a_w)/2.0,
                            False, True
                        )*2
                        + c_w_metal_ram
                    ) * self.num_cols_fa_ram

                    self.R_wl_ram = r_w_metal_ram * self.num_cols_fa_ram
                else:
                    self.C_wl_ram = 0
                    self.R_wl_ram = 0

                # CHECK C_b_metal
                self.C_wl = self.C_wl_cam + self.C_wl_ram
                # Overhead for NAND gate + drivers
                overhead_pitch = (16 + 128) * g_tp.wire_local.pitch
                self.C_wl += overhead_pitch * g_tp.wire_local.C_per_um
                self.R_wl  = self.R_wl_cam + self.R_wl_ram
                self.R_wl += overhead_pitch * g_tp.wire_local.R_per_um

                # Use the same "cam_cell.h" for both CAM and SRAM bitline:
                C_b_metal = self.cam_cell.h * g_tp.wire_local.C_per_um

                # CAM portion:
                C_b_row_drain_C_cam = drain_C_(
                    g_tp.cam.cell_a_w, NCH, 1, 0, self.cam_cell.w, False, True
                )/2.0
                self.C_bl_cam = (self.num_rows + 1) * (C_b_row_drain_C_cam + C_b_metal)

                # SRAM portion:
                C_b_row_drain_C_ram = drain_C_(
                    g_tp.sram.cell_a_w, NCH, 1, 0, self.cell.w, False, True
                )/2.0
                self.C_bl = (self.num_rows + 1) * (C_b_row_drain_C_ram + C_b_metal)


    def get_total_cell_area(self):
        """
        Python version of Subarray::get_total_cell_area()
        """
        if not (self.is_fa or self.dp.pure_cam):
            return self.cell.get_area() * self.num_rows * self.num_cols
        elif self.is_fa:
            # for FA, area includes dummy cells in SRAM arrays
            # area = cam_cell.h * (num_rows+1) * (cam_cell.w * num_cols_fa_cam + cell.w * num_cols_fa_ram)
            return ( self.cam_cell.h
                     * (self.num_rows + 1)
                     * ( self.cam_cell.w * self.num_cols_fa_cam
                         + self.cell.w * self.num_cols_fa_ram ) )
        else:
            # pure cam
            return self.cam_cell.get_area()*(self.num_rows + 1)*self.num_cols_fa_cam
