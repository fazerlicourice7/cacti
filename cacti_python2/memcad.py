import math
from functools import cmp_to_key

# ------------------------------------------------------------------
# Global placeholders for "INF", "EPS", etc.
# In C++ code, it often includes <limits>, <cmath>, or const.h
# We'll define them here:
INF = float('inf')
EPS = 1e-9

# ------------------------------------------------------------------
# Enumerations or constants that appear to be used
# in memcad.cc code.
from .cacti_interface import MemCad_metrics, DIMM_Model, Mem_IO_type
# class MemCad_metrics:
#     Cost = 0
#     Bandwidth = 1
#     Energy = 2

# class DIMM_Model:
#     JUST_UDIMM = 0
#     JUST_RDIMM = 1
#     JUST_LRDIMM = 2
#     ALL = 3

# class Mem_IO_type:
#     DDR3 = 0
#     DDR4 = 1
#     LPDDR2 = 2
#     WideIO = 3
#     Low_Swing_Diff = 4
#     Serial = 5

class MemoryParameters:
    """
    Placeholder for references like MemoryParameters::cost, MemoryParameters::bandwidth_load.
    In the original C++ code, these might come from a big table of memory data.
    
    We'll define them as static variables that you must fill in as needed.
    """
    # For example, cost[io_type][dimm_type][capacity_index],
    # or some large 3D array.  We'll use placeholders.
    cost = None
    bandwidth_load = None

# Define a dummy for "bw_index" used in find_all_channels
def bw_index(io_type, bw_value):
    """
    The original code calls something like:
       int max_index = bw_index(current_io_type,
                                MemoryParameters::bandwidth_load[current_io_type][4 - num_dimm_per_channel]);
    This function presumably returns an integer index for iteration.
    
    This is a placeholder that you must implement or adapt.
    """
    # Put your real logic here:
    return 4  # or something

# ------------------------------------------------------------------
# Classes that the code manipulates.  In the real code, they likely come
# from other headers like "channel_conf.h", "bob_conf.h", "memory_conf.h", etc.
# We only see them used in memcad.cc, so we'll provide stubs.

class MemCadParameters:
    """
    This is a placeholder for 'MemCadParameters * memcad_params'
    that the code references extensively.
    """
    def __init__(self):
        self.capacity = 0
        self.io_type = Mem_IO_type.DDR3
        self.dimm_model = DIMM_Model.ALL
        self.low_power_permitted = False
        self.verbose = False
        self.mirror_in_bob = False
        self.same_bw_in_bob = True
        self.num_channels_per_bob = 1
        self.num_bobs = 1

        # Which metrics to optimize or compare
        self.first_metric = MemCad_metrics.Cost
        self.second_metric = MemCad_metrics.Bandwidth
        self.third_metric = MemCad_metrics.Energy

class channel_conf:
    """
    A placeholder for the channel_conf object.  The C++ code constructs it as:
       new channel_conf(memcad_params, dimm_cap, bandwidth, LRDIMM, low_power)
    It has attributes like capacity, cost, bandwidth, energy_per_access, memcad_params, etc.
    We'll store them in the constructor.
    """
    def __init__(self, memcad_params, dimm_cap_list, bandwidth, dimm_type, low_power):
        self.memcad_params = memcad_params
        self.bandwidth = bandwidth

        # capacity is sum of the dimm_cap_list
        self.capacity = sum(dimm_cap_list)

        # For demonstration, define cost/energy as placeholders:
        # In real code, you might fetch from MemoryParameters::cost, etc.
        self.cost = 0.0
        self.energy_per_access = 0.0

        # If we see "cost < INF" is used as a condition, let's set some logic:
        # We'll assume if capacity>0, cost < INF.  Otherwise cost=INF
        if self.capacity == 0:
            self.cost = INF
        else:
            # Simplified cost.  Real code uses MemoryParameters::cost[..]
            self.cost = 100.0 / (1.0 if low_power else 0.9)
            self.energy_per_access = 10.0  # placeholder

        # If the code sets low_power and we want a different cost, we can do so.
        # This is only to replicate the "if(new_channel->cost < INF) push_back(...)"
        # usage in memcad.cc
        self.dimm_type = dimm_type
        self.low_power = low_power

    def __str__(self):
        """
        The code does:  cout << *(*memcad_all_channels)[i] << endl;
        We'll replicate with a string representation
        """
        return (f"[channel_conf: capacity={self.capacity}, "
                f"bandwidth={self.bandwidth}, cost={self.cost:.2f}, "
                f"energy_per_access={self.energy_per_access:.2f}, low_power={self.low_power}]")

