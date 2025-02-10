# memcad_parameters.py

import math
from typing import List

# We'll assume these enumerations or constants are defined somewhere:
#   - Mem_IO_type: an enum { DDR3, DDR4, LPDDR2, WideIO, Low_Swing_Diff, Serial }, or at least the first two
#   - Mem_DIMM: { UDIMM, RDIMM, LRDIMM }
#   - MemCad_metrics: { Bandwidth=0, Energy=1, Cost=2 } or similar
#   - DIMM_Model: { JUST_UDIMM=0, JUST_RDIMM=1, JUST_LRDIMM=2, ALL=3 }
#   - InputParameter: the Python version of CACTI's input parameter class

# For the sake of completeness, let's define minimal placeholders:
from enum import IntEnum
from .cacti_interface import Mem_IO_type, Mem_DIMM, MemCad_metrics, DIMM_Model, InputParameter

# class Mem_IO_type(IntEnum):
#     DDR3 = 0
#     DDR4 = 1
#     LPDDR2 = 2
#     WideIO = 3
#     Low_Swing_Diff = 4
#     Serial = 5

# class Mem_DIMM(IntEnum):
#     UDIMM = 0
#     RDIMM = 1
#     LRDIMM= 2

# class MemCad_metrics(IntEnum):
#     Bandwidth=0
#     Energy=1
#     Cost=2

# class DIMM_Model(IntEnum):
#     JUST_UDIMM=0
#     JUST_RDIMM=1
#     JUST_LRDIMM=2
#     ALL=3

# If you have a standard CACTI "InputParameter" class:
# class InputParameter:
#     def __init__(self):
#         self.io_type = Mem_IO_type.DDR4
#         self.capacity=400
#         self.num_bobs=4
#         self.num_channels_per_bob=2
#         self.first_metric=MemCad_metrics.Cost
#         self.second_metric=MemCad_metrics.Bandwidth
#         self.third_metric=MemCad_metrics.Energy
#         self.dimm_model=DIMM_Model.ALL
#         self.mirror_in_bob=True
#         self.verbose=False
#         # etc.

# --------------- MemCadParameters class ---------------

class MemCadParameters:
    """
    Python translation of the C++ MemCadParameters class.
    """
    def __init__(self, g_ip):
        """
        Constructor that reads defaults, then overrides them with g_ip fields.
        """
        # default values (as in the C++ constructor)
        self.io_type = Mem_IO_type.DDR4
        self.capacity = 400   # in GB
        self.num_bobs = 4
        self.num_channels_per_bob = 2
        self.capacity_wise = True
        self.first_metric = MemCad_metrics.Cost
        self.second_metric= MemCad_metrics.Bandwidth
        self.third_metric = MemCad_metrics.Energy
        self.dimm_model   = DIMM_Model.ALL
        self.low_power_permitted = False
        self.load = 0.9
        self.row_buffer_hit_rate = 1.0
        self.rd_2_wr_ratio = 2.0
        self.same_bw_in_bob = True
        self.mirror_in_bob  = True
        self.total_power = False
        self.verbose = False

        # Now override with g_ip values if present:
        self.io_type         = g_ip.io_type
        self.capacity        = g_ip.capacity
        self.num_bobs        = g_ip.num_bobs
        self.num_channels_per_bob = g_ip.num_channels_per_bob
        self.first_metric    = g_ip.first_metric
        self.second_metric   = g_ip.second_metric
        self.third_metric    = g_ip.third_metric
        self.dimm_model      = g_ip.dimm_model
        # optional fields if present:
        # e.g. self.mirror_in_bob = g_ip.mirror_in_bob
        # e.g. self.verbose       = g_ip.verbose
        # etc.

    def print_inputs(self):
        """
        Placeholder. The C++ version is empty. You can fill in as needed.
        """
        print("MemCadParameters:")
        print(f"  io_type={self.io_type}, capacity={self.capacity}GB, "
              f"num_bobs={self.num_bobs}, channels_per_bob={self.num_channels_per_bob}")
        # etc.

    def sanity_check(self) -> bool:
        """
        Return True if consistent, else False. 
        Currently the C++ version is a placeholder returning true.
        """
        # do your checks
        return True


# --------------- MemoryParameters: static arrays ---------------

