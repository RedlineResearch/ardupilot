#!/bin/bash

AP_HOME="/data/hhuang04/ap3.5.1"
OSCOPEAPI="/data/hhuang04/autopilotsim/oscope/instrumentation"
INSTRUMENTER="/data/hhuang04/DroneInstrumenter/build"

# echo "Generating Ardupilot bitcode"
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

echo "Inject instrumentation into Ardupilot bitcode"

$INSTRUMENTER/instrumenter -debug -allF -init_func=_ZN5Plane4loopEv -sfile=$AP_HOME/ArduPlane/filelist.txt -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc 


#-arg=/data/hhuang04/ap3.5.1/ArduPlane/varlist.txt
echo "Compiling to assembly"
llc -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc 

echo "Compiling Assembly into ArduPlane.elf"
g++ -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane.elf $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s -lm -pthread
