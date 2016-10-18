#!/bin/bash

echo "Compiling bitcode"
rm -f /tmp/ArduPlane.build2/ArduPlane_full.bc
llvm-link -o /tmp/ArduPlane.build2/ArduPlane_full.bc `find /tmp/ArduPlane.build2/ -name "*.bc"`
llc -o /tmp/ArduPlane.build2/ArduPlane_full.s /tmp/ArduPlane.build2/ArduPlane_full.bc 
echo "Compiling Assembly into ArduPlane.elf"
g++ -D_GNU_SOURCE  -g  -Wformat -Wshadow -Wpointer-arith -Wcast-align -Wlogical-op -Wwrite-strings -Wformat=2 -Wno-unused-parameter -Wl,--gc-sections -Wl,-Map -Wl,/tmp/ArduPlane.build2/ArduPlane.map -o /tmp/ArduPlane.build2/ArduPlane.elf /tmp/ArduPlane.build2/ArduPlane_full.s -lm -pthread
cp /tmp/ArduPlane.build2/ArduPlane.elf .
echo "Firmware is in ArduPlane.elf"
