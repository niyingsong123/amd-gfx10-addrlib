# Upstream AddrLib

## Snapshot policy

This directory is intended to hold a source snapshot of Mesa's AMD AddrLib, with emphasis on GFX10.

As of 2026-09-06, Mesa 26.1.8 is the newest Mesa version identified during this repository setup. The 26.1.8 debug-source package contains the expected AddrLib GFX10 sources, including `gfx10addrlib.cpp`, `gfx10addrlib.h`, and `gfx10SwizzlePattern.h`.

The upstream project is Mesa at:

https://gitlab.freedesktop.org/mesa/mesa

The source files use AMD's MIT license header. Copyright notices must be preserved in any copied source.

## GFX10 core files

Expected source set:

- `src/amd/addrlib/inc/addrinterface.h`
- `src/amd/addrlib/inc/addrtypes.h`
- `src/amd/addrlib/src/addrinterface.cpp`
- `src/amd/addrlib/src/amdgpu_asic_addr.h`
- `src/amd/addrlib/src/core/addrcommon.h`
- `src/amd/addrlib/src/core/addrlib.cpp`
- `src/amd/addrlib/src/core/addrlib.h`
- `src/amd/addrlib/src/core/addrlib1.cpp`
- `src/amd/addrlib/src/core/addrlib1.h`
- `src/amd/addrlib/src/core/addrlib2.cpp`
- `src/amd/addrlib/src/core/addrlib2.h`
- `src/amd/addrlib/src/core/addrlib3.cpp`
- `src/amd/addrlib/src/core/addrlib3.h`
- `src/amd/addrlib/src/core/addrobject.cpp`
- `src/amd/addrlib/src/core/addrobject.h`
- `src/amd/addrlib/src/core/addrswizzler.cpp`
- `src/amd/addrlib/src/core/addrswizzler.h`
- `src/amd/addrlib/src/core/coord.cpp`
- `src/amd/addrlib/src/core/coord.h`
- `src/amd/addrlib/src/gfx10/gfx10addrlib.cpp`
- `src/amd/addrlib/src/gfx10/gfx10addrlib.h`
- `src/amd/addrlib/src/gfx10/gfx10SwizzlePattern.h`
- `src/amd/addrlib/src/chip/gfx10/gfx10_gb_reg.h`

## Important note

The upstream source is intentionally tracked separately from our derived analysis and RTL-oriented implementation. We should not modify the upstream snapshot when deriving algorithms; changes belong under `analysis/` or `verilog/`.
