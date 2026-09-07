# GFX10 AddrLib MipTail RTL Analysis

> 本文整理此前针对用户提供的 GFX10 AddrLib RTL 抽取代码中，关于 mipmap / mip tail 后半部分计算的分析。
>
> 分析重点不是 RTL pipeline/register staging，而是恢复其算法意图，并与公开的 AMD GFX10 AddrLib 概念进行对应。

## 1. GFX10 MipTail 的总体模型

一个 texture 的 mip chain 可以理解为：

```text
Mip0
Mip1
Mip2
...
MipN
```

随着 mip level 增大，尺寸逐渐缩小。GFX10 不会让所有小 mip 都分别按照完整独立 surface tile 保存，而是在足够小时把若干个小 mip 集中放进一个 mip tail。

```text
large mip levels                 mip tail
-----------------          --------------------
Mip0                         MipK
Mip1                         MipK+1
Mip2                         MipK+2
...                          ...
MipK-1                       MipN
```

公开 GFX10 AddrLib 中存在与此直接对应的概念，例如：

- `GetMaxNumMipsInTail()`：一个 tail 最多可容纳多少级 mip
- `IsInMipTail()`：判断某一级 mip 是否满足进入 tail 的条件
- `firstMipIdInTail`：第一个进入 mip tail 的 mip level

公开 GFX10 AddrLib 的 `IsInMipTail()` 思路可以概括为：

```text
mipWidth  <= mipTailDim.w
mipHeight <= mipTailDim.h
numMipsToTheEnd <= maxNumMipsInTail
```

这与 RTL 中 `in_miptail`、`in_tail_chk`、`num_mips_in_tail` 的组合关系高度对应。

---

## 2. `l2_mip_offset`：不是 mip level offset，而是 256B granularity conversion

RTL：

```verilog
l2_mip_offset = (l2_ms < 5'd8) ? 5'd0 : l2_ms - 5'd8
```

这里的 `l2_ms` 表示：

```text
log2(block_size_bytes)
```

因为：

```text
256B = 2^8 bytes
```

所以：

```text
l2_mip_offset = max(l2_ms - 8, 0)
```

例如：

| Block | `l2_ms` | `l2_mip_offset` |
|---|---:|---:|
|128B|7|0|
|256B|8|0|
|4KB|12|4|
|64KB|16|8|
|256KB|18|10|

因此它表达的是：

> 一个较大的 block 相对于 256B 基本粒度要放大多少倍。

后面的：

```verilog
mip_offset_b_out = mip_offset_in_blks << l2_mip_offset;
```

可理解为把一个以 256B/block 为基础的 offset 转换到当前 block size 的地址尺度。

---

## 3. `l2_ms_256B`：把 block size 转换成以 256B 为基准的指数

RTL：

```verilog
l2_ms_256B = (l2_ms_128B == 'd0) ? 'd0 : (l2_ms_128B - 1)
```

结合前面的 block size 表，可以理解成：

```text
l2_ms_256B = log2(block_size / 256B)
```

例如：

### 64KB

```text
64KB / 256B = 256 = 2^8
```

所以：

```text
l2_ms_256B = 8
```

### 256KB

```text
256KB / 256B = 1024 = 2^10
```

所以：

```text
l2_ms_256B = 10
```

这样做的目的，是给后面的 `num_mips_in_tail` 提供统一的 block-size 参数。

---

## 4. 为什么 3D texture 要有 `l2_ms_256B_3d`

RTL：

```verilog
is_3d_blk_size = (sw_type == `SW_S_3D)

case(l2_ms_256B)
    4'd4:  l2_ms_256B_3d = 4'd3
    4'd8:  l2_ms_256B_3d = 4'd6
    4'd12: l2_ms_256B_3d = 4'd7
endcase

