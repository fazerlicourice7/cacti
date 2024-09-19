import math
from .bank import Bank
from .htree import Htree2
from .component import *
from .memorybus import Memorybus
from .tsv import TSV
import sympy as sp
import time

# used to have component?
class UCA(Component):
    def __init__(self, dyn_p):
        super().__init__()
        self.dp = dyn_p
        self.bank = Bank(self.dp)
        self.nbanks = g_ip.nbanks
        self.refresh_power = 0

        self.power_routing_to_bank = PowerDef()

        # CHANGE: relational
        # num_banks_ver_dir = 1 << int((math.log2(nbanks) / 2) if (h > w) else (math.log2(nbanks) - math.log2(nbanks) / 2))
        num_banks_ver_dir = 1 << int(math.log2(self.nbanks) / 2) # if (self.bank.h > self.bank.w) else (math.log2(self.nbanks) - math.log2(self.nbanks) / 2))
        num_banks_hor_dir = self.nbanks // num_banks_ver_dir

        if self.dp.use_inp_params:
            self.RWP = self.dp.num_rw_ports
            self.ERP = self.dp.num_rd_ports
            self.EWP = self.dp.num_wr_ports
            self.SCHP = self.dp.num_search_ports
        else:
            self.RWP = g_ip.num_rw_ports
            self.ERP = g_ip.num_rd_ports
            self.EWP = g_ip.num_wr_ports
            self.SCHP = g_ip.num_search_ports

        self.num_addr_b_bank = (self.dp.number_addr_bits_mat + self.dp.number_subbanks_decode) * (self.RWP + self.ERP + self.EWP)
        self.num_di_b_bank = self.dp.num_di_b_bank_per_port * (self.RWP + self.EWP)
        self.num_do_b_bank = self.dp.num_do_b_bank_per_port * (self.RWP + self.ERP)
        self.num_si_b_bank = self.dp.num_si_b_bank_per_port * self.SCHP
        self.num_so_b_bank = self.dp.num_so_b_bank_per_port * self.SCHP

        if not self.dp.fully_assoc and not self.dp.pure_cam:
            if g_ip.fast_access and not self.dp.is_tag:
                self.num_do_b_bank *= g_ip.data_assoc

            self.htree_in_add = Htree2(g_ip.wt, self.bank.area.w, self.bank.area.h,
                                       self.num_addr_b_bank, self.num_di_b_bank, 0, self.num_do_b_bank, 0,
                                       num_banks_ver_dir * 2, num_banks_hor_dir * 2, Add_htree, True)
            self.htree_in_data = Htree2(g_ip.wt, self.bank.area.w, self.bank.area.h,
                                        self.num_addr_b_bank, self.num_di_b_bank, 0, self.num_do_b_bank, 0,
                                        num_banks_ver_dir * 2, num_banks_hor_dir * 2, Data_in_htree, True)
            self.htree_out_data = Htree2(g_ip.wt, self.bank.area.w, self.bank.area.h,
                                         self.num_addr_b_bank, self.num_di_b_bank, 0, self.num_do_b_bank, 0,
                                         num_banks_ver_dir * 2, num_banks_hor_dir * 2, Data_out_htree, True)
        else:
            self.htree_in_add = Htree2(g_ip.wt, self.bank.area.w, self.bank.area.h,
                                       self.num_addr_b_bank, self.num_di_b_bank, self.num_si_b_bank, self.num_do_b_bank, self.num_so_b_bank,
                                       num_banks_ver_dir * 2, num_banks_hor_dir * 2, Add_htree, True)
            self.htree_in_data = Htree2(g_ip.wt, self.bank.area.w, self.bank.area.h,
                                        self.num_addr_b_bank, self.num_di_b_bank, self.num_si_b_bank, self.num_do_b_bank, self.num_so_b_bank,
                                        num_banks_ver_dir * 2, num_banks_hor_dir * 2, Data_in_htree, True)
            self.htree_out_data = Htree2(g_ip.wt, self.bank.area.w, self.bank.area.h,
                                         self.num_addr_b_bank, self.num_di_b_bank, self.num_si_b_bank, self.num_do_b_bank, self.num_so_b_bank,
                                         num_banks_ver_dir * 2, num_banks_hor_dir * 2, Data_out_htree, True)
            self.htree_in_search = Htree2(g_ip.wt, self.bank.area.w, self.bank.area.h,
                                          self.num_addr_b_bank, self.num_di_b_bank, self.num_si_b_bank, self.num_do_b_bank, self.num_so_b_bank,
                                          num_banks_ver_dir * 2, num_banks_hor_dir * 2, Data_in_htree, True)
            self.htree_out_search = Htree2(g_ip.wt, self.bank.area.w, self.bank.area.h,
                                           self.num_addr_b_bank, self.num_di_b_bank, self.num_si_b_bank, self.num_do_b_bank, self.num_so_b_bank,
                                           num_banks_ver_dir * 2, num_banks_hor_dir * 2, Data_out_htree, True)

        self.area.w = self.htree_in_data.area.w
        self.area.h = self.htree_in_data.area.h

        self.area_all_dataramcells = self.bank.mat.subarray.get_total_cell_area() * self.dp.num_subarrays * g_ip.nbanks

        if g_ip.print_detail_debug:
            print(f"uca.cc: g_ip->is_3d_mem = {g_ip.is_3d_mem}")

        if g_ip.is_3d_mem:
            self.membus_RAS = Memorybus(g_ip.wt, self.bank.mat.area.w, self.bank.mat.area.h, self.bank.mat.subarray.area.w, self.bank.mat.subarray.area.h,
                                        math.log2(self.dp.num_r_subarray * self.dp.Ndbl), math.log2(self.dp.num_c_subarray * self.dp.Ndwl),
                                        g_ip.burst_depth * g_ip.io_width, self.dp.Ndbl, self.dp.Ndwl, Row_add_path, self.dp)
            self.membus_CAS = Memorybus(g_ip.wt, self.bank.mat.area.w, self.bank.mat.area.h, self.bank.mat.subarray.area.w, self.bank.mat.subarray.area.h,
                                        math.log2(self.dp.num_r_subarray * self.dp.Ndbl), math.log2(self.dp.num_c_subarray * self.dp.Ndwl),
                                        g_ip.burst_depth * g_ip.io_width, self.dp.Ndbl, self.dp.Ndwl, Col_add_path, self.dp)
            self.membus_data = Memorybus(g_ip.wt, self.bank.mat.area.w, self.bank.mat.area.h, self.bank.mat.subarray.area.w, self.bank.mat.subarray.area.h,
                                         math.log2(self.dp.num_r_subarray * self.dp.Ndbl), math.log2(self.dp.num_c_subarray * self.dp.Ndwl),
                                         g_ip.burst_depth * g_ip.io_width, self.dp.Ndbl, self.dp.Ndwl, Data_path, self.dp)
            self.area.h = self.membus_RAS.area.h
            self.area.w = self.membus_RAS.area.w

            if g_ip.print_detail_debug:
                print(f"uca.cc: area.h = {self.area.h / 1e3} mm")
                print(f"uca.cc: area.w = {self.area.w / 1e3} mm")
                print(f"uca.cc: bank.area.h = {self.bank.area.h / 1e3} mm")
                print(f"uca.cc: bank.area.w = {self.bank.area.w / 1e3} mm")
                print(f"uca.cc: bank.mat.area.h = {self.bank.mat.area.h / 1e3} mm")
                print(f"uca.cc: bank.mat.area.w = {self.bank.mat.area.w / 1e3} mm")
                print(f"uca.cc: bank.mat.subarray.area.h = {self.bank.mat.subarray.area.h / 1e3} mm")
                print(f"uca.cc: bank.mat.subarray.area.w = {self.bank.mat.subarray.area.w / 1e3} mm")
                print(f"uca.cc: dp.num_subarrays = {self.dp.num_subarrays}")
                print(f"uca.cc: area efficiency = {self.area_all_dataramcells / (self.area.w * self.area.h) * 100} %")
                print(f"uca.cc: area = {self.area.get_area() / 1e6} mm2")

        inrisetime = 0.0
        self.compute_delays(inrisetime)
        self.compute_power_energy()

        if g_ip.is_3d_mem:
            tsv_os_bank = TSV("Coarse")
            tsv_is_subarray = TSV("Fine")
            if g_ip.print_detail_debug:
                tsv_os_bank.print_TSV()
                tsv_is_subarray.print_TSV()

            self.comm_bits = 6
            self.row_add_bits = math.log2(self.dp.num_r_subarray * self.dp.Ndbl)
            self.col_add_bits = math.log2(self.dp.num_c_subarray * self.dp.Ndwl)
            self.data_bits = g_ip.burst_depth * g_ip.io_width

            redundancy_perc_TSV = 0.5
            partition_gran = g_ip.partition_gran
            if partition_gran == 0:  # Coarse_rank_level
                self.delay_TSV_tot = (g_ip.num_die_3d - 1) * tsv_os_bank.delay
                self.num_TSV_tot = int((self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits * 2) * (1 + redundancy_perc_TSV))
                self.area_TSV_tot = self.num_TSV_tot * tsv_os_bank.area.get_area()
                self.dyn_pow_TSV_tot = self.num_TSV_tot * (g_ip.num_die_3d - 1) * tsv_os_bank.power.readOp.dynamic
                self.dyn_pow_TSV_per_access = (self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits) * (g_ip.num_die_3d - 1) * tsv_os_bank.power.readOp.dynamic
                self.area_address_bus = self.membus_RAS.area_address_bus * (1.0 + self.comm_bits / (self.row_add_bits + self.col_add_bits))
                self.area_data_bus = self.membus_RAS.area_data_bus
            elif partition_gran == 1:  # Fine_rank_level
                self.delay_TSV_tot = g_ip.num_die_3d * tsv_os_bank.delay
                self.num_TSV_tot = int((self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits / 2) * self.nbanks * (1 + redundancy_perc_TSV))
                self.area_TSV_tot = self.num_TSV_tot * tsv_os_bank.area.get_area()
                self.dyn_pow_TSV_tot = self.num_TSV_tot * g_ip.num_die_3d * tsv_os_bank.power.readOp.dynamic
                self.dyn_pow_TSV_per_access = (self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits) * g_ip.num_die_3d * tsv_os_bank.power.readOp.dynamic
            elif partition_gran == 2:  # Coarse_bank_level
                self.delay_TSV_tot = g_ip.num_die_3d * tsv_os_bank.delay
                self.num_TSV_tot = int((self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits / 2) * self.nbanks * g_ip.num_tier_row_sprd * g_ip.num_tier_col_sprd * (1 + redundancy_perc_TSV))
                self.area_TSV_tot = self.num_TSV_tot * tsv_os_bank.area.get_area()
                self.dyn_pow_TSV_tot = self.num_TSV_tot * g_ip.num_die_3d * tsv_os_bank.power.readOp.dynamic
                self.dyn_pow_TSV_per_access = (self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits) * g_ip.num_die_3d * tsv_os_bank.power.readOp.dynamic
            elif partition_gran == 3:  # Fine_bank_level
                self.delay_TSV_tot = g_ip.num_die_3d * tsv_os_bank.delay
                self.num_TSV_tot = int((self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits) * self.nbanks * g_ip.ndwl * g_ip.ndbl / g_ip.num_tier_col_sprd / g_ip.num_tier_row_sprd * (1 + redundancy_perc_TSV))
                self.area_TSV_tot = self.num_TSV_tot * tsv_os_bank.area.get_area()
                self.dyn_pow_TSV_tot = self.num_TSV_tot * g_ip.num_die_3d * tsv_os_bank.power.readOp.dynamic
                self.dyn_pow_TSV_per_access = (self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits) * g_ip.num_die_3d * tsv_os_bank.power.readOp.dynamic
            else:
                assert False

            if g_ip.print_detail_debug:
                print(f"uca.cc: num_TSV_tot = {self.num_TSV_tot}")

            self.area_lwl_drv = self.membus_RAS.area_lwl_drv * g_ip.nbanks
            self.area_row_predec_dec = self.membus_RAS.area_row_predec_dec * g_ip.nbanks
            self.area_col_predec_dec = self.membus_CAS.area_col_predec_dec * g_ip.nbanks

            self.area_subarray = self.membus_RAS.area_subarray * g_ip.nbanks
            self.area_bus = self.membus_RAS.area_bus * g_ip.nbanks

            self.area_data_drv = self.membus_data.area_data_drv * g_ip.nbanks
            self.area_IOSA = self.membus_data.area_IOSA * g_ip.nbanks
            self.area_sense_amp = self.membus_data.area_sense_amp * g_ip.nbanks

            self.area_address_bus = self.membus_RAS.area_address_bus * (1.0 + self.comm_bits / (self.row_add_bits + self.col_add_bits)) * g_ip.nbanks
            self.area_data_bus = self.membus_RAS.area_data_bus + self.membus_data.area_local_dataline * g_ip.nbanks

            self.area_per_bank = (self.area_lwl_drv + self.area_row_predec_dec + self.area_col_predec_dec +
                                  self.area_subarray + self.area_bus + self.area_data_drv + self.area_IOSA +
                                  self.area_address_bus + self.area_data_bus) / g_ip.nbanks + self.area_sense_amp

            self.t_RCD += self.delay_TSV_tot
            self.t_RAS += self.delay_TSV_tot
            self.t_RC += self.delay_TSV_tot
            self.t_RP += self.delay_TSV_tot
            self.t_CAS += 2 * self.delay_TSV_tot
            self.t_RRD += self.delay_TSV_tot

            self.activate_energy += self.dyn_pow_TSV_per_access
            self.read_energy += self.dyn_pow_TSV_per_access
            self.write_energy += self.dyn_pow_TSV_per_access
            self.precharge_energy += self.dyn_pow_TSV_per_access

            if g_ip.num_die_3d > 1 or g_ip.partition_gran > 0:
                self.total_area_per_die = self.area_all_dataramcells + self.area_TSV_tot
            else:
                self.total_area_per_die = self.area_all_dataramcells

            if g_ip.is_3d_mem and g_ip.print_detail_debug:
                print("-------  CACTI 3D DRAM Main Memory -------")
                print("\nMemory Parameters:\n")
                print(f"    Total memory size (Gb): {int(g_ip.cache_sz)}")
                print(f"    Number of banks: {int(g_ip.nbanks)}")
                print(f"    Technology size (nm): {g_ip.F_sz_nm}")
                print(f"    Page size (bits): {g_ip.page_sz_bits}")
                print(f"    Burst depth: {g_ip.burst_depth}")
                print(f"    Chip IO width: {g_ip.io_width}")
                print(f"    Ndwl: {self.dp.Ndwl}")
                print(f"    Ndbl: {self.dp.Ndbl}")
                print(f"    # rows in subarray: {self.dp.num_r_subarray}")
                print(f"    # columns in subarray: {self.dp.num_c_subarray}")
                print("\nResults:\n")
                print("    ******************Timing terms******************")
                print(f"    t_RCD (Row to Column command Delay): {self.t_RCD * 1e9} ns")
                print(f"    t_RAS (Row Access Strobe latency): {self.t_RAS * 1e9} ns")
                print(f"    t_RC (Row Cycle): {self.t_RC * 1e9} ns")
                print(f"    t_CAS (Column Access Strobe latency): {self.t_CAS * 1e9} ns")
                print(f"    t_RP (Row Precharge latency): {self.t_RP * 1e9} ns")
                print("    *******************Power terms******************")
                print(f"    Activation energy: {self.activate_energy * 1e9} nJ")
                print(f"    Read energy: {self.read_energy * 1e9} nJ")
                print(f"    Write energy: {self.write_energy * 1e9} nJ")
                print(f"    Activation power: {self.activate_power * 1e3} mW")
                print(f"    Read power: {self.read_power * 1e3} mW")
                print(f"    Write power: {self.write_power * 1e3} mW")
                print("    ********************Area terms******************")
                print(f"    DRAM+peri Area: {self.area.get_area() / 1e6} mm2")
                print(f"    Total Area: {self.total_area_per_die / 1e6 / 0.5} mm2")

                if g_ip.print_detail_debug:
                    act_bus_energy = (self.membus_RAS.center_stripe.power.readOp.dynamic +
                                      self.membus_RAS.bank_bus.power.readOp.dynamic +
                                      self.membus_RAS.add_predec.power.readOp.dynamic +
                                      self.membus_RAS.add_dec.power.readOp.dynamic)
                    print(f"    Act Bus Energy: {act_bus_energy * 1e9} nJ")
                    print(f"    Act Bank Energy: {(self.activate_energy - act_bus_energy) * 1e9} nJ")
                    act_bus_latency = (self.membus_RAS.center_stripe.delay +
                                       self.membus_RAS.bank_bus.delay +
                                       self.membus_RAS.add_predec.delay +
                                       self.membus_RAS.add_dec.delay)
                    print(f"    Act Bus Latency: {act_bus_latency * 1e9} ns")
                    print(f"    Act Bank Latency: {(self.t_RCD - act_bus_latency) * 1e9} ns")
                    print(f"    activate_energy: {self.activate_energy * 1e9} nJ")

                if g_ip.num_die_3d > 1:
                    print("    ********************TSV terms******************")
                    print(f"    TSV area overhead: {self.area_TSV_tot / 1e6} mm2")
                    print(f"    TSV latency overhead: {self.delay_TSV_tot * 1e9} ns")
                    print(f"    TSV energy overhead per access: {self.dyn_pow_TSV_per_access * 1e9} nJ")
                print("\n\n\n")

    # def __del__(self):
    #     del self.htree_in_add
    #     del self.htree_in_data
    #     del self.htree_out_data

    #     if g_ip.is_3d_mem:
    #         del self.membus_RAS
    #         del self.membus_CAS
    #         del self.membus_data

    def compute_delays(self, inrisetime):
        outrisetime = self.bank.compute_delays(inrisetime)
        if g_ip.is_3d_mem:
            outrisetime = self.bank.compute_delays(self.membus_RAS.out_rise_time)

            self.t_RCD = self.membus_RAS.add_dec.delay + self.membus_RAS.lwl_drv.delay + self.bank.mat.delay_bitline + self.bank.mat.delay_sa
            self.t_RAS = self.membus_RAS.delay + self.bank.mat.delay_bitline + self.bank.mat.delay_sa + self.bank.mat.delay_bl_restore
            self.precharge_delay = self.bank.mat.delay_writeback + self.bank.mat.delay_wl_reset + self.bank.mat.delay_bl_restore
            self.t_RP = self.precharge_delay
            self.t_RC = self.t_RAS + self.t_RP
            self.t_CAS = self.membus_CAS.delay + self.bank.mat.delay_subarray_out_drv + self.membus_data.delay
            self.t_RRD = self.membus_RAS.center_stripe.delay + self.membus_RAS.bank_bus.delay
            self.access_time = self.t_RCD + self.t_CAS
            self.multisubbank_interleave_cycle_time = self.membus_RAS.center_stripe.delay + self.membus_RAS.bank_bus.delay
            self.cycle_time = self.t_RC + self.precharge_delay
            outrisetime = self.t_RCD / (1.0 - 0.5)

            if g_ip.print_detail_debug:
                print("\nNetwork delays:\n")
                print(f"uca.cc: membus_RAS->delay = {self.membus_RAS.delay * 1e9} ns")
                print(f"uca.cc: membus_CAS->delay = {self.membus_CAS.delay * 1e9} ns")
                print(f"uca.cc: membus_data->delay = {self.membus_data.delay * 1e9} ns")
                print("Row Address Delay components:\n")
                print(f"uca.cc: membus_RAS->center_stripe->delay = {self.membus_RAS.center_stripe.delay * 1e9} ns")
                print(f"uca.cc: membus_RAS->bank_bus->delay = {self.membus_RAS.bank_bus.delay * 1e9} ns")
                print(f"uca.cc: membus_RAS->add_predec->delay = {self.membus_RAS.add_predec.delay * 1e9} ns")
                print(f"uca.cc: membus_RAS->add_dec->delay = {self.membus_RAS.add_dec.delay * 1e9} ns")
                print(f"uca.cc: membus_RAS->lwl_drv->delay = {self.membus_RAS.lwl_drv.delay * 1e9} ns")
                print("Bank Delay components:\n")
                print(f"uca.cc: bank.mat.delay_bitline = {self.bank.mat.delay_bitline * 1e9} ns")
                print(f"uca.cc: bank.mat.delay_sa = {self.bank.mat.delay_sa * 1e9} ns")
                print("Column Address Delay components:\n")
                print(f"uca.cc: membus_CAS->bank_bus->delay = {self.membus_CAS.bank_bus.delay * 1e9} ns")
                print(f"uca.cc: membus_CAS->add_predec->delay = {self.membus_CAS.add_predec.delay * 1e9} ns")
                print(f"uca.cc: membus_CAS->add_dec->delay = {self.membus_CAS.add_dec.delay * 1e9} ns")
                print(f"uca.cc: membus_CAS->column_sel->delay = {self.membus_CAS.column_sel.delay * 1e9} ns")
                print("Data IO Path Delay components:\n")
                print(f"uca.cc: bank.mat.delay_subarray_out_drv = {self.bank.mat.delay_subarray_out_drv * 1e9} ns")
                print(f"uca.cc: membus_data->bank_bus->delay = {self.membus_data.bank_bus.delay * 1e9} ns")
                print(f"uca.cc: membus_data->global_data->delay = {self.membus_data.global_data.delay * 1e9} ns")
                print(f"uca.cc: membus_data->local_data->delay = {self.membus_data.local_data.delay * 1e9} ns")
                print("Bank precharge/restore delay components:\n")
                print(f"uca.cc: bank.mat.delay_bl_restore = {self.bank.mat.delay_bl_restore * 1e9} ns")
                print("General delay components:\n")
                print(f"uca.cc: t_RCD = {self.t_RCD * 1e9} ns")
                print(f"uca.cc: t_RAS = {self.t_RAS * 1e9} ns")
                print(f"uca.cc: t_RC = {self.t_RC * 1e9} ns")
                print(f"uca.cc: t_CAS = {self.t_CAS * 1e9} ns")
                print(f"uca.cc: t_RRD = {self.t_RRD * 1e9} ns")
                print(f"uca.cc: access_time = {self.access_time * 1e9} ns")
        else:
            delay_array_to_mat = self.htree_in_add.delay + self.bank.htree_in_add.delay
            max_delay_before_row_decoder = delay_array_to_mat + self.bank.mat.r_predec.delay
            self.delay_array_to_sa_mux_lev_1_decoder = delay_array_to_mat + self.bank.mat.sa_mux_lev_1_predec.delay + self.bank.mat.sa_mux_lev_1_dec.delay
            # self.delay_array_to_sa_mux_lev_1_decoder = self.bank.mat.sa_mux_lev_1_dec.delay
            self.delay_array_to_sa_mux_lev_2_decoder = delay_array_to_mat + self.bank.mat.sa_mux_lev_2_predec.delay + self.bank.mat.sa_mux_lev_2_dec.delay
            delay_inside_mat = self.bank.mat.row_dec.delay + self.bank.mat.delay_bitline + self.bank.mat.delay_sa

            # Change: MAX - option 1 and 2 make the expressions extremely long but have higher accuracy

            # OPTION 1: ORIGINAL
            # self.delay_before_subarray_output_driver = sp.Max(max_delay_before_row_decoder + delay_inside_mat,
            #                                             delay_array_to_mat + self.bank.mat.b_mux_predec.delay + self.bank.mat.bit_mux_dec.delay + self.bank.mat.delay_sa,
            #                                             sp.Max(self.delay_array_to_sa_mux_lev_1_decoder, self.delay_array_to_sa_mux_lev_2_decoder))
            
            # OPTION 2: USING symbolic... takes a while
            # print("before uca compute delay max")
            # self.delay_before_subarray_output_driver = symbolic_convex_max(max_delay_before_row_decoder + delay_inside_mat, 
            #                                                                (delay_array_to_mat + self.bank.mat.b_mux_predec.delay + 
            #                                                                self.bank.mat.bit_mux_dec.delay + self.bank.mat.delay_sa))
            # tmp_max = symbolic_convex_max(self.delay_array_to_sa_mux_lev_1_decoder, self.delay_array_to_sa_mux_lev_2_decoder)
            # self.delay_before_subarray_output_driver = symbolic_convex_max(self.delay_before_subarray_output_driver, tmp_max)

            # OPTION 3: just select 1 - will decrease accuracy
            # a
            # self.delay_before_subarray_output_driver = max_delay_before_row_decoder + delay_inside_mat
            # b
            self.delay_before_subarray_output_driver = delay_array_to_mat + self.bank.mat.b_mux_predec.delay + self.bank.mat.bit_mux_dec.delay + self.bank.mat.delay_sa
            # c
            # self.delay_before_subarray_output_driver = self.delay_array_to_sa_mux_lev_1_decoder
            # d
            # self.delay_before_subarray_output_driver = self.delay_array_to_sa_mux_lev_2_decoder

            self.delay_from_subarray_out_drv_to_out = self.bank.mat.delay_subarray_out_drv_htree + self.bank.htree_out_data.delay + self.htree_out_data.delay
            self.access_time = self.bank.mat.delay_comparator

            if self.dp.fully_assoc:
                ram_delay_inside_mat = self.bank.mat.delay_bitline + self.bank.mat.delay_matchchline
                self.access_time = self.htree_in_add.delay + self.bank.htree_in_add.delay + ram_delay_inside_mat + self.delay_from_subarray_out_drv_to_out
            else:
                self.access_time = self.delay_before_subarray_output_driver + self.delay_from_subarray_out_drv_to_out

            if self.dp.is_main_mem:
                t_rcd = max_delay_before_row_decoder + delay_inside_mat
                # cas_latency = symbolic_convex_max(self.delay_array_to_sa_mux_lev_1_decoder, self.delay_array_to_sa_mux_lev_2_decoder) + self.delay_from_subarray_out_drv_to_out
                cas_latency = self.delay_array_to_sa_mux_lev_1_decoder + self.delay_from_subarray_out_drv_to_out
                self.access_time = t_rcd + cas_latency

            if not self.dp.fully_assoc:
                temp = delay_inside_mat + self.bank.mat.delay_wl_reset + self.bank.mat.delay_bl_restore
                if self.dp.is_dram:
                    temp += self.bank.mat.delay_writeback

                # Uneeded since for cycle time
                # temp = symbolic_convex_max(temp, self.bank.mat.r_predec.delay)
                # temp = symbolic_convex_max(temp, self.bank.mat.b_mux_predec.delay)
                # temp = symbolic_convex_max(temp, self.bank.mat.sa_mux_lev_1_predec.delay)
                # temp = symbolic_convex_max(temp, self.bank.mat.sa_mux_lev_2_predec.delay)
                # temp = sp.Max(
                #     temp,
                #     self.bank.mat.r_predec.delay,
                #     self.bank.mat.b_mux_predec.delay,
                #     self.bank.mat.sa_mux_lev_1_predec.delay,
                #     self.bank.mat.sa_mux_lev_2_predec.delay
                # )               

                # Uneeded since for cycle time
                # max1 = symbolic_convex_max(self.bank.mat.r_predec.delay, self.bank.mat.b_mux_predec.delay)
                # max2 = symbolic_convex_max(self.bank.mat.sa_mux_lev_1_predec.delay, self.bank.mat.sa_mux_lev_2_predec.delay)
                # max3 = symbolic_convex_max(max1, max2)
                # temp = symbolic_convex_max(temp, max3)
                temp = self.bank.mat.r_predec.delay

            else:
                ram_delay_inside_mat = self.bank.mat.delay_bitline + self.bank.mat.delay_matchchline
                temp = ram_delay_inside_mat + self.bank.mat.delay_cam_sl_restore + self.bank.mat.delay_cam_ml_reset + self.bank.mat.delay_bl_restore + self.bank.mat.delay_hit_miss_reset + self.bank.mat.delay_wl_reset
                # temp = symbolic_convex_max(temp, self.bank.mat.b_mux_predec.delay)
                # temp = symbolic_convex_max(temp, self.bank.mat.sa_mux_lev_1_predec.delay)
                # temp = symbolic_convex_max(temp, self.bank.mat.sa_mux_lev_2_predec.delay)
                
                # Uneeded since for cycle time
                # temp = sp.Max(
                #     temp,
                #     self.bank.mat.b_mux_predec.delay,
                #     self.bank.mat.sa_mux_lev_1_predec.delay,
                #     self.bank.mat.sa_mux_lev_2_predec.delay
                # )

                # Uneeded since for cycle time
                # max1 = symbolic_convex_max(temp, self.bank.mat.b_mux_predec.delay)
                # max2 = symbolic_convex_max(self.bank.mat.sa_mux_lev_2_predec.delay, self.bank.mat.sa_mux_lev_1_predec.delay)
                # temp = symbolic_convex_max(max1, max2)
                temp = self.bank.mat.b_mux_predec.delay

            print ("UCA completed... please wait for expression to write.")
            g_ip.rpters_in_htree = True
            if g_ip.rpters_in_htree == False:
                temp = symbolic_convex_max(temp, self.bank.htree_in_add.max_unpipelined_link_delay)
            self.cycle_time = temp

            delay_req_network = max_delay_before_row_decoder
            delay_rep_network = self.delay_from_subarray_out_drv_to_out
            self.multisubbank_interleave_cycle_time = symbolic_convex_max(delay_req_network, delay_rep_network)

            if self.dp.is_main_mem:
                self.multisubbank_interleave_cycle_time = self.htree_in_add.delay
                self.precharge_delay = self.htree_in_add.delay + self.bank.htree_in_add.delay + self.bank.mat.delay_writeback + self.bank.mat.delay_wl_reset + self.bank.mat.delay_bl_restore
                self.cycle_time = self.access_time + self.precharge_delay
            else:
                self.precharge_delay = 0

        return outrisetime

    def compute_power_energy(self):
        self.bank.compute_power_energy()
        self.power = self.bank.power
        
        if g_ip.is_3d_mem:
            datapath_energy = 0.505e-9 * g_ip.F_sz_nm / 55
            self.activate_energy = (
                self.membus_RAS.power.readOp.dynamic +
                (self.bank.mat.power_bitline.readOp.dynamic + self.bank.mat.power_sa.readOp.dynamic) * self.dp.Ndwl
            )
            self.read_energy = (
                self.membus_CAS.power.readOp.dynamic +
                self.bank.mat.power_subarray_out_drv.readOp.dynamic +
                self.membus_data.power.readOp.dynamic +
                datapath_energy
            )
            self.write_energy = (
                self.membus_CAS.power.readOp.dynamic +
                self.bank.mat.power_subarray_out_drv.readOp.dynamic +
                self.membus_data.power.readOp.dynamic +
                self.bank.mat.power_sa.readOp.dynamic * g_ip.burst_depth * g_ip.io_width / g_ip.page_sz_bits +
                datapath_energy
            )
            self.precharge_energy = (
                self.bank.mat.power_bitline.readOp.dynamic +
                self.bank.mat.power_bl_precharge_eq_drv.readOp.dynamic
            ) * self.dp.Ndwl
            
            self.activate_power = self.activate_energy / self.t_RC
            col_cycle_act_row = (1e-6 / g_ip.sys_freq_MHz) / 2 * g_ip.burst_depth
            self.read_power = 0.25 * self.read_energy / col_cycle_act_row
            self.write_power = 0.15 * self.write_energy / col_cycle_act_row

            if g_ip.print_detail_debug:
                print("Network power terms:")
                print(f"uca.cc: membus_RAS->power.readOp.dynamic = {self.membus_RAS.power.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_CAS->power.readOp.dynamic = {self.membus_CAS.power.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_data->power.readOp.dynamic = {self.membus_data.power.readOp.dynamic * 1e9} nJ")
                print("Row Address Power components:")
                print(f"uca.cc: membus_RAS->power_bus.readOp.dynamic = {self.membus_RAS.power_bus.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_RAS->power_add_predecoder.readOp.dynamic = {self.membus_RAS.power_add_predecoder.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_RAS->power_add_decoders.readOp.dynamic = {self.membus_RAS.power_add_decoders.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_RAS->power_lwl_drv.readOp.dynamic = {self.membus_RAS.power_lwl_drv.readOp.dynamic * 1e9} nJ")
                print("Bank Power components:")
                print(f"uca.cc: bank.mat.power_bitline = {self.bank.mat.power_bitline.readOp.dynamic * self.dp.Ndwl * 1e9} nJ")
                print(f"uca.cc: bank.mat.power_sa = {self.bank.mat.power_sa.readOp.dynamic * self.dp.Ndwl * 1e9} nJ")
                print("Column Address Power components:")
                print(f"uca.cc: membus_CAS->power_bus.readOp.dynamic = {self.membus_CAS.power_bus.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_CAS->power_add_predecoder.readOp.dynamic = {self.membus_CAS.power_add_predecoder.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_CAS->power_add_decoders.readOp.dynamic = {self.membus_CAS.power_add_decoders.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_CAS->power.readOp.dynamic = {self.membus_CAS.power.readOp.dynamic * 1e9} nJ")
                print("Data Path Power components:")
                print(f"uca.cc: bank.mat.power_subarray_out_drv.readOp.dynamic = {self.bank.mat.power_subarray_out_drv.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: membus_data->power.readOp.dynamic = {self.membus_data.power.readOp.dynamic * 1e9} nJ")
                print(f"uca.cc: bank.mat.power_sa = {self.bank.mat.power_sa.readOp.dynamic * g_ip.burst_depth * g_ip.io_width / g_ip.page_sz_bits * 1e9} nJ")
                print("General Power components:")
                print(f"uca.cc: activate_energy = {self.activate_energy * 1e9} nJ")
                print(f"uca.cc: read_energy = {self.read_energy * 1e9} nJ")
                print(f"uca.cc: write_energy = {self.write_energy * 1e9} nJ")
                print(f"uca.cc: precharge_energy = {self.precharge_energy * 1e9} nJ")
                print(f"uca.cc: activate_power = {self.activate_power * 1e3} mW")
                print(f"uca.cc: read_power = {self.read_power * 1e3} mW")
                print(f"uca.cc: write_power = {self.write_power * 1e3} mW")
        
        else:
            self.power_routing_to_bank.readOp.dynamic = self.htree_in_add.power.readOp.dynamic + self.htree_out_data.power.readOp.dynamic
            self.power_routing_to_bank.writeOp.dynamic = self.htree_in_add.power.readOp.dynamic + self.htree_in_data.power.readOp.dynamic
            if self.dp.fully_assoc or self.dp.pure_cam:
                self.power_routing_to_bank.searchOp.dynamic = self.htree_in_search.power.searchOp.dynamic + self.htree_out_search.power.searchOp.dynamic
            
            self.power_routing_to_bank.readOp.leakage += (
                self.htree_in_add.power.readOp.leakage +
                self.htree_in_data.power.readOp.leakage +
                self.htree_out_data.power.readOp.leakage
            )

            self.power_routing_to_bank.readOp.gate_leakage += (
                self.htree_in_add.power.readOp.gate_leakage +
                self.htree_in_data.power.readOp.gate_leakage +
                self.htree_out_data.power.readOp.gate_leakage
            )

            if self.dp.fully_assoc or self.dp.pure_cam:
                self.power_routing_to_bank.readOp.leakage += self.htree_in_search.power.readOp.leakage + self.htree_out_search.power.readOp.leakage
                self.power_routing_to_bank.readOp.gate_leakage += self.htree_in_search.power.readOp.gate_leakage + self.htree_out_search.power.readOp.gate_leakage
            
            self.power.searchOp.dynamic += self.power_routing_to_bank.searchOp.dynamic
            self.power.readOp.dynamic += self.power_routing_to_bank.readOp.dynamic
            self.power.readOp.leakage += self.power_routing_to_bank.readOp.leakage
            self.power.readOp.gate_leakage += self.power_routing_to_bank.readOp.gate_leakage
            
            self.power.writeOp.dynamic = (
                self.power.readOp.dynamic -
                self.bank.mat.power_bitline.readOp.dynamic * self.dp.num_act_mats_hor_dir +
                self.bank.mat.power_bitline.writeOp.dynamic * self.dp.num_act_mats_hor_dir -
                self.power_routing_to_bank.readOp.dynamic +
                self.power_routing_to_bank.writeOp.dynamic +
                self.bank.htree_in_data.power.readOp.dynamic -
                self.bank.htree_out_data.power.readOp.dynamic
            )
            
            if not self.dp.is_dram:
                self.power.writeOp.dynamic -= self.bank.mat.power_sa.readOp.dynamic * self.dp.num_act_mats_hor_dir
            
            self.dyn_read_energy_from_closed_page = self.power.readOp.dynamic
            self.dyn_read_energy_from_open_page = (
                self.power.readOp.dynamic -
                (
                    self.bank.mat.r_predec.power.readOp.dynamic +
                    self.bank.mat.power_row_decoders.readOp.dynamic +
                    self.bank.mat.power_bl_precharge_eq_drv.readOp.dynamic +
                    self.bank.mat.power_sa.readOp.dynamic +
                    self.bank.mat.power_bitline.readOp.dynamic
                ) * self.dp.num_act_mats_hor_dir
            )

            self.dyn_read_energy_remaining_words_in_burst = (
                symbolic_convex_max(g_ip.burst_len / g_ip.int_prefetch_w, 1) - 1
            ) * (
                (
                    self.bank.mat.sa_mux_lev_1_predec.power.readOp.dynamic +
                    self.bank.mat.sa_mux_lev_2_predec.power.readOp.dynamic +
                    self.bank.mat.power_sa_mux_lev_1_decoders.readOp.dynamic +
                    self.bank.mat.power_sa_mux_lev_2_decoders.readOp.dynamic +
                    self.bank.mat.power_subarray_out_drv.readOp.dynamic
                ) * self.dp.num_act_mats_hor_dir +
                self.bank.htree_out_data.power.readOp.dynamic +
                self.power_routing_to_bank.readOp.dynamic
            )

            self.dyn_read_energy_from_closed_page += self.dyn_read_energy_remaining_words_in_burst
            self.dyn_read_energy_from_open_page += self.dyn_read_energy_remaining_words_in_burst

            self.activate_energy = (
                self.htree_in_add.power.readOp.dynamic +
                self.bank.htree_in_add.power_bit.readOp.dynamic * self.bank.num_addr_b_routed_to_mat_for_act +
                (
                    self.bank.mat.r_predec.power.readOp.dynamic +
                    self.bank.mat.power_row_decoders.readOp.dynamic +
                    self.bank.mat.power_sa.readOp.dynamic
                ) * self.dp.num_act_mats_hor_dir
            )

            self.read_energy = (
                self.htree_in_add.power.readOp.dynamic +
                self.bank.htree_in_add.power_bit.readOp.dynamic * self.bank.num_addr_b_routed_to_mat_for_rd_or_wr +
                (
                    self.bank.mat.sa_mux_lev_1_predec.power.readOp.dynamic +
                    self.bank.mat.sa_mux_lev_2_predec.power.readOp.dynamic +
                    self.bank.mat.power_sa_mux_lev_1_decoders.readOp.dynamic +
                    self.bank.mat.power_sa_mux_lev_2_decoders.readOp.dynamic +
                    self.bank.mat.power_subarray_out_drv.readOp.dynamic
                ) * self.dp.num_act_mats_hor_dir +
                self.bank.htree_out_data.power.readOp.dynamic +
                self.htree_in_data.power.readOp.dynamic
            ) * g_ip.burst_len

            self.write_energy = (
                self.htree_in_add.power.readOp.dynamic +
                self.bank.htree_in_add.power_bit.readOp.dynamic * self.bank.num_addr_b_routed_to_mat_for_rd_or_wr +
                self.htree_in_data.power.readOp.dynamic +
                self.bank.htree_in_data.power.readOp.dynamic +
                (
                    self.bank.mat.sa_mux_lev_1_predec.power.readOp.dynamic +
                    self.bank.mat.sa_mux_lev_2_predec.power.readOp.dynamic +
                    self.bank.mat.power_sa_mux_lev_1_decoders.readOp.dynamic +
                    self.bank.mat.power_sa_mux_lev_2_decoders.readOp.dynamic
                ) * self.dp.num_act_mats_hor_dir
            ) * g_ip.burst_len

            self.precharge_energy = (
                self.bank.mat.power_bitline.readOp.dynamic +
                self.bank.mat.power_bl_precharge_eq_drv.readOp.dynamic
            ) * self.dp.num_act_mats_hor_dir
        
        self.leak_power_subbank_closed_page = (
            (
                self.bank.mat.r_predec.power.readOp.leakage +
                self.bank.mat.b_mux_predec.power.readOp.leakage +
                self.bank.mat.sa_mux_lev_1_predec.power.readOp.leakage +
                self.bank.mat.sa_mux_lev_2_predec.power.readOp.leakage +
                self.bank.mat.power_row_decoders.readOp.leakage +
                self.bank.mat.power_bit_mux_decoders.readOp.leakage +
                self.bank.mat.power_sa_mux_lev_1_decoders.readOp.leakage +
                self.bank.mat.power_sa_mux_lev_2_decoders.readOp.leakage +
                self.bank.mat.leak_power_sense_amps_closed_page_state
            ) * self.dp.num_act_mats_hor_dir +
            (
                self.bank.mat.r_predec.power.readOp.gate_leakage +
                self.bank.mat.b_mux_predec.power.readOp.gate_leakage +
                self.bank.mat.sa_mux_lev_1_predec.power.readOp.gate_leakage +
                self.bank.mat.sa_mux_lev_2_predec.power.readOp.gate_leakage +
                self.bank.mat.power_row_decoders.readOp.gate_leakage +
                self.bank.mat.power_bit_mux_decoders.readOp.gate_leakage +
                self.bank.mat.power_sa_mux_lev_1_decoders.readOp.gate_leakage +
                self.bank.mat.power_sa_mux_lev_2_decoders.readOp.gate_leakage
            ) * self.dp.num_act_mats_hor_dir
        )
        
        self.leak_power_subbank_open_page = (
            (
                self.bank.mat.r_predec.power.readOp.leakage +
                self.bank.mat.b_mux_predec.power.readOp.leakage +
                self.bank.mat.sa_mux_lev_1_predec.power.readOp.leakage +
                self.bank.mat.sa_mux_lev_2_predec.power.readOp.leakage +
                self.bank.mat.power_row_decoders.readOp.leakage +
                self.bank.mat.power_bit_mux_decoders.readOp.leakage +
                self.bank.mat.power_sa_mux_lev_1_decoders.readOp.leakage +
                self.bank.mat.power_sa_mux_lev_2_decoders.readOp.leakage +
                self.bank.mat.leak_power_sense_amps_open_page_state
            ) * self.dp.num_act_mats_hor_dir +
            (
                self.bank.mat.r_predec.power.readOp.gate_leakage +
                self.bank.mat.b_mux_predec.power.readOp.gate_leakage +
                self.bank.mat.sa_mux_lev_1_predec.power.readOp.gate_leakage +
                self.bank.mat.sa_mux_lev_2_predec.power.readOp.gate_leakage +
                self.bank.mat.power_row_decoders.readOp.gate_leakage +
                self.bank.mat.power_bit_mux_decoders.readOp.gate_leakage +
                self.bank.mat.power_sa_mux_lev_1_decoders.readOp.gate_leakage +
                self.bank.mat.power_sa_mux_lev_2_decoders.readOp.gate_leakage
            ) * self.dp.num_act_mats_hor_dir
        )
        
        self.leak_power_request_and_reply_networks = (
            self.power_routing_to_bank.readOp.leakage +
            self.bank.htree_in_add.power.readOp.leakage +
            self.bank.htree_in_data.power.readOp.leakage +
            self.bank.htree_out_data.power.readOp.leakage +
            self.power_routing_to_bank.readOp.gate_leakage +
            self.bank.htree_in_add.power.readOp.gate_leakage +
            self.bank.htree_in_data.power.readOp.gate_leakage +
            self.bank.htree_out_data.power.readOp.gate_leakage
        )
        
        if self.dp.fully_assoc or self.dp.pure_cam:
            self.leak_power_request_and_reply_networks += (
                self.htree_in_search.power.readOp.leakage +
                self.htree_out_search.power.readOp.leakage +
                self.htree_in_search.power.readOp.gate_leakage +
                self.htree_out_search.power.readOp.gate_leakage
            )
        
        if self.dp.is_dram:
            self.refresh_power = (
                (
                    self.bank.mat.r_predec.power.readOp.dynamic * self.dp.num_act_mats_hor_dir +
                    self.bank.mat.row_dec.power.readOp.dynamic
                ) * self.dp.num_r_subarray * self.dp.num_subarrays +
                self.bank.mat.per_bitline_read_energy * self.dp.num_c_subarray * self.dp.num_r_subarray * self.dp.num_subarrays +
                self.bank.mat.power_bl_precharge_eq_drv.readOp.dynamic * self.dp.num_act_mats_hor_dir +
                self.bank.mat.power_sa.readOp.dynamic * self.dp.num_act_mats_hor_dir
            ) / self.dp.dram_refresh_period
        
        if not self.dp.is_tag:
            self.power.readOp.dynamic = self.dyn_read_energy_from_closed_page

            self.power.writeOp.dynamic = (
                self.dyn_read_energy_from_closed_page -
                self.dyn_read_energy_remaining_words_in_burst -
                self.bank.mat.power_bitline.readOp.dynamic * self.dp.num_act_mats_hor_dir +
                self.bank.mat.power_bitline.writeOp.dynamic * self.dp.num_act_mats_hor_dir +
                (
                    self.power_routing_to_bank.writeOp.dynamic -
                    self.power_routing_to_bank.readOp.dynamic -
                    self.bank.htree_out_data.power.readOp.dynamic +
                    self.bank.htree_in_data.power.readOp.dynamic
                ) * (symbolic_convex_max(g_ip.burst_len / g_ip.int_prefetch_w, 1) - 1)
            )
            
            if not self.dp.is_dram:
                self.power.writeOp.dynamic -= self.bank.mat.power_sa.readOp.dynamic * self.dp.num_act_mats_hor_dir
        
        if self.dp.is_dram:
            self.power.readOp.leakage += self.refresh_power
        
        if g_ip.is_3d_mem:
            self.power.readOp.dynamic = self.read_energy
            self.power.writeOp.dynamic = self.write_energy
            self.power.readOp.leakage = (
                self.membus_RAS.power.readOp.leakage +
                self.membus_CAS.power.readOp.leakage +
                self.membus_data.power.readOp.leakage
            )
        
        # assert self.power.readOp.dynamic > 0
        # assert self.power.writeOp.dynamic > 0
        # assert self.power.readOp.leakage > 0
