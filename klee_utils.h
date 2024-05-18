#ifndef KLEE_UTILS_H


double klee_symbolic_double(const char * name);
double klee_symbolic_relax_double(const char * name, double mean, double rel_error);
double klee_double_var_summary(const char * name, void* variable);
#endif
