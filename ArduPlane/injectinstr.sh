#!/bin/bash

LOCAL_APHOME="/home/moses/research/software/ap_plane3.5.1"
SERVER_APHOME="/home/hhuang04/ap_plane3.5.1"
LOCAL_INSTR="/home/moses/research/software/codeinstrumenter"
SERVER_INSTR="/home/hhuang04/instrumenter"

if [ "$1" == "local" ]; then
    AP_HOME=$LOCAL_APHOME
    INSTRUMENTER=$LOCAL_INSTR
else
    AP_HOME=$SERVER_APHOME
    INSTRUMENTER=$SERVER_INSTR
fi 

echo $AP_HOME
echo $INSTRUMENTER

# # echo "Generating Ardupilot bitcode"
# echo "Inject instrumentation into Ardupilot bitcode"
# $INSTRUMENTER/instrumenter $2 -debug -init_func=_ZN5Plane4loopEv -sfile=$AP_HOME/ArduPlane/filelist.txt -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_instr.bc 

# #-arg=/data/hhuang04/ap3.5.1/ArduPlane/varlist.txt
# echo "Compiling to assembly"
# llc -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.bc 

# echo "Compiling Assembly into ArduPlane.elf"
# g++ -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -o $AP_HOME/tmp/ArduPlane.build2/ArduPlane.elf $AP_HOME/tmp/ArduPlane.build2/ArduPlane_full_inject.s -lm -pthread
