# TODO figure out area

import math
from math import ceil, log, pow
import sys
from .const import *
from .decoder import *
#from .basic_circuit import *
from .parameter import *
from .const import *
from .component import *
import sympy as sp

class Subarray(Component):
    def __init__(self, dp_, is_fa_):
        super().__init__()
        self.dp = dp_
        self.num_rows = dp_.num_r_subarray
        self.num_cols = dp_.num_c_subarray
        self.num_cols_fa_cam = dp_.tag_num_c_subarray
        self.num_cols_fa_ram = dp_.data_num_c_subarray
        self.cell = dp_.cell
        self.cam_cell = dp_.cam_cell
        self.is_fa = is_fa_

        print("\n CURR DEBUG")
        print(f"Number of rows: {self.num_rows}")
        print(f"Number of columns: {self.num_cols}")
        print(f"Number of columns for FA CAM: {self.num_cols_fa_cam}")
        print(f"Number of columns for FA RAM: {self.num_cols_fa_ram}")
        print(f"Cell: {self.cell}")
        print(f"CAM Cell: {self.cam_cell}")
        print(f"Is FA: {self.is_fa}")
        #self.area = Area()
        
        if not (is_fa_ or dp_.pure_cam):
            self.num_cols += sp.ceiling(self.num_cols / num_bits_per_ecc_b_) if g_ip.add_ecc_b_ else 0
            
            ram_num_cells_wl_stitching = (
                dram_num_cells_wl_stitching_ if dp_.ram_cell_tech_type == lp_dram else
                comm_dram_num_cells_wl_stitching_ if dp_.ram_cell_tech_type == comm_dram else
                sram_num_cells_wl_stitching_
            )
            
            self.area.h = self.cell.h * self.num_rows
            self.area.w = self.cell.w * self.num_cols + sp.ceiling(self.num_cols / ram_num_cells_wl_stitching) * g_tp.ram_wl_stitching_overhead_
            
            if g_ip.print_detail_debug:
                print("subarray.cc: ram_num_cells_wl_stitching =", ram_num_cells_wl_stitching)
                print("subarray.cc: g_tp.ram_wl_stitching_overhead_ =", g_tp.ram_wl_stitching_overhead_, "um")
        else:
            if is_fa_:
                self.num_cols_fa_cam += sp.ceiling(self.num_cols_fa_cam / num_bits_per_ecc_b_) if g_ip.add_ecc_b_ else 0
                self.num_cols_fa_ram += sp.ceiling(self.num_cols_fa_ram / num_bits_per_ecc_b_) if g_ip.add_ecc_b_ else 0
                self.num_cols = self.num_cols_fa_cam + self.num_cols_fa_ram
            else:
                self.num_cols_fa_cam += sp.ceiling(self.num_cols_fa_cam / num_bits_per_ecc_b_) if g_ip.add_ecc_b_ else 0
                self.num_cols_fa_ram = 0
                self.num_cols = self.num_cols_fa_cam
                
            self.area.h = self.cam_cell.h * (self.num_rows + 1)
            self.area.w = (
                self.cam_cell.w * self.num_cols_fa_cam + self.cell.w * self.num_cols_fa_ram
                + sp.ceiling((self.num_cols_fa_cam + self.num_cols_fa_ram) / sram_num_cells_wl_stitching_) * g_tp.ram_wl_stitching_overhead_
                + 16 * g_tp.wire_local.pitch
                + 128 * g_tp.wire_local.pitch
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
        c_w_metal = self.cell.w * g_tp.wire_local.C_per_um
        r_w_metal = self.cell.w * g_tp.wire_local.R_per_um
        C_b_metal = self.cell.h * g_tp.wire_local.C_per_um
        C_b_row_drain_C = 0
        
        if self.dp.is_dram:
            self.C_wl = (gate_C_pass(g_tp.dram.cell_a_w, g_tp.dram.b_w, True, True) + c_w_metal) * self.num_cols
            if self.dp.ram_cell_tech_type == comm_dram:
                self.C_bl = self.num_rows * C_b_metal
            else:
                C_b_row_drain_C = drain_C_(g_tp.dram.cell_a_w, NCH, 1, 0, self.cell.w, True, True) / 2.0
                self.C_bl = self.num_rows * (C_b_row_drain_C + C_b_metal)
        else:
            if not (self.is_fa or self.dp.pure_cam):
                self.C_wl = (
                    gate_C_pass(g_tp.sram.cell_a_w, (g_tp.sram.b_w - 2 * g_tp.sram.cell_a_w) / 2.0, False, True) * 2 +
                    c_w_metal
                ) * self.num_cols
                C_b_row_drain_C = drain_C_(g_tp.sram.cell_a_w, NCH, 1, 0, self.cell.w, False, True) / 2.0
                self.C_bl = self.num_rows * (C_b_row_drain_C + C_b_metal)
            else:
                c_w_metal = self.cam_cell.w * g_tp.wire_local.C_per_um
                r_w_metal = self.cam_cell.w * g_tp.wire_local.R_per_um
                self.C_wl_cam = (
                    gate_C_pass(g_tp.cam.cell_a_w, (g_tp.cam.b_w - 2 * g_tp.cam.cell_a_w) / 2.0, False, True) * 2 +
                    c_w_metal
                ) * self.num_cols_fa_cam
                self.R_wl_cam = r_w_metal * self.num_cols_fa_cam
                
                if not self.dp.pure_cam:
                    c_w_metal = self.cell.w * g_tp.wire_local.C_per_um
                    r_w_metal = self.cell.w * g_tp.wire_local.R_per_um
                    self.C_wl_ram = (
                        gate_C_pass(g_tp.sram.cell_a_w, (g_tp.sram.b_w - 2 * g_tp.sram.cell_a_w) / 2.0, False, True) * 2 +
                        c_w_metal
                    ) * self.num_cols_fa_ram
                    self.R_wl_ram = r_w_metal * self.num_cols_fa_ram
                else:
                    self.C_wl_ram = self.R_wl_ram = 0
                
                self.C_wl = self.C_wl_cam + self.C_wl_ram
                self.C_wl += (16 + 128) * g_tp.wire_local.pitch * g_tp.wire_local.C_per_um
                
                self.R_wl = self.R_wl_cam + self.R_wl_ram
                self.R_wl += (16 + 128) * g_tp.wire_local.pitch * g_tp.wire_local.R_per_um
                
                C_b_metal = self.cam_cell.h * g_tp.wire_local.C_per_um
                C_b_row_drain_C = drain_C_(g_tp.cam.cell_a_w, NCH, 1, 0, self.cam_cell.w, False, True) / 2.0
                self.C_bl_cam = (self.num_rows + 1) * (C_b_row_drain_C + C_b_metal)
                C_b_row_drain_C = drain_C_(g_tp.sram.cell_a_w, NCH, 1, 0, self.cell.w, False, True) / 2.0
                self.C_bl = (self.num_rows + 1) * (C_b_row_drain_C + C_b_metal)

# class DynamicParameter:
#     def __init__(self, num_r_subarray, num_c_subarray, tag_num_c_subarray, data_num_c_subarray, cell, cam_cell, pure_cam, ram_cell_tech_type, is_dram):
#         self.num_r_subarray = num_r_subarray
#         self.num_c_subarray = num_c_subarray
#         self.tag_num_c_subarray = tag_num_c_subarray
#         self.data_num_c_subarray = data_num_c_subarray
#         self.cell = cell
#         self.cam_cell = cam_cell
#         self.pure_cam = pure_cam
#         self.ram_cell_tech_type = ram_cell_tech_type
#         self.is_dram = is_dram


