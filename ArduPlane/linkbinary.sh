#!/bin/bash

AP_HOME="/home/moses/research/software/ap_plane_bug2835"
INSTRUMENTER="/home/moses/research/software/codeinstrumenter"
flist_tmp="filelist_tmp.txt"
flist="filelist.txt"


echo "Generating Ardupilot bitcode"
rm -f $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc
rm -f $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc
rm -f $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane.elf
llvm-link -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc `find $AP_HOME/tmp/ArduPlane.build2/ -name "*.bc"`

echo "Make sure that Instrumenter and Oscope API is built"
cd $INSTRUMENTER
make oscope
make instr

echo "Combine Ardupilot and Instrumentation Bicodes"
llvm-link -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc $INSTRUMENTER/oscopeAPI.bc

echo "Build the list of files to instrument"
# Current directory
find . -name "*.cpp" | cut -d'/' -f 2- | grep -v "test" >> $flist_tmp
cd ../libraries
find `pwd` -name "*.cpp" | grep -v "example" | egrep -v "c\+\+" | grep -v "benchmark" | grep -v "AC_" | grep -v "tests" | grep -v "AP_HAL_FLYMAPLE" | grep -v "AP_HAL_Linux" | grep -v "AP_HAL_PX4" | grep -v "AP_HAL_QURT" | grep -v "AP_HAL_VRBRAIN" | grep -v "utility/Print.cpp" >> ../ArduPlane/filelist_test.txt

cd ../ArduPlane
echo "# This should contain the filename of the files that need to be instrumented" > $flist
echo "# To comment out a line,  add # to start of line" >> $flist
echo "" >> $flist
sort < $flist_tmp >> $flist
rm $flist_tmp

echo "Inject instrumentation into Ardupilot bitcode"

$INSTRUMENTER/instrumenter -debug -allF -init_func=_ZN5Plane4loopEv -sfile=$AP_HOME/ArduPlane/$flist -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc 


#-arg=/data/hhuang04/ap3.5.1/ArduPlane/varlist.txt
echo "Compiling to assembly"
llc -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc 

echo "Compiling Assembly into ArduPlane.elf"
g++ -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane.elf $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s -lm -pthread
