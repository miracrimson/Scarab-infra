// lab2_cmiss.h
#ifndef __LAB2_CMISS_H__
#define __LAB2_CMISS_H__

#ifdef __cplusplus
extern "C" {
#endif

// Include the header that defines Addr (adjust the path if necessary)
#include "globals/global_types.h"  // Assuming this is where Addr is defined
#include "statistics.h"

// Declaration of the tracking function
void track_3C_miss(Addr va, Addr line_addr, uns proc_id);

// Declaration of the function to print miss statistics
void print_3C_stats();

#ifdef __cplusplus
}
#endif

#endif