import csv
import os, sys

# get the stats of interest
def get_acc_stat_from_file(file_name, stat_name, stat_pos):
    with open(file_name, "r") as infile:
        # bug: might not be the only match
        for line in infile:
            splitLine = line.split()
            if stat_name in splitLine:
                if stat_pos == 2 or stat_pos == 4:
                    val_string = splitLine[stat_pos][:-1]
                    return float(val_string)
                else:
                    val_string = splitLine[stat_pos]
                    return int(val_string)

class StatGroup:
    def __init__(self, g_name, f_name, s_list):
        self.g_name = g_name
        self.f_name = f_name
        self.s_list = s_list
        self.weighted_total = 0

class Stat:
    # file name, stat name, stat column number
    def __init__(self, s_name, pos):
        self.s_name = s_name
        self.pos = pos
        self.weighted_average = 0
        self.weighted_ratio = 0

class Simpoint:
    def __init__(self, seg_id, weight, sim_dir):
        self.seg_id = seg_id
        self.weight = weight
        self.sim_dir = sim_dir
        # paralell with stat groups
        # 2-d
        self.stat_vals = []
        self.w_stat_vals = []

def read_simpoints(sp_dir, sim_root_dir):
    total_weight = 0
    simpoints = []
    with open(sp_dir + "opt.p", "r") as f1, open(sp_dir + "opt.w", "r") as f2:
        for line1, line2 in zip(f1, f2):
            seg_id = int(line1.split()[0])
            weight = float(line2.split()[0])
            assert(int(line1.split()[1]) == int(line2.split()[1]))
            total_weight += weight
            simpoints.append(Simpoint(seg_id, weight, sim_root_dir + "/" + str(seg_id)))
    
    if total_weight - 1 > 1e-5:
        print("total weight of SimPoint does not add up to 1? {}".format(total_weight))
        exit
    
    return simpoints

def read_simpoint_stats(stat_groups, simpoints):
    for simp in simpoints:
        for g in stat_groups:
            simp.stat_vals.append([])
            for s in g.s_list:
                stat_val = get_acc_stat_from_file(simp.sim_dir + "/" + g.f_name,
                                                s.s_name, s.pos)
                simp.stat_vals[-1].append(stat_val)

def calculate_weighted_average(stat_groups, simpoints):
    for simp in simpoints:
        for g_id, g in enumerate(stat_groups):
            simp.w_stat_vals.append([])
            for s_id, s in enumerate(g.s_list):
                simp.w_stat_vals[-1].append(simp.weight * float(simp.stat_vals[g_id][s_id]))

    for g_id, g in enumerate(stat_groups):
        for s_id, s in enumerate(g.s_list):
            for simp in simpoints:
                s.weighted_average += simp.w_stat_vals[g_id][s_id]

    for g in stat_groups:
        for s in g.s_list:
            g.weighted_total += s.weighted_average

    for g in stat_groups:
        for s in g.s_list:
            if g.weighted_total != 0:
                s.weighted_ratio = s.weighted_average / g.weighted_total
            else:
                s.weighted_ratio = "NA"

def report(stat_groups, simpoints, sim_root_dir):
# simps,  weight, stat0 val, stat0 weighted, stat1 val, stat1 weighted,
# simp 0
# simp 1
# simp x
# w avg,    NA  ,  NA      , stat0 w avg   ,  NA  
# w %  ,    NA  ,  NA      , stat1 w rat   ,  NA
    for g_id, g in enumerate(stat_groups):
        with open(sim_root_dir + "/{}.csv".format(g.g_name), "w") as outfile:
            writer = csv.writer(outfile)

            # title
            # ref: https://stackoverflow.com/questions/11868964/list-comprehension-returning-two-or-more-items-for-each-item
            f1 = lambda x: "{}_val".format(x.s_name)
            f2 = lambda x: "{}_w_val".format(x.s_name)
            writer.writerow(["Simpoints", "Weight"] + [f(stat) for stat in g.s_list for f in (f1,f2)])

            # middle rows
            for simp in simpoints:
                row = [simp.seg_id, simp.weight]
                for s_id, s in enumerate(g.s_list):
                    row.append(simp.stat_vals[g_id][s_id])
                    row.append(simp.w_stat_vals[g_id][s_id])
                writer.writerow(row)

            writer.writerow([])
            # weighted average
            f1 = lambda x: "NA"
            f2 = lambda x: x.weighted_average
            writer.writerow(["weighted_avg", "NA"] + [f(stat) for stat in g.s_list for f in (f1,f2)])

            # weighted ratio
            f1 = lambda x: "NA"
            f2 = lambda x: x.weighted_ratio
            writer.writerow(["weighted_%", "NA"] + [f(stat) for stat in g.s_list for f in (f1,f2)])

            # weighted total
            writer.writerow(["weighted_total", g.weighted_total])