l2_ms_256B_eff = (is_3d_blk_size) ? l2_ms_256B_3d : l2_ms_256B
```

算法意图是：

> 2D 和 3D texture 的 mip 尺寸缩小规律不同，因此不能直接使用同一个 tail capacity 参数。

2D mip：

```text
W x H
```

每降低一级，通常近似变成：

```text
W/2 x H/2
```

面积约缩小到 1/4。

3D mip：

```text
W x H x D
```

每降低一级，近似变成：

```text
W/2 x H/2 x D/2
```

体积约缩小到 1/8。

因此 RTL 对 3D block size 做了专门的 effective correction，然后统一送到 `num_mips_in_tail`。

公开 GFX10 AddrLib 也确实区分 3D texture 的 thin/thick 组织，而不是简单复用 2D 规则。

> 注意：你给出的 RTL 是抽取/整理后的版本，`case` 中一些中间值的精确编码还需要结合完整 `blk_type` 定义才能完全恢复；这里解释的是算法意图，而不是对每个编码值做无条件假设。

---

## 5. `num_mips_in_tail`：tail 最大容量

RTL：

```verilog
case (l2_ms_256B_eff)
    4'd0:
        num_mips_in_tail = 'd1

    4'd3:
        num_mips_in_tail = 'd5

    4'd4, 4'd6, 4'd7, 4'd8,
    4'd9, 4'd10, 4'd11, 4'd12:
        num_mips_in_tail = l2_ms_256B_eff + 4'd4
endcase
```

这个变量最核心的含义是：

> 一个 mip tail 最多可以容纳多少个 mip level。

它对应公开 GFX10 AddrLib 的：

```text
GetMaxNumMipsInTail(...)
```

因此这里先不是判断“某一级 mip 是否进入 tail”，而是在计算一个**capacity upper bound**：

```text
block size
   ↓
maximum number of mip levels that tail can accommodate
```

---

## 6. 为什么需要 `mips_outside_tail`

RTL：

```verilog
mips_outside_tail = (maxmip_in - mips_in_tail)
```

例如：

```text
maxmip_in = 11
mips_in_tail = 6
```

则：

```text
mips_outside_tail = 5
```

于是可以理解成：

```text
Mip0 ~ Mip5   outside tail
Mip6 ~ Mip11  tail candidates
```

所以：

> `mips_outside_tail` 表示 tail 前面需要保留在独立 surface layout 中的 mip 数量/边界。

---

## 7. 为什么 `mips_outside_tail` 要多留一位

注释明确写：

```text
extra bit to allow for negative result
```

这是因为可能出现：

```text
maxmip_in < mips_in_tail
```

例如：

```text
maxmip_in = 5
mips_in_tail = 12
```

数学结果：

```text
5 - 12 = -7
```

负值的真正意义是：

> 整条 mip chain 本身还没有长到足以填满 tail 的最大容量，因此所有 mip 都可以被视作 tail 中的候选。

RTL 因此故意保留额外 bit，以便后面的 `in_tail_chk` 正确处理这种情况。

---

## 8. `in_tail_chk[m]`：只检查“tail 数量限制”

RTL：

```verilog
assign in_tail_chk[m] = ((m > mips_outside_tail) | mips_outside_tail)
```

这里需要拆成两种情况。

### 情况 A：`mips_outside_tail >= 0`

它等价于：

```text
m > mips_outside_tail
```

也就是说：

```text
mip <= outside boundary
    => 不允许进入 tail

mip > outside boundary
    => 满足“tail 数量容量”这一条件
