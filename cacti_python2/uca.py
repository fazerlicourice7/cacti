# uca.py

import math
import sys

from component import Component   # Hypothetical Python version of your Component base class
from parameter import g_ip        # The global InputParameter, as in your code
from basic_circuit import _log2   # If you have a Python version of _log2
from cacti_interface import powerDef
from bank import Bank
from htree2 import Htree2
from memorybus import Memorybus, Memorybus_type
from tsv import TSV, TSV_type     # If you have these in your Python environment


class UCA(Component):
    """
    Python translation of the C++ UCA class (uca.h), implementing
    the partial logic shown in uca.cc. This class depends on classes:
      - DynamicParameter, Bank, Memorybus, Htree2, TSV, ...
      - global config object g_ip
      - the 'Component' base class for area/power.

    We'll fill in the rest once the remaining parts of uca.cc are provided.
    """

    def __init__(self, dyn_p):
        """
        UCA constructor, matching `UCA(const DynamicParameter & dyn_p)`.
        """
        super().__init__()  # init base class
        self.dp = dyn_p
        # Create a Bank object
        self.bank = Bank(self.dp)

        # Member variables from the .h
        self.nbanks = g_ip.nbanks
        self.membus_RAS = None
        self.membus_CAS = None
        self.membus_data = None
        self.power_routing_to_bank = powerDef()

        self.htree_in_add   = None
        self.htree_in_data  = None
        self.htree_out_data = None
        self.htree_in_search  = None
        self.htree_out_search = None

        self.num_addr_b_bank = 0
        self.num_di_b_bank   = 0
        self.num_do_b_bank   = 0
        self.num_si_b_bank   = 0
        self.num_so_b_bank   = 0
        self.RWP = 0
        self.ERP = 0
        self.EWP = 0
        self.SCHP= 0

        self.area_all_dataramcells = 0.0
        self.total_area_per_die = 0.0

        self.dyn_read_energy_from_closed_page = 0.0
        self.dyn_read_energy_from_open_page   = 0.0
        self.dyn_read_energy_remaining_words_in_burst = 0.0

        self.refresh_power = 0.0
        self.activate_energy = 0.0
        self.read_energy     = 0.0
        self.write_energy    = 0.0
        self.precharge_energy= 0.0
        self.leak_power_subbank_closed_page = 0.0
        self.leak_power_subbank_open_page   = 0.0
        self.leak_power_request_and_reply_networks = 0.0

        self.delay_array_to_sa_mux_lev_1_decoder = 0.0
        self.delay_array_to_sa_mux_lev_2_decoder = 0.0
        self.delay_before_subarray_output_driver = 0.0
        self.delay_from_subarray_out_drv_to_out  = 0.0
        self.access_time  = 0.0
        self.precharge_delay = 0.0
        self.multisubbank_interleave_cycle_time = 0.0

        self.t_RAS = 0.0
        self.t_CAS = 0.0
        self.t_RCD = 0.0
        self.t_RC  = 0.0
        self.t_RP  = 0.0
        self.t_RRD = 0.0

        self.activate_power = 0.0
        self.read_power     = 0.0
        self.write_power    = 0.0

        self.delay_TSV_tot = 0.0
        self.area_TSV_tot  = 0.0
        self.dyn_pow_TSV_tot = 0.0
        self.dyn_pow_TSV_per_access = 0.0
        self.num_TSV_tot   = 0

        self.comm_bits     = 0
        self.row_add_bits  = 0
        self.col_add_bits  = 0
        self.data_bits     = 0

        self.area_lwl_drv         = 0.0
        self.area_row_predec_dec  = 0.0
        self.area_col_predec_dec  = 0.0
        self.area_subarray        = 0.0
        self.area_bus            = 0.0
        self.area_address_bus    = 0.0
        self.area_data_bus       = 0.0
        self.area_data_drv       = 0.0
        self.area_IOSA           = 0.0
        self.area_sense_amp      = 0.0
        self.area_per_bank       = 0.0

        # ---- Replicate the constructor logic from uca.cc ----
        # 1) figure out number banks in horizontal/vertical direction
        if self.bank.area.h > self.bank.area.w:
            # integer shift
            banks_v_dir = 1 << (int(_log2(self.nbanks)/2))
        else:
            banks_v_dir = 1 << (int(_log2(self.nbanks) - _log2(self.nbanks)/2))
        banks_h_dir = self.nbanks // banks_v_dir

        # 2) set port counts
        if self.dp.use_inp_params:
            self.RWP  = self.dp.num_rw_ports
            self.ERP  = self.dp.num_rd_ports
            self.EWP  = self.dp.num_wr_ports
            self.SCHP = self.dp.num_search_ports
        else:
            self.RWP  = g_ip.num_rw_ports
            self.ERP  = g_ip.num_rd_ports
            self.EWP  = g_ip.num_wr_ports
            self.SCHP = g_ip.num_search_ports

        # 3) compute #bits in htrees
        self.num_addr_b_bank = (self.dp.number_addr_bits_mat + self.dp.number_subbanks_decode) * (self.RWP + self.ERP + self.EWP)
        self.num_di_b_bank   = self.dp.num_di_b_bank_per_port * (self.RWP + self.EWP)
        self.num_do_b_bank   = self.dp.num_do_b_bank_per_port * (self.RWP + self.ERP)
        self.num_si_b_bank   = self.dp.num_si_b_bank_per_port * self.SCHP
        self.num_so_b_bank   = self.dp.num_so_b_bank_per_port * self.SCHP

        # 4) create Htrees for non-FA / non-CAM
        if not self.dp.fully_assoc and not self.dp.pure_cam:
            # If fast_access and data array, scale num_do_b_bank
            if g_ip.fast_access and not self.dp.is_tag:
                self.num_do_b_bank *= g_ip.data_assoc

            self.htree_in_add = Htree2(
                g_ip, g_ip.g_tp,  # or however you pass the technology param
                wire_model=g_ip.wt,
                mat_w=self.bank.area.w,
                mat_h=self.bank.area.h,
                a_bits=self.num_addr_b_bank,
                d_inbits=self.num_di_b_bank,
                search_data_in_bits=0,
                d_outbits=self.num_do_b_bank,
                search_data_out_bits=0,
                bl=banks_v_dir*2,
                wl=banks_h_dir*2,
                htree_type=0,  # Add_htree
                uca_tree_=True
            )
            self.htree_in_data = Htree2(
                g_ip, g_ip.g_tp,
                g_ip.wt,
                self.bank.area.w,
                self.bank.area.h,
                self.num_addr_b_bank,
                self.num_di_b_bank,
                0,
                self.num_do_b_bank,
                0,
                banks_v_dir*2,
                banks_h_dir*2,
                1,  # Data_in_htree
                True
            )
            self.htree_out_data = Htree2(
                g_ip, g_ip.g_tp,
                g_ip.wt,
                self.bank.area.w,
                self.bank.area.h,
                self.num_addr_b_bank,
                self.num_di_b_bank,
                0,
                self.num_do_b_bank,
                0,
                banks_v_dir*2,
                banks_h_dir*2,
                2,  # Data_out_htree
                True
            )
        else:
            # fully_assoc or pure_cam => 5 htrees
            self.htree_in_add = Htree2(
                g_ip, g_ip.g_tp,
                g_ip.wt,
                self.bank.area.w,
                self.bank.area.h,
                self.num_addr_b_bank,
                self.num_di_b_bank,
                self.num_si_b_bank,
                self.num_do_b_bank,
                self.num_so_b_bank,
                banks_v_dir*2,
                banks_h_dir*2,
                0,  # Add_htree
                True
            )
            self.htree_in_data = Htree2(
                g_ip, g_ip.g_tp,
                g_ip.wt,
                self.bank.area.w,
                self.bank.area.h,
                self.num_addr_b_bank,
                self.num_di_b_bank,
                self.num_si_b_bank,
                self.num_do_b_bank,
                self.num_so_b_bank,
                banks_v_dir*2,
                banks_h_dir*2,
                1,  # Data_in_htree
                True
            )
            self.htree_out_data = Htree2(
                g_ip, g_ip.g_tp,
                g_ip.wt,
                self.bank.area.w,
                self.bank.area.h,
                self.num_addr_b_bank,
                self.num_di_b_bank,
                self.num_si_b_bank,
                self.num_do_b_bank,
                self.num_so_b_bank,
                banks_v_dir*2,
                banks_h_dir*2,
                2,  # Data_out_htree
                True
            )
            self.htree_in_search = Htree2(
                g_ip, g_ip.g_tp,
                g_ip.wt,
                self.bank.area.w,
                self.bank.area.h,
                self.num_addr_b_bank,
                self.num_di_b_bank,
                self.num_si_b_bank,
                self.num_do_b_bank,
                self.num_so_b_bank,
                banks_v_dir*2,
                banks_h_dir*2,
                1,   # Data_in_htree
                True,
                True  # search_tree_
            )
            self.htree_out_search = Htree2(
                g_ip, g_ip.g_tp,
                g_ip.wt,
                self.bank.area.w,
                self.bank.area.h,
                self.num_addr_b_bank,
                self.num_di_b_bank,
                self.num_si_b_bank,
                self.num_do_b_bank,
                self.num_so_b_bank,
                banks_v_dir*2,
                banks_h_dir*2,
                2,   # Data_out_htree
                True,
                False
            )

        # area is set to that of htree_in_data, as in c++ code
        # (assuming that all 3 are the same dimension)
        self.area.w = self.htree_in_data.area.w
        self.area.h = self.htree_in_data.area.h

        # area of all data RAM cells:
        self.area_all_dataramcells = (self.bank.mat.subarray.get_total_cell_area()
                                      * self.dp.num_subarrays * g_ip.nbanks)

        # if g_ip->is_3d_mem => create the memory buses
        if g_ip.is_3d_mem:
            # create RAS, CAS, data memorybuses
            self.membus_RAS = Memorybus(
                g_ip,
                g_ip.g_tp,
                wire_model=g_ip.wt,
                mat_w=self.bank.mat.area.w,
                mat_h=self.bank.mat.area.h,
                subarray_w=self.bank.mat.subarray.area.w,
                subarray_h=self.bank.mat.subarray.area.h,
                row_add_bits=_log2(self.dp.num_r_subarray * self.dp.Ndbl),
                col_add_bits=_log2(self.dp.num_c_subarray * self.dp.Ndwl),
                data_bits=g_ip.burst_depth*g_ip.io_width,
                ndbl=self.dp.Ndbl,
                ndwl=self.dp.Ndwl,
                membus_type=Memorybus_type.Row_add_path,
                dp=self.dp
            )
            self.membus_CAS = Memorybus(
                g_ip,
                g_ip.g_tp,
                wire_model=g_ip.wt,
                mat_w=self.bank.mat.area.w,
                mat_h=self.bank.mat.area.h,
                subarray_w=self.bank.mat.subarray.area.w,
                subarray_h=self.bank.mat.subarray.area.h,
                row_add_bits=_log2(self.dp.num_r_subarray * self.dp.Ndbl),
                col_add_bits=_log2(self.dp.num_c_subarray * self.dp.Ndwl),
                data_bits=g_ip.burst_depth*g_ip.io_width,
                ndbl=self.dp.Ndbl,
                ndwl=self.dp.Ndwl,
                membus_type=Memorybus_type.Col_add_path,
                dp=self.dp
            )
            self.membus_data = Memorybus(
                g_ip,
                g_ip.g_tp,
                wire_model=g_ip.wt,
                mat_w=self.bank.mat.area.w,
                mat_h=self.bank.mat.area.h,
                subarray_w=self.bank.mat.subarray.area.w,
                subarray_h=self.bank.mat.subarray.area.h,
                row_add_bits=_log2(self.dp.num_r_subarray * self.dp.Ndbl),
                col_add_bits=_log2(self.dp.num_c_subarray * self.dp.Ndwl),
                data_bits=g_ip.burst_depth*g_ip.io_width,
                ndbl=self.dp.Ndbl,
                ndwl=self.dp.Ndwl,
                membus_type=Memorybus_type.Data_path,
                dp=self.dp
            )

            # override area with the memory bus area
            self.area.h = self.membus_RAS.area.h
            self.area.w = self.membus_RAS.area.w

        # done constructor logic so far
        # next: compute delays and power
        inrisetime = 0.0
        self.compute_delays(inrisetime)
        self.compute_power_energy()

        # partial TSV logic from the partial .cc
        if g_ip.is_3d_mem:
            # create TSV objects, etc.
            # partial usage
            tsv_os_bank = TSV(TSV_type.Coarse)
            tsv_is_subarray = TSV(TSV_type.Fine)
            if g_ip.print_detail_debug:
                tsv_os_bank.print_TSV()
                tsv_is_subarray.print_TSV()

            self.comm_bits = 6
            self.row_add_bits = _log2(self.dp.num_r_subarray * self.dp.Ndbl)
            self.col_add_bits = _log2(self.dp.num_c_subarray * self.dp.Ndwl)
            self.data_bits    = g_ip.burst_depth * g_ip.io_width

            # do partial assignment of delay_TSV_tot, area_TSV_tot, etc.
            # for now we just replicate the code snippet
            redundancy_perc_TSV = 0.5
            if g_ip.partition_gran == 0:
                # Coarse_rank_level
                self.delay_TSV_tot = (g_ip.num_die_3d-1)*tsv_os_bank.delay
                self.num_TSV_tot   = int((self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits*2)*(1+redundancy_perc_TSV))
                self.area_TSV_tot  = self.num_TSV_tot * tsv_os_bank.area.get_area()
                self.dyn_pow_TSV_tot = self.num_TSV_tot*(g_ip.num_die_3d-1)*tsv_os_bank.power.readOp.dynamic
                self.dyn_pow_TSV_per_access = (self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits)*(g_ip.num_die_3d-1)*tsv_os_bank.power.readOp.dynamic
                # adjust area bus
                self.area_address_bus = self.membus_RAS.area_address_bus*(1.0 + float(self.comm_bits)/float(self.row_add_bits+self.col_add_bits))
                self.area_data_bus    = self.membus_RAS.area_data_bus
            elif g_ip.partition_gran == 1:
                # Fine_rank_level
                self.delay_TSV_tot = g_ip.num_die_3d*tsv_os_bank.delay
                self.num_TSV_tot   = int((self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits/2)*g_ip.nbanks*(1+redundancy_perc_TSV))
                self.area_TSV_tot  = self.num_TSV_tot * tsv_os_bank.area.get_area()
                self.dyn_pow_TSV_tot = self.num_TSV_tot*g_ip.num_die_3d*tsv_os_bank.power.readOp.dynamic
                self.dyn_pow_TSV_per_access = (self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits)*g_ip.num_die_3d*tsv_os_bank.power.readOp.dynamic
                # left commented out area bus lines, etc.
            elif g_ip.partition_gran == 2:
                # Coarse_bank_level
                self.delay_TSV_tot = g_ip.num_die_3d*tsv_os_bank.delay
                self.num_TSV_tot   = int((self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits/2)*g_ip.nbanks
                                         * g_ip.num_tier_row_sprd*g_ip.num_tier_col_sprd*(1+redundancy_perc_TSV))
                self.area_TSV_tot  = self.num_TSV_tot*tsv_os_bank.area.get_area()
                self.dyn_pow_TSV_tot = self.num_TSV_tot*g_ip.num_die_3d*tsv_os_bank.power.readOp.dynamic
                self.dyn_pow_TSV_per_access = (self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits)*g_ip.num_die_3d*tsv_os_bank.power.readOp.dynamic
            elif g_ip.partition_gran == 3:
                # Fine_bank_level
                self.delay_TSV_tot = g_ip.num_die_3d*tsv_os_bank.delay
                self.num_TSV_tot   = int((self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits)*g_ip.nbanks*g_ip.ndwl*g_ip.ndbl
                                         /(g_ip.num_tier_col_sprd*g_ip.num_tier_row_sprd)*(1+redundancy_perc_TSV))
                self.area_TSV_tot  = self.num_TSV_tot*tsv_os_bank.area.get_area()
                self.dyn_pow_TSV_tot = self.num_TSV_tot*g_ip.num_die_3d*tsv_os_bank.power.readOp.dynamic
                self.dyn_pow_TSV_per_access = (self.comm_bits + self.row_add_bits + self.col_add_bits + self.data_bits)*g_ip.num_die_3d*tsv_os_bank.power.readOp.dynamic
            else:
                assert False, "Invalid partition gran"

            if g_ip.print_detail_debug:
                print("uca.cc: num_TSV_tot =", self.num_TSV_tot)

            self.area_lwl_drv = self.membus_RAS.area_lwl_drv*g_ip.nbanks
            self.area_row_predec_dec = self.membus_RAS.area_row_predec_dec*g_ip.nbanks
            self.area_col_predec_dec = self.membus_CAS.area_col_predec_dec*g_ip.nbanks
            self.area_subarray       = self.membus_RAS.area_subarray*g_ip.nbanks
            self.area_bus            = self.membus_RAS.area_bus*g_ip.nbanks

            self.area_data_drv      = self.membus_data.area_data_drv*g_ip.nbanks
            self.area_IOSA          = self.membus_data.area_IOSA*g_ip.nbanks
            self.area_sense_amp     = self.membus_data.area_sense_amp*g_ip.nbanks

            self.area_address_bus   = (self.membus_RAS.area_address_bus
                                       *(1.0+float(self.comm_bits)/float(self.row_add_bits+self.col_add_bits))
                                       * g_ip.nbanks)
            self.area_data_bus      = (self.membus_RAS.area_data_bus
                                       + self.membus_data.area_local_dataline*g_ip.nbanks)

            self.area_per_bank = (( self.area_lwl_drv + self.area_row_predec_dec
                                    + self.area_col_predec_dec + self.area_subarray + self.area_bus
                                    + self.area_data_drv + self.area_IOSA + self.area_address_bus
                                    + self.area_data_bus )/g_ip.nbanks
                                  + self.area_sense_amp)

            # add TSV overhead to timing/power
            self.t_RCD += self.delay_TSV_tot
            self.t_RAS += self.delay_TSV_tot
            self.t_RC  += self.delay_TSV_tot
            self.t_RP  += self.delay_TSV_tot
            self.t_CAS += (2*self.delay_TSV_tot)
            self.t_RRD += self.delay_TSV_tot

            self.activate_energy += self.dyn_pow_TSV_per_access
            self.read_energy     += self.dyn_pow_TSV_per_access
            self.write_energy    += self.dyn_pow_TSV_per_access
            self.precharge_energy+= self.dyn_pow_TSV_per_access

            if g_ip.num_die_3d>1 or g_ip.partition_gran>0:
                self.total_area_per_die = self.area_all_dataramcells + self.area_TSV_tot
            else:
                self.total_area_per_die = self.area_all_dataramcells

            if g_ip.is_3d_mem and g_ip.print_detail_debug:
                # print final debug lines (partial)
                print("-------  CACTI 3D DRAM Main Memory -------")
                # ... etc. replicate the debug prints as needed
                # (For brevity, omitted here, but you can replicate.)
                pass


    def __del__(self):
        """
        Python version of the UCA destructor.  Typically, Python GC handles it,
        but we can explicitly delete references if desired.
        """
        # In C++, we do: delete htree_in_add, etc. 
        # In Python, we can set them to None or just pass
        # to allow garbage collection.
        pass


    def compute_delays(self, inrisetime: float) -> float:
      """
      Python translation of UCA::compute_delays(double inrisetime).
      Returns the output rise time (outrisetime).
      """
      # First part: outrisetime from the bank
      outrisetime = self.bank.compute_delays(inrisetime)

      # If 3D memory => do CACTI3DD flow
      if g_ip.is_3d_mem:
          # recompute outrisetime using the RAS memory bus
          outrisetime = self.bank.compute_delays(self.membus_RAS.out_rise_time)

          # Using local references for clarity:
          # bank.mat.* are the mat-level delays from the subarray
          # membus_RAS, membus_CAS, membus_data are the 3D Memorybus objects
          self.t_RCD = (self.membus_RAS.add_dec.delay
                        + self.membus_RAS.lwl_drv.delay
                        + self.bank.mat.delay_bitline
                        + self.bank.mat.delay_sa)

          self.t_RAS = (self.membus_RAS.delay
                        + self.bank.mat.delay_bitline
                        + self.bank.mat.delay_sa
                        + self.bank.mat.delay_bl_restore)

          self.precharge_delay = (self.bank.mat.delay_writeback
                                  + self.bank.mat.delay_wl_reset
                                  + self.bank.mat.delay_bl_restore)

          self.t_RP = self.precharge_delay
          self.t_RC = self.t_RAS + self.t_RP
          self.t_CAS = (self.membus_CAS.delay
                        + self.bank.mat.delay_subarray_out_drv
                        + self.membus_data.delay)

          self.t_RRD = (self.membus_RAS.center_stripe.delay
                        + self.membus_RAS.bank_bus.delay)
          # self.t_RRD = membus_RAS->delay;  // commented out in c++

          self.access_time = self.t_RCD + self.t_CAS
          self.multisubbank_interleave_cycle_time = (self.membus_RAS.center_stripe.delay
                                                    + self.membus_RAS.bank_bus.delay)

          # We define cycle_time in terms of t_RC + precharge_delay
          # but in the code, it states: cycle_time = t_RC + precharge_delay.
          # Then outrisetime is t_RCD/(1.0 - 0.5).
          self.cycle_time = self.t_RC + self.precharge_delay
          outrisetime = self.t_RCD / (1.0 - 0.5)  # "correct?" as in code

          # Print debug if requested
          if g_ip.print_detail_debug:
              print("\nNetwork delays:")
              print(f"uca.cc: membus_RAS->delay = {self.membus_RAS.delay * 1e9} ns")
              print(f"uca.cc: membus_CAS->delay = {self.membus_CAS.delay * 1e9} ns")
              print(f"uca.cc: membus_data->delay = {self.membus_data.delay * 1e9} ns")

              print("Row Address Delay components:")
              print(f"uca.cc: membus_RAS->center_stripe->delay = {self.membus_RAS.center_stripe.delay * 1e9} ns")
              print(f"uca.cc: membus_RAS->bank_bus->delay      = {self.membus_RAS.bank_bus.delay * 1e9} ns")
              print(f"uca.cc: membus_RAS->add_predec->delay    = {self.membus_RAS.add_predec.delay * 1e9} ns")
              print(f"uca.cc: membus_RAS->add_dec->delay       = {self.membus_RAS.add_dec.delay * 1e9} ns")
              print(f"uca.cc: membus_RAS->lwl_drv->delay       = {self.membus_RAS.lwl_drv.delay * 1e9} ns")

              print("Bank Delay components:")
              print(f"uca.cc: bank.mat.delay_bitline = {self.bank.mat.delay_bitline * 1e9} ns")
              print(f"uca.cc: bank.mat.delay_sa      = {self.bank.mat.delay_sa * 1e9} ns")

              print("Column Address Delay components:")
              print(f"uca.cc: membus_CAS->bank_bus->delay   = {self.membus_CAS.bank_bus.delay * 1e9} ns")
              print(f"uca.cc: membus_CAS->add_predec->delay = {self.membus_CAS.add_predec.delay * 1e9} ns")
              print(f"uca.cc: membus_CAS->add_dec->delay    = {self.membus_CAS.add_dec.delay * 1e9} ns")
              print(f"uca.cc: membus_CAS->column_sel->delay = {self.membus_CAS.column_sel.delay * 1e9} ns")

              print("Data IO Path Delay components:")
              print(f"uca.cc: bank.mat.delay_subarray_out_drv = {self.bank.mat.delay_subarray_out_drv * 1e9} ns")
              print(f"uca.cc: membus_data->bank_bus->delay    = {self.membus_data.bank_bus.delay * 1e9} ns")
              print(f"uca.cc: membus_data->global_data->delay = {self.membus_data.global_data.delay * 1e9} ns")
              print(f"uca.cc: membus_data->local_data->delay  = {self.membus_data.local_data.delay * 1e9} ns")

              print("Bank precharge/restore delay components:")
              print(f"uca.cc: bank.mat.delay_bl_restore = {self.bank.mat.delay_bl_restore * 1e9} ns")

              print("General delay components:")
              print(f"uca.cc: t_RCD       = {self.t_RCD * 1e9} ns")
              print(f"uca.cc: t_RAS       = {self.t_RAS * 1e9} ns")
              print(f"uca.cc: t_RC        = {self.t_RC * 1e9} ns")
              print(f"uca.cc: t_CAS       = {self.t_CAS * 1e9} ns")
              print(f"uca.cc: t_RRD       = {self.t_RRD * 1e9} ns")
              print(f"uca.cc: access_time = {self.access_time * 1e9} ns")

      else:
          # Non-3D flow
          # bank + htree_in_add => row addressing
          delay_array_to_mat = self.htree_in_add.delay + self.bank.htree_in_add.delay
          max_delay_before_row_decoder = (delay_array_to_mat + self.bank.mat.r_predec.delay)

          self.delay_array_to_sa_mux_lev_1_decoder = (
              delay_array_to_mat
              + self.bank.mat.sa_mux_lev_1_predec.delay
              + self.bank.mat.sa_mux_lev_1_dec.delay
          )
          self.delay_array_to_sa_mux_lev_2_decoder = (
              delay_array_to_mat
              + self.bank.mat.sa_mux_lev_2_predec.delay
              + self.bank.mat.sa_mux_lev_2_dec.delay
          )

          delay_inside_mat = (self.bank.mat.row_dec.delay
                              + self.bank.mat.delay_bitline
                              + self.bank.mat.delay_sa)

          self.delay_before_subarray_output_driver = max(
              max(max_delay_before_row_decoder + delay_inside_mat,  # row_path
                  delay_array_to_mat
                  + self.bank.mat.b_mux_predec.delay
                  + self.bank.mat.bit_mux_dec.delay
                  + self.bank.mat.delay_sa),  # col_path
              max(self.delay_array_to_sa_mux_lev_1_decoder,  # sa_mux_lev_1_path
                  self.delay_array_to_sa_mux_lev_2_decoder)  # sa_mux_lev_2_path
          )

          self.delay_from_subarray_out_drv_to_out = (
              self.bank.mat.delay_subarray_out_drv_htree
              + self.bank.htree_out_data.delay
              + self.htree_out_data.delay
          )

          self.access_time = self.bank.mat.delay_comparator

          # fully-associative => includes CAM tag + RAM data
          if self.dp.fully_assoc:
              ram_delay_inside_mat = self.bank.mat.delay_bitline + self.bank.mat.delay_matchchline
              # "access_time" for the CAM portion
              self.access_time = self.htree_in_add.delay + self.bank.htree_in_add.delay
              # add fully-associative data array
              self.access_time += ram_delay_inside_mat + self.delay_from_subarray_out_drv_to_out
          else:
              self.access_time = (self.delay_before_subarray_output_driver
                                  + self.delay_from_subarray_out_drv_to_out)

          # If main memory => add t_rcd + CAS
          if self.dp.is_main_mem:
              t_rcd = max_delay_before_row_decoder + delay_inside_mat
              cas_latency = max(self.delay_array_to_sa_mux_lev_1_decoder,
                                self.delay_array_to_sa_mux_lev_2_decoder) + self.delay_from_subarray_out_drv_to_out
              self.access_time = t_rcd + cas_latency

          # figure out cycle_time
          if not self.dp.fully_assoc:
              temp = (delay_inside_mat
                      + self.bank.mat.delay_wl_reset
                      + self.bank.mat.delay_bl_restore)
              if self.dp.is_dram:
                  temp += self.bank.mat.delay_writeback
              temp = max(temp, self.bank.mat.r_predec.delay)
              temp = max(temp, self.bank.mat.b_mux_predec.delay)
              temp = max(temp, self.bank.mat.sa_mux_lev_1_predec.delay)
              temp = max(temp, self.bank.mat.sa_mux_lev_2_predec.delay)
          else:
              # fully-associative
              ram_delay_inside_mat = (self.bank.mat.delay_bitline
                                      + self.bank.mat.delay_matchchline)
              temp = (ram_delay_inside_mat
                      + self.bank.mat.delay_cam_sl_restore
                      + self.bank.mat.delay_cam_ml_reset
                      + self.bank.mat.delay_bl_restore
                      + self.bank.mat.delay_hit_miss_reset
                      + self.bank.mat.delay_wl_reset)
              temp = max(temp, self.bank.mat.b_mux_predec.delay)
              temp = max(temp, self.bank.mat.sa_mux_lev_1_predec.delay)
              temp = max(temp, self.bank.mat.sa_mux_lev_2_predec.delay)

          # If repeaters_in_htree == false => limit cycle_time by link delays
          if not g_ip.rpters_in_htree:
              temp = max(temp, self.bank.htree_in_add.max_unpipelined_link_delay)
          self.cycle_time = temp

          # request network + reply network => for multi-subbank
          delay_req_network = max_delay_before_row_decoder
          delay_rep_network = self.delay_from_subarray_out_drv_to_out
          self.multisubbank_interleave_cycle_time = max(delay_req_network, delay_rep_network)

          if self.dp.is_main_mem:
              self.multisubbank_interleave_cycle_time = self.htree_in_add.delay
              self.precharge_delay = (self.htree_in_add.delay
                                      + self.bank.htree_in_add.delay
                                      + self.bank.mat.delay_writeback
                                      + self.bank.mat.delay_wl_reset
                                      + self.bank.mat.delay_bl_restore)
              self.cycle_time = self.access_time + self.precharge_delay
          else:
              self.precharge_delay = 0.0

      return outrisetime



    def compute_power_energy(self):
      """
      Python translation of UCA::compute_power_energy(), matching the final part
      of uca.cc you provided.

      The method updates 'self.power' using:
        - bank.compute_power_energy()
        - If 3D memory: the RAS/CAS/data memorybuses
        - else the standard flow for read/write energies
      """
      # 1) First do bank-level power
      self.bank.compute_power_energy()

      # 2) By default, total UCA power is the bank's power
      self.power = self.bank.power

      # 3) If 3D memory => do CACTI3DD logic
      if g_ip.is_3d_mem:
          # a small constant datapath energy that depends on F_sz_nm
          datapath_energy = 0.505e-9 * g_ip.F_sz_nm / 55.0

          # Activate energy: row bus + bank mat 
          self.activate_energy = (
              self.membus_RAS.power.readOp.dynamic
              + (
                  self.bank.mat.power_bitline.readOp.dynamic
                  + self.bank.mat.power_sa.readOp.dynamic
              )
              * self.dp.Ndwl
          )

          # Read energy: col bus + subarray out + data bus + external datapath
          self.read_energy = (
              self.membus_CAS.power.readOp.dynamic
              + self.bank.mat.power_subarray_out_drv.readOp.dynamic
              + self.membus_data.power.readOp.dynamic
              + datapath_energy
          )

          # Write energy: col bus + subarray out + data bus + sense amps scaled + datapath
          self.write_energy = (
              self.membus_CAS.power.readOp.dynamic
              + self.bank.mat.power_subarray_out_drv.readOp.dynamic
              + self.membus_data.power.readOp.dynamic
              + (
                  self.bank.mat.power_sa.readOp.dynamic
                  * g_ip.burst_depth
                  * g_ip.io_width
                  / g_ip.page_sz_bits
              )
              + datapath_energy
          )

          # Precharge energy: bitline + precharge eq driver
          self.precharge_energy = (
              self.bank.mat.power_bitline.readOp.dynamic
              + self.bank.mat.power_bl_precharge_eq_drv.readOp.dynamic
          ) * self.dp.Ndwl

          # Activate power => activate_energy / t_RC
          self.activate_power = self.activate_energy / self.t_RC

          # a local "col_cycle_act_row" from the snippet
          # col_cycle_act_row = (1e-6 / (double)g_ip->sys_freq_MHz)/2 * g_ip->burst_depth
          col_cycle_act_row = (1e-6 / float(g_ip.sys_freq_MHz)) / 2.0 * g_ip.burst_depth

          # read_power: 0.25 * read_energy / col_cycle_act_row
          self.read_power = 0.25 * self.read_energy / col_cycle_act_row

          # write_power: 0.15 * write_energy / col_cycle_act_row
          self.write_power = 0.15 * self.write_energy / col_cycle_act_row

          if g_ip.print_detail_debug:
              print("Row Address Delay components:")
              print("Row Address Delay components:")
              print("Network power terms:")
              print(f"uca.cc: membus_RAS->power.readOp.dynamic    = {self.membus_RAS.power.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_CAS->power.readOp.dynamic    = {self.membus_CAS.power.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_data->power.readOp.dynamic   = {self.membus_data.power.readOp.dynamic * 1e9} nJ")

              print("Row Address Power components:")
              print(f"uca.cc: membus_RAS->power_bus.readOp.dynamic          = {self.membus_RAS.power_bus.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_RAS->power_add_predecoder.readOp.dynamic= {self.membus_RAS.power_add_predecoder.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_RAS->power_add_decoders.readOp.dynamic  = {self.membus_RAS.power_add_decoders.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_RAS->power_lwl_drv.readOp.dynamic       = {self.membus_RAS.power_lwl_drv.readOp.dynamic * 1e9} nJ")

              print("Bank Power components:")
              print(f"uca.cc: bank.mat.power_bitline = {self.bank.mat.power_bitline.readOp.dynamic * self.dp.Ndwl * 1e9} nJ")
              print(f"uca.cc: bank.mat.power_sa      = {self.bank.mat.power_sa.readOp.dynamic * self.dp.Ndwl * 1e9} nJ")

              print("Column Address Power components:")
              print(f"uca.cc: membus_CAS->power_bus.readOp.dynamic           = {self.membus_CAS.power_bus.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_CAS->power_add_predecoder.readOp.dynamic = {self.membus_CAS.power_add_predecoder.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_CAS->power_add_decoders.readOp.dynamic   = {self.membus_CAS.power_add_decoders.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_CAS->power.readOp.dynamic               = {self.membus_CAS.power.readOp.dynamic * 1e9} nJ")

              print("Data Path Power components:")
              print(f"uca.cc: bank.mat.power_subarray_out_drv.readOp.dynamic = {self.bank.mat.power_subarray_out_drv.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: membus_data->power.readOp.dynamic             = {self.membus_data.power.readOp.dynamic * 1e9} nJ")
              print(f"uca.cc: bank.mat.power_sa                             = {(self.bank.mat.power_sa.readOp.dynamic * g_ip.burst_depth * g_ip.io_width / g_ip.page_sz_bits) * 1e9} nJ")

              print("General Power components:")
              print(f"uca.cc: activate_energy   = {self.activate_energy * 1e9} nJ")
              print(f"uca.cc: read_energy       = {self.read_energy * 1e9} nJ")
              print(f"uca.cc: write_energy      = {self.write_energy * 1e9} nJ")
              print(f"uca.cc: precharge_energy  = {self.precharge_energy * 1e9} nJ")
              print(f"uca.cc: activate_power    = {self.activate_power * 1e3} mW")
              print(f"uca.cc: read_power        = {self.read_power * 1e3} mW")
              print(f"uca.cc: write_power       = {self.write_power * 1e3} mW")

      else:
          # Non-3D Memory flow
          # Summation for htrees
          self.power_routing_to_bank.readOp.dynamic  = (self.htree_in_add.power.readOp.dynamic
                                                        + self.htree_out_data.power.readOp.dynamic)
          self.power_routing_to_bank.writeOp.dynamic = (self.htree_in_add.power.readOp.dynamic
                                                        + self.htree_in_data.power.readOp.dynamic)
          if self.dp.fully_assoc or self.dp.pure_cam:
              self.power_routing_to_bank.searchOp.dynamic = (
                  self.htree_in_search.power.searchOp.dynamic
                  + self.htree_out_search.power.searchOp.dynamic
              )

          self.power_routing_to_bank.readOp.leakage += (
              self.htree_in_add.power.readOp.leakage
              + self.htree_in_data.power.readOp.leakage
              + self.htree_out_data.power.readOp.leakage
          )
          self.power_routing_to_bank.readOp.gate_leakage += (
              self.htree_in_add.power.readOp.gate_leakage
              + self.htree_in_data.power.readOp.gate_leakage
              + self.htree_out_data.power.readOp.gate_leakage
          )
          if self.dp.fully_assoc or self.dp.pure_cam:
              self.power_routing_to_bank.readOp.leakage += (
                  self.htree_in_search.power.readOp.leakage
                  + self.htree_out_search.power.readOp.leakage
              )
              self.power_routing_to_bank.readOp.gate_leakage += (
                  self.htree_in_search.power.readOp.gate_leakage
                  + self.htree_out_search.power.readOp.gate_leakage
              )

          self.power.searchOp.dynamic += self.power_routing_to_bank.searchOp.dynamic
          self.power.readOp.dynamic   += self.power_routing_to_bank.readOp.dynamic
          self.power.readOp.leakage   += self.power_routing_to_bank.readOp.leakage
          self.power.readOp.gate_leakage += self.power_routing_to_bank.readOp.gate_leakage

          # total write dynamic
          self.power.writeOp.dynamic = (
              self.power.readOp.dynamic
              - self.bank.mat.power_bitline.readOp.dynamic * self.dp.num_act_mats_hor_dir
              + self.bank.mat.power_bitline.writeOp.dynamic * self.dp.num_act_mats_hor_dir
              - self.power_routing_to_bank.readOp.dynamic
              + self.power_routing_to_bank.writeOp.dynamic
              + self.bank.htree_in_data.power.readOp.dynamic
              - self.bank.htree_out_data.power.readOp.dynamic
          )

          if not self.dp.is_dram:
              self.power.writeOp.dynamic -= (self.bank.mat.power_sa.readOp.dynamic
                                            * self.dp.num_act_mats_hor_dir)

          self.dyn_read_energy_from_closed_page = self.power.readOp.dynamic

          self.dyn_read_energy_from_open_page = (
              self.power.readOp.dynamic
              - (
                  self.bank.mat.r_predec.power.readOp.dynamic
                  + self.bank.mat.power_row_decoders.readOp.dynamic
                  + self.bank.mat.power_bl_precharge_eq_drv.readOp.dynamic
                  + self.bank.mat.power_sa.readOp.dynamic
                  + self.bank.mat.power_bitline.readOp.dynamic
              )
              * self.dp.num_act_mats_hor_dir
          )

          # for multiple-burst reads
          burst_words = max((g_ip.burst_len / g_ip.int_prefetch_w), 1)
          self.dyn_read_energy_remaining_words_in_burst = (
              (burst_words - 1)
              * (
                  (
                      self.bank.mat.sa_mux_lev_1_predec.power.readOp.dynamic
                      + self.bank.mat.sa_mux_lev_2_predec.power.readOp.dynamic
                      + self.bank.mat.power_sa_mux_lev_1_decoders.readOp.dynamic
                      + self.bank.mat.power_sa_mux_lev_2_decoders.readOp.dynamic
                      + self.bank.mat.power_subarray_out_drv.readOp.dynamic
                  )
                  * self.dp.num_act_mats_hor_dir
                  + self.bank.htree_out_data.power.readOp.dynamic
                  + self.power_routing_to_bank.readOp.dynamic
              )
          )
          self.dyn_read_energy_from_closed_page += self.dyn_read_energy_remaining_words_in_burst
          self.dyn_read_energy_from_open_page   += self.dyn_read_energy_remaining_words_in_burst

          # Summaries
          self.activate_energy = (
              self.htree_in_add.power.readOp.dynamic
              + self.bank.htree_in_add.power_bit.readOp.dynamic
                * self.bank.num_addr_b_routed_to_mat_for_act
              + (
                  self.bank.mat.r_predec.power.readOp.dynamic
                  + self.bank.mat.power_row_decoders.readOp.dynamic
                  + self.bank.mat.power_sa.readOp.dynamic
              )
              * self.dp.num_act_mats_hor_dir
          )
          self.read_energy = (
              self.htree_in_add.power.readOp.dynamic
              + self.bank.htree_in_add.power_bit.readOp.dynamic
                * self.bank.num_addr_b_routed_to_mat_for_rd_or_wr
              + (
                  self.bank.mat.sa_mux_lev_1_predec.power.readOp.dynamic
                  + self.bank.mat.sa_mux_lev_2_predec.power.readOp.dynamic
                  + self.bank.mat.power_sa_mux_lev_1_decoders.readOp.dynamic
                  + self.bank.mat.power_sa_mux_lev_2_decoders.readOp.dynamic
                  + self.bank.mat.power_subarray_out_drv.readOp.dynamic
              )
              * self.dp.num_act_mats_hor_dir
              + self.bank.htree_out_data.power.readOp.dynamic
              + self.htree_in_data.power.readOp.dynamic
          ) * g_ip.burst_len
          self.write_energy = (
              self.htree_in_add.power.readOp.dynamic
              + self.bank.htree_in_add.power_bit.readOp.dynamic
                * self.bank.num_addr_b_routed_to_mat_for_rd_or_wr
              + self.htree_in_data.power.readOp.dynamic
              + self.bank.htree_in_data.power.readOp.dynamic
              + (
                  self.bank.mat.sa_mux_lev_1_predec.power.readOp.dynamic
                  + self.bank.mat.sa_mux_lev_2_predec.power.readOp.dynamic
                  + self.bank.mat.power_sa_mux_lev_1_decoders.readOp.dynamic
                  + self.bank.mat.power_sa_mux_lev_2_decoders.readOp.dynamic
              )
              * self.dp.num_act_mats_hor_dir
          ) * g_ip.burst_len
          self.precharge_energy = (
              self.bank.mat.power_bitline.readOp.dynamic
              + self.bank.mat.power_bl_precharge_eq_drv.readOp.dynamic
          ) * self.dp.num_act_mats_hor_dir

      # 4) Common logic for leak powers
      self.leak_power_subbank_closed_page = (
          self.bank.mat.r_predec.power.readOp.leakage
          + self.bank.mat.b_mux_predec.power.readOp.leakage
          + self.bank.mat.sa_mux_lev_1_predec.power.readOp.leakage
          + self.bank.mat.sa_mux_lev_2_predec.power.readOp.leakage
          + self.bank.mat.power_row_decoders.readOp.leakage
          + self.bank.mat.power_bit_mux_decoders.readOp.leakage
          + self.bank.mat.power_sa_mux_lev_1_decoders.readOp.leakage
          + self.bank.mat.power_sa_mux_lev_2_decoders.readOp.leakage
          + self.bank.mat.leak_power_sense_amps_closed_page_state
      ) * self.dp.num_act_mats_hor_dir
      self.leak_power_subbank_closed_page += (
          self.bank.mat.r_predec.power.readOp.gate_leakage
          + self.bank.mat.b_mux_predec.power.readOp.gate_leakage
          + self.bank.mat.sa_mux_lev_1_predec.power.readOp.gate_leakage
          + self.bank.mat.sa_mux_lev_2_predec.power.readOp.gate_leakage
          + self.bank.mat.power_row_decoders.readOp.gate_leakage
          + self.bank.mat.power_bit_mux_decoders.readOp.gate_leakage
          + self.bank.mat.power_sa_mux_lev_1_decoders.readOp.gate_leakage
          + self.bank.mat.power_sa_mux_lev_2_decoders.readOp.gate_leakage
      ) * self.dp.num_act_mats_hor_dir

      self.leak_power_subbank_open_page = (
          self.bank.mat.r_predec.power.readOp.leakage
          + self.bank.mat.b_mux_predec.power.readOp.leakage
          + self.bank.mat.sa_mux_lev_1_predec.power.readOp.leakage
          + self.bank.mat.sa_mux_lev_2_predec.power.readOp.leakage
          + self.bank.mat.power_row_decoders.readOp.leakage
          + self.bank.mat.power_bit_mux_decoders.readOp.leakage
          + self.bank.mat.power_sa_mux_lev_1_decoders.readOp.leakage
          + self.bank.mat.power_sa_mux_lev_2_decoders.readOp.leakage
          + self.bank.mat.leak_power_sense_amps_open_page_state
      ) * self.dp.num_act_mats_hor_dir
      self.leak_power_subbank_open_page += (
          self.bank.mat.r_predec.power.readOp.gate_leakage
          + self.bank.mat.b_mux_predec.power.readOp.gate_leakage
          + self.bank.mat.sa_mux_lev_1_predec.power.readOp.gate_leakage
          + self.bank.mat.sa_mux_lev_2_predec.power.readOp.gate_leakage
          + self.bank.mat.power_row_decoders.readOp.gate_leakage
          + self.bank.mat.power_bit_mux_decoders.readOp.gate_leakage
          + self.bank.mat.power_sa_mux_lev_1_decoders.readOp.gate_leakage
          + self.bank.mat.power_sa_mux_lev_2_decoders.readOp.gate_leakage
      ) * self.dp.num_act_mats_hor_dir

      self.leak_power_request_and_reply_networks = (
          self.power_routing_to_bank.readOp.leakage
          + self.bank.htree_in_add.power.readOp.leakage
          + self.bank.htree_in_data.power.readOp.leakage
          + self.bank.htree_out_data.power.readOp.leakage
      )
      self.leak_power_request_and_reply_networks += (
          self.power_routing_to_bank.readOp.gate_leakage
          + self.bank.htree_in_add.power.readOp.gate_leakage
          + self.bank.htree_in_data.power.readOp.gate_leakage
          + self.bank.htree_out_data.power.readOp.gate_leakage
      )
      if self.dp.fully_assoc or self.dp.pure_cam:
          self.leak_power_request_and_reply_networks += (
              self.htree_in_search.power.readOp.leakage
              + self.htree_out_search.power.readOp.leakage
              + self.htree_in_search.power.readOp.gate_leakage
              + self.htree_out_search.power.readOp.gate_leakage
          )

      # if DRAM => add refresh power
      if self.dp.is_dram:
          # add row predec & dec plus bitline read energy, sense amps, etc.
          self.refresh_power = (
              (self.bank.mat.r_predec.power.readOp.dynamic * self.dp.num_act_mats_hor_dir
              + self.bank.mat.row_dec.power.readOp.dynamic)
              * self.dp.num_r_subarray * self.dp.num_subarrays
          )
          self.refresh_power += (
              self.bank.mat.per_bitline_read_energy
              * self.dp.num_c_subarray
              * self.dp.num_r_subarray
              * self.dp.num_subarrays
          )
          self.refresh_power += (
              self.bank.mat.power_bl_precharge_eq_drv.readOp.dynamic
              * self.dp.num_act_mats_hor_dir
          )
          self.refresh_power += (
              self.bank.mat.power_sa.readOp.dynamic
              * self.dp.num_act_mats_hor_dir
          )
          self.refresh_power /= self.dp.dram_refresh_period

      # If not tag => finalize power
      if not self.dp.is_tag:
          self.power.readOp.dynamic = self.dyn_read_energy_from_closed_page
          # writeOp.dynamic is derived from read dynamic minus certain terms plus bitline changes
          self.power.writeOp.dynamic = (
              self.dyn_read_energy_from_closed_page
              - self.dyn_read_energy_remaining_words_in_burst
              - (self.bank.mat.power_bitline.readOp.dynamic * self.dp.num_act_mats_hor_dir)
              + (self.bank.mat.power_bitline.writeOp.dynamic * self.dp.num_act_mats_hor_dir)
              + (
                  self.power_routing_to_bank.writeOp.dynamic
                  - self.power_routing_to_bank.readOp.dynamic
                  - self.bank.htree_out_data.power.readOp.dynamic
                  + self.bank.htree_in_data.power.readOp.dynamic
              )
              * (max((g_ip.burst_len / g_ip.int_prefetch_w), 1) - 1)
          )

          if not self.dp.is_dram:
              self.power.writeOp.dynamic -= (
                  self.bank.mat.power_sa.readOp.dynamic * self.dp.num_act_mats_hor_dir
              )

      # if DRAM, add refresh power to total leakage
      if self.dp.is_dram:
          self.power.readOp.leakage += self.refresh_power

      # if 3D => override the final read/write dynamic and readOp.leakage
      # this ensures no asserts from 0 or negative values
      if g_ip.is_3d_mem:
          self.power.readOp.dynamic  = self.read_energy
          self.power.writeOp.dynamic = self.write_energy
          self.power.readOp.leakage  = (
              self.membus_RAS.power.readOp.leakage
              + self.membus_CAS.power.readOp.leakage
              + self.membus_data.power.readOp.leakage
          )

      # final checks
      assert self.power.readOp.dynamic > 0,   "UCA read dynamic must be > 0"
      assert self.power.writeOp.dynamic > 0,  "UCA write dynamic must be > 0"
      assert self.power.readOp.leakage > 0,   "UCA read leakage must be > 0"
