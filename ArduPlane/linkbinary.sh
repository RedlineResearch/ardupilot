#!/bin/bash
AP_HOME="/data/hhuang04/ap3.5.1"
OSCOPEAPI="/data/hhuang04/autopilotsim/oscope/instrumentation"
INSTRUMENTER="/data/hhuang04/DroneInstrumenter/build"

echo "Generating Ardupilot bitcode"
#rm -f $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc
#llvm-link -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc `find $AP_HOME/tmp/ArduPlane.build2/ -name "*.bc"`
#llc -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc 

echo "Make Oscope bitcode"
#cd $OSCOPEAPI
#make oscope

echo "Make sure that Instrumenter is built"
#cd $INSTRUMENTER
#make

echo "Combine Ardupilot and Instrumentation Bicodes"
#llvm-link -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full.bc $OSCOPEAPI/oscopeAPI.bc

echo "Inject instrumentation into Ardupilot bitcode"
#opt -load $INSTRUMENTER/varpass/libVarPass.so -varpassTest -allF $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc > $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc



# echo "Compiling Assembly into ArduPlane.elf"
# g++ -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -Wl,--gc-sections -Wl,-Map -Wl,../tmp/ArduPlane.build2/ArduPlane.map -o ../tmp/ArduPlane.build2/ArduPlane.elf ../tmp/ArduPlane.build2/ArduPlane_full.s -lm -pthread

