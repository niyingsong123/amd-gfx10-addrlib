# AMD AddrLib 三个完整地址计算例子

> 本文记录三个用于打通 AddrLib 地址计算流程的手算例子。
>
> 重点是把参数 → tile/block 几何 → macro-block index → tile 内坐标 → swizzle → miptail → 最终地址这一整条链路串起来。
>
> 第三个例子在复核后修正了一个关键的 off-by-one：对于 `SW_256KB_3D / 1X / 8bpp / 256x256x256 / maxmip=12`，mip2 而不是 mip3 开始进入 miptail。因此原先得到的 `0x2000` 应修正为 `0x1000`。

---

## Example 1 — SW_256B_2D / 1X / 8bpp / 64x64 / mip0

### 1. 输入参数

| 参数 | 值 |
|---|---:|
| Swizzle | `SW_256B_2D` |
| AA | `1X` |
| BPE | `8bpp` = 1 byte/element |
| Surface | `64 x 64` |
| mip | `0` |
| Base address | `0x10000000` |
| x | `20` |
| y | `18` |
| z | `0` |

### 2. Tile / macro-block 尺寸

`l2_ms = 8`，所以一个 tile 是：

```text
2^8 = 256 B
```

8bpp 即 1 byte/element，因此 block 中共有：

```text
256 / 1 = 256 elements
```

2D block dimension：

```text
l2_blk_w = 4
l2_blk_h = 4
```

即：

```text
16 x 16 elements
```

### 3. Surface 中 macro-block 数量

```text
Wb0 = 64 >> 4 = 4
Hb0 = 64 >> 4 = 4
```

pitch：

```text
pitch = 4
```

### 4. 当前坐标属于哪个 macro block

```text
xb = 20 >> 4 = 1
yb = 18 >> 4 = 1
```

因此 block index：

```text
block_index = pitch * yb + xb
             = 4 * 1 + 1
             = 5
```

macro-block offset：

```text
5 << 8 = 0x500
```

### 5. 当前 macro block 内坐标

```text
x_in_block = 20 & 0xf = 4
y_in_block = 18 & 0xf = 2
```

### 6. 256B swizzle

本例使用的 256B 2D、1X、8bpp 对应 bit mapping 可写成：

```text
{ y[3], x[3], y[2], y[1], x[2], y[0], x[1], x[0] }
```

代入：

```text
x = 4 = 0100b
y = 2 = 0010b
```

得到：

```text
blk_offset = 0x18
```

### 7. 最终地址

```text
address = base + macro_block_offset + blk_offset
        = 0x10000000 + 0x500 + 0x18
        = 0x10000518
```

**结果：**

```text
0x10000518
```

这个例子主要用于建立最基本的：

```text
surface coordinate
    -> macro block
    -> intra-block coordinate
    -> swizzle
    -> address
```

链路。

---

# Example 2 — SW_64KB_2D / 4X / 32bpp / 1024x1024 / mip0

## 1. 输入参数

| 参数 | 值 |
|---|---:|
| Swizzle | `SW_64KB_2D` |
| AA | `4X` |
| BPE | `32bpp` = 4 bytes/element |
| Surface | `1024 x 1024` |
| mip | `0` |
| Base address | `0x20000000` |
| x | `130` |
| y | `70` |
| sample | `2` |

### 2. Tile / macro-block 尺寸

```text
l2_ms = 16
```

因此 tile：

```text
2^16 = 64KB
```

32bpp：

```text
l2_eb = 2
```

4X AA：

```text
l2_ns = 2
```

所以：

```text
block_size_elements = 2^(16 - 2 - 2)
                     = 2^12
                     = 4096 elements
```

2D block dimension：

```text
l2_blk_w = 6
l2_blk_h = 6
```

即：

```text
64 x 64 elements
```

注意：

```text
64 * 64 * 4 bytes = 16384 bytes
```

剩余的容量由 4X sample dimension 体现。

### 3. Surface 中 macro-block 数量

```text
Wb0 = 1024 >> 6 = 16
Hb0 = 1024 >> 6 = 16
```

因此：

```text
pitch = 16
```

### 4. 当前坐标属于哪个 macro block

```text
xb = 130 >> 6 = 2
yb = 70  >> 6 = 1
```

block index：

```text
block_index = pitch * yb + xb
             = 16 * 1 + 2
             = 18
```

macro-block offset：

```text
18 << 16 = 0x120000
```

### 5. 当前 macro block 内坐标

```text
x_in_block = 130 & 63 = 2
y_in_block = 70  & 63 = 6
sample = 2
```

### 6. 64KB 2D swizzle

本例使用的 bit mapping：

```text
{ x[5], y[5], x[4], y[4], x[3], y[3],
  y[2], x[2], y[1], x[1], y[0], x[0],
  s[1], s[0], 0, 0 }
```

代入：

```text
x = 2 = 000010b
y = 6 = 000110b
s = 2 = 10b
```

得到：

