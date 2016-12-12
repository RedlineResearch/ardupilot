#!/bin/bash
AP_HOME="/data/hhuang04/ap3.5.1"
OSCOPEAPI="/data/hhuang04/autopilotsim/oscope/instrumentation"
INSTRUMENTER="/data/hhuang04/DroneInstrumenter/build"

echo "Generating Ardupilot bitcode"
rm -f $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc
rm -f $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc
rm -f $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc
llvm-link -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc `find $AP_HOME/tmp/ArduPlane.build2/ -name "*.bc"`

echo "Make Oscope bitcode"
cd $OSCOPEAPI
make clean
make oscope

echo "Make sure that Instrumenter is built"
cd $INSTRUMENTER
make clean
make

echo "Combine Ardupilot and Instrumentation Bicodes"
llvm-link -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc $OSCOPEAPI/oscopeAPI.bc

echo "Inject instrumentation into Ardupilot bitcode"
opt -load $INSTRUMENTER/varpass/libVarPass.so -varpassTest -allF $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc > $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc

echo "Compiling to assembly"
llc -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc 

echo "Compiling Assembly into ArduPlane.elf"
g++ -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane.elf $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s -lm -pthread