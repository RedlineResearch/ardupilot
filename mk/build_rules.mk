
#
# Build sketch objects
#

$(BUILDROOT)/%.bc: $(BUILDROOT)/%.cpp $(GENERATE_TARGETS) $(MAVLINK_HEADERS)
	$(RULEHDR)
	$(v)$(CXX) $(CXXFLAGS) -c -emit-llvm -Xclang -fdump-record-layouts -o $@ $< $(SKETCH_INCLUDES) > $@.txt

$(BUILDROOT)/%.bc: $(BUILDROOT)/make.flags $(SRCROOT)/%.cpp $(GENERATE_TARGETS) $(MAVLINK_HEADERS)
	$(RULEHDR)
	$(v)$(CXX) $(CXXFLAGS) -c -emit-llvm -Xclang -fdump-record-layouts -o $@ $*.cpp $(SKETCH_INCLUDES) > $@.txt

$(BUILDROOT)/%.bc: $(SRCROOT)/%.c
	$(RULEHDR)
	$(v)$(CC) $(CFLAGS) -c -emit-llvm -Xclang -fdump-record-layouts -o $@ $< $(SKETCH_INCLUDES) > $@.txt

$(BUILDROOT)/%.bc: $(SRCROOT)/%.S
	$(RULEHDR)
	$(v)$(AS) $(ASFLAGS) -c -emit-llvm -Xclang -fdump-record-layouts -o $@ $< $(SKETCH_INCLUDES) > $@.txt

#
# Build library objects from sources in the sketchbook
#

$(BUILDROOT)/libraries/%.bc: $(SKETCHBOOK)/libraries/%.cpp $(GENERATE_TARGETS) $(MAVLINK_HEADERS)
	$(RULEHDR)
	$(v)$(CXX) $(CXXFLAGS) -c -emit-llvm -Xclang -fdump-record-layouts -o $@ $< $(SLIB_INCLUDES) > $@.txt

$(BUILDROOT)/libraries/%.bc: $(SKETCHBOOK)/libraries/%.c
	$(RULEHDR)
	$(v)$(CC) $(CFLAGS) -c -emit-llvm -Xclang -fdump-record-layouts -o $@ $< $(SLIB_INCLUDES) > $@.txt

$(BUILDROOT)/libraries/%.bc: $(SKETCHBOOK)/libraries/%.S
	$(RULEHDR)
	$(v)$(AS) $(ASFLAGS) -c -emit-llvm -Xclang -fdump-record-layouts -o $@ $< $(SLIB_INCLUDES) > $@.txt