def customized_report(stat_groups, simpoints, sim_root_dir):
    i = 0
    for g in stat_groups:
        if g.g_name == "instructions":
            # weighted_total is the weighted avg of the stat though
            i = g.weighted_total
            assert(g.weighted_total == g.s_list[0].weighted_average)
            break
    c = 0
    for g in stat_groups:
        if g.g_name == "cycles":
            c = g.weighted_total
            assert(g.weighted_total == g.s_list[0].weighted_average)
            break

    with open(sim_root_dir + "/ipc.csv", "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["instructions", "cycles", "IPC"])
        writer.writerow([i, c, float(i)/float(c)])

    blocks = 0
    for g in stat_groups:
        if g.g_name == "fdip_ftq_occupancy_blocks_accumulated":
            blocks = g.weighted_total
            assert(g.weighted_total == g.s_list[0].weighted_average)
            break

    with open(sim_root_dir + "/bpc.csv", "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["fdip_ftq_occupancy_blocks_accumulated", "cycles", "BPC"])
        writer.writerow([blocks, c, float(blocks)/float(c)])

stat_groups = [
    StatGroup("dcache_access", "memory.stat.0.out",
            [
            Stat("DCACHE_MISS", 1),
            Stat("DCACHE_ST_BUFFER_HIT", 1),
            Stat("DCACHE_HIT", 1)
            ]),
    StatGroup("cycles", "core.stat.0.out",
            [
            Stat("NODE_CYCLE", 1)
            ]),
    StatGroup("instructions", "core.stat.0.out",
            [
            Stat("NODE_INST_COUNT", 1)
            ]),

    StatGroup("icache_access", "memory.stat.0.out",
            [
            Stat("ICACHE_HIT", 1),
            Stat("ICACHE_MISS", 1)
            ]),
    StatGroup("icache_miss_reason", "memory.stat.0.out",
            [
            Stat("ICACHE_MISS_NOT_PREFETCHED", 1),
            Stat("ICACHE_MISS_PREFETCHED_AND_EVICTED_BY_IFETCH", 1),
            Stat("ICACHE_MISS_PREFETCHED_AND_EVICTED_BY_FDIP", 1),
            Stat("ICACHE_MISS_MSHR_HIT", 1)
            ]),
    StatGroup("icache_hit_by_fdip_on_off", "memory.stat.0.out",
            [
            Stat("ICACHE_HIT_BY_FDIP_ONPATH", 1),
            Stat("ICACHE_HIT_BY_FDIP_OFFPATH", 1)
            ]),
    StatGroup("icache_miss_mshr_hit_by_fdip_on_off", "memory.stat.0.out",
            [
            Stat("ICACHE_MISS_MSHR_HIT_BY_FDIP_ONPATH", 1),
            Stat("ICACHE_MISS_MSHR_HIT_BY_FDIP_OFFPATH", 1)
            ]),
    StatGroup("icache_hit_on_off_by_fdip", "memory.stat.0.out",
            [
            Stat("ICACHE_HIT_ONPATH_BY_FDIP", 1),
            Stat("ICACHE_HIT_OFFPATH_BY_FDIP", 1)
            ]),
    StatGroup("icache_miss_mshr_hit_on_off_by_fdip", "memory.stat.0.out",
            [
            Stat("ICACHE_MISS_MSHR_HIT_ONPATH_BY_FDIP", 1),
            Stat("ICACHE_MISS_MSHR_HIT_OFFPATH_BY_FDIP", 1)
            ]),
    StatGroup("icache_evict_miss_on_off_by_fdip", "memory.stat.0.out",
            [
            Stat("ICACHE_EVICT_MISS_ONPATH_BY_FDIP", 1),
            Stat("ICACHE_EVICT_MISS_OFFPATH_BY_FDIP", 1)
            ]),
    StatGroup("icache_evict_miss_by_fdip", "memory.stat.0.out",
            [
            Stat("ICACHE_EVICT_MISS_BY_FDIP_ONPATH", 1),
            Stat("ICACHE_EVICT_MISS_BY_FDIP_OFFPATH", 1)
            ]),

    StatGroup("fdip_new_prefetches_on_off", "pref.stat.0.out",
            [
            Stat("FDIP_NEW_PREFETCHES_ONPATH", 1),
            Stat("FDIP_NEW_PREFETCHES_OFFPATH", 1)
            ]),
    StatGroup("fdip_pref_icache_probe_hit_on_off", "pref.stat.0.out",
            [
            Stat("FDIP_PREF_ICACHE_PROBE_HIT_ONPATH", 1),
            Stat("FDIP_PREF_ICACHE_PROBE_HIT_OFFPATH", 1)
            ]),
    StatGroup("fdip_pref_mshr_probe_hit_on_off", "pref.stat.0.out",
            [
            Stat("FDIP_PREF_MSHR_PROBE_HIT_ONPATH", 1),
            Stat("FDIP_PREF_MSHR_PROBE_HIT_OFFPATH", 1)
            ]),
    StatGroup("fdip_attempted_pref_on_off", "pref.stat.0.out",
            [
            Stat("FDIP_ATTEMPTED_PREF_ONPATH", 1),
            Stat("FDIP_ATTEMPTED_PREF_OFFPATH", 1)
            ]),
    StatGroup("fdip_avg_ftq_occupancy", "pref.stat.0.out",
            [
            Stat("FDIP_AVG_FTQ_OCCUPANCY", 1)
            ]),
    StatGroup("fdip_conf", "pref.stat.0.out",
            [
            Stat("FDIP_OFF_CONF_ON", 1),
            Stat("FDIP_OFF_CONF_OFF", 1),
            Stat("FDIP_ON_CONF_ON", 1),
            Stat("FDIP_ON_CONF_OFF", 1)
            ]),
    StatGroup("fdip_conf_true_miss", "pref.stat.0.out",
            [
            Stat("FDIP_OFF_CONF_ON_EMIT_UNUSEFUL", 1),
            Stat("FDIP_ON_CONF_OFF_MISS_USEFUL", 1)
            ]),

    StatGroup("inst_lost_wait_for_icache_miss", "fetch.stat.0.out",
            [
            Stat("INST_LOST_WAIT_FOR_ICACHE_MISS", 1)
            ]),
    StatGroup("inst_lost_wait_for_icache_miss_reason", "fetch.stat.0.out",
            [
            Stat("INST_LOST_WAIT_FOR_ICACHE_MISS_NOT_PREFETCHED", 1),
            Stat("INST_LOST_WAIT_FOR_ICACHE_MISS_PREFETCHED_AND_EVICTED_BY_IFETCH", 1),
            Stat("INST_LOST_WAIT_FOR_ICACHE_MISS_PREFETCHED_AND_EVICTED_BY_FDIP", 1),
            Stat("INST_LOST_WAIT_FOR_ICACHE_MISS_MSHR_HIT", 1)
            ]),
    StatGroup("cf_ratio", "inst.stat.0.out",
            [
            Stat("ST_OP_CF", 2)
            ]),


    StatGroup("fdip_ftq_occupancy_ops_accumulated", "pref.stat.0.out",
            [
            Stat("FDIP_FTQ_OCCUPANCY_OPS_ACCUMULATED", 1)
            ]),
    StatGroup("fdip_ftq_occupancy_blocks_accumulated", "pref.stat.0.out",
            [
            Stat("FDIP_FTQ_OCCUPANCY_BLOCKS_ACCUMULATED", 1)
            ]),
    StatGroup("cbr", "bp.stat.0.out",
            [
            Stat("CBR_CORRECT", 1),
            Stat("CBR_CORRECT_BTB_MISS_NT_NT", 1),
            Stat("CBR_RECOVER_MISPREDICT", 1),
            Stat("CBR_RECOVER_MISFETCH", 1),
            Stat("CBR_RECOVER_BTB_MISS_T_T", 1),
            Stat("CBR_RECOVER_BTB_MISS_T_NT", 1),
            Stat("CBR_RECOVER_BTB_MISS_NT_T", 1)
            ])
]

if __name__ == "__main__":
    if not os.path.isdir(sys.argv[1]):
        print("simpoint directory {} does not exist!")
        exit
    if not os.path.isdir(sys.argv[2]):
        print("simulation directory {} does not exist!")
        exit

    simpoints = read_simpoints(sys.argv[1], sys.argv[2])
    read_simpoint_stats(stat_groups, simpoints)
    # will calculate Stat.weighted_average, StatGroup.weighted_total, and Stat.weighted_ratio, 
    calculate_weighted_average(stat_groups, simpoints)
    # simpoints.result
    report(stat_groups, simpoints, sys.argv[2])
    customized_report(stat_groups, simpoints, sys.argv[2])
