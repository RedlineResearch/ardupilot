#!/bin/bash
AP_HOME="/home/moses/research/software/ap_plane_bug2835"
INSTRUMENTER="/home/moses/research/software/codeinstrumenter"

# echo "Generating Ardupilot bitcode"
echo "Inject instrumentation into Ardupilot bitcode"
$INSTRUMENTER/instrumenter -debug -allF -init_func=_ZN5Plane4loopEv -sfile=$AP_HOME/ArduPlane/filelist.txt -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc 

#-arg=/data/hhuang04/ap3.5.1/ArduPlane/varlist.txt
echo "Compiling to assembly"
llc -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc 

echo "Compiling Assembly into ArduPlane.elf"
g++ -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane.elf $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s -lm -pthread
