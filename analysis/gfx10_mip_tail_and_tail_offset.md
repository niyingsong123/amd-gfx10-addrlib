# GFX10 AddrLib：Mipmap Tail 与 `tailOffset` 深入分析

> 本文整理了两个连续问题：
>
> 1. 为什么 AMD GPU 的 addrlib 需要对 mipmap tail 做专门处理？
> 2. 以 GFX10 为例，`tailOffset` 的计算思路是什么？
>
> 本文重点放在 AddrLib 的**算法模型和地址布局逻辑**，而不是某一个具体 Mesa/AMD addrlib 版本中的逐行源码。实际源码中的函数名、条件和特定 alignment 常数可能随版本、surface 类型和 swizzle mode 而变化，因此文中的伪代码应理解为对实现逻辑的抽象。

---

## 1. 先给出核心结论

对于一个带 mipmap 的 tiled surface，整体显存布局可以抽象成：

```text
Surface Base
    |
    +-- Mip 0
    +-- Mip 1
    +-- Mip 2
    +-- ...
    +-- Last non-tail mip
    |
    +-- [alignment]
    |
    +-- Mipmap Tail
          +-- tail mip A
          +-- tail mip B
          +-- tail mip C
          +-- ...
```

其中：

```text
firstMipInTail
    = 第一个进入 mip tail 的 mip level
```

而：

```text
 tailOffset
    = mip tail 区域相对于整个 surface base 的起始 byte offset
```

因此，对一个 tail mip 的地址计算，可以抽象成：

```text
Address(level, x, y, z)
    = SurfaceBase
    + tailOffset
    + MipTailOffset(level)
    + InTailSwizzledOffset(x, y, z)
```

这里最重要的是区分三个层次：

1. `tailOffset`：整个 tail 在 surface 中从哪里开始。
2. `MipTailOffset(level)`：某个 mip 在 tail 区域内部从哪里开始。
3. `InTailSwizzledOffset(...)`：该 mip 内部某个 texel/element 的地址。

`tailOffset` 本身并不是某个像素的最终地址。

---

# 2. 为什么需要 mipmap tail？

## 2.1 如果所有 mip 都使用完整 tile，会产生巨大的空间浪费

假设一个 RGBA8 texture：

```text
4096 x 4096
4 bytes / pixel
```

其 mip chain 大致为：

```text
L0  4096 x 4096
L1  2048 x 2048
L2  1024 x 1024
L3   512 x  512
L4   256 x  256
L5   128 x  128
L6    64 x   64
L7    32 x   32
L8    16 x   16
L9     8 x    8
L10    4 x    4
L11    2 x    2
L12    1 x    1
```

对于较大的 mip，tile layout 很有价值：它可以提供二维 locality，同时结合 pipe/bank 分布提高 memory parallelism。

但当 mip 缩小之后，例如：

```text
16 x 16 x 4 bytes = 1024 bytes
```

如果每一级都强制独立占据一个较大的 tile/alignment unit，例如按 64 KiB 级别分配，那么有效数据远小于实际占用空间：

```text
actual data       ~ 1 KiB
allocated region  64 KiB
```

这会造成非常严重的 internal fragmentation。

因此需要把多个很小的 mip 聚集到一个较紧凑的区域中，这个区域就是 **mipmap tail**。

---

## 2.2 mip tail 的本质不是“换成 linear”

一个非常容易产生的误解是：

```text
normal mip  -> tiled
small mip   -> linear
```

更准确的理解是：

```text
normal mip  -> 独立的大 tile / surface layout
small mip   -> 进入共享的 tail 区域，并采用适合小尺寸资源的 tail layout
```

也就是说，**tail 首先改变的是空间组织方式和分配粒度**；这并不意味着所有底层地址 swizzle、tile 或 memory-distribution 行为都会消失。

对于 GFX10，具体的 tail address equation 仍然和所选的 swizzle mode、bpp、sample 数、surface 类型等有关。

---

# 3. 为什么不能让所有 mip 都使用 tail？

因为大 mip 的主要问题不是内部碎片，而是：

- wavefront 会并发访问大量相邻 texel；
- 需要二维 locality；
- 需要把访问分布到不同 pipe/bank；
- texture cache、L2 以及 memory controller 都需要较规则的 tile 粒度。

如果一个非常大的 mip 直接采用小 mip tail 的紧凑布局，那么可能失去大尺度 tiling 和 memory-level parallelism 带来的收益。

因此一般存在一个逻辑分界：

```text
mip 0 ... mip K-1  -> normal tiled mip
mip K ... end      -> mip tail
```

这个 `K` 就是 `firstMipInTail`。

---

# 4. `firstMipInTail` 是怎么理解的？

概念上，addrlib 会根据 mip 的尺寸和当前 surface 的 tile/layout 约束判断：

