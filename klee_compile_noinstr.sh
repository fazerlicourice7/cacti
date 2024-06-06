#!/bin/bash

SYM_SRCS="area.cc bank.cc mat.cc Ucache.cc io.cc technology.cc basic_circuit.cc  \
		decoder.cc component.cc uca.cc subarray.cc wire.cc htree2.cc extio.cc extio_technology.cc \
	    router.cc nuca.cc crossbar.cc arbiter.cc powergating.cc TSV.cc memorybus.cc \
		memcad.cc memcad_parameters.cc cacti_interface.cc parameter.cc main.cc"

SYM_HEADERS="extio_technology.h io.h decoder.h const.h extio.h htree2.h  
        mat.h memcad_parameters.h memcad.h nuca.h parameter.h powergating.h"
        
LDLIB=$(llvm-config --ldflags --system-libs --libs core)
CXXFLAGS=$(llvm-config --cxxflags)
CFLAGS=$(llvm-config --cflags)
CLANG=clang++
LLVMLINK=llvm-link
BUILDDIR="klee-build"

mkdir -p ${BUILDDIR}
cd ${BUILDDIR}
rm *.ll *.bc

for SRC in $SYM_SRCS
do 
	OUTNAME=$(basename $SRC .cc).ll
    echo $SRC $OUTNAME
    echo ${CLANG} -O0 --emit-llvm -static -S -g  ${CXXFLAGS} -I. -c ../$SRC -o $OUTNAME
    if ! ${CLANG} -O0 -emit-llvm -static -S -g  ${CXXFLAGS} -I. -c ../$SRC -o $OUTNAME; then 
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


echo "linking binary file"
llc -filetype=obj cacti.bc -o cacti.o
${CLANG} cacti.o -o cacti 
chmod +x cacti

cd ..
echo "copying .ll file"
cp ${BUILDDIR}/cacti.ll cacti.ll
echo "copying .bc file"
cp ${BUILDDIR}/cacti.bc cacti.bc
echo "copying .binary file"
cp ${BUILDDIR}/cacti cacti