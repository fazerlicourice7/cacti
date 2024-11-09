from .parameter import InputParameter

class Extio:
    def __init__(self, g_ip: InputParameter, io_param):
        self.g_ip = g_ip
        self.io_param = io_param
        self.io_area = 0.0 # don't convert
        self.io_power_term = 0.0 # don't convert
        self.power_termination_write = 0.0 # don't convert
        self.power_termination_read = 0.0 # don't convert
        self.power_bias = 0.0 # don't convert
        self.power_clk_bias = 0.0 # don't convert
        self.phy_power = 0.0 # don't convert
        self.phy_wtime = 0.0 # don't convert
        self.phy_static_power = 0.0 # don't convert
        self.phy_dynamic_power = 0.0 # don't convert
        self.io_power_dynamic = 0.0 # don't convert
        self.power_dq_write = 0.0 # don't convert
        self.power_dqs_write = 0.0 # don't convert
        self.power_ca_write = 0.0 # don't convert
        self.power_dq_read = 0.0 # don't convert
        self.power_dqs_read = 0.0 # don't convert
        self.power_ca_read = 0.0 # don't convert
        self.power_clk = 0.0 # don't convert
        self.io_tmargin = 0.0 # don't convert
        self.io_vmargin = 0.0 # don't convert

    def extio_area(self):
        single_io_area = (self.io_param.ioarea_c +
                          (self.io_param.ioarea_k0 / self.io_param.r_on) +
                          (1 / self.io_param.r_on) * (self.io_param.ioarea_k1 * self.io_param.frequency +
                                                      self.io_param.ioarea_k2 * self.io_param.frequency**2 +
                                                      self.io_param.ioarea_k3 * self.io_param.frequency**3))

        # CHANGE: Relational
        # if 2 * self.io_param.rtt1_dq_read < self.io_param.r_on:
        #     single_io_area = (self.io_param.ioarea_c +
        #                       (self.io_param.ioarea_k0 / (2 * self.io_param.rtt1_dq_read)) +
        #                       (1 / self.io_param.r_on) * (self.io_param.ioarea_k1 * self.io_param.frequency +
        #                                                   self.io_param.ioarea_k2 * self.io_param.frequency**2 +
        #                                                   self.io_param.ioarea_k3 * self.io_param.frequency**3))

        self.io_area = (self.g_ip.num_dq + self.g_ip.num_dqs + self.g_ip.num_ca + self.g_ip.num_clk) * single_io_area

        # print("IO Area (sq.mm) =", self.io_area)
        return self.io_area

    def extio_power_term(self):
        self.power_bias = (self.io_param.i_bias * self.io_param.vdd_io +
                           self.io_param.i_leak * (self.g_ip.num_dq +
                                                   self.g_ip.num_dqs +
                                                   self.g_ip.num_clk +
                                                   self.g_ip.num_ca) * self.io_param.vdd_io / 1e6)

        self.power_termination_read = (1000 * (self.g_ip.num_dq + self.g_ip.num_dqs) * self.io_param.vdd_io**2 * 0.25 *
                                       (1 / (self.io_param.r_on + self.io_param.rpar_read + self.io_param.rs1_dq) +
                                        1 / self.io_param.rtt1_dq_read +
                                        1 / self.io_param.rtt2_dq_read) +
                                       1000 * self.g_ip.num_ca * self.io_param.vdd_io**2 *
                                       (0.5 / (2 * (self.io_param.r_on_ca + self.io_param.rtt_ca))))

        self.power_termination_write = (1000 * (self.g_ip.num_dq + self.g_ip.num_dqs) * self.io_param.vdd_io**2 * 0.25 *
                                        (1 / (self.io_param.r_on + self.io_param.rpar_write) +
                                         1 / self.io_param.rtt1_dq_write +
                                         1 / self.io_param.rtt2_dq_write) +
                                        1000 * self.g_ip.num_ca * self.io_param.vdd_io**2 *
                                        (0.5 / (2 * (self.io_param.r_on_ca + self.io_param.rtt_ca))))

        self.power_clk_bias = (self.io_param.vdd_io * self.io_param.v_sw_clk /
                               self.io_param.r_diff_term * 1000)

        if self.io_param.io_type == 'Serial':
            self.power_termination_read = 1000 * self.g_ip.num_dq * self.io_param.vdd_io * self.io_param.v_sw_clk / self.io_param.r_diff_term
            self.power_termination_write = 1000 * self.g_ip.num_dq * self.io_param.vdd_io * self.io_param.v_sw_clk / self.io_param.r_diff_term
            self.power_clk_bias = 0

        elif self.io_param.io_type == 'DDR4':
            self.power_termination_read = (1000 * (self.g_ip.num_dq + self.g_ip.num_dqs) * self.io_param.vdd_io**2 * 0.5 *
                                           (1 / (self.io_param.r_on + self.io_param.rpar_read + self.io_param.rs1_dq)) +
                                           1000 * self.g_ip.num_ca * self.io_param.vdd_io**2 *
                                           (0.5 / (2 * (self.io_param.r_on_ca + self.io_param.rtt_ca))))

            self.power_termination_write = (1000 * (self.g_ip.num_dq + self.g_ip.num_dqs) * self.io_param.vdd_io**2 * 0.5 *
                                            (1 / (self.io_param.r_on + self.io_param.rpar_write)) +
                                            1000 * self.g_ip.num_ca * self.io_param.vdd_io**2 *
                                            (0.5 / (2 * (self.io_param.r_on_ca + self.io_param.rtt_ca))))

        if self.g_ip.iostate == 'READ':
            self.io_power_term = self.g_ip.duty_cycle * (self.power_termination_read + self.power_bias + self.power_clk_bias)
        elif self.g_ip.iostate == 'WRITE':
            self.io_power_term = self.g_ip.duty_cycle * (self.power_termination_write + self.power_bias + self.power_clk_bias)
        elif self.g_ip.iostate == 'IDLE':
            self.io_power_term = self.g_ip.duty_cycle * (self.power_termination_write + self.power_bias + self.power_clk_bias)
            if self.io_param.io_type == 'DDR4':
                self.io_power_term = 1e-6 * self.io_param.i_leak * self.io_param.vdd_io
        elif self.g_ip.iostate == 'SLEEP':
            self.io_power_term = 1e-6 * self.io_param.i_leak * self.io_param.vdd_io
        else:
            self.io_power_term = 0

        # print("IO Termination and Bias Power (mW) =", self.io_power_term)
        return self.io_power_term

    def extio_power_phy(self):
        self.phy_static_power = (self.io_param.phy_datapath_s +
                                 self.io_param.phy_phase_rotator_s +
                                 self.io_param.phy_clock_tree_s +
                                 self.io_param.phy_rx_s +
                                 self.io_param.phy_dcc_s +
                                 self.io_param.phy_deskew_s +
                                 self.io_param.phy_leveling_s +
                                 self.io_param.phy_pll_s)

        self.phy_dynamic_power = (self.io_param.phy_datapath_d +
                                  self.io_param.phy_phase_rotator_d +
                                  self.io_param.phy_clock_tree_d +
                                  self.io_param.phy_rx_d +
                                  self.io_param.phy_dcc_d +
                                  self.io_param.phy_deskew_d +
                                  self.io_param.phy_leveling_d +
                                  self.io_param.phy_pll_d)

        if self.g_ip.iostate == 'READ' or self.g_ip.iostate == 'WRITE':
            self.phy_power = self.phy_static_power + 2 * self.io_param.frequency * self.g_ip.num_dq * self.phy_dynamic_power / 1000
        elif self.g_ip.iostate == 'IDLE':
            self.phy_power = self.phy_static_power
        elif self.g_ip.iostate == 'SLEEP':
            self.phy_power = 0
        else:
            self.phy_power = 0

        self.phy_wtime = (self.io_param.phy_pll_wtime +
                          self.io_param.phy_phase_rotator_wtime +
                          self.io_param.phy_rx_wtime +
                          self.io_param.phy_bandgap_wtime +
                          self.io_param.phy_deskew_wtime +
                          self.io_param.phy_vrefgen_wtime)

        # print("PHY Power (mW) =", self.phy_power, "PHY Wakeup Time (us) =", self.phy_wtime)
        return self.phy_power

    def extio_power_dynamic(self):
        if self.io_param.io_type == 'Serial':
            self.power_dq_write = 0
            self.power_dqs_write = 0
            self.power_ca_write = 0
            self.power_dq_read = 0
            self.power_dqs_read = 0
            self.power_ca_read = 0
            self.power_clk = 0
        else:
            c_line = 1e6 / (self.io_param.z0 * 2 * self.io_param.frequency)
            c_line_ca = c_line
            c_line_sdr = 1e6 / (self.io_param.z0 * self.io_param.frequency)
            c_line_2T = 1e6 * 2 / (self.io_param.z0 * self.io_param.frequency)
            c_line_3T = 1e6 * 3 / (self.io_param.z0 * self.io_param.frequency)

            # TODO CHECK: ask if just set these values
            # if float(self.io_param.t_flight) < 1e3 / (4 * float(self.io_param.frequency)):
            #     c_line = 1e3 * float(self.io_param.t_flight) / float(self.io_param.z0)

            # if float(self.io_param.t_flight_ca) < 1e3 / (4 * float(self.io_param.frequency)):
            #     c_line_ca = 1e3 * float(self.io_param.t_flight_ca) / float(self.io_param.z0)

            # if float(self.io_param.t_flight_ca) < 1e3 / (2 * float(self.io_param.frequency)):
            #     c_line_sdr = 1e3 * float(self.io_param.t_flight_ca) / float(self.io_param.z0)

            # if float(self.io_param.t_flight_ca) < 1e3 * 2 / (2 * float(self.io_param.frequency)):
            #     c_line_2T = 1e3 * float(self.io_param.t_flight_ca) / float(self.io_param.z0)

            # if float(self.io_param.t_flight_ca) < 1e3 * 3 / (2 * float(self.io_param.frequency)):
            #     c_line_3T = 1e3 * float(self.io_param.t_flight_ca) / float(self.io_param.z0)

            # if self.g_ip.addr_timing == 1.0:
            #     c_line_ca = c_line_sdr
            # elif self.g_ip.addr_timing == 2.0:
            #     c_line_ca = c_line_2T
            # elif self.g_ip.addr_timing == 3.0:
            #     c_line_ca = c_line_3T

            self.power_dq_write = (self.g_ip.num_dq * self.g_ip.activity_dq *
                                   (self.io_param.c_tx + c_line) * self.io_param.vdd_io *
                                   self.io_param.v_sw_data_write_line * self.io_param.frequency / 1000 +
                                   self.g_ip.num_dq * self.g_ip.activity_dq * self.io_param.c_data *
                                   self.io_param.vdd_io * self.io_param.v_sw_data_write_load1 *
                                   self.io_param.frequency / 1000 +
                                   self.g_ip.num_dq * self.g_ip.activity_dq * ((self.g_ip.num_mem_dq - 1) * self.io_param.c_data) *
                                   self.io_param.vdd_io * self.io_param.v_sw_data_write_load2 *
                                   self.io_param.frequency / 1000 +
                                   self.g_ip.num_dq * self.g_ip.activity_dq * self.io_param.c_int *
                                   self.io_param.vdd_io * self.io_param.vdd_io * self.io_param.frequency / 1000)

            self.power_dqs_write = (self.g_ip.num_dqs * (self.io_param.c_tx + c_line) *
                                    self.io_param.vdd_io * self.io_param.v_sw_data_write_line *
                                    self.io_param.frequency / 1000 +
                                    self.g_ip.num_dqs * self.io_param.c_data * self.io_param.vdd_io *
                                    self.io_param.v_sw_data_write_load1 * self.io_param.frequency / 1000 +
                                    self.g_ip.num_dqs * ((self.g_ip.num_mem_dq - 1) * self.io_param.c_data) *
                                    self.io_param.vdd_io * self.io_param.v_sw_data_write_load2 *
                                    self.io_param.frequency / 1000 +
                                    self.g_ip.num_dqs * self.io_param.c_int * self.io_param.vdd_io *
                                    self.io_param.vdd_io * self.io_param.frequency / 1000)

            self.power_ca_write = (self.g_ip.num_ca * self.g_ip.activity_ca *
                                   (self.io_param.c_tx + self.io_param.num_mem_ca * self.io_param.c_addr +
                                    c_line_ca) *
                                   self.io_param.vdd_io * self.io_param.v_sw_addr * self.io_param.frequency / 1000 +
                                   self.g_ip.num_ca * self.g_ip.activity_ca * self.io_param.c_int *
                                   self.io_param.vdd_io * self.io_param.vdd_io * self.io_param.frequency / 1000)

            self.power_dq_read = (self.g_ip.num_dq * self.g_ip.activity_dq *
                                  (self.io_param.c_tx + c_line) * self.io_param.vdd_io *
                                  self.io_param.v_sw_data_read_line * self.io_param.frequency / 1000 +
                                  self.g_ip.num_dq * self.g_ip.activity_dq * self.io_param.c_data *
                                  self.io_param.vdd_io * self.io_param.v_sw_data_read_load1 * self.io_param.frequency / 1000 +
                                  self.g_ip.num_dq * self.g_ip.activity_dq * ((self.g_ip.num_mem_dq - 1) * self.io_param.c_data) *
                                  self.io_param.vdd_io * self.io_param.v_sw_data_read_load2 * self.io_param.frequency / 1000 +
                                  self.g_ip.num_dq * self.g_ip.activity_dq * self.io_param.c_int * self.io_param.vdd_io *
                                  self.io_param.vdd_io * self.io_param.frequency / 1000)

            self.power_dqs_read = (self.g_ip.num_dqs * (self.io_param.c_tx + c_line) *
                                   self.io_param.vdd_io * self.io_param.v_sw_data_read_line *
                                   self.io_param.frequency / 1000 +
                                   self.g_ip.num_dqs * self.io_param.c_data * self.io_param.vdd_io *
                                   self.io_param.v_sw_data_read_load1 * self.io_param.frequency / 1000 +
                                   self.g_ip.num_dqs * ((self.g_ip.num_mem_dq - 1) * self.io_param.c_data) *
                                   self.io_param.vdd_io * self.io_param.v_sw_data_read_load2 * self.io_param.frequency / 1000 +
                                   self.g_ip.num_dqs * self.io_param.c_int * self.io_param.vdd_io * self.io_param.vdd_io *
                                   self.io_param.frequency / 1000)

            self.power_ca_read = (self.g_ip.num_ca * self.g_ip.activity_ca *
                                  (self.io_param.c_tx + self.io_param.num_mem_ca *
                                   self.io_param.c_addr + c_line_ca) *
                                  self.io_param.vdd_io * self.io_param.v_sw_addr * self.io_param.frequency / 1000 +
                                  self.g_ip.num_ca * self.g_ip.activity_ca * self.io_param.c_int *
                                  self.io_param.vdd_io * self.io_param.vdd_io * self.io_param.frequency / 1000)

            self.power_clk = (self.g_ip.num_clk *
                              (self.io_param.c_tx + self.io_param.num_mem_clk *
                               self.io_param.c_data + c_line) *
                              self.io_param.vdd_io * self.io_param.v_sw_clk * self.io_param.frequency / 1000 +
                              self.g_ip.num_clk * self.io_param.c_int * self.io_param.vdd_io *
                              self.io_param.vdd_io * self.io_param.frequency / 1000)

        if self.g_ip.iostate == 'READ':
            self.io_power_dynamic = self.g_ip.duty_cycle * (self.power_dq_read +
                                                       self.power_ca_read + self.power_dqs_read + self.power_clk)
        elif self.g_ip.iostate == 'WRITE':
            self.io_power_dynamic = self.g_ip.duty_cycle * (self.power_dq_write + self.power_ca_write + self.power_dqs_write + self.power_clk)
        elif self.g_ip.iostate == 'IDLE':
            self.io_power_dynamic = self.g_ip.duty_cycle * self.power_clk
        elif self.g_ip.iostate == 'SLEEP':
            self.io_power_dynamic = 0
        else:
            self.io_power_dynamic = 0

        # print("IO Dynamic Power (mW) =", self.io_power_dynamic)
        return self.io_power_dynamic

    def extio_eye(self):
        if self.io_param.io_type == 'Serial':
            self.io_vmargin = 0
        else:
            v_noise_write = (self.io_param.k_noise_write_sen * self.io_param.v_sw_data_write_line +
                             self.io_param.v_noise_independent_write)
            v_noise_read = (self.io_param.k_noise_read_sen * self.io_param.v_sw_data_read_line +
                            self.io_param.v_noise_independent_read)
            v_noise_addr = (self.io_param.k_noise_addr_sen * self.io_param.v_sw_addr +
                            self.io_param.v_noise_independent_addr)

            # CHANGE: Min
            if self.g_ip.iostate == 'READ':
                self.io_vmargin = self.io_param.v_sw_data_read_line / 2 - v_noise_read
                # self.io_vmargin = min(self.io_param.v_sw_data_read_line / 2 - v_noise_read,
                #                       self.io_param.v_sw_addr / 2 - v_noise_addr)
            elif self.g_ip.iostate == 'WRITE':
                self.io_vmargin = self.io_param.v_sw_data_write_line / 2 - v_noise_write
                # self.io_vmargin = min(self.io_param.v_sw_data_write_line / 2 - v_noise_write,
                #                       self.io_param.v_sw_addr / 2 - v_noise_addr)
            else:
                self.io_vmargin = 0

        if self.io_param.io_type == 'Serial':
            t_margin_write_setup = (1e6 / (4 * self.io_param.frequency)) - \
                self.io_param.t_ds - self.io_param.t_jitter_setup_sen

            t_margin_write_hold = (1e6 / (4 * self.io_param.frequency)) - \
                self.io_param.t_dh - self.io_param.t_dcd_soc - \
                self.io_param.t_jitter_hold_sen

            t_margin_read_setup = (1e6 / (4 * self.io_param.frequency)) - \
                self.io_param.t_soc_setup - self.io_param.t_jitter_setup_sen

            t_margin_read_hold = (1e6 / (4 * self.io_param.frequency)) - \
                self.io_param.t_soc_hold - self.io_param.t_dcd_dram - \
                self.io_param.t_dcd_soc - self.io_param.t_jitter_hold_sen

            t_margin_addr_setup = (1e6 * self.g_ip.addr_timing / (2 * self.io_param.frequency))
            t_margin_addr_hold = (1e6 * self.g_ip.addr_timing / (2 * self.io_param.frequency))
        else:
            t_margin_write_setup = (1e6 / (4 * self.io_param.frequency)) - \
                self.io_param.t_ds - self.io_param.t_error_soc - \
                self.io_param.t_jitter_setup_sen - \
                self.io_param.t_skew_setup + self.io_param.t_cor_margin

            t_margin_write_hold = (1e6 / (4 * self.io_param.frequency)) - \
                self.io_param.t_dh - self.io_param.t_dcd_soc - \
                self.io_param.t_error_soc - \
                self.io_param.t_jitter_hold_sen - \
                self.io_param.t_skew_hold + self.io_param.t_cor_margin

            t_margin_read_setup = (1e6 / (4 * self.io_param.frequency)) - \
                self.io_param.t_soc_setup - self.io_param.t_error_soc - \
                self.io_param.t_jitter_setup_sen - \
                self.io_param.t_skew_setup - \
                self.io_param.t_dqsq + self.io_param.t_cor_margin

            t_margin_read_hold = (1e6 / (4 * self.io_param.frequency)) - \
                self.io_param.t_soc_hold - self.io_param.t_dcd_dram - \
                self.io_param.t_dcd_soc - self.io_param.t_error_soc - \
                self.io_param.t_jitter_hold_sen - \
                self.io_param.t_skew_hold + self.io_param.t_cor_margin

            t_margin_addr_setup = (1e6 * self.g_ip.addr_timing / (2 * self.io_param.frequency)) - \
                self.io_param.t_is - self.io_param.t_error_soc - \
                self.io_param.t_jitter_addr_setup_sen - \
                self.io_param.t_skew_setup + self.io_param.t_cor_margin

            t_margin_addr_hold = (1e6 * self.g_ip.addr_timing / (2 * self.io_param.frequency)) - \
                self.io_param.t_ih - self.io_param.t_dcd_soc - \
                self.io_param.t_error_soc - \
                self.io_param.t_jitter_addr_hold_sen - \
                self.io_param.t_skew_hold + self.io_param.t_cor_margin

        # CHANGE: min
        if self.g_ip.iostate == 'READ':
            self.io_tmargin = t_margin_read_setup
            # self.io_tmargin = min(t_margin_read_setup, t_margin_read_hold, t_margin_addr_setup, t_margin_addr_hold)
        elif self.g_ip.iostate == 'WRITE':
            self.io_tmargin = t_margin_write_setup
            # self.io_tmargin = min(t_margin_write_setup, t_margin_write_hold, t_margin_addr_setup, t_margin_addr_hold)
        else:
            self.io_tmargin = 0

        # print("IO Timing Margin (ps) =", self.io_tmargin)
        # print("IO Voltage Margin (V) =", self.io_vmargin)
        return self.io_tmargin
