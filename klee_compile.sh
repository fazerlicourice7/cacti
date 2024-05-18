#!/bin/bash

SYM_SRCS="area.cc bank.cc mat.cc Ucache.cc io.cc technology.cc basic_circuit.cc  \
		decoder.cc component.cc uca.cc subarray.cc wire.cc htree2.cc extio.cc extio_technology.cc \
	    router.cc nuca.cc crossbar.cc arbiter.cc powergating.cc TSV.cc memorybus.cc \
		memcad.cc memcad_parameters.cc cacti_interface.cc klee_utils.cc klee_parameter.cc klee_io.cc klee_main.cc"

LDLIB=$(llvm-config --ldflags --system-libs --libs core)
CXXFLAGS=$(llvm-config --cxxflags)
CLANG=clang
CXXCLANG=llc
LLVMLINK=llvm-link
BUILDDIR="klee-build"

mkdir -p ${BUILDDIR}
cd ${BUILDDIR}
rm *.ll *.bc
echo "CXXFLAGS=${CXXFLAGS}"

for SRC in $SYM_SRCS
do 
	OUTNAME_LL=$(basename $SRC .cc).ll
	OUTNAME_C=$(basename $SRC .cc).c
    echo ${CLANG} -O0 -emit-llvm -std=c++98 -S -g -c ../$SRC -o $OUTNAME_LL
    if ! ${CLANG} -O0 -emit-llvm -std=c++98 -S -g -c ../$SRC -o $OUTNAME_LL; then 
        echo "[[Compile Error]]"
        exit 1
    fi

done
echo "linking .bc file"
echo ${LLVMLINK} ${LDLIBS} -o cacti.bc *.ll
${LLVMLINK} ${LDLIBS} -o cacti.bc *.ll
echo "linking .ll file"
echo ${LLVMLINK} ${LDLIBS} -S -o cacti.ll *.ll
${LLVMLINK} ${LDLIBS} -S -o cacti.ll *.ll
cd ..
echo "copying .ll file"
cp ${BUILDDIR}/cacti.ll klee_cacti.ll
echo "copying .bc file"
cp ${BUILDDIR}/cacti.bc klee_cacti.bc