def clone_channel(ch):
    """
    The C++ code uses clone((*memcad_all_channels)[i]) to create a copy.
    We'll do a simple deep-ish copy in Python:
    """
    new_obj = channel_conf(ch.memcad_params, [ch.capacity], ch.bandwidth, ch.dimm_type, ch.low_power)
    new_obj.cost = ch.cost
    new_obj.energy_per_access = ch.energy_per_access
    return new_obj

class bob_conf:
    """
    The code calls: new bob_conf(memcad_params, &temp)
    and then references bob->cost, bob->bandwidth, bob->capacity, etc.
    We'll create a placeholder to mimic those.
    """
    def __init__(self, memcad_params, channel_list):
        self.memcad_params = memcad_params

        # capacity is sum of channel capacities
        self.capacity = sum(ch.capacity for ch in channel_list)

        # cost is sum
        self.cost = sum(ch.cost for ch in channel_list)

        # bandwidth is sum or maybe min?  The code uses it in comparisons. The original code is unclear.
        # We'll assume sum, as a guess:
        self.bandwidth = sum(ch.bandwidth for ch in channel_list)

        # energy could also be some combination:
        self.energy_per_access = sum(ch.energy_per_access for ch in channel_list)

    def __str__(self):
        return (f"[bob_conf: capacity={self.capacity}, cost={self.cost:.2f}, "
                f"bandwidth={self.bandwidth}, energy={self.energy_per_access:.2f}]")

def clone_bob(bob):
    new_obj = bob_conf(bob.memcad_params, [])
    new_obj.capacity = bob.capacity
    new_obj.cost = bob.cost
    new_obj.bandwidth = bob.bandwidth
    new_obj.energy_per_access = bob.energy_per_access
    return new_obj

class memory_conf:
    """
    The code calls: new memory_conf(memcad_params, &temp)
    The code references memory->capacity, memory->cost, memory->bandwidth, memory->energy_per_access.
    We'll define that logic here.
    """
    def __init__(self, memcad_params, bob_list):
        self.memcad_params = memcad_params
        self.capacity = sum(b.capacity for b in bob_list)
        self.cost = sum(b.cost for b in bob_list)
        # Bandwidth might be sum or min; the code uses it in compare_memories. We'll guess sum again.
        self.bandwidth = sum(b.bandwidth for b in bob_list)
        self.energy_per_access = sum(b.energy_per_access for b in bob_list)

    def __str__(self):
        return (f"[memory_conf: capacity={self.capacity}, cost={self.cost:.2f}, "
                f"bandwidth={self.bandwidth}, energy={self.energy_per_access:.2f}]")

def clone_memory(mem):
    new_obj = memory_conf(mem.memcad_params, [])
    new_obj.capacity = mem.capacity
    new_obj.cost = mem.cost
    new_obj.bandwidth = mem.bandwidth
    new_obj.energy_per_access = mem.energy_per_access
    return new_obj

# ------------------------------------------------------------------
# The "extern" global vectors in C++ become global Python lists here:
memcad_all_channels = []
memcad_all_bobs = []
memcad_all_memories = []
memcad_best_results = []  # The code mentions it, but never populates it in the snippet

# ------------------------------------------------------------------
# compare_channels(...) must become a comparator returning negative if first<second,
# positive if first>second, 0 if they are effectively equal.
def compare_channels_cmp(first, second):
    if abs(first.capacity - second.capacity) > EPS:
        return -1 if (first.capacity < second.capacity) else 1

    # If capacity is equal, we check up to 3 metrics from first->memcad_params
    first_metric = first.memcad_params.first_metric
    second_metric = first.memcad_params.second_metric
    third_metric = first.memcad_params.third_metric

    # We'll define a small helper to compare one metric:
    def compare_metric(m, a, b):
        if m == MemCad_metrics.Cost:
            if abs(a.cost - b.cost) > EPS:
                return -1 if (a.cost < b.cost) else 1
        elif m == MemCad_metrics.Bandwidth:
            if abs(a.bandwidth - b.bandwidth) > EPS:
                return -1 if (a.bandwidth > b.bandwidth) else 1
        elif m == MemCad_metrics.Energy:
            if abs(a.energy_per_access - b.energy_per_access) > EPS:
                return -1 if (a.energy_per_access < b.energy_per_access) else 1
        return 0

    # Compare first_metric
    c = compare_metric(first_metric, first, second)
    if c != 0: return c

    # Compare second_metric
    c = compare_metric(second_metric, first, second)
    if c != 0: return c

    # Compare third_metric
    c = compare_metric(third_metric, first, second)
    if c != 0: return c

    # If all else is equal, we return 0
    return 0

