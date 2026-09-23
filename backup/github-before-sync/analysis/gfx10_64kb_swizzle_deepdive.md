# GFX10 64KB XOR Swizzle Deep Dive

> Research note. Focus is the functional address-generation algorithm, not RTL register-pipeline staging.
>
> Source inspected: AMD-BC-250/mesa mirror commit `01607e57af2d0b57e08a38f01980b23c6aeffccd` for `src/amd/addrlib/src/gfx10/gfx10addrlib.cpp` and `gfx10SwizzlePattern.h`. This mirror is used for source inspection and must not be assumed identical to Mesa 26.2.2 until the exact tag is verified.

## 1. Why this document exists

The main research path is:

```text
swizzle mode
  -> PATINFO
  -> compressed nibble pattern
  -> full ADDR_BIT_SETTING pattern
  -> ConvertSwizzlePatternToEquation()
  -> ADDR_EQUATION
  -> per-address-bit Boolean/XOR equations
  -> hardware/Verilog model
```

This is the most reliable way to understand GFX10 tiling instead of guessing address-bit meanings from final addresses.

## 2. 64KB_S_X is an XOR swizzle

`Gfx10Lib::SwizzleModeTable` marks `ADDR_SW_64KB_S_X` as a 64KB, standard, XOR swizzle. The same table distinguishes it from `ADDR_SW_64KB_S` and `ADDR_SW_64KB_D`.

The source selects `GFX10_SW_64K_S_X_PATINFO` for `ADDR_SW_64KB_S_X`, or `GFX10_SW_64K_S_X_RBPLUS_PATINFO` when RB+ is enabled.

Therefore RB+ and non-RB+ must be analyzed separately.

## 3. PATINFO is not the equation itself

`ADDR_SW_PATINFO` contains:

```text
maxItemCount
nibble01Idx
nibble2Idx
nibble3Idx
nibble4Idx
```

`gfx10SwizzlePattern.h` stores these indices in mode-specific tables. The pattern is reconstructed by copying the corresponding nibble arrays into a full `ADDR_BIT_SETTING[]` array.

`ADDR_BIT_SETTING` has four coordinate components:

```text
x, y, z, s
```

and a packed `value` field.

A single pattern entry can therefore represent more than one coordinate component. That is the key reason XOR modes cannot be reduced to a simple X/Y bit permutation.

## 4. First address bits are element-byte bits

`ConvertSwizzlePatternToEquation()` initializes the first `elemLog2` equation bits directly from X:

```text
for i = 0 .. elemLog2-1:
    addr[i] = X[i]
```

Thus for 4 BPE (`elemLog2 = 2`):

```text
A0 = X0
A1 = X1
```

For 8 BPE (`elemLog2 = 3`):

```text
A0 = X0
A1 = X1
A2 = X2
```

This is the byte offset inside one element.

## 5. Non-XOR versus XOR

For non-XOR swizzles, each remaining pattern entry is required to be a power of two. It maps directly to one X/Y/Z coordinate bit.

Conceptually:

```text
A[i] = X[k]
A[i] = Y[k]
A[i] = Z[k]
```

For XOR swizzles, an entry may contain multiple coordinate components. AddrLib decomposes these into `addr[i]`, `xor1[i]`, and `xor2[i]`.

The useful hardware abstraction is therefore:

```text
A[i] = direct_term XOR xor_term_1 XOR xor_term_2
```

where every term is a single coordinate bit such as X[k], Y[k], or Z[k].

## 6. Important constraint: XOR is bit-level

During decomposition, the source checks `IsPow2(x)`, `IsPow2(y)`, and `IsPow2(z)` before accepting a component.

Therefore an individual selected component is one coordinate bit, not an arbitrary multi-bit field.

This gives a clean RTL interpretation:

```verilog
addr[i] = x[x_idx] ^ y[y_idx] ^ z[z_idx];
```

with unused terms omitted.

## 7. Pipe-interleave boundary

The XOR conversion uses:

```text
pipeIntMask = (1 << m_pipeInterleaveLog2) - 1
blockMask   = (1 << blockSizeLog2) - 1
```

and asserts:

```text
(bMask & pipeIntMask) == pipeIntMask
```

The subsequent unresolved-equation loop starts at:

```text
m_pipeInterleaveLog2
```

This shows that the pipe-interleave region is a structural boundary in equation construction. It is unsafe to assume that all GFX10 pipe selection can be represented by simply slicing a final address bus.

## 8. Mask-driven equation resolution

The converter maintains masks for already-consumed coordinate bits:

```text
xMask
 yMask
 zMask
 bMask
```

When a pattern entry is a single coordinate bit, AddrLib records it as a direct address equation and adds that coordinate bit to the appropriate mask.

When an entry contains multiple components, the components already represented by the current masks are extracted and placed into XOR slots.

The process continues until:

```text
bMask == blockMask
```