```

### 情况 B：`mips_outside_tail < 0`

表示 tail 最大容量大于整个 mip chain 的长度。

这时该条件应让所有 mip 通过。

因此 `in_tail_chk[m]` 实际对应公开 AddrLib `IsInMipTail()` 中的：

```text
numMipsToTheEnd <= maxNumMipsInTail
```

这一部分只负责“距离 mip chain 末尾还有多少级”这个条件。

它还不能单独决定一个 mip 是否进入 tail，因为还需要结合 mip 的实际尺寸。

---

## 9. `pad_to_log2sz_gc()`：先得到 block-aligned mip0 尺寸

RTL：

```verilog
function pad_to_log2sz_gc
(
    input dim_in,
    input l2_pad_sz_in,
    output pad_out
)
```

内部：

```verilog
pad_sz_mask = (1'b1 << l2_pad_sz_in) - 1'b1

pad_out = (dim_in >> l2_pad_sz_in) +
          |(dim_in & pad_sz_mask)
```

这实际上是在做：

```text
ceil(dim_in / 2^l2_pad_sz_in)
```

也可以理解为：

> 求输入尺寸需要多少个 block，并且不足一个完整 block 的部分向上取整。

例如：

```text
W = 13 elements
block width = 8 elements
```

那么：

```text
13 / 8 = 1.625
```

需要：

```text
2 blocks
```

RTL：

```text
13 >> 3 = 1
```

低 3 bit 为：

```text
101
```

存在 1，因此：

```text
1 + 1 = 2
```

所以：

```text
Wb0 = ceil(W0 / blockWidth)
```

这一步非常重要，因为后面 `Wb[m]`、`Hb[m]` 都是在它的基础上做 mip 缩小。

---

## 10. `Wb0 / Hb0 / Wb_slice0`

RTL：

```verilog
Wb0        = pad_to_log2sz_gc(map0_w, l2_blk_w)
Hb0        = pad_to_log2sz_gc(map0_h, l2_blk_h)
Wb_slice0  = pad_to_log2sz_gc(map0_w, l2_blk_w_slice)
```

这里得到的是：

```text
Wb0        = mip0 在普通 block 宽度下需要多少 block
Hb0        = mip0 在 block 高度方向需要多少 block
Wb_slice0  = mip0 在 slice-size 计算使用的 width granularity 下需要多少 block
```

为什么 `Wb_slice0` 和 `Wb0` 不完全一样？

因为前面 RTL 对 linear case 有额外的 256B slice alignment 规则。也就是说：

```text
address/pitch layout 的 block width
```
和
```text
slice size 统计的最小 granularity
```
不是完全相同的概念。

---

## 11. 每一级 mip 的 `Wb[m] / Hb[m]`

RTL：

```verilog
Wb[m] = (Wb0 >> m) + |Wb0[`PAD_W_MSB(m):0]
Hb[m] = (Hb0 >> m) + |Hb0[`PAD_H_MSB(m):0]
Wb_slice[m] = (Wb_slice0 >> m) + |Wb_slice0[`PAD_W_MSB(m):0]
```

数学上就是：

```text
Wb[m]       = ceil(Wb0 / 2^m)
Hb[m]       = ceil(Hb0 / 2^m)
Wb_slice[m] = ceil(Wb_slice0 / 2^m)
```

公开 GFX10 AddrLib 中也存在对应的 `GetMipSize()` / `ShiftCeil()` 思路。

例如：

```text
Wb0 = 13
m = 2
```

则：

```text
13 >> 2 = 3
```

低两位：

```text
01
```

存在 1，因此：

```text
Wb[2] = 3 + 1 = 4
```

恰好：

```text
ceil(13 / 4) = 4
```

---

## 12. `in_miptail`：真正判断 mip 是否进入 tail

RTL：

```verilog
w_tail_sz = y_bias ? pad_sz_w : (pad_sz_w >> 1)
h_tail_sz = y_bias ? (pad_sz_h >> 1) : pad_sz_h

in_miptail = (H <= h_tail_sz) &
             (W <= w_tail_sz) &
             in_tail_chk
```

这是整个 mip-tail 判定的核心。

它要求三个条件同时满足：

```text
1. mip width 足够小
2. mip height 足够小
3. 从 mip-chain 末端反向数，剩余 mip 数量没有超过 tail capacity
```

可以直接和 GFX10 AddrLib 的判断对应起来：

```text
mip width  <= mipTailDim.w
mip height <= mipTailDim.h
numMipsToTheEnd <= maxNumMipsInTail
```

因此这里非常重要：

> **mip tail 不是“尺寸小了就一定进入”。**
>
> 它同时受“尺寸条件”和“tail 最大 mip 数”限制。

---

## 13. 为什么 `w_tail_sz / h_tail_sz` 有两个方向

普通情况：

```text
width  <= block_width / 2
height <= block_height
```

即：

```text
Wb <= 1
Hb <= 2
```

`y_bias` 情况：

```text
width  <= block_width
height <= block_height / 2
```

即：

```text
Wb <= 2
Hb <= 1
```

这说明 GFX10 的 tail packing 并不是简单的一个固定正方形区域，而存在不同的二维 orientation。

RTL 中：

```verilog
y_bias_intail = (sw_type == `SW_S_3D) &
                (blk_type[0] == 1'b1)
```

表明这种特殊 orientation 和 3D block 类型有关。

---

## 14. `tail_mipid_raw`：找第一个进入 tail 的 mip

RTL：

```verilog
tail_mipid_raw = {MAXMIP}

for(i=0; i<MAXMIP; i++) begin
    if(i==0) begin
        if(in_miptail[i])
            tail_mipid_raw = i;
    end
    else begin
        if(in_miptail[i] ^ in_miptail[i-1])
            tail_mipid_raw = i;
    end
end
```

核心操作：

```text
in_miptail[i] XOR in_miptail[i-1]
```

也就是寻找：

```text
0 -> 1
```

这个 transition。

例如：

```text
mip0 : 0
mip1 : 0
mip2 : 0
mip3 : 0
mip4 : 1   <-- first mip in tail
mip5 : 1
mip6 : 1
```

那么：

```text
tail_mipid_raw = 4
```

这直接对应公开 AddrLib 输出概念：

```text
firstMipIdInTail
```

如果没有 tail，则保持 `MAXMIP`，作为“无 tail”标志。

---

## 15. 为什么 `tail_mipid` 还要再处理一次

RTL：

```verilog
tail_mipid =
    ((maxmip == 0) | ((l2_ms_128B >> 1) == 0))
    ? MAXMIP
    : tail_mipid_raw
```

注释说明：

```text
linear and SW_*_256B are treated same - no miptails
```

所以：

```text
linear
256B swizzle
```

直接认为：

```text
no mip tail
```

也就是：

```text
tail_mipid = MAXMIP
```

因此 `tail_mipid_raw` 是“算法检测出来的 tail 起点”，而 `tail_mipid` 是综合当前 swizzle/block mode 约束后真正启用的 tail 起点。

---

## 16. `mipsize[m]`：每个 mip 对外占多少 block

RTL：

```verilog
if(mip_idx > tail_mipid)
    mipsize[mip_idx] = 'd0;
else if((mip_idx == tail_mipid) ||
        (mip_idx == (MAXMIP-1)))
    mipsize[mip_idx] = 'd1;
else
    mipsize[mip_idx] = Wb_slice[mip_idx] * Hb[mip_idx];
```

这里必须特别注意：

`mipsize` 不是简单的 pixel 数，而是用于整个 surface layout 累加的 **block-level footprint**。

### tail 之前

```text
mipsize = Wb_slice * Hb
```

例如：

```text
Wb_slice = 10
Hb = 8
```

那么：

```text
mipsize = 80 blocks
```

### tail 起点

```text
mipsize = 1
```

因为 tail 被作为一个 packed region 对外处理，而不是每个 tiny mip 单独占一个完整 macro-block。

### tail 后面的 mip

```text
mipsize = 0
```

因为这些 mip 已经被包含在 tail region 中。

因此可以把整个 mip chain 的外部 layout 抽象成：

```text
Mip0      independent footprint
Mip1      independent footprint
Mip2      independent footprint
...
MipK      tail region = 1 block
MipK+1    packed inside same tail
MipK+2    packed inside same tail
...
```

---

## 17. 为什么 tail 起点 `mipsize = 1` 很重要

这不是说 tail 内每个 mip 都占 1 block。

真正含义是：

> **在宏观 surface layout 层面，整个 mip tail 被折叠成一个 tail region。**

后面的 slice/mip-offset 累加只需要知道：

```text
tail 在整个 surface 中占据一个 tail region
```

至于 tail region 内部的具体：

```text
MipK
MipK+1
MipK+2
...
```

如何摆放，则属于更细一级的 mip-tail addressing/packing 逻辑。

---

## 18. `mip_mask`：构造 0..current_mip 的 mask

RTL：

```verilog
mip_mask = ((1'b1 << (mip_level + 4'd1)) - 1'b1)
```

例如：

```text
mip_level = 3
```

则：

```text
1 << 4 = 10000b
10000b - 1 = 01111b
```

所以：

```text
bit0 ~ bit3 = 1
```

即：

> 用一个 bit mask 表示 mip 0 到当前 mip level 的范围。

---

## 19. `maxmip_mask`

RTL：

```verilog
maxmip_mask = ((1'b1 << (maxmip + 4'd1)) - 1'b1)
```

表示：

```text
bit0 ~ bit(maxmip) = 1
```

所以：

```verilog
slice_input_en = maxmip_mask
```

表示在 slice-size 计算中，把整个有效 mip chain 纳入计算。

---

## 20. `slice_b`：整个 mip chain 的 block footprint

RTL：

```verilog
slice_b =
    Σ(
        slice_input_en[m]
        ? mipsize[m]
        : 0
      )
```

所以：

```text
slice_b = mip0 block footprint
        + mip1 block footprint
        + ...
        + tail block footprint
```

它是整个 surface 在当前 block granularity 下的总 footprint。

---

## 21. `slice_out`

RTL：

```verilog
slice_out =
    slice_b << (l2_blk_w_slice + l2_blk_h)
```

因为：

```text
2^l2_blk_w_slice = 每个 slice-width block 对应的 element/byte scaling
2^l2_blk_h       = 高度方向 scaling
```

所以这个 shift 把：

```text
block count
```
转换成对应的更高一级 byte/element footprint。

---

## 22. 一个重要的待确认点：`mip_off_input_en`

RTL：

```verilog
mip_mask = ((1'b1<<(mip_level + 4'd1)) - 1'b1)
maxmip_mask = ((1'b1)<<(maxmip + 4'd1) - 1b1)

slice_input_en = maxmip_mask
mip_off_input_en = slice_input_en & ~mip_mask
```

从纯 bit-mask 数学上看：

```text
slice_input_en   = valid mip range
mip_mask         = mip 0..current level
~mip_mask        = current+1 .. upper levels
```

因此 `mip_off_input_en` 看起来更像是在选“当前 mip 之后的 mip”。

但如果 `mip_offset_in_blks` 的语义是通常意义上的“当前 mip 起始地址”，那么通常预期应该累加当前 mip 之前的 mip footprint。

所以这里存在一个需要结合后续 address-generation 使用方式进一步确认的问题：

1. `mip_off_input_en` 的方向可能在你抽取 RTL 时被反转/简化；或者
2. 这个硬件里的 `mip_offset` 定义不是传统的“surface base -> mip start”；或者
3. `mip_off_en` / `mip_mask` 在完整 RTL 中还有额外逻辑未保留。

这个地方不宜仅凭当前片段武断下结论。

---

## 23. 最终 `mip_offset_b_out`

RTL：

```verilog
mip_offset_b_out = mip_offset_in_blks << l2_mip_offset
```

其结构可以理解成：

```text
先在统一 block 单位中累计 mip offset
                ↓
再根据 block size / 256B granularity 放大
                ↓
得到输出的 byte-address-scale offset
```

---

# 24. 整个 GFX10 MipTail 算法的统一数学模型

把 RTL 与公开 GFX10 AddrLib 概念对齐，可以总结成：

### Step 1：mip 尺寸

```text
W_m = ceil(W_0 / 2^m)
H_m = ceil(H_0 / 2^m)
```

RTL：

```verilog
(Wb0 >> m) + OR(low bits)
```

对应 GFX10 AddrLib 的 `GetMipSize()` / `ShiftCeil()` 思路。

### Step 2：tail 最大容量

```text
max_tail_mips = f(block_size, 2D/3D)
```

RTL：

```verilog
num_mips_in_tail
```

对应：

```text
GetMaxNumMipsInTail()
```

### Step 3：tail 数量约束

```text
numMipsToEnd <= max_tail_mips
```

RTL：

```verilog
in_tail_chk[m]
```

### Step 4：tail 尺寸约束

```text
W_m <= tailWidth
H_m <= tailHeight
```

RTL：

```verilog
width_in_tail
height_in_tail
```

### Step 5：综合判断

```text
in_miptail[m] = size_condition & count_condition
```

对应：

```text
IsInMipTail()
```

### Step 6：找第一个 tail mip

```text
first 0 -> 1 transition
```

RTL：

```verilog
in_miptail[m] ^ in_miptail[m-1]
```

对应：

```text
firstMipIdInTail
```

### Step 7：计算 surface footprint

```text
mipsize[m] = Wb_slice[m] * Hb[m]    (tail 前)
```

而整个 tail：

```text
mipsize[tail_mipid] = 1
```

tail 后：

```text
mipsize[m] = 0
```

最后累加成为：

```text
slice_b
mip_offset_in_blks
```

---

# 25. 最核心的理解

这段 RTL 最值得记住的不是某一个公式，而是 GFX10 mip-tail 的三个层次：

```text
                  mip chain
                      |
          +-----------+-----------+
          |                       |
          v                       v
    mip geometry              tail capacity
          |                       |
          +-----------+-----------+
                      |
                      v
                in_miptail[m]
                      |
                      v
                tail_mipid
                      |
          +-----------+-----------+
          |                       |
          v                       v
   independent mip          packed mip tail
          |                       |
          +-----------+-----------+
                      |
                      v
              mipsize / offset / slice
```

换句话说：

> **GFX10 mip tail 的本质不是简单地“把小 mip 放到一起”，而是先用 block geometry 算出每个 mip 的 footprint，再同时用“尺寸限制”和“距离 mip chain 尾部的级数限制”决定哪些 mip 属于 tail，最后把整个 tail 在更高一级的 surface-layout 计算中折叠成一个共享 region。**

---

## 26. 与公开 GFX10 AddrLib 的关键对应

| RTL | GFX10 AddrLib 概念 |
|---|---|
|`Wb[m]`, `Hb[m]`|`GetMipSize()` / `ShiftCeil()`|
|`num_mips_in_tail`|`GetMaxNumMipsInTail()`|
|`in_tail_chk[m]`|`numMipsToTheEnd <= maxNumMipsInTail`|
|`width_in_tail` / `height_in_tail`|`mipWidth <= mipTailDim`|
|`in_miptail[m]`|`IsInMipTail()`|
|`tail_mipid_raw`|`firstMipIdInTail`|
|`mipsize[m]`|mip-level surface footprint |
|`slice_b`|aggregate surface footprint |
|`mip_offset_in_blks`|mip-level accumulated offset |

---

## 27. 资料依据

公开 AMD/Mesa GFX10 AddrLib：

- GFX10 AddrLib header / implementation structure：
  - `gfx10addrlib.h`
  - `gfx10addrlib.cpp`
- GFX10 mip-tail related concepts：
  - `GetMaxNumMipsInTail()`
  - `IsInMipTail()`
  - `firstMipIdInTail`
  - `GetMipSize()` / `ShiftCeil()`
- Mesa `ac_surface.c` 中对 AddrLib mip/surface 信息的使用。

这些公开接口用于交叉验证 RTL 中变量和公式的算法语义；具体硬件 pipeline 和本 RTL 未展示的内部数据通路，不应仅凭公开软件代码臆测。
