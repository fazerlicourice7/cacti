#!/bin/bash
rm -rf klee-out-*
klee --posix-runtime  --libcxx --libc=klee -write-cvcs -write-smt2s -write-cov -write-test-info  klee_cacti.bc