def compare_channels_bw_cmp(first, second):
    """
    The code for 'compare_channels_bw' returns (first->bandwidth < second->bandwidth).
    We'll do a comparator returning negative if first<second, etc.
    """
    if abs(first.bandwidth - second.bandwidth) < EPS:
        return 0
    return -1 if (first.bandwidth < second.bandwidth) else 1

# ------------------------------------------------------------------
def prune_channels():
    global memcad_all_channels
    temp = []
    last_added = -1
    # The code checks if last_added != channel->capacity, then clones/push_back
    for ch in memcad_all_channels:
        if ch.capacity != last_added:
            temp.append(clone_channel(ch))
            last_added = ch.capacity

    # In C++, we do: delete original pointers, clear the vector, etc.
    # In Python, we can just reassign:
    for c in memcad_all_channels:
        del c
    memcad_all_channels.clear()

    memcad_all_channels = temp

def find_all_channels(memcad_params):
    global memcad_all_channels
    memcad_all_channels = []

    DIMM_size = [0,4,8,16,32,64]
    current_io_type = memcad_params.io_type
    current_dimm_model = memcad_params.dimm_model

    # The code: for up to 3 DIMMs per channel:  d1, d2, d3
    for d1 in range(6):
        for d2 in range(d1, 6):
            for d3 in range(d2, 6):
                total_cap = DIMM_size[d1] + DIMM_size[d2] + DIMM_size[d3]
                if total_cap > memcad_params.capacity:
                    continue

                # For LRDIMM:
                if ((current_dimm_model == DIMM_Model.JUST_LRDIMM or current_dimm_model == DIMM_Model.ALL)
                    and ((d1==0) or (MemoryParameters.cost[current_io_type][2][d1-1] < INF))
                    and ((d2==0) or (MemoryParameters.cost[current_io_type][2][d2-1] < INF))
                    and ((d3==0) or (MemoryParameters.cost[current_io_type][2][d3-1] < INF))):
                    dimm_cap = []
                    num_dimm_per_channel = 0
                    if d1>0:
                        dimm_cap.append(DIMM_size[d1])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)
                    if d2>0:
                        dimm_cap.append(DIMM_size[d2])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)
                    if d3>0:
                        dimm_cap.append(DIMM_size[d3])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)

                    max_index = bw_index(current_io_type, MemoryParameters.bandwidth_load[current_io_type][4 - num_dimm_per_channel])
                    for bw_id in range(max_index+1):
                        bandwidth = MemoryParameters.bandwidth_load[current_io_type][bw_id]
                        new_channel = channel_conf(memcad_params, dimm_cap, bandwidth, 2, False)
                        if new_channel.cost < INF:
                            memcad_all_channels.append(new_channel)

                        if total_cap == 0:
                            continue

                        if memcad_params.low_power_permitted:
                            new_channel = channel_conf(memcad_params, dimm_cap, bandwidth, 2, True)
                            if new_channel.cost < INF:
                                memcad_all_channels.append(new_channel)

                # For RDIMM:
                if ((current_dimm_model == DIMM_Model.JUST_RDIMM or current_dimm_model == DIMM_Model.ALL)
                    and ((d1==0) or (MemoryParameters.cost[current_io_type][1][d1-1] < INF))
                    and ((d2==0) or (MemoryParameters.cost[current_io_type][1][d2-1] < INF))
                    and ((d3==0) or (MemoryParameters.cost[current_io_type][1][d3-1] < INF))):

                    dimm_cap = []
                    num_dimm_per_channel = 0
                    if d1>0:
                        dimm_cap.append(DIMM_size[d1])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)
                    if d2>0:
                        dimm_cap.append(DIMM_size[d2])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)
                    if d3>0:
                        dimm_cap.append(DIMM_size[d3])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)

                    if total_cap == 0:
                        continue

                    max_index = bw_index(current_io_type, MemoryParameters.bandwidth_load[current_io_type][4 - num_dimm_per_channel])
                    for bw_id in range(max_index+1):
                        bandwidth = MemoryParameters.bandwidth_load[current_io_type][bw_id]
                        new_channel = channel_conf(memcad_params, dimm_cap, bandwidth, 1, False)
                        if new_channel.cost < INF:
                            memcad_all_channels.append(new_channel)

                        if memcad_params.low_power_permitted:
                            new_channel = channel_conf(memcad_params, dimm_cap, bandwidth, 1, True)
                            if new_channel.cost < INF:
                                memcad_all_channels.append(new_channel)

                # For UDIMM:
                if ((current_dimm_model == DIMM_Model.JUST_UDIMM or current_dimm_model == DIMM_Model.ALL)
                    and ((d1==0) or (MemoryParameters.cost[current_io_type][0][d1-1] < INF))
                    and ((d2==0) or (MemoryParameters.cost[current_io_type][0][d2-1] < INF))
                    and ((d3==0) or (MemoryParameters.cost[current_io_type][0][d3-1] < INF))):

                    dimm_cap = []
                    num_dimm_per_channel = 0
                    if d1>0:
                        dimm_cap.append(DIMM_size[d1])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)
                    if d2>0:
                        dimm_cap.append(DIMM_size[d2])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)
                    if d3>0:
                        dimm_cap.append(DIMM_size[d3])
                        num_dimm_per_channel+=1
                    else:
                        dimm_cap.append(0)

                    if total_cap == 0:
                        continue

                    max_index = bw_index(current_io_type, MemoryParameters.bandwidth_load[current_io_type][4 - num_dimm_per_channel])
                    for bw_id in range(max_index+1):
                        bandwidth = MemoryParameters.bandwidth_load[current_io_type][bw_id]
                        new_channel = channel_conf(memcad_params, dimm_cap, bandwidth, 0, False)
                        if new_channel.cost < INF:
                            memcad_all_channels.append(new_channel)

                        if memcad_params.low_power_permitted:
                            new_channel = channel_conf(memcad_params, dimm_cap, bandwidth, 0, True)
                            if new_channel.cost < INF:
                                memcad_all_channels.append(new_channel)

    # sort with compare_channels
    memcad_all_channels.sort(key=cmp_to_key(compare_channels_cmp))

    prune_channels()

    if memcad_params.verbose:
        for i, ch in enumerate(memcad_all_channels):
            print(ch)