```text
当前 mip 是否已经小到值得进入 tail？
```

判断因素可能包括：

- mip width / height / depth
- bpp
- tile size
- swizzle mode
- sample count
- surface type（2D / array / 3D）
- 对齐要求

可以把它抽象成：

```cpp
for (level = 0; level < numMipLevels; ++level) {
    if (IsSmallEnoughForTail(level)) {
        firstMipInTail = level;
        break;
    }
}
```

注意：`IsSmallEnoughForTail()` 不是简单的：

```cpp
width <= 某个固定值 && height <= 某个固定值
```

真实实现还要结合具体 swizzle/tile 规则以及 alignment 约束。

---

# 5. `tailOffset` 的第一层含义：普通 mip 的结束位置

确定了：

```text
firstMipInTail = K
```

那么 mip `0 ... K-1` 属于 non-tail mip。

首先需要为它们分别计算 surface size / slice size / alignment 等。

概念上：

```text
endOfLastNonTailMip
    = size(mip0)
    + size(mip1)
    + ...
    + size(mipK-1)
```

因此第一版的 `tailOffset` 可以写成：

```text
candidateTailOffset
    = Σ size(non-tail mip)
```

但这通常还不是最终结果，因为 tail 自己也有 alignment 约束。

---

# 6. `tailOffset` 的关键：alignment

真实模型通常更接近：

```text
tailOffset
    = Align(
          endOfLastNonTailMip,
          tailAlignment
      )
```

例如概念上：

```text
endOfLastNonTailMip = 0x05523400

tailAlignment       = 0x00040000   // 256 KiB

-----------------------------------

tailOffset           = 0x05600000
```

也就是说：

```text
 tailOffset
    >= endOfLastNonTailMip
```

两者之间可能存在 padding。

这个 padding 并不是浪费的 bug，而是为了满足硬件地址布局规则，例如 tile / pipe / bank / cache / page 等约束。

---

# 7. 为什么 tail alignment 不是永远一个固定值？

因为 tail 本质上仍然是一个 GPU surface layout，而 surface layout 会受到很多因素影响：

```text
bpp
sample count
swizzle mode
tile size
pipe interleave
slice layout
surface type
```

例如 MSAA 会把 sample dimension 纳入底层布局；高 bpp 也会改变一个逻辑 texel 对应多少 byte；不同 swizzle mode 又会改变地址 equation 的 bit partition。

因此不要把：

```text
tailAlignment = 某个固定常数
```

当成 GFX10 addrlib 的普遍规律。

正确的思路是：

```text
surface parameters
        |
        v
layout requirements
        |
        v
normal mip sizes + tail requirements
        |
        v
aligned tailOffset
```

---

# 8. tail 里面为什么还需要继续做地址 swizzle？

这是另外一个非常重要的点。

可以把最终地址拆成：

```text
SurfaceBase
    +
Tile/Region Offset
    +
Mip Offset
    +
In-Mip Offset
```

对于大 mip，In-Mip Offset 通常直接体现完整的 tiled/swizzled layout。

对于 tail mip，虽然 mip 被压缩/pack 到一个共享 tail region 中，但不等于 pixel address 就变成：

```text
row * pitch + x * bytesPerPixel
```

仍可能存在：

- micro-tile / local swizzle
- Morton/Z-order 类局部布局
- pipe/bank 相关的 address bits
- 其他与 GFX10 swizzle mode 对应的 bit permutation / XOR

因此：

```text
Tail packing
```

和：

```text
Within-tail pixel swizzle
```

是两个不同概念。

---

# 9. 为什么 tail 仍然可能需要 pipe / bank XOR？

## 9.1 两者解决的问题不同

**Morton/Z-order** 主要解决的是二维空间 locality：

```text
(x, y)
   |
   v
交错 bit
   |
   v
Z-order / Morton index
```

而 **pipe/bank XOR** 主要解决的是 memory parallelism：

```text
address bits
    |
    +--> pipe select
    |
    +--> bank select
```

因此：

```text
Morton != pipe/bank XOR
```

也就是说，即使 tail 内部采用一种紧凑的二维 packing，底层 address equation 仍然可能需要保留影响 pipe/bank 选择的 bit。

---

## 9.2 为什么小 mip 也有必要保持 memory distribution？

假设一个小 mip：

```text
16 x 16
```

它在单次 shader 访问中的数据量确实很小，但在一个大型 wavefront / 大量像素同时做纹理采样时，可能出现大量并发请求集中访问这个 mip。

如果 tail 完全去掉 memory-distribution 相关的 address 规则，那么大量请求可能更容易形成：

```text
很多 request
      |
      v
同一个 pipe / bank
      |
      v
memory contention
```

