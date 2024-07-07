from .component import Component
import sympy as sp
from .const import *
from .parameter import g_tp

class NucaOrgT:
    def __init__(self):
        self.nuca_pda = Component()
        self.bank_pda = Component()
        self.wire_pda = Component()
        self.h_wire = None
        self.v_wire = None
        self.router = None
        self.contention = 0.0
        self.avg_hops = 0.0
        self.rows = 0
        self.columns = 0
        self.bank_count = 0

    def __del__(self):
        if self.h_wire:
            del self.h_wire
        if self.v_wire:
            del self.v_wire
        if self.router:
            del self.router

class Nuca(Component):
    def __init__(self, dt=None):
        if dt is None:
            dt = g_tp.peri_global
        self.deviceType = dt
        self.wt_min = 0
        self.wt_max = WIRE_TYPES - 1
        self.wire_vertical = [None] * WIRE_TYPES
        self.wire_horizontal = [None] * WIRE_TYPES
        self.init_cont()

    def init_cont(self):
        cont_stats = [[[[[0 for _ in range(8)] for _ in range(7)] for _ in range(ROUTER_TYPES)] for _ in range(5)] for _ in range(2)]
        try:
            print("HUH")
            with open("contention.dat", "r") as cont:
                print("BUH")
                for i in range(2):
                    for j in range(2, 5):
                        for k in range(ROUTER_TYPES):
                            for l in range(7):
                                line = cont.readline().strip()
                                parts = line.split(":")[1].strip().split()
                                for m in range(8):
                                    #TODO deleted int
                                    cont_stats[i][j][k][l][m] = parts[m]
        except FileNotFoundError:
            print("BRUH")
            print("contention.dat file is missing!")
            exit(0)
        self.cont_stats = cont_stats

    def print_cont_stats(self):
        for i in range(2):
            for j in range(2, 5):
                for k in range(ROUTER_TYPES):
                    for l in range(7):
                        for m in range(8):
                            print(self.cont_stats[i][j][k][l][m], end=" ")
                        print()
        print()

    def __del__(self):
        for i in range(self.wt_min, self.wt_max + 1):
            if self.wire_vertical[i]:
                del self.wire_vertical[i]
            if self.wire_horizontal[i]:
                del self.wire_horizontal[i]

    def calc_cycles(self, lat, oper_freq):
        cycle_time = 1.0 / (oper_freq * 1e9)
        cycle_time -= LATCH_DELAY
        cycle_time -= FIXED_OVERHEAD
        #TODO deleted int
        return sp.ceiling(lat / cycle_time)

# Constants and placeholder classes/functions for the sake of completeness
MIN_BANKSIZE = 65536
FIXED_OVERHEAD = 55e-12
LATCH_DELAY = 28e-12
CONTR_2_BANK_LAT = 0