and final assertions verify that the required X/Y/Z block bits have been consumed.

This is effectively a constrained decomposition of the compressed swizzle pattern into a set of one-bit Boolean equations.

## 9. 64KB block dimensions

GFX10 contains explicit 3D block-size tables. For 64KB resources the inspected table is:

```text
Block64K_Log2_3d =
    { {6,5,5},
      {5,5,5},
      {5,5,4},
      {5,4,4},
      {4,4,4} }
```

The exact row selected depends on element size/resource configuration.

For thin resources, the implementation can instead derive dimensions with `ComputeThinBlockDimension()`.

The important invariant is:

```text
2^(Xlog2 + Ylog2 + Zlog2) * element_size
    = 64KB
```

when expressed in the appropriate element/block coordinate representation.

## 10. S_X versus D_X versus Z_X

GFX10 has distinct XOR swizzle modes:

```text
ADDR_SW_4KB_S_X
ADDR_SW_4KB_D_X
ADDR_SW_4KB_R_X
ADDR_SW_64KB_Z_X
ADDR_SW_64KB_S_X
ADDR_SW_64KB_D_X
ADDR_SW_64KB_R_X
ADDR_SW_VAR_Z_X
ADDR_SW_VAR_R_X
```

The mode flags show that S/D/Z/R are not cosmetic names; they select different addressing behavior and/or pattern tables.

For the current investigation, start with 2D `64KB_S_X`, non-RB+.

## 11. Why PATINFO tables depend on pipe count and BPE

The pattern tables are indexed by combinations of pipe count and bytes-per-element. The inspected 64KB pattern tables contain entries for:

```text
1, 2, 4, 8, 16, 32, 64 pipes
```

and:

```text
1, 2, 4, 8, 16 BPE
```

Consequently, there is no single universal 64KB_S_X equation table. The actual equation depends on configuration.

This is especially important for RTL: the final implementation should either parameterize the equation generator or select from pre-derived equation tables according to the hardware configuration.

## 12. Current verified conceptual equation

For any address bit inside the tile:

```text
A[i] = direct(i) XOR xor1(i) XOR xor2(i)
```

where each term is one of:

```text
X[k], Y[k], Z[k]
```

The first `elemLog2` bits are:

```text
A[i] = X[i]
```

The remaining bits are derived from the swizzle pattern and the block masks.

## 13. What still needs exact extraction

The next task is not to speculate. It is to extract the exact table for one concrete configuration:

```text
resource = 2D
swizzle  = ADDR_SW_64KB_S_X
RB+      = disabled
BPE      = 4
pipes    = 4
```

Then resolve:

```text
PATINFO index
 -> nibble01Idx/nibble2Idx/nibble3Idx/nibble4Idx
 -> complete pattern entries
 -> ADDR_EQUATION[0..15]
```

The final deliverable should be a table of the form:

| Address bit | Direct | XOR1 | XOR2 | Boolean equation |
|---:|---|---|---|---|
| 0 | X0 | - | - | X0 |
| 1 | X1 | - | - | X1 |
| ... | ... | ... | ... | ... |
| 15 | ... | ... | ... | ... |

Only after that should the result be translated into Verilog.

## 14. Current research caution

Do not confuse these three layers:

```text
coordinate -> swizzle equation -> tile-local address
```

and:

```text
tile-local address -> pipe/bank/channel placement -> physical address
```

They are related, but not identical. In particular, XOR swizzle equations can encode information that would otherwise be described as pipe/bank/XOR selection.

Also do not treat a source mirror commit as the Mesa 26.2.2 canonical source until the exact tag/commit has been verified.

## 15. Research roadmap

1. Locate exact `GFX10_SW_64K_S_X_PATINFO` entries.
2. Identify the pattern indices for 4 pipes / 4 BPE.
3. Extract the corresponding nibble arrays.
4. Reconstruct the complete `ADDR_BIT_SETTING[]` pattern.
5. Execute `ConvertSwizzlePatternToEquation()` manually for that configuration.
6. Produce A0-A15 equations.
7. Validate the equations against representative coordinates.
8. Translate to combinational Verilog.
9. Compare against upstream AddrLib behavior.
10. Repeat for D_X, Z_X, R_X and RB+.

## 16. Fixed-source audit (2026-09-08)

This note has now been cross-checked against [AMD PAL GFX10 at c5e800072a32f68b6ccc4422936d96167c6e0728](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp). This does not establish equivalence to a Mesa release. PI must be 256B in this implementation, despite decoder cases for larger values ([assertion](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L854)).

In sections 4/12, X is the equation's byte coordinate, not unscaled texel x: the caller supplies x << elemLog2 ([caller](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L4798)). Thus A0/A1 for 4BPE are byte-within-element positions, normally zero for an element base address. Pipe/bank layout terms are not a full model of external DRAM topology. The detailed per-bit extraction in the roadmap remains planned work, not a completed validation.
