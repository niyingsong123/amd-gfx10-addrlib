# GFX10 64KB Tiled Address Decomposition

> Research focus: functional address-generation algorithm. Exact RTL register pipeline staging is intentionally ignored.

## 1. Core model

For a tiled surface, the address should be understood as a hierarchy rather than as one monolithic expression:

```text
coordinate (x,y,z,sample)
        |
        +--> surface/block selection
        |
        +--> swizzle-pattern evaluation
        |
        +--> pipe/bank/XOR contribution
        |
        +--> byte address
```

The most useful abstraction for RTL work is to split the address into:

```text
address = macro_block_base + intra_block_offset
```

and then further decompose the intra-block offset into byte/element bits and swizzle-controlled bits.

## 2. Evidence from GFX10 AddrLib

`ConvertSwizzlePatternToEquation()` starts by expanding the compressed pattern into `ADDR_BIT_SETTING` entries. The lowest `elemLog2` address bits are direct byte-within-element bits: address bit `i` maps to X bit `i` for `i < elemLog2`. fileciteturn13file0L2-L2

For non-XOR swizzles, every remaining address bit is a direct selection from X, Y, or Z. The selected coordinate bit is recorded in `pEquation->addr[i]`. fileciteturn13file0L2-L2

For XOR swizzles, the pattern can contain multiple coordinate components in one address equation bit. AddrLib separates these into `xor1` and `xor2` terms. Higher coordinate bits outside the current block dimensions are explicitly classified as XOR inputs. fileciteturn12file0L2-L2

## 3. Important consequence

A GFX10 swizzle pattern is effectively a Boolean/XOR address equation.

For an address bit `A[i]`, the conceptual form is:

```text
A[i] = X[x_index] XOR Y[y_index] XOR Z[z_index] XOR ...
```

but not every equation bit contains every term. The exact terms are encoded by the generated `ADDR_EQUATION` structure.

This is much closer to the eventual Verilog implementation than treating AddrLib as a sequence of arithmetic operations.

## 4. Block size

GFX10 keeps explicit 3D block-dimension tables for 64KB and 4KB tiling. The 64KB table is indexed by element-size `elemLog2`; the resulting X/Y/Z logarithms determine which coordinate bits are considered intra-block bits. The source also has a separate path for thin resources, where `ComputeThinBlockDimension()` derives the block dimensions. fileciteturn12file0L2-L2

For a 64KB block:

```text
block_size = 2^16 bytes
```

Therefore, after element addressing and swizzle selection, the low 16 address bits describe the position within the 64KB tile. The exact mapping is not simply linear X/Y; GFX10's swizzle equation determines the permutation/XOR of coordinate bits.

## 5. Pipe interleave

The GFX10 global configuration selects both the number of pipes and pipe-interleave size. The implementation maps NUM_PIPES to `m_pipesLog2`, and PIPE_INTERLEAVE_SIZE to `m_pipeInterleaveLog2`. Supported interleave sizes in the inspected implementation are 256B, 512B, 1KB, and 2KB. fileciteturn9file0L2-L2

This gives a useful hardware boundary:

```text
low pipe-interleave bits
    |
    +--> determine position inside a pipe-interleave unit

higher intra-tile bits
    |
    +--> swizzle / pipe / bank / XOR equations
```

Do not assume that `pipe = address[interleave_log2 +: pipe_log2]` for every GFX10 swizzle. In XOR/tiled modes, the effective pipe contribution can be folded into the equation.

## 6. Metadata address example

The same decomposition is visible very clearly in the GFX10 DCC address path. AddrLib computes a block size, derives the block's X/Y index, evaluates a swizzle pattern for the offset, and then XORs a pipe-derived value into that offset:

```text
slice_base
+ block_index * block_size
+ (swizzled_offset XOR pipe_xor)
```

The inspected implementation computes:

```text
xb       = x / metaBlkWidth
yb       = y / metaBlkHeight
pb       = pitch / metaBlkWidth
blkIndex = yb * pb + xb
pipeXor  = ((pipeXor & pipeMask) << pipeInterleaveLog2) & blkMask
```

and finally adds the swizzled block offset and pipe XOR to the slice base. fileciteturn9file0L2-L2

This is a particularly useful template for later reverse engineering of color-surface addressing.

## 7. Next derivation step

The next step is to build a concrete equation table for one GFX10 64KB mode, for example:

```text
ADDR_SW_64KB_S_X
```

The table should have one row per address bit:

| Address bit | Source | Operation |
|---:|---|---|
| 0..elemLog2-1 | X | direct byte bits |
| ... | X/Y/Z | direct or XOR |
| ... | pipe/bank | XOR/selection |
| 16+ | macro-tile | block/slice indexing |

Once this table is extracted from `gfx10SwizzlePattern.h` and the corresponding pattern-index tables in `gfx10addrlib.cpp`, it can be translated almost mechanically into combinational Verilog.

## 8. Key research rule

Do not start from the final 64-bit address and guess bit meanings. Start from:

```text
swizzle mode
 -> pattern index
 -> swizzle pattern
 -> ADDR_EQUATION
 -> per-bit Boolean equation
 -> RTL
```

That path preserves the actual AddrLib algorithm and avoids confusing implementation-time pipeline registers with address-generation semantics.
