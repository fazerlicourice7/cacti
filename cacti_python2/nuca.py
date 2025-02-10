"""
nuca.py
Python version of nuca.h / nuca.cc snippet.

We separate out the NUCA code into:
  1) class nuca_org_t
  2) class Nuca

We also replicate constants, arrays (cont_stats), macros, etc. from the snippet.
We'll assume you import or define the following classes from your code:
  - Wire (from wire.py)
  - Router (from router.py or similar)
  - powerDef, powerComponents, etc.
  - min_values_t
  - mem_array, uca_org_t
  - solve(...) or update(...) that solves for bank org

We replicate logic so it is functionally the same as C++ version.
"""

import math
import sys

# Some constants from the snippet:
MIN_BANKSIZE = 65536
FIXED_OVERHEAD = 55e-12  # clock skew and jitter in s
LATCH_DELAY = 28e-12     # latch delay in s
CONTR_2_BANK_LAT = 0
BIGNUM = 1e99
INF = 1e99

# We see "cont_stats[2][5][ROUTER_TYPES][7][8]"
# We'll define an array or we can define it as a list of lists in Python:
ROUTER_TYPES = 3

# cont_stats is used in init_cont() and is a global array in the snippet.
cont_stats = [
    [ 
      [ 
        [ [0]*8 for _ in range(7) ] for _ in range(ROUTER_TYPES) 
      ] for _ in range(5)
    ] for _ in range(2)
]
# cont_stats[i][j][k][l][m] = integer

def logtwo(x: float) -> float:
    """Helper to replicate _log2 or logtwo from basic_circuit."""
    return math.log2(x)

class min_values_t:
    """
    Stub to replicate 'min_values_t' usage in nuca code. 
    Typically used to hold min_area, min_delay, etc. for feasibility checks.
    """
    def __init__(self):
        self.min_delay = 1e99
        self.min_dyn   = 1e99
        self.min_leakage = 0.0
        self.min_cyc   = 1e99
        self.min_area  = 1e99

    def update_min_values(self, nuca):
        """
        The snippet calls: minval.update_min_values(nuca_list.back()).
        We'll replicate. We glean that we want to keep track of the
        smallest area, delay, dynamic, leakage, cycle_time seen so far.
        """
        if nuca.nuca_pda.delay < self.min_delay:
            self.min_delay = nuca.nuca_pda.delay
        if nuca.nuca_pda.power.readOp.dynamic < self.min_dyn:
            self.min_dyn = nuca.nuca_pda.power.readOp.dynamic
        if nuca.nuca_pda.power.readOp.leakage < self.min_leakage or self.min_leakage == 0.0:
            self.min_leakage = nuca.nuca_pda.power.readOp.leakage
        if nuca.nuca_pda.cycle_time < self.min_cyc:
            self.min_cyc = nuca.nuca_pda.cycle_time
        current_area = nuca.nuca_pda.area.get_area() if hasattr(nuca.nuca_pda.area, "get_area") else 1e99
        if current_area < self.min_area:
            self.min_area = current_area

class Area:
    """
    Stub for 'Component::area'. We assume it has .h and .w for height and width,
    plus a get_area() method returning h*w.
    """
    def __init__(self):
        self.h = 0.0
        self.w = 0.0
    def get_area(self):
        return self.h * self.w

class powerComponents:
    """
    Minimal placeholder for power components. 
    """
    def __init__(self):
        self.dynamic = 0.0
        self.leakage = 0.0

class powerDef:
    """
    Minimal placeholder for readOp, writeOp, etc.
    """
    def __init__(self):
        self.readOp = powerComponents()
        self.writeOp = powerComponents()
        self.searchOp = powerComponents()

class Component:
    """
    C++ snippet has "class Component" with 
      - power (type powerDef),
      - area (with .h, .w),
      - delay, cycle_time, etc.
    We'll replicate.
    """
    def __init__(self):
        self.power = powerDef()
        self.area = Area()
        self.delay = 0.0
        self.cycle_time = 0.0