class MemoryParameters:
    """
    Python translation of the C++ MemoryParameters static arrays, etc.
    We'll store them here as class variables.
    """

    # VDD => [lp:hp][ddr3:ddr4][frequency index 0..3]
    VDD = [
        [ [1.5, 1.5, 1.5, 1.5], [1.2, 1.2, 1.2, 1.2] ],
        [ [1.35,1.35,1.35,1.35],[1.0,1.0,1.0,1.0]   ]
    ]

    IDD0 = [
        [55,60,65,75],
        [58,58,60,64]
    ]
    # IDD1 not in your posted code? Possibly missing or replaced by IDD2... 
    # If you need IDD1 define it similarly

    IDD2P0 = [
        [20,20,20,20],
        [20,20,20,20]
    ]
    IDD2P1 = [
        [30,30,32,37],
        [30,30,30,32]
    ]
    IDD2N = [
        [40,42,45,50],
        [44,44,46,50]
    ]
    IDD3P = [
        [45,50,55,60],
        [44,44,44,44]
    ]
    IDD3N = [
        [42,47,52,57],
        [44,44,44,44]
    ]
    IDD4R = [
        [120,135,155,175],
        [140,140,150,160]
    ]
    IDD4W = [
        [100,125,145,165],
        [156,156,176,196]
    ]
    IDD5 = [
        [150,205,210,220],
        [190,190,190,192]
    ]

    # io_energy_read => [ddr3:0, ddr4:1][udimm:0,rdimm:1,lrdimm:2][load=1..3][freq=0..3]
    io_energy_read = [
        [ # ddr3
          [ [2592.33,2593.33,3288.784,4348.612],
            [2638.23,2640.23,3941.584,5415.492],
            [2978.659,2981.659,4816.644,6964.162] ],
          [ [2592.33,3087.071,3865.044,4844.982],
            [2932.759,3733.318,4237.634,5415.492],
            [3572.509,4603.109,5300.004,6964.162] ],
          [ [4628.966,6357.625,7079.348,9680.454],
            [5368.26,6418.788,7428.058,10057.164],
            [5708.689,7065.038,7808.678,10627.674] ]
        ],
        [ # ddr4
          [ [2135.906,2633.317,2750.919,2869.406],
            [2458.714,2695.791,2822.298,3211.111],
            [2622.85, 3030.048,3160.265,3534.448] ],
          [ [2135.906,2633.317,2750.919,2869.406],
            [2458.714,2695.791,3088.886,3211.111],
            [2622.85, 3030.048,3312.468,3758.445] ],
          [ [4226.903,5015.342,5490.61,5979.864],
            [4280.471,5319.132,5668.945,6060.216],
            [4603.279,5381.605,5740.325,6401.926] ]
        ]
    ]

    io_energy_write = [
        [ # ddr3
          [ [2758.951,2984.854,3571.804,4838.902],
            [2804.851,3768.524,4352.214,5580.362],
            [3213.897,3829.684,5425.854,6933.512] ],
          [ [2758.951,3346.104,3931.154,4838.902],
            [3167.997,4114.754,4696.724,5580.362],
            [3561.831,3829.684,6039.994,8075.542] ],
          [ [4872.238,5374.314,7013.868,9267.574],
            [5701.502,6214.348,7449.758,10045.004],
            [5747.402,6998.018,8230.168,10786.464] ]
        ],
        [ # ddr4
          [ [2525.129,2840.853,2979.037,3293.608],
            [2933.756,3080.126,3226.497,3979.698],
            [3293.964,3753.37,3906.137,4312.448] ],
          [ [2525.129,2840.853,3155.117,3293.608],
            [2933.756,3080.126,3834.757,3979.698],
            [3293.964,3753.37,4413.037,5358.078] ],
          [ [4816.453,5692.314,5996.134,6652.936],
            [4870.021,5754.788,6067.514,6908.636],
            [5298.373,5994.07,6491.054,7594.726] ]
        ]
    ]

    T_RAS= [35,35]
    T_RC = [47.5,47.5]
    T_RP = [13,13]
    T_RFC= [340,260]
    T_REFI=[7800,7800]

    bandwidth_load = [
        [400,533,667,800],
        [800,933,1066,1200]
    ]

    cost = [
        [ # ddr3
          [40.38, 76.13, math.inf, math.inf, math.inf],
          [42.24, 64.17, 122.6, 304.3, math.inf],
          [math.inf, math.inf, 211.3, 287.5, 1079.5]
        ],
        [ # ddr4
          [25.99,45.99, math.inf, math.inf, math.inf],
          [32.99,60.45,126,296.3, math.inf],
          [math.inf, math.inf,278.99,333,1474]
        ]
    ]

    def __init__(self):
        """
        In the C++ code, the constructor is empty. 
        We do nothing or set up if needed.
        """
        pass

    def bw_index(self, type_: Mem_IO_type, bandwidth: int) -> int:
        """
        from memcad_parameters.cc => int bw_index(Mem_IO_type type, int bandwidth)
        """
        if type_ == Mem_IO_type.DDR3:
            if bandwidth <= 400:
                return 0
            elif bandwidth <= 533:
                return 1
            elif bandwidth <= 667:
                return 2
            else:
                return 3
        else: # DDR4
            if bandwidth <= 800:
                return 0
            elif bandwidth <= 933:
                return 1
            elif bandwidth <= 1066:
                return 2
            else:
                return 3


