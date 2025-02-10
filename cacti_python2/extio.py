from math import isclose

# Suppose you have these enumerations already somewhere in your code:
# from cacti_interface import Mem_state, Mem_IO_type
# But let's define them here for completeness:
from .cacti_interface import Mem_state, Mem_IO_type
# class Mem_state:
#     READ  = 0
#     WRITE = 1
#     IDLE  = 2
#     SLEEP = 3

# class Mem_IO_type:
#     DDR3 = 0
#     DDR4 = 1
#     LPDDR2 = 2
#     WideIO = 3
#     Low_Swing_Diff = 4
#     Serial = 5

# Extio corresponds to the C++ "Extio : public Component" but we'll omit any base class
# unless you have one. We just define a normal Python class.

class Extio:
    def __init__(self, g_ip, io_param):
        """
        Python version of:

          Extio::Extio(IOTechParam *iot):
              io_param(iot) {}
        
        We also store a reference to g_ip (the InputParameter) so we can
        access fields like g_ip.num_dq, g_ip.iostate, etc.
        """
        self.io_param = io_param
        self.g_ip = g_ip

        # The following are the same data members from extio.h,
        # all initialized to 0.0. We’ll fill them in the methods.
        self.io_area = 0.0

        self.io_power_term = 0.0
        self.power_termination_write = 0.0
        self.power_termination_read  = 0.0
        self.power_bias = 0.0
        self.power_clk_bias = 0.0

        self.phy_power = 0.0
        self.phy_wtime = 0.0
        self.phy_static_power = 0.0
        self.phy_dynamic_power = 0.0

        self.io_power_dynamic = 0.0

        self.power_dq_write  = 0.0
        self.power_dqs_write = 0.0
        self.power_ca_write  = 0.0
        self.power_dq_read   = 0.0
        self.power_dqs_read  = 0.0
        self.power_ca_read   = 0.0
        self.power_clk       = 0.0

        self.io_tmargin = 0.0
        self.io_vmargin = 0.0

    def extio_area(self):
        """
        Python version of Extio::extio_area()
        External IO area calculation.
        
        The code uses:
          single_io_area = ...
          if (2*rtt1_dq_read < r_on): single_io_area = ...
          io_area = (g_ip->num_dq + g_ip->num_dqs + g_ip->num_ca + g_ip->num_clk)*single_io_area
        Then prints the result.
        Returns io_area.
        """
        ip = self.g_ip
        iop = self.io_param

        # same formula as C++:
        single_io_area = (
            iop.ioarea_c
            + (iop.ioarea_k0 / iop.r_on)
            + (1.0 / iop.r_on)
              * (
                  iop.ioarea_k1 * iop.frequency
                  + iop.ioarea_k2 * iop.frequency * iop.frequency
                  + iop.ioarea_k3 * iop.frequency * iop.frequency * iop.frequency
                )
        )

        # If 2*rtt1_dq_read < r_on => override single_io_area
        if 2 * iop.rtt1_dq_read < iop.r_on:
            single_io_area = (
                iop.ioarea_c
                + (iop.ioarea_k0 / (2 * iop.rtt1_dq_read))
                + (1.0 / iop.r_on)
                  * (
                      iop.ioarea_k1 * iop.frequency
                      + iop.ioarea_k2 * iop.frequency * iop.frequency
                      + iop.ioarea_k3 * iop.frequency * iop.frequency * iop.frequency
                    )
            )

        # total IO area
        total_ios = ip.num_dq + ip.num_dqs + ip.num_ca + ip.num_clk
        self.io_area = total_ios * single_io_area

        print(f"IO Area (sq.mm) = {self.io_area}")
        return self.io_area

    def extio_power_term(self):
        """
        Python version of Extio::extio_power_term()
        Compute termination/bias/ODT power based on the current I/O state.
        """
        ip = self.g_ip
        iop = self.io_param

        # Bias & leakage power
        #   i_bias * vdd_io
        # + i_leak*(num_dq + num_dqs + num_clk + num_ca)*vdd_io / 1e6
        self.power_bias = (
            iop.i_bias * iop.vdd_io
            + iop.i_leak * (ip.num_dq + ip.num_dqs + ip.num_clk + ip.num_ca)
              * iop.vdd_io / 1000000.0
        )

        # power_termination_read:
        #   1000*(num_dq+num_dqs)*vdd_io^2 * 0.25*[ ... ] + 1000*num_ca*...
        self.power_termination_read = (
            1000.0 * (ip.num_dq + ip.num_dqs) * iop.vdd_io * iop.vdd_io * 0.25
            * (
                1.0/(iop.r_on + iop.rpar_read + iop.rs1_dq)
                + 1.0/iop.rtt1_dq_read
                + 1.0/iop.rtt2_dq_read
              )
            + 1000.0 * ip.num_ca * iop.vdd_io * iop.vdd_io
              * (0.5 / (2.0*(iop.r_on_ca + iop.rtt_ca)))
        )

        # power_termination_write:
        self.power_termination_write = (
            1000.0*(ip.num_dq + ip.num_dqs)*iop.vdd_io*iop.vdd_io*0.25
            * (
                1.0/(iop.r_on + iop.rpar_write)
                + 1.0/iop.rtt1_dq_write
                + 1.0/iop.rtt2_dq_write
              )
            + 1000.0 * ip.num_ca * iop.vdd_io * iop.vdd_io
              * (0.5 / (2.0*(iop.r_on_ca + iop.rtt_ca)))
        )

        self.power_clk_bias = iop.vdd_io * iop.v_sw_clk / iop.r_diff_term * 1000.0

        # If io_type == Serial, override:
        if iop.io_type == Mem_IO_type.Serial:
            self.power_termination_read = (
                1000.0*(ip.num_dq)*iop.vdd_io*iop.v_sw_clk / iop.r_diff_term
            )
            self.power_termination_write = (
                1000.0*(ip.num_dq)*iop.vdd_io*iop.v_sw_clk / iop.r_diff_term
            )
            self.power_clk_bias = 0.0

        # If io_type == DDR4, recalc special:
        if iop.io_type == Mem_IO_type.DDR4:
            self.power_termination_read = (
                1000.0*(ip.num_dq + ip.num_dqs)*iop.vdd_io*iop.vdd_io*0.5
                * (1.0/(iop.r_on + iop.rpar_read + iop.rs1_dq))
                + 1000.0*ip.num_ca*iop.vdd_io*iop.vdd_io
                  * (0.5 / (2.0*(iop.r_on_ca + iop.rtt_ca)))
            )
            self.power_termination_write = (
                1000.0*(ip.num_dq + ip.num_dqs)*iop.vdd_io*iop.vdd_io*0.5
                * (1.0/(iop.r_on + iop.rpar_write))
                + 1000.0*ip.num_ca*iop.vdd_io*iop.vdd_io
                  * (0.5 / (2.0*(iop.r_on_ca + iop.rtt_ca)))
            )

        # Combine terms based on iostate
        # read => duty_cycle*(power_termination_read + bias + clk_bias)
        # etc.
        if ip.iostate == Mem_state.READ:
            self.io_power_term = (
                ip.duty_cycle * (
                    self.power_termination_read
                    + self.power_bias
                    + self.power_clk_bias
                )
            )
        elif ip.iostate == Mem_state.WRITE:
            self.io_power_term = (
                ip.duty_cycle * (
                    self.power_termination_write
                    + self.power_bias
                    + self.power_clk_bias
                )
            )
        elif ip.iostate == Mem_state.IDLE:
            # default is the write calc from the code snippet
            self.io_power_term = (
                ip.duty_cycle * (
                    self.power_termination_write
                    + self.power_bias
                    + self.power_clk_bias
                )
            )
            if iop.io_type == Mem_IO_type.DDR4:
                # override with just the leakage
                self.io_power_term = 1e-6*iop.i_leak*iop.vdd_io
        elif ip.iostate == Mem_state.SLEEP:
            # just leakage
            self.io_power_term = 1e-6*iop.i_leak*iop.vdd_io
        else:
            self.io_power_term = 0.0

        print(f"IO Termination and Bias Power (mW) = {self.io_power_term}")
        return self.io_power_term

    def extio_power_phy(self):
        """
        Python version of Extio::extio_power_phy()
        External PHY power & wakeup time.
        """
        ip = self.g_ip
        iop = self.io_param

        # static & dynamic power in mW
        self.phy_static_power = (
            iop.phy_datapath_s
            + iop.phy_phase_rotator_s
            + iop.phy_clock_tree_s
            + iop.phy_rx_s
            + iop.phy_dcc_s
            + iop.phy_deskew_s
            + iop.phy_leveling_s
            + iop.phy_pll_s
        )

        self.phy_dynamic_power = (
            iop.phy_datapath_d
            + iop.phy_phase_rotator_d
            + iop.phy_clock_tree_d
            + iop.phy_rx_d
            + iop.phy_dcc_d
            + iop.phy_deskew_d
            + iop.phy_leveling_d
            + iop.phy_pll_d
        )  # in mW/Gbps

        # Combine based on state:
        if ip.iostate == Mem_state.READ:
            self.phy_power = (
                self.phy_static_power
                + 2.0*iop.frequency*ip.num_dq*self.phy_dynamic_power / 1000.0
            )
        elif ip.iostate == Mem_state.WRITE:
            self.phy_power = (
                self.phy_static_power
                + 2.0*iop.frequency*ip.num_dq*self.phy_dynamic_power / 1000.0
            )
        elif ip.iostate == Mem_state.IDLE:
            self.phy_power = self.phy_static_power
        elif ip.iostate == Mem_state.SLEEP:
            self.phy_power = 0.0
        else:
            self.phy_power = 0.0

        # sum of wakeup times
        self.phy_wtime = (
            iop.phy_pll_wtime
            + iop.phy_phase_rotator_wtime
            + iop.phy_rx_wtime
            + iop.phy_bandgap_wtime
            + iop.phy_deskew_wtime
            + iop.phy_vrefgen_wtime
        )

        print(f"PHY Power (mW) = {self.phy_power}  PHY Wakeup Time (us) = {self.phy_wtime}")
        return self.phy_power

    def extio_power_dynamic(self):
        """
        Python version of Extio::extio_power_dynamic()
        External IO dynamic power, not including termination or PHY.
        """
        ip = self.g_ip
        iop = self.io_param

        if iop.io_type == Mem_IO_type.Serial:
            # If serial, all zero
            self.power_dq_write  = 0.0
            self.power_dqs_write = 0.0
            self.power_ca_write  = 0.0
            self.power_dq_read   = 0.0
            self.power_dqs_read  = 0.0
            self.power_ca_read   = 0.0
            self.power_clk       = 0.0
        else:
            # line caps
            # c_line for DDR signals
            c_line = 1e6/(iop.z0*2.0*iop.frequency)
            c_line_ca = c_line
            c_line_sdr = 1e6/(iop.z0*iop.frequency)
            c_line_2T  = 1e6*2.0/(iop.z0*iop.frequency)
            c_line_3T  = 1e6*3.0/(iop.z0*iop.frequency)

            # If flight time < half bit period => c_line = ...
            half_bit = 1e3/(4.0*iop.frequency)
            if iop.t_flight < half_bit:
                c_line = (1e3*iop.t_flight)/iop.z0
            if iop.t_flight_ca < half_bit:
                c_line_ca = (1e3*iop.t_flight_ca)/iop.z0

            # For SDR CA => 1/2 freq
            if iop.t_flight_ca < (1e3/(2.0*iop.frequency)):
                c_line_sdr = (1e3*iop.t_flight_ca)/iop.z0
            # For 2T => times 2
            if iop.t_flight_ca < (1e3*2.0/(2.0*iop.frequency)):
                c_line_2T = (1e3*iop.t_flight_ca)/iop.z0
            # For 3T => times 3
            if iop.t_flight_ca < (1e3*3.0/(2.0*iop.frequency)):
                c_line_3T = (1e3*iop.t_flight_ca)/iop.z0

            # address timing pick
            if isclose(ip.addr_timing, 1.0):
                c_line_ca = c_line_sdr
            elif isclose(ip.addr_timing, 2.0):
                c_line_ca = c_line_2T
            elif isclose(ip.addr_timing, 3.0):
                c_line_ca = c_line_3T

            freq   = iop.frequency
            vdd    = iop.vdd_io
            # Write:
            self.power_dq_write = (
                ip.num_dq*ip.activity_dq*(iop.c_tx + c_line)*vdd*iop.v_sw_data_write_line*freq/1000.0
                + ip.num_dq*ip.activity_dq*iop.c_data*vdd*iop.v_sw_data_write_load1*freq/1000.0
                + ip.num_dq*ip.activity_dq*((iop.num_mem_dq-1.0)*iop.c_data)*vdd*iop.v_sw_data_write_load2*freq/1000.0
                + ip.num_dq*ip.activity_dq*iop.c_int*vdd*vdd*freq/1000.0
            )

            self.power_dqs_write = (
                ip.num_dqs*(iop.c_tx + c_line)*vdd*iop.v_sw_data_write_line*freq/1000.0
                + ip.num_dqs*iop.c_data*vdd*iop.v_sw_data_write_load1*freq/1000.0
                + ip.num_dqs*((iop.num_mem_dq-1.0)*iop.c_data)*vdd*iop.v_sw_data_write_load2*freq/1000.0
                + ip.num_dqs*iop.c_int*vdd*vdd*freq/1000.0
            )

            self.power_ca_write = (
                ip.num_ca*ip.activity_ca*(iop.c_tx + iop.num_mem_ca*iop.c_addr + c_line_ca)*vdd*iop.v_sw_addr*freq/1000.0
                + ip.num_ca*ip.activity_ca*iop.c_int*vdd*vdd*freq/1000.0
            )

            # Read:
            self.power_dq_read = (
                ip.num_dq*ip.activity_dq*(iop.c_tx + c_line)*vdd*iop.v_sw_data_read_line*freq/1000.0
                + ip.num_dq*ip.activity_dq*iop.c_data*vdd*iop.v_sw_data_read_load1*freq/1000.0
                + ip.num_dq*ip.activity_dq*((iop.num_mem_dq-1.0)*iop.c_data)*vdd*iop.v_sw_data_read_load2*freq/1000.0
                + ip.num_dq*ip.activity_dq*iop.c_int*vdd*vdd*freq/1000.0
            )
            self.power_dqs_read = (
                ip.num_dqs*(iop.c_tx + c_line)*vdd*iop.v_sw_data_read_line*freq/1000.0
                + ip.num_dqs*iop.c_data*vdd*iop.v_sw_data_read_load1*freq/1000.0
                + ip.num_dqs*((iop.num_mem_dq-1.0)*iop.c_data)*vdd*iop.v_sw_data_read_load2*freq/1000.0
                + ip.num_dqs*iop.c_int*vdd*vdd*freq/1000.0
            )
            self.power_ca_read = (
                ip.num_ca*ip.activity_ca*(iop.c_tx + iop.num_mem_ca*iop.c_addr + c_line_ca)*vdd*iop.v_sw_addr*freq/1000.0
                + ip.num_ca*ip.activity_ca*iop.c_int*vdd*vdd*freq/1000.0
            )
            self.power_clk = (
                ip.num_clk*(iop.c_tx + iop.num_mem_clk*iop.c_data + c_line)*vdd*iop.v_sw_clk*freq/1000.0
                + ip.num_clk*iop.c_int*vdd*vdd*freq/1000.0
            )

        # combine based on state
        if ip.iostate == Mem_state.READ:
            self.io_power_dynamic = ip.duty_cycle * (
                self.power_dq_read + self.power_ca_read
                + self.power_dqs_read + self.power_clk
            )
        elif ip.iostate == Mem_state.WRITE:
            self.io_power_dynamic = ip.duty_cycle * (
                self.power_dq_write + self.power_ca_write
                + self.power_dqs_write + self.power_clk
            )
        elif ip.iostate == Mem_state.IDLE:
            self.io_power_dynamic = ip.duty_cycle * (self.power_clk)
        elif ip.iostate == Mem_state.SLEEP:
            self.io_power_dynamic = 0.0
        else:
            self.io_power_dynamic = 0.0

        print(f"IO Dynamic Power (mW) = {self.io_power_dynamic}")
        return self.io_power_dynamic

    def extio_eye(self):
        """
        Python version of Extio::extio_eye()
        Compute I/O timing margin (ps) and voltage margin (V).
        """
        ip = self.g_ip
        iop = self.io_param

        # If serial, no voltage margin is computed
        if iop.io_type == Mem_IO_type.Serial:
            self.io_vmargin = 0.0
        else:
            # compute voltage noise
            v_noise_write = iop.k_noise_write_sen*iop.v_sw_data_write_line + iop.v_noise_independent_write
            v_noise_read  = iop.k_noise_read_sen *iop.v_sw_data_read_line  + iop.v_noise_independent_read
            v_noise_addr  = iop.k_noise_addr_sen *iop.v_sw_addr            + iop.v_noise_independent_addr

            # choose the smaller margin of DQ vs CA
            if ip.iostate == Mem_state.READ:
                dq_margin = iop.v_sw_data_read_line*0.5 - v_noise_read
                ca_margin = iop.v_sw_addr*0.5 - v_noise_addr
                self.io_vmargin = dq_margin if (dq_margin < ca_margin) else ca_margin
            elif ip.iostate == Mem_state.WRITE:
                dq_margin = iop.v_sw_data_write_line*0.5 - v_noise_write
                ca_margin = iop.v_sw_addr*0.5 - v_noise_addr
                self.io_vmargin = dq_margin if (dq_margin < ca_margin) else ca_margin
            else:
                self.io_vmargin = 0.0

        # Now compute timing margin
        freq = iop.frequency
        if iop.io_type == Mem_IO_type.Serial:
            # specialized formula in the code
            t_margin_write_setup = (1e6/(4.0*freq)) - iop.t_ds - iop.t_jitter_setup_sen
            t_margin_write_hold  = (1e6/(4.0*freq)) - iop.t_dh - iop.t_dcd_soc - iop.t_jitter_hold_sen
            t_margin_read_setup  = (1e6/(4.0*freq)) - iop.t_soc_setup - iop.t_jitter_setup_sen
            t_margin_read_hold   = (1e6/(4.0*freq)) - iop.t_soc_hold - iop.t_dcd_dram - iop.t_dcd_soc - iop.t_jitter_hold_sen

            t_margin_addr_setup = (1e6*ip.addr_timing/(2.0*freq))
            t_margin_addr_hold  = (1e6*ip.addr_timing/(2.0*freq))

        else:
            # normal DDR formula
            t_margin_write_setup = (
                (1e6/(4.0*freq))
                - iop.t_ds - iop.t_error_soc - iop.t_jitter_setup_sen - iop.t_skew_setup
                + iop.t_cor_margin
            )
            t_margin_write_hold = (
                (1e6/(4.0*freq))
                - iop.t_dh - iop.t_dcd_soc - iop.t_error_soc - iop.t_jitter_hold_sen
                - iop.t_skew_hold + iop.t_cor_margin
            )
            t_margin_read_setup = (
                (1e6/(4.0*freq))
                - iop.t_soc_setup - iop.t_error_soc - iop.t_jitter_setup_sen
                - iop.t_skew_setup - iop.t_dqsq + iop.t_cor_margin
            )
            t_margin_read_hold = (
                (1e6/(4.0*freq))
                - iop.t_soc_hold - iop.t_dcd_dram - iop.t_dcd_soc
                - iop.t_error_soc - iop.t_jitter_hold_sen - iop.t_skew_hold
                + iop.t_cor_margin
            )
            t_margin_addr_setup = (
                (1e6*ip.addr_timing/(2.0*freq))
                - iop.t_is - iop.t_error_soc - iop.t_jitter_addr_setup_sen
                - iop.t_skew_setup + iop.t_cor_margin
            )
            t_margin_addr_hold = (
                (1e6*ip.addr_timing/(2.0*freq))
                - iop.t_ih - iop.t_dcd_soc - iop.t_error_soc - iop.t_jitter_addr_hold_sen
                - iop.t_skew_hold + iop.t_cor_margin
            )

        # figure out the worst-case timing margin
        if ip.iostate == Mem_state.READ:
            # pick the min among read_setup/read_hold/addr_setup/addr_hold
            tmp1 = min(t_margin_read_setup, t_margin_read_hold)
            tmp2 = min(t_margin_addr_setup, t_margin_addr_hold)
            self.io_tmargin = tmp1 if (tmp1 < tmp2) else tmp2
        elif ip.iostate == Mem_state.WRITE:
            tmp1 = min(t_margin_write_setup, t_margin_write_hold)
            tmp2 = min(t_margin_addr_setup, t_margin_addr_hold)
            self.io_tmargin = tmp1 if (tmp1 < tmp2) else tmp2
        else:
            self.io_tmargin = 0.0

        print(f"IO Timing Margin (ps) = {self.io_tmargin}")
        print(f"IO Voltage Margin (V) = {self.io_vmargin}")
        return self.io_tmargin
