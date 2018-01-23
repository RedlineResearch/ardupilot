#!/bin/bash

COMPILER=g++-5
LOCAL_APHOME="/home/moses/research/software/ap_plane3.5.1"
SERVER_APHOME="/hom/hhuang04/ap_382"
LOCAL_INSTR="/home/moses/research/software/codeinstrumenter"
SERVER_INSTR="/home/hhuang04/codeinstr"

if [ "$1" == "local" ]; then
    AP_HOME=$LOCAL_APHOME
    INSTRUMENTER=$LOCAL_INSTR
else
    AP_HOME=$SERVER_APHOME
    INSTRUMENTER=$SERVER_INSTR
fi 

echo $AP_HOME
echo $INSTRUMENTER

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

if [ "$1" == "local" ]; then
    make local_instr
else
    make server_instr
fi

echo "Combine Ardupilot and Instrumentation Bicodes"
llvm-link -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc $INSTRUMENTER/oscopeAPI.bc

echo "Build the list of files to instrument"
# Current directory
cd $AP_HOME/ArduPlane
find . -name "*.cpp" | cut -d'/' -f 2- | grep -v "test" >> $flist_tmp
cd $AP_HOME/libraries
find `pwd` -name "*.cpp" | grep -v "example" | egrep -v "c\+\+" | grep -v "benchmark" | grep -v "AC_" | grep -v "tests" | grep -v "AP_HAL_FLYMAPLE" | grep -v "AP_HAL_Linux" | grep -v "AP_HAL_PX4" | grep -v "AP_HAL_QURT" | grep -v "AP_HAL_VRBRAIN" | grep -v "utility/Print.cpp" >> $AP_HOME/ArduPlane/$flist_tmp

cd $AP_HOME/ArduPlane
echo "# This should contain the filename of the files that need to be instrumented" > $flist
echo "# To comment out a line,  add # to start of line" >> $flist
echo "" >> $flist
sort < $flist_tmp >> $flist
rm $flist_tmp

echo "Inject instrumentation into Ardupilot bitcode"
$INSTRUMENTER/instrumenter $2 -instrIO -init_func=_ZN5Plane4loopEv -filelist=$AP_HOME/ArduPlane/$flist -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc 

echo "Compiling to assembly"
llc -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc 

echo "Compiling Assembly into ArduPlane.elf"
$COMPILER -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane.elf $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s -lm -pthread
