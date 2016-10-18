
#
# Build sketch objects
#

$(BUILDROOT)/%.bc: $(BUILDROOT)/%.cpp $(GENERATE_TARGETS) $(MAVLINK_HEADERS) $(UAVCAN_HEADERS)
	$(RULEHDR)
	$(v)$(CXX) $(CXXFLAGS) -c -emit-llvm -o $@ $< $(SKETCH_INCLUDES)

$(BUILDROOT)/%.bc: $(BUILDROOT)/make.flags $(SRCROOT)/%.cpp $(GENERATE_TARGETS) $(MAVLINK_HEADERS) $(UAVCAN_HEADERS)
	$(RULEHDR)
	$(v)$(CXX) $(CXXFLAGS) -c -emit-llvm -o $@ $*.cpp $(SKETCH_INCLUDES)

$(BUILDROOT)/%.bc: $(SRCROOT)/%.c $(UAVCAN_HEADERS)
	$(RULEHDR)
	$(v)$(CC) $(CFLAGS) -c -emit-llvm -o $@ $< $(SKETCH_INCLUDES)

$(BUILDROOT)/%.bc: $(SRCROOT)/%.S
	$(RULEHDR)
	$(v)$(AS) $(ASFLAGS) -c -emit-llvm -o $@ $< $(SKETCH_INCLUDES)

#
# Build library objects from sources in the sketchbook
#

$(BUILDROOT)/libraries/%.bc: $(SKETCHBOOK)/libraries/%.cpp $(GENERATE_TARGETS) $(MAVLINK_HEADERS) $(UAVCAN_HEADERS)
	$(RULEHDR)
	$(v)$(CXX) $(CXXFLAGS) -c -emit-llvm -o $@ $< $(SLIB_INCLUDES)

$(BUILDROOT)/libraries/%.bc: $(SKETCHBOOK)/libraries/%.c
	$(RULEHDR)
	$(v)$(CC) $(CFLAGS) -c -emit-llvm -o $@ $< $(SLIB_INCLUDES)

$(BUILDROOT)/libraries/%.bc: $(SKETCHBOOK)/libraries/%.S
	$(RULEHDR)
	$(v)$(AS) $(ASFLAGS) -c -emit-llvm -o $@ $< $(SLIB_INCLUDES)