# ------------------------------------------------------------------
# compare_bobs
def compare_bobs_cmp(first, second):
    if abs(first.capacity - second.capacity) > EPS:
        return -1 if (first.capacity < second.capacity) else 1

    first_metric = first.memcad_params.first_metric
    second_metric = first.memcad_params.second_metric
    third_metric = first.memcad_params.third_metric

    def compare_metric(m, a, b):
        if m == MemCad_metrics.Cost:
            if abs(a.cost - b.cost) > EPS:
                return -1 if (a.cost < b.cost) else 1
        elif m == MemCad_metrics.Bandwidth:
            if abs(a.bandwidth - b.bandwidth) > EPS:
                return -1 if (a.bandwidth > b.bandwidth) else 1
        elif m == MemCad_metrics.Energy:
            if abs(a.energy_per_access - b.energy_per_access) > EPS:
                return -1 if (a.energy_per_access < b.energy_per_access) else 1
        return 0

    c = compare_metric(first_metric, first, second)
    if c != 0: return c
    c = compare_metric(second_metric, first, second)
    if c != 0: return c
    c = compare_metric(third_metric, first, second)
    if c != 0: return c
    return 0

def prune_bobs():
    global memcad_all_bobs
    temp = []
    last_added = -1
    for bb in memcad_all_bobs:
        if bb.capacity != last_added:
            temp.append(clone_bob(bb))
            last_added = bb.capacity

    for b in memcad_all_bobs:
        del b
    memcad_all_bobs.clear()

    memcad_all_bobs = temp

def find_bobs_recursive(memcad_params, start, end, nb, channel_index):
    if nb == 1:
        for i in range(start, end+1):
            channel_index.append(i)

            # build a temp list of channels
            tmp = []
            for idx in channel_index:
                tmp.append(memcad_all_channels[idx])
            memcad_all_bobs.append(bob_conf(memcad_params, tmp))
            tmp.clear()

            channel_index.pop()
        return

    for i in range(start, end+1):
        channel_index.append(i)
        find_bobs_recursive(memcad_params, i, end, nb-1, channel_index)
        channel_index.pop()