class mem_array:
    """
    Minimal placeholder for the snippet usage 'mem_array tag, data'.
    """
    def __init__(self):
        pass

class uca_org_t:
    """
    Minimal placeholder. snippet references:
      ures.tag_array2 = &tag;
      ures.data_array2 = &data;
      ures.cache_ht;
      ures.cache_len;
      ures.access_time;
      ures.power, ...
    We'll keep those fields in Python style.
    """
    def __init__(self):
        self.tag_array2 = None
        self.data_array2 = None
        self.cache_ht = 0.0
        self.cache_len = 0.0
        self.access_time = 0.0
        self.power = powerDef()
        self.cycle_time = 0.0
        self.valid = False


def solve(fin_res):
    """
    Stub for 'solve' or 'update' that the snippet references. 
    Should fill fin_res with solutions about bank org, etc.
    We'll just do a dummy placeholder or no-op here.
    """
    # In real code, you do the official solve, 
    # setting fin_res.cache_ht, fin_res.cache_len, fin_res.access_time, etc.
    fin_res.cache_ht = 0.01
    fin_res.cache_len = 0.02
    fin_res.access_time = 1e-9
    fin_res.power.readOp.dynamic = 0.05
    fin_res.power.readOp.leakage = 0.001
    fin_res.cycle_time = 1e-9
    fin_res.valid = True


class Router(Component):
    """
    Stub class for 'Router' references in the snippet. The snippet does:
      router_s[0] = new Router(64.0, 8, 4, &(g_tp.peri_global));
      ...
    We'll store those as fields:
       flit_size, etc.
    We'll have a print_router() method.
    """
    def __init__(self, flit_size, inputs, outputs, dt):
        super().__init__()
        self.flit_size = flit_size
        self.inputs = inputs
        self.outputs = outputs
        self.deviceType = dt

        # Some placeholders for cycle_time, power:
        self.cycle_time = 1e-9
        # let's say:
        self.power.readOp.dynamic = 0.01
        self.power.readOp.leakage = 0.0001
        self.delay = 1e-10  # used in snippet

    def print_router(self):
        print(f"Router: flit_size={self.flit_size}, cyc_time={self.cycle_time}, power_dyn={self.power.readOp.dynamic}, leak={self.power.readOp.leakage}")


class Wire(Component):
    """
    Stub for 'Wire' as used in snippet. We store wire_width, wire_spacing, delay, power.
    In the snippet:
      wire_vertical[wr] = new Wire((enum Wire_type) wr, vlength);
    We'll define a constructor that sets .delay, .wire_width, .wire_spacing, etc.
    """
    def __init__(self, wire_type=0, length=0.0):
        super().__init__()
        self.wt = wire_type
        self.length = length
        self.wire_width = 1e-6
        self.wire_spacing = 1e-6
        # Some default values for demonstration:
        self.delay = 5e-10
        self.power.readOp.dynamic = 0.001
        self.power.readOp.leakage = 0.00001

    def print_wire(self):
        print(f"Wire: type={self.wt}, length={self.length}, delay={self.delay}, p_dyn={self.power.readOp.dynamic}, p_leak={self.power.readOp.leakage}")


class nuca_org_t:
    """
    Equivalent to c++ struct/class nuca_org_t:
      - nuca_pda, bank_pda, wire_pda => Components
      - h_wire, v_wire => Wire
      - router => Router
      - contention => double
      - avg_hops => double
      - rows, columns, bank_count => int
    """
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
        """
        In C++: 
          nuca_org_t::~nuca_org_t() { ... }
        We'll rely on normal Python GC. If we want to replicate the snippet's
        comment about h_wire, v_wire, router, we can do so but it's not typical
        in Python to do explicit in a destructor.
        """
        pass


