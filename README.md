# AMD GFX10 AddrLib Research

A dedicated research repository for AMD GFX10 AddrLib.

## Goals

- Preserve upstream Mesa AddrLib source for GFX10 reference.
- Reverse-engineer GFX10 address, swizzle, pipe, bank and XOR calculations.
- Translate relevant algorithms into hardware-oriented equations and Verilog.
- Build small, reproducible tests to compare the RTL-oriented model against the upstream implementation.

## Upstream

The initial upstream snapshot will track the latest Mesa release used for this research. The upstream source and version will be recorded explicitly in the repository.

## Research structure

- `upstream/` — upstream AddrLib source snapshot
- `analysis/` — algorithm and mathematical analysis
- `verilog/` — register-pipeline-independent RTL-oriented implementations
- `tests/` — verification and comparison tests
- `docs/` — architecture and research notes

## Research principle

The main focus is the **algorithm**, not the exact register-pipeline staging. Register boundaries may therefore be removed or reorganized when producing the RTL-oriented model, while preserving the functional calculation.