def find_all_bobs(memcad_params):
    global memcad_all_bobs
    memcad_all_bobs = []

    if memcad_params.mirror_in_bob:
        # replicate the same channel multiple times
        for i, ch in enumerate(memcad_all_channels):
            channels = []
            for _ in range(memcad_params.num_channels_per_bob):
                channels.append(ch)
            memcad_all_bobs.append(bob_conf(memcad_params, channels))
            channels.clear()
    elif memcad_params.same_bw_in_bob:
        # sort memcad_all_channels by bandwidth
        memcad_all_channels.sort(key=cmp_to_key(compare_channels_bw_cmp))

        start_index = [0]
        end_index = []
        last_bw = memcad_all_channels[0].bandwidth
        for i in range(len(memcad_all_channels)):
            bw = memcad_all_channels[i].bandwidth
            if abs(last_bw - bw) > EPS:
                end_index.append(i-1)
                start_index.append(i)
                last_bw = bw
        end_index.append(len(memcad_all_channels)-1)

        channel_index = []
        # for each chunk of channels that share the same bandwidth:
        for i in range(len(start_index)):
            find_bobs_recursive(memcad_params,
                                start_index[i],
                                end_index[i],
                                memcad_params.num_channels_per_bob,
                                channel_index)
    else:
        print("We do not support different frequencies per in a BoB!")
        # in C++: assert(false)
        raise RuntimeError("We do not support different frequencies in a BoB!")

    memcad_all_bobs.sort(key=cmp_to_key(compare_bobs_cmp))
    prune_bobs()
    if memcad_params.verbose:
        for b in memcad_all_bobs:
            print(b)

# ------------------------------------------------------------------
# compare_memories
def compare_memories_cmp(first, second):
    if abs(first.capacity - second.capacity) > EPS:
        return -1 if (first.capacity < second.capacity) else 1

    first_metric = first.memcad_params.first_metric
    second_metric = first.memcad_params.second_metric
    third_metric = first.memcad_params.third_metric

    def compare_metric(m, a, b):
        if m == MemCad_metrics.Cost:
            if abs(a.cost - b.cost) > EPS:
                return -1 if (a.cost < b.cost) else 1
        elif m == MemCad_metrics.Bandwidth:
            if abs(a.bandwidth - b.bandwidth) > EPS:
                return -1 if (a.bandwidth > b.bandwidth) else 1
        elif m == MemCad_metrics.Energy:
            if abs(a.energy_per_access - b.energy_per_access) > EPS:
                return -1 if (a.energy_per_access < b.energy_per_access) else 1
        return 0

    c = compare_metric(first_metric, first, second)
    if c != 0: return c
    c = compare_metric(second_metric, first, second)
    if c != 0: return c
    c = compare_metric(third_metric, first, second)
    if c != 0: return c
    # default
    return 0

def find_mems_recursive(memcad_params, remaining_capacity, start, nb, bobs_index):
    if nb == 1:
        for i in range(start, len(memcad_all_bobs)):
            if abs(memcad_all_bobs[i].capacity - remaining_capacity) < EPS:
                bobs_index.append(i)
                tmp = []
                for idx in bobs_index:
                    tmp.append(memcad_all_bobs[idx])
                memcad_all_memories.append(memory_conf(memcad_params, tmp))
                tmp.clear()
                bobs_index.pop()
        return

    for i in range(start, len(memcad_all_bobs)):
        if memcad_all_bobs[i].capacity > remaining_capacity:
            continue
        new_remaining_capacity = remaining_capacity - memcad_all_bobs[i].capacity
        bobs_index.append(i)
        find_mems_recursive(memcad_params, new_remaining_capacity, i, nb-1, bobs_index)
        bobs_index.pop()

def find_all_memories(memcad_params):
    global memcad_all_memories
    memcad_all_memories = []

    bobs_index = []
    find_mems_recursive(memcad_params, memcad_params.capacity, 0, memcad_params.num_bobs, bobs_index)

    memcad_all_memories.sort(key=cmp_to_key(compare_memories_cmp))

    if memcad_params.verbose:
        print("all possible results:")
        for m in memcad_all_memories:
            print(m)

    if len(memcad_all_memories) == 0:
        print("No result found")
        return False

    print("top 3 best memory configurations are:")
    min_num_results = 3 if len(memcad_all_memories) > 3 else len(memcad_all_memories)
    for i in range(min_num_results):
        print(memcad_all_memories[i])

    return True

def clean_results():
    global memcad_all_channels, memcad_all_bobs, memcad_all_memories, memcad_best_results

    for ch in memcad_all_channels:
        del ch
    memcad_all_channels.clear()

    for b in memcad_all_bobs:
        del b
    memcad_all_bobs.clear()

    for mm in memcad_all_memories:
        del mm
    memcad_all_memories.clear()

    # If memcad_best_results used
    memcad_best_results.clear()

def solve_memcad(memcad_params):
    find_all_channels(memcad_params)
    find_all_bobs(memcad_params)
    find_all_memories(memcad_params)
    clean_results()