# A free function matching the C++ signature (but we typically do it as a method).
def bw_index(type_: Mem_IO_type, bandwidth: int) -> int:
    """
    Matches the global function int bw_index(Mem_IO_type type, int bandwidth)
    from the c++ code.
    """
    if type_ == Mem_IO_type.DDR3:
        if bandwidth <= 400:
            return 0
        elif bandwidth <= 533:
            return 1
        elif bandwidth <= 667:
            return 2
        else:
            return 3
    else: # DDR4
        if bandwidth <= 800:
            return 0
        elif bandwidth <= 933:
            return 1
        elif bandwidth <= 1066:
            return 2
        else:
            return 3


# --------------- channel_conf ---------------

class channel_conf:
    """
    Python version of C++ channel_conf. 
    - memcad_params: MemCadParameters
    - type: Mem_DIMM
    - low_power: bool
    - capacity, bandwidth, cost, etc.
    """
    def __init__(
        self,
        memcad_params: MemCadParameters,
        dimm_cap: List[int],
        bandwidth: int,
        dimm_type: Mem_DIMM,
        low_power: bool
    ):
        self.memcad_params = memcad_params
        self.type = dimm_type
        self.low_power = low_power
        self.bandwidth = bandwidth
        self.latency = 0.0
        self.valid = True

        # init histogram
        self.histogram_capacity = [0]*5
        self.num_dimm_per_channel = 0
        self.capacity = 0

        # fill histogram
        #  dimm_cap is e.g. a vector of size <= DIMM_PER_CHANNEL
        # we check capacity
        for i in range(len(dimm_cap)):
            val = dimm_cap[i]
            if val==0:
                continue
            index = int(math.log2(val+0.1)) -2
            if index<0:
                index=0
            if index>4:
                index=4
            self.histogram_capacity[index]+=1
            self.num_dimm_per_channel+=1
            self.capacity += val

        # the c++ code: if capacity>0 => bandwidth=0 ??? The code says:
        #   if(capacity>0) bandwidth=0
        if self.capacity>0:
            self.bandwidth=0

        # cost
        from .memcad_parameters import MemoryParameters
        self.cost = 0.0
        for i in range(5):
            self.cost += self.histogram_capacity[i]*MemoryParameters.cost[self.memcad_params.io_type][self.type][i]

        # compute energy
        self.energy_per_read  =0.0
        self.energy_per_write =0.0
        self.energy_per_access=0.0
        self.calc_power()

    def calc_power(self):
        """
        from c++ channel_conf::calc_power()
        """
        read_ratio = self.memcad_params.rd_2_wr_ratio / (1.0 + self.memcad_params.rd_2_wr_ratio)
        write_ratio= 1.0 / (1.0 + self.memcad_params.rd_2_wr_ratio)

        current_io_type = self.memcad_params.io_type
        capacity_ratio  = (self.capacity/(self.memcad_params.capacity*1.0)) if self.memcad_params.capacity>0 else 0.0

        T_BURST = 4.0  # memory cycles

        # from MemoryParameters
        from .memcad_parameters import MemoryParameters, bw_index
        freqIndex = bw_index(current_io_type, self.bandwidth)

        # read
        self.energy_per_read = MemoryParameters.io_energy_read[current_io_type][self.type][self.num_dimm_per_channel-1][freqIndex]
        self.energy_per_read /= ( (self.bandwidth or 1) / T_BURST )

        # write
        self.energy_per_write = MemoryParameters.io_energy_write[current_io_type][self.type][self.num_dimm_per_channel-1][freqIndex]
        self.energy_per_write/= ( (self.bandwidth or 1) / T_BURST )

        if self.memcad_params.capacity_wise:
            self.energy_per_read  *= capacity_ratio
            self.energy_per_write *= capacity_ratio

        self.energy_per_access = read_ratio*self.energy_per_read + write_ratio*self.energy_per_write

    def __str__(self):
        s= (f"cap: {self.capacity} GB "
            f"bw: {self.bandwidth} (MHz) "
            f"cost: ${self.cost} "
            f"dpc: {self.num_dimm_per_channel} "
            f"energy: {self.energy_per_access} (nJ) "
            f"DIMM: {('UDIMM' if self.type==Mem_DIMM.UDIMM else ('RDIMM' if self.type==Mem_DIMM.RDIMM else 'LRDIMM'))} "
            f"low_power: {('T' if self.low_power else 'F')} "
            f"[ ")
        for i in range(5):
            if self.histogram_capacity[i]>0:
                s += f"{self.histogram_capacity[i]}({1<<(i+2)}GB) "
        s+="]"
        return s

