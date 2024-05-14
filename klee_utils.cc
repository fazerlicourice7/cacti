#include "klee_utils.h"
#include "math.h"
#include "klee/klee.h"

#define KLEE_SCI_RANGE 16

double klee_symbolic_double(const char * name){
    double value = klee_int(name);
    double order = klee_range(-KLEE_SCI_RANGE, KLEE_SCI_RANGE, name);
    value *= pow(10,order);
    return value;
}