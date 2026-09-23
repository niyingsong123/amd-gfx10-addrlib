# AddrLib Analysis

Start with the [GFX10/GFX11/GFX12 per-section audit](addrlib_version_audit.md). The supplied pseudo-RTL is primarily GFX12 in mode/alignment policy; the GFX10 background notes are not proof of its provenance.

- [Mip parameters and units](mip_tail_gfx10_analysis.md)
- [GFX10 tail memory layout](gfx10_mip_tail_and_tail_offset.md)
- [GFX12 arithmetic examples](three_address_calculation_examples.md)
- [GFX10 introduction](gfx10_addrlib_深入浅出总览.md)
- [GFX10 64KB decomposition](gfx10_64kb.md)
- [GFX10 XOR details](gfx10_64kb_swizzle_deepdive.md)
- [Arithmetic checks](verify_version_audit.ps1)

Fixed-source provenance: [upstream/README.md](../upstream/README.md). Claims of full RTL or full driver validation are outside the current results.