def clone_channel_conf(origin: channel_conf) -> channel_conf:
    """
    Python version of friend channel_conf* clone(channel_conf*)
    Rebuild the dimm_cap array from histogram
    """
    # The c++ code re-constructs the dimms from histogram (?), 
    # it sets size=4 => then for i in 0..4, for j in 0..histogram => pushback size => size<<=1
    dimms = []
    sizeVal=4
    for i in range(5):
        for j in range(origin.histogram_capacity[i]):
            dimms.append(sizeVal)
        sizeVal <<=1

    newcc = channel_conf(
        origin.memcad_params,
        dimm_cap=dimms,
        bandwidth=origin.bandwidth,
        dimm_type=origin.type,
        low_power=origin.low_power
    )
    return newcc


# --------------- bob_conf ---------------

class bob_conf:
    """
    Python translation of C++ bob_conf
    Has an array of up to MAX_NUM_CHANNELS_PER_BOB channel_conf.
    """
    def __init__(
        self,
        memcad_params: MemCadParameters,
        in_channels: List[channel_conf]
    ):
        self.memcad_params= memcad_params
        self.num_channels = 0
        self.channels     = [None]*2  # up to MAX_NUM_CHANNELS_PER_BOB=2 by default?

        self.capacity=0
        self.bandwidth=0
        self.energy_per_read=0.0
        self.energy_per_write=0.0
        self.energy_per_access=0.0
        self.cost=0.0
        self.latency=0.0
        self.valid=True

        # from c++ code, we do a loop:
        # for i in range(len(in_channels)):
        #   channels[i]=in_channels[i]
        #   capacity += ...
        i=0
        for ch in in_channels:
            self.channels[i]=ch
            i+=1
            self.num_channels+=1
            self.capacity  += ch.capacity
            self.cost      += ch.cost
            self.bandwidth += ch.bandwidth
            self.energy_per_read   += ch.energy_per_read
            self.energy_per_write  += ch.energy_per_write
            self.energy_per_access += ch.energy_per_access

    def __str__(self):
        s= (f"BoB       cap: {self.capacity} GB "
            f"num_channels: {self.num_channels} "
            f"bw: {self.bandwidth} (MHz) "
            f"cost: ${self.cost} "
            f"energy: {self.energy_per_access} (nJ)\n")
        s+= "   ==============\n"
        for i in range(self.num_channels):
            s+= f"   ({i}) {self.channels[i]}\n"
        s+= "   ==============\n"
        return s

def clone_bob_conf(origin: bob_conf) -> bob_conf:
    """
    Python version of friend bob_conf* clone(bob_conf*);
    We just gather the origin channels in a new list, then pass to constructor.
    """
    in_channels=[]
    for i in range(origin.num_channels):
        in_channels.append(origin.channels[i])
    newbob = bob_conf(origin.memcad_params, in_channels)
    return newbob


# --------------- memory_conf ---------------

class memory_conf:
    """
    Python translation of the C++ memory_conf.
    Aggregates up to MAX_NUM_BOBS bob_conf.
    """
    def __init__(
        self,
        memcad_params: MemCadParameters,
        in_bobs: List[bob_conf]
    ):
        self.memcad_params = memcad_params
        self.num_bobs=0
        self.bobs = [None]*6  # up to MAX_NUM_BOBS=6

        self.capacity=0
        self.bandwidth=0
        self.energy_per_read=0.0
        self.energy_per_write=0.0
        self.energy_per_access=0.0
        self.cost=0.0
        self.latency=0.0
        self.valid=True

        i=0
        for b in in_bobs:
            self.bobs[i]=b
            i+=1
            self.num_bobs+=1
            self.capacity += b.capacity
            self.cost     += b.cost
            self.bandwidth+= b.bandwidth
            self.energy_per_read   += b.energy_per_read
            self.energy_per_write  += b.energy_per_write
            self.energy_per_access += b.energy_per_access

    def __str__(self):
        s= (f"Memory    cap: {self.capacity} GB "
            f"num_bobs: {self.num_bobs} "
            f"bw: {self.bandwidth} (MHz) "
            f"cost: ${self.cost} "
            f"energy: {self.energy_per_access} (nJ)\n"
            " {\n")
        for i in range(self.num_bobs):
            s+= f"  ({i}) {self.bobs[i]}\n"
        s+= " }\n"
        return s

# The c++ code's friend operator << usage => we do __str__ in python.

# If you want a function to do memory_conf => str:
# def print_memory_conf(mem_cnf: memory_conf):
#     print(str(mem_cnf))