class Nuca(Component):
    """
    Python class for 'Nuca : public Component' from the snippet.
    We replicate the constructor logic, methods like sim_nuca(), etc.
    """
    def __init__(self, deviceType):
        super().__init__()
        self.deviceType = deviceType
        self.wt_min = 0
        self.wt_max = 0
        # We'll keep arrays wire_vertical, wire_horizontal:
        self.wire_vertical = [None]*100  # big enough for WIRE_TYPES
        self.wire_horizontal = [None]*100
        self.init_cont()

    def init_cont(self):
        """
        Python version of Nuca::init_cont().
        snippet:
          cont = fopen("contention.dat", "r");
          ...
        We'll replicate reading the file "contention.dat" and filling cont_stats.
        We'll do a direct translation, or provide a placeholder if "contention.dat" doesn't exist.
        """
        try:
            contfile = open("contention.dat","r")
        except FileNotFoundError:
            print("contention.dat file is missing!")
            sys.exit(1)

        lines = contfile.read().splitlines()
        contfile.close()

        idx = 0
        # The snippet does nested loops: i in [0..1], j in [2..4], k in [0..ROUTER_TYPES-1], l in [0..6]
        for i in range(2):
            for j in range(2,5):
                for k in range(ROUTER_TYPES):
                    for l in range(7):
                        line = lines[idx].strip()
                        idx += 1
                        # e.g. "someLabel: 1 2 3 4 5 6 7 8"
                        # parse with "jk, &temp[0]..[7]"
                        parts = line.split(":")
                        # left side = label, right side = " 1 2 3 4 5 6 7 8"
                        rightside = parts[1].split()
                        for m in range(8):
                            cont_stats[i][j][k][l][m] = int(rightside[m])

    def print_cont_stats(self):
        """
        Python version of Nuca::print_cont_stats().
        The snippet does:
          for i in [0..1], j in [2..4], k in [0..ROUTER_TYPES-1], ...
          print cont_stats[i][j][k][l][m].
        We'll replicate carefully.
        """
        for i in range(2):
            for j in range(2,5):
                for k in range(ROUTER_TYPES):
                    for l in range(7):
                        for m in range(7):
                            # The snippet is a bug: "for(int m=0;l<7; l++)"? We'll assume
                            # they meant m in range(8)? The snippet is a mismatch but let's do a safe approach:
                            print(cont_stats[i][j][k][l][m], end=" ")
                        print()
                print()
            print()

    def __del__(self):
        """
        Nuca::~Nuca() in snippet. 
        deletes wire_vertical[i], wire_horizontal[i].
        In Python, rely on GC. If we want to replicate, we can do:
        """
        for i in range(self.wt_min, self.wt_max+1):
            if self.wire_vertical[i]:
                del self.wire_vertical[i]
            if self.wire_horizontal[i]:
                del self.wire_horizontal[i]

    def calc_cycles(self, lat, oper_freq):
        """
        Python version of int Nuca::calc_cycles(double lat, double oper_freq)
        'lat' is latency in seconds, 'oper_freq' is in GHz in snippet, so
        1/(oper_freq*1e9) is cycle time in s. Then subtract LATCH_DELAY, FIXED_OVERHEAD, etc.
        Then see how many cycles for 'lat'.

        Return int(ceil( lat / cycle_time ))
        """
        cycle_time = 1.0 / (oper_freq*1e9)  # s
        cycle_time -= LATCH_DELAY
        cycle_time -= FIXED_OVERHEAD
        return int(math.ceil(lat / cycle_time))

    def sim_nuca(self, g_ip=None):
        """
        Python version of Nuca::sim_nuca().

        The snippet references g_ip->..., a global. 
        We can accept g_ip as a parameter or store it as self.g_ip.
        We'll do it as a function argument. 
        If you prefer it as a class field, define self.g_ip in constructor.
        """

        # local references
        if g_ip is None:
            print("Error: sim_nuca() requires g_ip as argument.")
            return

        # local constants
        # the snippet references local variables
        global MIN_BANKSIZE

        bank_count = 0
        ures = uca_org_t()
        opt_n = None
        tag = mem_array()
        data = mem_array()
        nuca_list = []
        router_s = []

        # Create 3 routers (for ro in [0..2])
        router_s.append(Router(64.0, 8, 4, self.deviceType))
        router_s[0].print_router()
        router_s.append(Router(128.0, 8, 4, self.deviceType))
        router_s[1].print_router()
        router_s.append(Router(256.0, 8, 4, self.deviceType))
        router_s[2].print_router()

        # The snippet does some logic about "core_in"
        if g_ip.cores <= 4:
            core_in = 2
        elif g_ip.cores <= 8:
            core_in = 3
        elif g_ip.cores <= 16:
            core_in = 4
        else:
            print("Number of cores should be <= 16!")
            sys.exit(0)

        # i = 2 => while i != g_ip.assoc => MIN_BANKSIZE *=2 ...
        # We'll skip some details for brevity, or replicate exactly:
        local_min_banksize = MIN_BANKSIZE
        if g_ip.assoc > 2:
            i = 2
            while i != g_ip.assoc:
                local_min_banksize *= 2
                i *= 2

        # iterations = log2( cache_sz / local_min_banksize )
        # e.g. (int)logtwo( g_ip.cache_sz / MIN_BANKSIZE )
        # We'll do a floor or an int-cast:
        if g_ip.cache_sz < local_min_banksize:
            iterations = 0
        else:
            iterations = int(logtwo(g_ip.cache_sz / local_min_banksize))

        # force_wiretype logic
        if g_ip.force_wiretype:
            if g_ip.wt == 5:  # Low_swing
                self.wt_min = 5
                self.wt_max = 5
            else:
                self.wt_min = 0  # Global
                self.wt_max = 4  # Low_swing - 1
        else:
            self.wt_min = 0  # Global
            self.wt_max = 5  # Low_swing

        bank_start = 0
        if g_ip.nuca_bank_count != 0:
            # log2 g_ip.nuca_bank_count => bank_start
            # Then set iterations = bank_start+1
            # reduce g_ip.cache_sz
            if g_ip.nuca_bank_count not in [2,4,8,16,32,64]:
                sys.stderr.write("Incorrect bank count value! Fix value in cache.cfg.\n")

            bank_start = int(logtwo(float(g_ip.nuca_bank_count)))
            iterations = bank_start + 1
            g_ip.cache_sz = g_ip.cache_sz / g_ip.nuca_bank_count

        print("Simulating various NUCA configurations")
        # Create a first nuca_org_t and push into nuca_list:
        nuca_list.append(nuca_org_t())

        for it in range(bank_start, iterations):
            # fill in ures
            ures.tag_array2 = tag
            ures.data_array2 = data
            solve(ures)  # sets bank org

            bank_count = int(g_ip.nuca_cache_sz / g_ip.cache_sz)
            print(f"===={g_ip.cache_sz}\n")

            # We'll keep track of best cost among wire types, router config, etc.
            for wr in range(self.wt_min, self.wt_max+1):
                for ro in range(ROUTER_TYPES):
                    flit_width = int(router_s[ro].flit_size)
                    nuca_list[-1].nuca_pda.cycle_time = router_s[ro].cycle_time

                    # length from ures
                    vlength = ures.cache_ht
                    hlength = ures.cache_len

                    # create wire objects
                    self.wire_vertical[wr] = Wire(wr, vlength)
                    self.wire_horizontal[wr] = Wire(wr, hlength)

                    hor_hop_lat = self.calc_cycles(self.wire_horizontal[wr].delay,
                                                   1.0/(nuca_list[-1].nuca_pda.cycle_time*0.001))
                    ver_hop_lat = self.calc_cycles(self.wire_vertical[wr].delay,
                                                   1.0/(nuca_list[-1].nuca_pda.cycle_time*0.001))

                    # Try grid org of banks: for c in [1..bank_count], while bank_count%c!=0 => c++
                    # snippet merges i and j. We'll replicate carefully:
                    opt_acclat = BIGNUM
                    opt_dyn_power = 0.0
                    opt_leakage_power = 0.0
                    opt_rows = 0
                    opt_columns = 0
                    opt_avg_hop = 0.0

                    c = 1
                    while c <= bank_count:
                        if bank_count % c != 0:
                            c += 1
                            continue
                        r = bank_count // c

                        totno_hops = 0.0
                        tot_lat = 0.0
                        totno_hhops = 0.0
                        totno_vhops = 0.0

                        # double loop i=0..r-1, j=0..c-1
                        for i in range(r):
                            for j in range(c):
                                # curr_hop = i+1 + j
                                # ...
                                curr_hop = (i+1) + j
                                totno_hhops += j
                                totno_vhops += (i+1)
                                curr_acclat = i*ver_hop_lat + CONTR_2_BANK_LAT + j*hor_hop_lat
                                tot_lat += curr_acclat
                                totno_hops += curr_hop
                        bankCount_f = float(bank_count)
                        avg_lat = tot_lat/bankCount_f
                        avg_hop = totno_hops/bankCount_f
                        avg_hhop = totno_hhops/bankCount_f
                        avg_vhop = totno_vhops/bankCount_f

                        curr_acclat = 2*avg_lat + 2*(router_s[ro].delay*avg_hop) + \
                            self.calc_cycles(ures.access_time,
                                             1.0/(nuca_list[-1].nuca_pda.cycle_time*0.001))

                        avg_dyn_power = avg_hop*(router_s[ro].power.readOp.dynamic) + \
                                        avg_hhop*(self.wire_horizontal[wr].power.readOp.dynamic)*(g_ip.block_sz*8+64) + \
                                        avg_vhop*(self.wire_vertical[wr].power.readOp.dynamic)*(g_ip.block_sz*8+64) + \
                                        ures.power.readOp.dynamic

                        avg_leakage_power = bank_count*(router_s[ro].power.readOp.leakage) + \
                            avg_hhop*(self.wire_horizontal[wr].power.readOp.leakage * self.wire_horizontal[wr].delay)*flit_width + \
                            avg_vhop*(self.wire_vertical[wr].power.readOp.leakage * self.wire_horizontal[wr].delay)

                        if curr_acclat < opt_acclat:
                            opt_acclat = curr_acclat
                            opt_avg_hop = avg_hop
                            opt_rows = r
                            opt_columns = c
                            opt_dyn_power = avg_dyn_power
                            opt_leakage_power = avg_leakage_power

                        c += 1

                    # now fill the nuca_list entry
                    nuca_list[-1].wire_pda.power.readOp.dynamic = opt_avg_hop*flit_width*(
                        self.wire_horizontal[wr].power.readOp.dynamic + self.wire_vertical[wr].power.readOp.dynamic)
                    nuca_list[-1].avg_hops = opt_avg_hop
                    nuca_list[-1].h_wire = self.wire_horizontal[wr]
                    nuca_list[-1].v_wire = self.wire_vertical[wr]
                    nuca_list[-1].router = router_s[ro]
                    nuca_list[-1].bank_pda.delay = ures.access_time
                    nuca_list[-1].bank_pda.power = ures.power
                    nuca_list[-1].bank_pda.area.h = ures.cache_ht
                    nuca_list[-1].bank_pda.area.w = ures.cache_len
                    nuca_list[-1].bank_pda.cycle_time = ures.cycle_time

                    num_cyc = self.calc_cycles(nuca_list[-1].bank_pda.delay,
                                               1.0/(nuca_list[-1].nuca_pda.cycle_time*0.001))
                    if num_cyc%2 != 0:
                        num_cyc+=1
                    if num_cyc>16:
                        num_cyc=16
                    l2_c = 1 if g_ip.cache_level==0 else 0

                    # We pick "it < 7 => cont_stats[l2_c][core_in][ro][it][num_cyc/2-1]" else index = 7
                    use_index = it
                    if it>=7: 
                        use_index=7
                    half_cyc = int(num_cyc/2 -1)
                    if half_cyc<0:
                        half_cyc=0
                    # add contention
                    contn = cont_stats[l2_c][core_in][ro][use_index][half_cyc]
                    nuca_list[-1].nuca_pda.delay = opt_acclat + contn
                    nuca_list[-1].contention = contn
                    nuca_list[-1].nuca_pda.power.readOp.dynamic = opt_dyn_power
                    nuca_list[-1].nuca_pda.power.readOp.leakage = opt_leakage_power
                    nuca_list[-1].bank_count = bank_count
                    nuca_list[-1].rows = opt_rows
                    nuca_list[-1].columns = opt_columns
                    self.calculate_nuca_area(nuca_list[-1])
                    # update min
                    # we want a minval global or local:
                    # We'll create a local minval, but snippet has it outside. We'll do:
                    if not hasattr(self, 'minval'):
                        self.minval = min_values_t()
                    self.minval.update_min_values(nuca_list[-1])
                    # push new
                    nuca_list.append(nuca_org_t())

            g_ip.cache_sz = g_ip.cache_sz/2.0

        # remove the last empty
        del nuca_list[-1]

        opt_n = self.find_optimal_nuca(nuca_list, self.minval, g_ip)
        self.print_nuca(opt_n)

        g_ip.cache_sz = g_ip.nuca_cache_sz / opt_n.bank_count
        # cleanup
        for niter in nuca_list:
            del niter
        nuca_list.clear()

        for r in router_s:
            del r


    def check_nuca_org(self, n, minval, g_ip):
        """
        Python version of Nuca::check_nuca_org (nuca_org_t *n, min_values_t *minval).
        We also pass g_ip to read the dev constraints: delay_dev_nuca, etc.
        """
        pd = (n.nuca_pda.delay - minval.min_delay)*100/minval.min_delay
        if pd > g_ip.delay_dev_nuca:
            return 0
        dyp = ((n.nuca_pda.power.readOp.dynamic - minval.min_dyn)/minval.min_dyn)*100
        if dyp > g_ip.dynamic_power_dev_nuca:
            return 0
        # for leakage
        if minval.min_leakage == 0:
            minval.min_leakage = 0.1
        lkp = ((n.nuca_pda.power.readOp.leakage - minval.min_leakage)/minval.min_leakage)*100
        if lkp > g_ip.leakage_power_dev_nuca:
            return 0
        cyc_dev = ((n.nuca_pda.cycle_time - minval.min_cyc)/minval.min_cyc)*100
        if cyc_dev > g_ip.cycle_time_dev_nuca:
            return 0
        area_ = n.nuca_pda.area.get_area()
        areadev = ((area_ - minval.min_area)/minval.min_area)*100
        if areadev > g_ip.area_dev_nuca:
            return 0
        return 1

    def find_optimal_nuca(self, n_list, minval, g_ip):
        """
        Python version of Nuca::find_optimal_nuca (list<nuca_org_t *> *n, min_values_t *minval).
        We pass g_ip as well for weighting.
        """
        dp = g_ip.dynamic_power_wt_nuca
        lp = g_ip.leakage_power_wt_nuca
        a  = g_ip.area_wt_nuca
        d  = g_ip.delay_wt_nuca
        c  = g_ip.cycle_time_wt_nuca

        min_cost = BIGNUM
        res = None

        for nn in n_list:
            print(f"\n--------------------------------------\n")
            print(f"NUCA___stats {nn.bank_count}\tbankcount: lat = {nn.nuca_pda.delay}\t"
                  f"dynP = {nn.nuca_pda.power.readOp.dynamic}\twt = {nn.h_wire.wt}\t"
                  f"bank_dpower = {nn.bank_pda.power.readOp.dynamic}\t"
                  f"leak = {nn.nuca_pda.power.readOp.leakage}\t"
                  f"cycle = {nn.nuca_pda.cycle_time}")

            if g_ip.ed==1:
                # ED
                cost = (nn.nuca_pda.delay/minval.min_delay)* \
                       (nn.nuca_pda.power.readOp.dynamic/minval.min_dyn)
                if cost < min_cost:
                    min_cost = cost
                    res = nn
            elif g_ip.ed==2:
                # ED^2
                cost = ((nn.nuca_pda.delay/minval.min_delay)**2)* \
                       (nn.nuca_pda.power.readOp.dynamic/minval.min_dyn)
                if cost < min_cost:
                    min_cost = cost
                    res = nn
            else:
                # Weighted cost
                v = self.check_nuca_org(nn, minval, g_ip)
                if v:
                    area_ = nn.nuca_pda.area.get_area()
                    cost = d*(nn.nuca_pda.delay/minval.min_delay) + \
                           c*(nn.nuca_pda.cycle_time/minval.min_cyc) + \
                           dp*(nn.nuca_pda.power.readOp.dynamic/minval.min_dyn) + \
                           lp*(nn.nuca_pda.power.readOp.leakage/minval.min_leakage) + \
                           a*(area_/minval.min_area)
                    print(f"cost = {cost}")
                    if cost< min_cost:
                        min_cost = cost
                        res = nn
                else:
                    # remove nn from n_list in c++. In python, we can skip it.
                    pass

        return res

    def calculate_nuca_area(self, nuca):
        """
        Python version of Nuca::calculate_nuca_area (nuca_org_t *nuca).
        snippet:
          nuca->nuca_pda.area.h = nuca->rows * ((nuca->h_wire->wire_width + nuca->h_wire->wire_spacing)*nuca->router->flit_size + nuca->bank_pda.area.h)
        etc.
        """
        nuca.nuca_pda.area.h = nuca.rows * (
            (nuca.h_wire.wire_width + nuca.h_wire.wire_spacing)*nuca.router.flit_size +
            nuca.bank_pda.area.h
        )
        nuca.nuca_pda.area.w = nuca.columns * (
            (nuca.v_wire.wire_width + nuca.v_wire.wire_spacing)*nuca.router.flit_size +
            nuca.bank_pda.area.w
        )


    def print_router(self):
        """Matches snippet but in python we do not need to do anything special here."""
        pass

    def print_nuca(self, fr):
        """
        Python version of Nuca::print_nuca(nuca_org_t *fr).
        Just prints out data. 
        """
        print("\n---------- CACTI version 6.5, Non-uniform Cache Access ----------\n")
        print(f"Optimal number of banks - {fr.bank_count}")
        print(f"Grid organization rows x columns - {fr.rows} x {fr.columns}")
        print(f"Network frequency - {1/fr.nuca_pda.cycle_time*1e3} GHz")
        print(f"Cache dimension (mm x mm) - {fr.nuca_pda.area.h*1e-3} x {fr.nuca_pda.area.w*1e-3}")

        fr.router.print_router()

        print("\n\nWire stats:")
        if fr.h_wire.wt == 0:  # Global
            print("\tWire type - Full swing global wires with least possible delay")
        elif fr.h_wire.wt == 1:  # Global_5
            print("\tWire type - Full swing global wires with 5% delay penalty")
        elif fr.h_wire.wt == 2:  # Global_10
            print("\tWire type - Full swing global wires with 10% delay penalty")
        elif fr.h_wire.wt == 3:  # Global_20
            print("\tWire type - Full swing global wires with 20% delay penalty")
        elif fr.h_wire.wt == 4:  # Global_30
            print("\tWire type - Full swing global wires with 30% delay penalty")
        elif fr.h_wire.wt == 5:  # Low_swing
            print("\tWire type - Low swing wires")

        print(f"\tHorizontal link delay - {fr.h_wire.delay*1e9} (ns)")
        print(f"\tVertical link delay - {fr.v_wire.delay*1e9} (ns)")
        if fr.bank_pda.area.w == 0:
            print("\tDelay/length = ??? (division by zero?)")
        else:
            print(f"\tDelay/length - {fr.h_wire.delay*1e9/fr.bank_pda.area.w} (ns/mm)")

        print(f"\tHorizontal link energy -dynamic/access {fr.h_wire.power.readOp.dynamic*1e9} (nJ)")
        print(f"\t                       -leakage {fr.h_wire.power.readOp.leakage*1e9} (nW)\n")
        print(f"\tVertical link energy -dynamic/access {fr.v_wire.power.readOp.dynamic*1e9} (nJ)")
        print(f"\t                     -leakage {fr.v_wire.power.readOp.leakage*1e9} (nW)\n")
        fr.v_wire.print_wire()
        print("\n\nBank stats:\n")