```text
blk_offset = 0x1340
```

### 7. 最终地址

```text
address = base + macro_block_offset + blk_offset
        = 0x20000000 + 0x120000 + 0x1340
        = 0x20121340
```

**结果：**

```text
0x20121340
```

这个例子加入了：

```text
BPE > 1
4X MSAA
sample bits
```

因此可以看到 tile geometry 和 sample bits 是如何共同进入地址计算的。

---

# Example 3 — SW_256KB_3D / 1X / 8bpp / 256x256x256 / mip4

> **重要：本例已经修正。**
>
> 原先分析错误地把 mip3 当成第一个进入 tail 的 mip，从而得到 `byte_offset = 0x2000`。重新严格按公式计算后，mip2 就已经进入 tail，因此当前 mip4 对应 `byte_offset = 0x1000`。

## 1. 输入参数

| 参数 | 值 |
|---|---:|
| Swizzle | `SW_256KB_3D` |
| AA | `1X` |
| BPE | `8bpp` = 1 byte/element |
| Surface | `256 x 256 x 256` |
| maxmip | `12` |
| current mip | `4` |
| Base address | `0x30000000` |

### 2. 256KB 3D macro block

```text
l2_ms = 18
```

所以 tile size：

```text
2^18 = 256KB
```

对于 8bpp / 1 byte per element，3D block dimension：

```text
l2_blk_w = 6
l2_blk_h = 6
l2_blk_d = 6
```

即：

```text
64 x 64 x 64 elements
```

验证：

```text
64 * 64 * 64 * 1 byte
= 262144 bytes
= 256KB
```

### 3. miptail 起点：关键 off-by-one 修正

本例：

```text
num_mips_in_tail = 11
maxmip_in = 12
```

代码中的：

```text
mips_outside_tail = maxmip_in - num_mips_in_tail
                   = 12 - 11
                   = 1
```

这里 `1` 在这套计算中对应 **最后一个位于 tail 外的 mip ID**，而不是“tail 外 mip 的数量”。

因此：

```text
mip0 -> tail 外
mip1 -> tail 外
mip2 -> 第一个进入 tail
```

所以：

```text
tail_mipid = 2
```

这一步是整个修正的核心。

### 4. 当前 mip4 在 tail 中的 index

```text
mip_in_tail = mip - tail_mipid
             = 4 - 2
             = 2
```

也就是说：

```text
mip2 -> tail index 0
mip3 -> tail index 1
mip4 -> tail index 2
```

### 5. reverse mip index

公式：

```text
mip_in_tail_reverse = num_mips_in_tail - (mip_in_tail + 1)
                     = 11 - (2 + 1)
                     = 8
```

因此：

```text
mip_in_tail_reverse = 8
```

### 6. 由 reverse index 计算 tail byte offset

因为：

```text
reverse = 8 > 6
```

所以：

```text
byte_offset = 16 << reverse
            = 16 << 8
            = 0x1000
```

**修正后的结果：**

```text
byte_offset = 0x1000
```

而不是之前错误的：

```text
0x2000
```

### 7. `0x1000` 拆成 X/Y micro-block

tail byte offset 的 bit mapping：

```text
{ x[5], y[5], x[4], y[4], x[3], y[3],
  x[2], y[2], x[1], y[1], x[0], y[0] }
    = byte_offset[19:8]
```

`0x1000` 的相关 12 bits 为：

```text
0001 0000 0000
```

按照交错 bit 顺序拆解：

```text
x5=0 y5=0
x4=0 y4=1
x3=0 y3=0
x2=0 y2=0
x1=0 y1=0
x0=0 y0=0
```

因此：

```text
x_mip_micro_block = 0
y_mip_micro_block = 8
```

即：

```text
(Xmicro, Ymicro) = (0, 8)
```

### 8. X/Y 是否交换

```text
l2_ms = 18
```

所以：

```text
l2_ms_odd = 0
```

不进行 X/Y swap：

```text
x_mip_micro_block_final = 0
y_mip_micro_block_final = 8
```

### 9. 计算 tail micro-block 尺寸

8bpp：

```text
l2_eb = 0
```

1X：

```text
l2_ns = 0
```

因此：

```text
block_bits = 8 - (l2_eb + l2_ns)
           = 8
```

3D q/r 分解：

```text
q_3 = 2
r_3 = 2
```

得到：

```text
l2_ublk_w = 3
l2_ublk_h = 2
l2_ublk_d = 3
```

所以一个 tail micro-block 是：

```text
2^3 x 2^2 x 2^3
= 8 x 4 x 8 elements
```

### 10. 从 micro-block index 得到 mip origin

```text
x_mip_in_tail_orig = x_mip_micro_block_final << l2_ublk_w
                   = 0 << 3
                   = 0
```

```text
y_mip_in_tail_orig = y_mip_micro_block_final << l2_ublk_h
                   = 8 << 2
                   = 32
```

```text
z_mip_in_tail_orig = 0
```