因此，**tail 优化的目标是降低空间浪费，并不是简单地取消所有底层的 memory organization 机制。**

---

# 10. tail 内部 mip 的 offset 是怎么理解的？

确定：

```text
tailOffset
```

之后，还要知道：

```text
mip K 在 tail 内部的位置
mip K+1 在 tail 内部的位置
mip K+2 在 tail 内部的位置
...
```

定义：

```text
MipTailOffset[level]
```

于是：

```text
mip K address base
    = tailOffset + MipTailOffset[K]
```

注意：

```text
MipTailOffset[K]
```

不应该简单理解为：

```text
sum(previous mip's raw byte size)
```

因为每一个 mip 的尺寸、对齐、tile footprint 以及 tail packing 规则都会影响它在 tail 中的位置。

---

# 11. 一个抽象的 tail packing 例子

假设：

```text
Mip 6: 64 x 64
Mip 7: 32 x 32
Mip 8: 16 x 16
Mip 9:  8 x  8
Mip10:  4 x  4
Mip11:  2 x  2
Mip12:  1 x  1
```

不应该理解成：

```text
+--------+
| Mip 6  |
+--------+
| Mip 7  |
+--------+
| Mip 8  |
+--------+
| Mip 9  |
+--------+
...
```

更适合用“在一个 tail region 中进行受约束的 packing”来理解：

```text
+----------------------------+
|            Mip 6           |
|                            |
+---------------+------------+
|     Mip 7     |   Mip 8    |
+-------+-------+------+-----+
| Mip 9 | Mip10 | Mip11| ... |
+-------+-------+------+-----+
```

上图只是概念示意，并不表示某个 GFX10 swizzle mode 的固定几何尺寸。

真实 addrlib 会根据具体 surface 参数计算每一级的 tail placement。

---

# 12. 概念化的 GFX10 `ComputeMipTail` 流程

可以把源码逻辑抽象成以下步骤：

```cpp
// 1. 先确定哪些 mip 是 normal mip
firstMipInTail = FindFirstMipInTail(surfaceDesc);

// 2. 先算完所有 non-tail mip 的布局
for (level = 0; level < firstMipInTail; ++level) {
    mip[level] = ComputeNormalMipLayout(level);
}

// 3. normal mip 结束位置
endOfNonTail = ComputeEndOfNonTailMips();

// 4. 对齐到 tail 要求的边界
tailOffset = Align(endOfNonTail, tailAlignment);

// 5. 在 tail 区域内部给每个 mip 分配位置
for (level = firstMipInTail; level < numMipLevels; ++level) {
    mip[level].tailOffset =
        ComputeTailMipOffset(level, tailLayout);
}
```

于是最终地址：

```cpp
if (level < firstMipInTail) {
    address = SurfaceBase
            + mip[level].offset
            + ComputeNormalMipAddress(x, y, z);
} else {
    address = SurfaceBase
            + tailOffset
            + mip[level].tailOffset
            + ComputeTailMipAddress(x, y, z);
}
```

这是理解源码最重要的抽象模型。

---

# 13. `tailOffset` 与 `MipTailOffset` 必须分开看

这是分析 addrlib 时非常容易搞混的一点。

### `tailOffset`

回答：

> **整个 mip tail 在 surface 中从哪里开始？**

它的单位通常是 byte offset。

### `MipTailOffset[level]`

回答：

> **某一级 tail mip 在 tail 内部从哪里开始？**

### `InTailSwizzledOffset(x,y,z)`

回答：

> **这个 mip 内某个坐标对应 tail 内部的哪个 byte？**

因此：

```text
surface base
      |
      +--> tailOffset
               |
               +--> mipTailOffset[level]
                         |
                         +--> swizzled pixel offset
```

如果把三者混在一起，就很容易误认为 `tailOffset` 就等于某个 mip 的地址。

---

# 14. 2D、Array、3D surface 为什么又会让问题变复杂？

因为 mip 的布局不仅有：

```text
width x height
```

还可能有：

```text
width x height x depth
```

或者：

```text
width x height x arraySlices
```

于是 tail 还需要考虑：

- slice pitch / slice size
- depth slice packing
- array slice layout
- 每一级 mip 对 depth 的缩减方式
- tail 是否跨 slice 共享/组织

因此对于一个 3D texture，不应该直接套用 2D texture 的：

```text
mipSize = width * height * bpp
```

这种过于简单的模型。

---

# 15. 为什么 addrlib 要单独计算 mip tail，而不是统一处理？

因为正常 mip 与 tail mip 的地址 equation 在“组织粒度”上已经发生了变化。

软件必须向硬件提供一组一致的信息，使得硬件在知道：

```text
base address
mip level
x/y/z
swizzle/tile information
```

以后，可以得到正确地址。

