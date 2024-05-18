#include "klee_utils.h"
#include "math.h"
#include "klee/klee.h"
#include "stdio.h"

#define KLEE_SCI_RANGE 16

double klee_symbolic_relax_double(const char * name,double mean, double rel_error){
    double new_value = mean;
    double delta = klee_range(-100, 100, name)*0.01*mean*rel_error;
    return new_value + delta;
}
double klee_symbolic_double(const char * name){
    double value = klee_int(name);
    double order = klee_range(-KLEE_SCI_RANGE, KLEE_SCI_RANGE, name);
    value *= pow(10,order);
    return value;
}

double klee_double_var_summary(const char * name, double variable){
    bool is_sym = klee_is_symbolic(variable);
    printf(is_sym ? "symbolic " : "concrete ");
    printf(name);
    klee_print_expr("=%s", variable);
}