# Upstream AddrLib

## Snapshot policy

This directory is intended to hold a source snapshot of Mesa's AMD AddrLib, with emphasis on GFX10.

As of 2026-09-06, the target upstream release for this research repository is **Mesa 26.2.2**. The repository should distinguish the exact upstream release being studied from any GitHub mirror used only for source inspection.

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

## Source-inspection provenance

Some detailed source inspection during development may use a GitHub mirror when the canonical Mesa GitLab tree is inconvenient to retrieve programmatically. Such a mirror is **not** treated as the authoritative version. Every analysis document should record the exact upstream release/commit when possible.