因此 addrlib 需要明确保存类似：

```text
firstMipInTail
 tailOffset
 tailSize
 mipTailOffset[level]
```

这也是为什么在源码里经常会看到：

```text
normal mip calculation
```

和：

```text
mip-tail calculation
```

是两个独立逻辑分支。

---

# 16. 与 DCC / HTILE tail 的关系

需要明确：

**Color surface 的 mip tail、DCC metadata 的 mip tail、HTILE 的 mip tail，不是同一个 layout。**

它们只是都存在“mipmap 很小时需要重新组织空间”的现象。

### Color mip tail

存放真实的：

```text
pixel / texel data
```

核心目标：

```text
texture sampling
+
locality
+
memory bandwidth
+
较低的空间浪费
```

### DCC tail

存放的是：

```text
color compression metadata
```

访问者主要是 render/compression 相关硬件，而不是普通 texture sampler。

因此 DCC 的：

```text
block size
metadata granularity
alignment
mip packing
```

都应该单独计算。

### HTILE tail

HTILE 是 depth hierarchy / depth compression 相关 metadata，layout 又围绕 depth tile 和 hierarchical depth access 来组织。

因此不能把：

```text
Color tail algorithm
```

直接复制给：

```text
DCC
HTILE
```

---

# 17. 从源码分析角度，建议关注哪些变量

当后续真正阅读 GFX10 addrlib 源码时，可以重点追踪以下几类变量：

```text
firstMipInTail
mipTailOffset
mipTailSize
tailOffset
sliceSize
surfSize
baseAlign
pipeInterleaveBytes
numPipes
bankBits
macroTileAspect
tileSplitBytes
```

不要只问“这个变量算出了多少”，更重要的是问：

```text
这个变量最终控制了 address equation 的哪几个 bit？
```

例如：

```text
alignment
    -> 决定低位哪些 bit 必须为 0

pipe selection
    -> 决定某些 address bit 如何映射到 pipe

bank selection
    -> 决定某些 address bit 如何映射到 bank

mip tail offset
    -> 决定 mip level 在 tail region 中的基地址
```

这比单纯逐行翻译源码更容易建立完整模型。

---

# 18. 一个更准确的整体模型

把 GFX10 mip layout 抽象成：

```text
                 Surface
                    |
          +---------+---------+
          |                   |
     Normal Mips          Mip Tail
          |                   |
   +------+------+      +-----+----------+
   |      |      |      |     |     |    |
  Mip0   Mip1   ...    MipK  MipK+1 ... End
   |      |      |      |     |     |    |
 tile   tile   tile    tail  tail  tail  tail
 layout layout layout  layout layout layout
   |      |      |      |     |     |    |
   +------+------+- ... +-----+-----+----+
                    |
                 Address
```

所以，从 addrlib 的角度：

```text
Surface layout
    = normal mip layout
    + mip tail layout
    + alignment rules
    + slice/depth rules
    + swizzle/address-equation rules
```

---

# 19. 最终结论

## 为什么需要 mip tail？

因为 mip 越小，如果继续采用完整 tile / 独立 alignment 粒度，internal fragmentation 会快速增加。把多个小 mip 组织进一个共享 tail 区域，可以显著提高显存利用率，同时仍然保留适合 GPU 访问的局部性和地址组织方式。

## `tailOffset` 是什么？

它是：

```text
mip tail 相对于 surface base 的起始 byte offset
```

概念上：

```text
tailOffset
    = Align(
        endOfLastNonTailMip,
        tailAlignment
      )
```

## tail 内部的 mip 又是什么？

每个 mip 还要有自己的：

```text
MipTailOffset[level]
```

然后在该 mip 内再计算具体 texel 的 swizzled offset。

所以完整地址模型是：

```text
Address
 = SurfaceBase
 + tailOffset
 + MipTailOffset[level]
 + InTailSwizzledOffset(x,y,z)
```

**真正分析 GFX10 addrlib 源码时，最关键的不是把 `tailOffset` 当成一个孤立的变量，而是把它放回 `firstMipInTail → non-tail mip sizes → tail alignment → tail packing → per-mip offset → pixel swizzle` 这整条数据流里。**

---

## 20. 后续源码级分析建议

下一步如果要继续深入 GFX10 addrlib，最值得直接跟踪的是：

```text
HwlComputeSurfaceInfo()
        |
        +--> normal mip layout
        |
        +--> first mip in tail
        |
        +--> ComputeMipTail / related tail logic
        |
        +--> per-mip offset
        |
        +--> surface size / alignment
```

然后再把源码中的每一个：

```text
shift
mask
alignment
XOR
```

映射到：

```text
address bit [N:M]
```

最终才能把 addrlib 软件代码和 GFX10 硬件 address equation 真正对应起来。
