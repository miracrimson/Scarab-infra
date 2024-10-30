#include <unordered_map>
#include "lab2_cmiss.h"


std::unordered_map<Addr, bool> accessed_addresses;
std::unordered_map<Addr, bool> cache_lines;

// unsigned int compulsory_miss = 0;//no use printing will crash whole build
// unsigned int capacity_miss = 0;
// unsigned int conflict_miss = 0;


void track_3C_miss(Addr va, Addr line_addr, uns proc_id) {
    if (accessed_addresses.find(va) == accessed_addresses.end()) {
        STAT_EVENT(proc_id, DCACHE_COMPULSORY_MISS);  //compulsory
        accessed_addresses[va] = true;
    } else if (cache_lines.find(line_addr) == cache_lines.end()) {
        STAT_EVENT(proc_id, DCACHE_CAPACITY_MISS);  //capacity
        cache_lines[line_addr] = true;
    } else {
        STAT_EVENT(proc_id, DCACHE_CONFLICT_MISS);  //conflict,everything else
    }
}
