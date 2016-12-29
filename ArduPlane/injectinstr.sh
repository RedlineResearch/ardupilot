#!/bin/bash
AP_HOME="/home/moses/research/software/ap_plane3.5.1"
OSCOPEAPI="/home/moses/research/software/aviation/oscope/instrumentation"
INSTRUMENTER="/home/moses/DroneInstrumenter/build"

# echo "Generating Ardupilot bitcode"
echo "Inject instrumentation into Ardupilot bitcode"
opt -load $INSTRUMENTER/varpass/libVarPass.so -varpassTest -allF -sfile=$AP_HOME/ArduPlane/filelist.txt $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc > $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc

#-arg=/data/hhuang04/ap3.5.1/ArduPlane/varlist.txt
echo "Compiling to assembly"
llc -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc 

echo "Compiling Assembly into ArduPlane.elf"
g++ -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane.elf $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s -lm -pthread