因此：

```text
mip4 tail origin = (0, 32, 0)
```

即：

```text
x_origin = 0
y_origin = 32
z_origin = 0
```

### 11. mip4 的逻辑坐标如何进入 tail 空间

mip4 的逻辑尺寸：

```text
256 >> 4 = 16
```

因此：

```text
mip4 = 16 x 16 x 16
```

加入 tail origin 后：

```text
x' = x + 0
   = x

y' = y + 32
z' = z + 0
   = z
```

所以 mip4 在 tail 中占据：

```text
x : 0  ~ 15
y : 32 ~ 47
z : 0  ~ 15
```

### 12. 当前 mip4 是否跨 macro block

macro block 是：

```text
64 x 64 x 64
```

因此：

```text
xb = x' >> 6
yb = y' >> 6
zb = z' >> 6
```

由于：

```text
x' = 0..15
y' = 32..47
z' = 0..15
```

所以整个 mip4 都落在：

```text
macro block (0, 0, 0)
```

之内。

这点非常重要：`y_origin=32` 并不是让 mip4 跳到下一个 64x64 macro block，而是在同一个 macro block 内把 mip4 放到 Y=32 开始的位置。

### 13. block 内坐标

对于 mip4 的任意逻辑坐标 `(x,y,z)`：

```text
x' = x
y' = 32 + y
z' = z
```

因为 mip4 的范围是 `0..15`，所以：

```text
x' = 0..15
y' = 32..47
z' = 0..15
```

macro block index 仍然是：

```text
xb = 0
yb = 0
zb = 0
```

随后这些 block 内坐标进入 3D 的 swizzle / `sheet_of_block_offset()` 计算，得到最终的 `blk_offset_final`。

### 14. mip offset 与 tail origin 的区别

当前 mip4 是 tail 内 mip，因此：

```text
mip_in_tail = 2
```

但 `mip_in_tail` 本身不是最终的 byte address offset。

它首先通过：

```text
reverse -> byte_offset -> micro-block coordinate -> mip origin
```

得到：

```text
mip4 tail origin = (0, 32, 0)
```

而常规的 `mip_offset_b` 则属于更外层的 mip offset/address composition。

因此需要把两个概念分开：

```text
mip_in_tail
    -> tail 内部布局位置

mip_offset_b
    -> mip-level/base-address 方向的 offset
```

### 15. 最终地址结构

对于 tail 中的访问，最终仍然可以理解成：

```text
base / mip-tail base
    + macro-block address contribution
    + swizzle / intra-block offset
```

在本例中，mip4 的 tail origin 已经确定为：

```text
(0, 32, 0)
```

然后对具体 `(x,y,z)`：

```text
(x', y', z') = (x, 32+y, z)
```

再计算：

```text
macro-block index
    -> swizzle bits
    -> blk_offset_final
    -> final address
```

---

# 三个例子的对比

| 项目 | Example 1 | Example 2 | Example 3 |
|---|---|---|---|
| Swizzle | 256B 2D | 64KB 2D | 256KB 3D |
| AA | 1X | 4X | 1X |
| BPE | 8bpp | 32bpp | 8bpp |
| 维度 | 2D | 2D | 3D |
| mip | 0 | 0 | 4 |
| Tile size | 256B | 64KB | 256KB |
| Macro block | 16x16 | 64x64 | 64x64x64 |
| 主要新增概念 | 基本 swizzle | sample bits | miptail + 3D |
| 关键结果 | `0x10000518` | `0x20121340` | tail origin `(0,32,0)` |

---

# 最重要的三个认知点

## 1. Ring / queue 式地拆分地址计算并不适用于这里；这里真正的层次是

```text
surface coordinate
    ↓
mip selection
    ↓
tile / macro-block geometry
    ↓
macro-block index
    ↓
intra-block coordinate
    ↓
(swizzle / sample / pipe / bank 等 bit mapping)
    ↓
final address
```

## 2. miptail 是另一套布局空间

进入 tail 后，不能继续把每个 mip 当作普通独立 tile array 处理，而是：

```text
mip ID
  ↓
mip_in_tail
  ↓
reverse index
  ↓
byte_offset
  ↓
X/Y micro-block
  ↓
3D micro-block geometry
  ↓
mip origin
```

## 3. 第三个例子的 off-by-one 是一个非常典型的陷阱

必须区分：

```text
num_mips_in_tail
```

这是 **数量**；

而本例公式产生的：

```text
mips_outside_tail = maxmip_in - num_mips_in_tail
```

在后续 `mip > mips_outside_tail` 的判断中，实际上承担的是 **最后一个 tail 外 mip ID** 的角色。

因此：

```text
maxmip = 12
num_mips_in_tail = 11
mips_outside_tail = 1
```

意味着：

```text
mip0, mip1 -> tail 外
mip2      -> tail 起点
```

而不是：

```text
mip0, mip1, mip2 -> tail 外
mip3             -> tail 起点
```
