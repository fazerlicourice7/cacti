import math
from math import ceil, log, pow
import sys

import sympy as sp

from .const import *
from .component import Component
from . import parameter

class Subarray(Component):
    def __init__(self, g_ip, g_tp, dp_, is_fa_):
        super().__init__()
        self.g_ip = g_ip
        self.g_tp = g_tp
        self.dp = dp_
        self.num_rows = dp_.num_r_subarray
        self.num_cols = dp_.num_c_subarray
        self.num_cols_fa_cam = dp_.tag_num_c_subarray
        self.num_cols_fa_ram = dp_.data_num_c_subarray
        self.cell = dp_.cell
        self.cam_cell = dp_.cam_cell
        self.is_fa = is_fa_
        
        if not (is_fa_ or dp_.pure_cam):
            self.num_cols += sp.ceiling(self.num_cols / num_bits_per_ecc_b_) if self.g_ip.add_ecc_b_ else 0
            
            ram_num_cells_wl_stitching = (
                dram_num_cells_wl_stitching_ if dp_.ram_cell_tech_type == lp_dram else
                comm_dram_num_cells_wl_stitching_ if dp_.ram_cell_tech_type == comm_dram else
                sram_num_cells_wl_stitching_
            )
            
            self.area.h = self.cell.h * self.num_rows
            self.area.w = self.cell.w * self.num_cols + sp.ceiling(self.num_cols / ram_num_cells_wl_stitching) * self.g_tp.ram_wl_stitching_overhead_
            
            if self.g_ip.print_detail_debug:
                print("subarray.cc: ram_num_cells_wl_stitching =", ram_num_cells_wl_stitching)
                print("subarray.cc: self.g_tp.ram_wl_stitching_overhead_ =", self.g_tp.ram_wl_stitching_overhead_, "um")
        else:
            if is_fa_:
                self.num_cols_fa_cam += sp.ceiling(self.num_cols_fa_cam / num_bits_per_ecc_b_) if self.g_ip.add_ecc_b_ else 0
                self.num_cols_fa_ram += sp.ceiling(self.num_cols_fa_ram / num_bits_per_ecc_b_) if self.g_ip.add_ecc_b_ else 0
                self.num_cols = self.num_cols_fa_cam + self.num_cols_fa_ram
            else:
                self.num_cols_fa_cam += sp.ceiling(self.num_cols_fa_cam / num_bits_per_ecc_b_) if self.g_ip.add_ecc_b_ else 0
                self.num_cols_fa_ram = 0
                self.num_cols = self.num_cols_fa_cam
                
            self.area.h = self.cam_cell.h * (self.num_rows + 1)
            self.area.w = (
                self.cam_cell.w * self.num_cols_fa_cam + self.cell.w * self.num_cols_fa_ram
                + sp.ceiling((self.num_cols_fa_cam + self.num_cols_fa_ram) / sram_num_cells_wl_stitching_) * self.g_tp.ram_wl_stitching_overhead_
                + 16 * self.g_tp.wire_local.pitch
                + 128 * self.g_tp.wire_local.pitch
            )
        
        # assert self.area.h > 0
        # assert self.area.w > 0
        self.compute_C()
    
    def __del__(self):
        pass
    
    def get_total_cell_area(self):
        if not (self.is_fa or self.dp.pure_cam):
            return self.cell.get_area() * self.num_rows * self.num_cols
        elif self.is_fa:
            return self.cam_cell.h * (self.num_rows + 1) * (self.cam_cell.w * self.num_cols_fa_cam + self.cell.w * self.num_cols_fa_ram)
        else:
            return self.cam_cell.get_area() * (self.num_rows + 1) * self.num_cols_fa_cam
    
    def compute_C(self):
        c_w_metal = self.cell.w * self.g_tp.wire_local.C_per_um
        r_w_metal = self.cell.w * self.g_tp.wire_local.R_per_um
        C_b_metal = self.cell.h * self.g_tp.wire_local.C_per_um
        C_b_row_drain_C = 0
        
        if self.dp.is_dram:
            self.C_wl = (parameter.gate_C_pass(self.g_tp, self.g_tp.dram.cell_a_w, self.g_tp.dram.b_w, True, True) + c_w_metal) * self.num_cols
            if self.dp.ram_cell_tech_type == comm_dram:
                self.C_bl = self.num_rows * C_b_metal
            else:
                C_b_row_drain_C = parameter.drain_C_(self.g_tp.dram.cell_a_w, NCH, 1, 0, self.cell.w, True, True) / 2.0
                self.C_bl = self.num_rows * (C_b_row_drain_C + C_b_metal)
        else:
            if not (self.is_fa or self.dp.pure_cam):
                self.C_wl = (
                    parameter.gate_C_pass(self.g_tp, self.g_tp.sram.cell_a_w, (self.g_tp.sram.b_w - 2 * self.g_tp.sram.cell_a_w) / 2.0, False, True) * 2 +
                    c_w_metal
                ) * self.num_cols
                C_b_row_drain_C = parameter.drain_C_(self.g_tp.sram.cell_a_w, NCH, 1, 0, self.cell.w, False, True) / 2.0
                self.C_bl = self.num_rows * (C_b_row_drain_C + C_b_metal)
            else:
                c_w_metal = self.cam_cell.w * self.g_tp.wire_local.C_per_um
                r_w_metal = self.cam_cell.w * self.g_tp.wire_local.R_per_um
                self.C_wl_cam = (
                    parameter.gate_C_pass(self.g_tp, self.g_tp.cam.cell_a_w, (self.g_tp.cam.b_w - 2 * self.g_tp.cam.cell_a_w) / 2.0, False, True) * 2 +
                    c_w_metal
                ) * self.num_cols_fa_cam
                self.R_wl_cam = r_w_metal * self.num_cols_fa_cam
                
                if not self.dp.pure_cam:
                    c_w_metal = self.cell.w * self.g_tp.wire_local.C_per_um
                    r_w_metal = self.cell.w * self.g_tp.wire_local.R_per_um
                    self.C_wl_ram = (
                        parameter.gate_C_pass(self.g_tp, self.g_tp.sram.cell_a_w, (self.g_tp.sram.b_w - 2 * self.g_tp.sram.cell_a_w) / 2.0, False, True) * 2 +
                        c_w_metal
                    ) * self.num_cols_fa_ram
                    self.R_wl_ram = r_w_metal * self.num_cols_fa_ram
                else:
                    self.C_wl_ram = self.R_wl_ram = 0
                
                self.C_wl = self.C_wl_cam + self.C_wl_ram
                self.C_wl += (16 + 128) * self.g_tp.wire_local.pitch * self.g_tp.wire_local.C_per_um
                
                self.R_wl = self.R_wl_cam + self.R_wl_ram
                self.R_wl += (16 + 128) * self.g_tp.wire_local.pitch * self.g_tp.wire_local.R_per_um
                
                C_b_metal = self.cam_cell.h * self.g_tp.wire_local.C_per_um
                C_b_row_drain_C = parameter.drain_C_(self.g_tp.cam.cell_a_w, NCH, 1, 0, self.cam_cell.w, False, True) / 2.0
                self.C_bl_cam = (self.num_rows + 1) * (C_b_row_drain_C + C_b_metal)
                C_b_row_drain_C = parameter.drain_C_(self.g_tp.sram.cell_a_w, NCH, 1, 0, self.cell.w, False, True) / 2.0
                self.C_bl = (self.num_rows + 1) * (C_b_row_drain_C + C_b_metal)