# Upstream provenance

## Fixed reference used in the 2026-09-08 audit

AMD official repository: GPUOpen-Drivers/pal.
Commit: c5e800072a32f68b6ccc4422936d96167c6e0728 (2025-04-29).
AddrLib root: [src/core/imported/addrlib](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/).

Compared files:

- GFX10 gfx10addrlib.cpp and gfx10addrlib.h
- GFX11 gfx11addrlib.cpp and gfx11addrlib.h
- GFX12 gfx12addrlib.cpp, gfx12addrlib.h and gfx12SwizzlePattern.h
- GFX12 shared/addr_shared.cpp and addr_shared.h
- core/addrlib2.cpp/.h and addrlib3.cpp/.h
- inc/addrtypes.h

The GFX12 shared and non-shared code paths were both inspected. The audit links to immutable source lines and distinguishes shared formulas from generation-specific modes.

## Repository state and prior Mesa target

This directory contains documentation only, not a checked-in upstream source snapshot. Earlier notes named Mesa 26.2.2 as a target, but this repository does not contain the matching tag/commit evidence or snapshot. That target must not be represented as a verified source baseline. The current audit does not establish that the AMD PAL files are byte-identical to a Mesa release, nor does it identify the exact private RTL revision of ADDRLIB.md.

Mesa's canonical project remains [mesa/mesa](https://gitlab.freedesktop.org/mesa/mesa). A future Mesa comparison should pin and record an actual commit, rather than infer a release from a mirror.

AMD source license headers must be retained if a future source snapshot is added. Derived corrections belong in analysis documents, not silent edits to upstream code or the preserved user excerpt.
