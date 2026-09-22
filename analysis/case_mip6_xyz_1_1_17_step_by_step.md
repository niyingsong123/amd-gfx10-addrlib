# mip6、坐标 (1,1,17)：按 ADDRLIB.md 逐步计算 tile address

本例采用 `SW_64KB_3D`、4 BPE、1 sample，访问 mip-tail 内的 mip6。最终结果为 **`address_final = 0x10160A2C`**。

宏块坐标索引为 `(xb,yb,zb)=(0,0,1)`。输入坐标 X/Y/Z 都非零，但合法 tail 内的宏块 X/Y 索引仍为 0。

以下沿用 ADDRLIB.md 的模块顺序和变量名。计算依据为此前核对的 873 行完整版，其 SHA-256 为 `05D4519FBF57BB516590AE397DD67EDB2FE6FF7A09570325D033A3D73702216D`。

原文有几处接口定义不完整，本例明确采用以下约定：

- `map0_*_minus_1` 先恢复成实际尺寸；`pitch/slice` 按正文公式输出实际数量，不采用注释中的减一编码。
- 含义相同的别名统一：`maxmip_in=maxmip`，`mips_in_tail=num_mips_in_tail`，`y_bias=y_bias_intail`，`pad_sz_w/h=pad_data_sz_w/h`，`blk_bit_mask_128B=ms_mask_128B`，`l2_block_ms=l2_ms`。`num_mips_inside_tail` 对应前面的 `al_num_mips_inside_tail`。
- 按文档对 64KB 模式的注释取 `blk_type[0]=0`；原文没有给出完整的 blk_type 二进制编码。
- 查位表前补上原文未明确写出的连接：输入坐标加上 tail 原点。块索引计算也使用这一组坐标；本例使用原始 X/Y 计算宏块索引同样为 0。
- 按公式的数学含义计算，信号位宽足够；位切片按对应的零扩展理解。求和沿用文档列出的 mip0～16，实际有效 mip 由 maxmip mask 选择。
- Base address 为 `0x10000000`，base swizzle 为 0。最后一步保留文档的 OR 公式，不将它改写成另一套算法。

## 1. 输入参数

| 输入 | 数值 |
|---|---:|
| `sw_mode` | `SW_64KB_3D` |
| mip0 实际尺寸 | `128 × 128 × 2048` |
| `map0_w_minus_1` | 127 |
| `map0_h_minus_1` | 127 |
| `map0_d_minus_1` | 2047 |
| `log2_element_bytes = l2_eb` | 2，即 4 BPE |
| `log2_num_samples = l2_ns` | 0，即 1 sample |
| `maxmip` | 11，共 12 个 mip |
| `mip_level` | 6 |
| 原始访问坐标 | `(x_in,y_in,z_in) = (1,1,17)` |
| Base address | `0x10000000` |

恢复实际尺寸：

```text
map0_w = map0_w_minus_1 + 1 = 128
map0_h = map0_h_minus_1 + 1 = 128
map0_d = map0_d_minus_1 + 1 = 2048
```

mip6 的实际尺寸：

```text
W6 = max(128  >> 6, 1) = 2
H6 = max(128  >> 6, 1) = 2
D6 = max(2048 >> 6, 1) = 32
```

因此 `(1,1,17)` 是合法坐标。

## 2. S0：解码模式，计算宏块参数

对应原文 L87～200。

```text
sw_mode  = SW_64KB_3D
blk_type = SZ_64KB
sw_type  = SW_S_3D

linear = 0
dim3D  = 1
```

查 `macro_blk_size_calc`：

```text
l2_ms        = 16
l2_ms_128B   = 9
ms_mask_128B = 0x1FF
```

接着：

```text
msaa = (dim3D | linear) ? 0 : l2_ns
     = 0

block_size_elements = l2_ms - (l2_eb + msaa)
                    = 16 - (2 + 0)
                    = 14
```

`block_size_elements` 是元素数量的 log2。

3D 分支按文档查表，查表索引为：

```text
l2_ms[4:1] = 8
l2_eb     = 2
```

得到：

```text
l2_blk_w = 5
l2_blk_h = 5
l2_blk_d = 4

宏块尺寸 = 32 × 32 × 16
```

容量检查：

```text
32 × 32 × 16 × 4 BPE = 65536 B = 64KB
```

后续对齐参数：

```text
l2_blk_w_slice
    = (linear && l2_blk_w < 8) ? (8 - l2_eb) : l2_blk_w
    = 5

l2_ms_256B
    = (l2_ms_128B == 0) ? 0 : l2_ms_128B - 1
    = 9 - 1
    = 8

l2_mip_offset
    = (l2_ms < 8) ? 0 : l2_ms - 8
    = 16 - 8
    = 8
```

## 3. S0：计算 tail 容量和数量条件

对应原文 L206～262。

进入 `al_num_mips_inside_tail`：

```text
is_3d_blk_size = 1
l2_ms_256B    = 8
```

查 3D 修正表：

```text
l2_ms_256B_3d = 6
```

因此：

```text
l2_ms_256B_eff = is_3d_blk_size ? l2_ms_256B_3d : l2_ms_256B
               = 6

num_mips_in_tail = l2_ms_256B_eff + 4
                 = 6 + 4
                 = 10
```

这里的 10 是最大容量，不是本例实际进入 tail 的 mip 数量。

数量条件：

```text
mips_outside_tail = maxmip - num_mips_in_tail
                  = 11 - 10
                  = 1

in_tail_chk[m]
    = (m > mips_outside_tail) | mips_outside_tail[msb]
    = (m > 1) | 0
    = (m > 1)
```

即：

```text
in_tail_chk[0] = 0
in_tail_chk[1] = 0
in_tail_chk[2及以后] = 1
```

这一步只检查剩余 mip 数量，尚未检查尺寸。

## 4. S0：计算 mip0 的 XY 宏块数量

对应原文 L272～305。

按文档对 64KB 的说明，取 `blk_type[0]=0`：

```text
y_bias_intail = (sw_type == SW_S_3D) & (blk_type[0] == 1)
              = 1 & 0
              = 0
```

`pad_to_log2sz_gc` 的公式：

```text
pad_sz_mask = (1 << l2_pad_sz_in) - 1

pad_out = (dim_in >> l2_pad_sz_in)
        + |(dim_in & pad_sz_mask)
```

这里 `|(...)` 是归约 OR：括号内非零返回 1，否则返回 0。

宽度代入：

```text
pad_sz_mask = (1 << 5) - 1 = 31

Wb0 = (128 >> 5) + |(128 & 31)
    = 4 + 0
    = 4
```

高度和 slice 使用的宽度同理：

```text
Hb0       = 4
Wb_slice0 = 4

pad_data_sz_w = 1 << 5 = 32
pad_data_sz_h = 1 << 5 = 32
```

Tail 的尺寸门槛：

```text
w_tail_sz = y_bias_intail ? 32 : (32 >> 1) = 16
h_tail_sz = y_bias_intail ? (32 >> 1) : 32 = 32
```

## 5. S1：逐 mip 计算块数量，确定 tail 起点

对应原文 L325～379。

```text
Wb[m] = (Wb0 >> m) + |Wb0[PAD_W_MSB(m):0]
Hb[m] = (Hb0 >> m) + |Hb0[PAD_H_MSB(m):0]
```

本例可以写成：

```text
Wb[m] = ceil(4 / 2^m)
Hb[m] = ceil(4 / 2^m)

Wb[0] = Hb[0] = 4
Wb[1] = Hb[1] = 2
Wb[2] = Hb[2] = 1
Wb[3及以后] = Hb[3及以后] = 1
```

例如 m=3 时，`4 >> 3=0`，而被移出的低位中有 1，所以归约 OR 为 1，结果仍为 1。`Wb_slice[m]` 与 `Wb[m]` 相同。

文档利用上一 mip 的块数量判断下一 mip 是否进入 tail。因为 `y_bias_intail=0`：

```text
height_in_tail = Hb[m] <= 2
width_in_tail  = Wb[m] <= 1

in_miptail[m+1]
    = height_in_tail
   && width_in_tail
   && in_tail_chk[m+1]
```

逐步代入：

| 待判断 mip | 使用上一 mip 的 Wb/Hb | 高度条件 | 宽度条件 | 数量条件 | in_miptail |
|---|---|---|---|---|---:|
| mip1 | 4 / 4 | 4≤2：假 | 4≤1：假 | 假 | 0 |
| mip2 | 2 / 2 | 2≤2：真 | 2≤1：假 | 真 | 0 |
| mip3 | 1 / 1 | 1≤2：真 | 1≤1：真 | 真 | 1 |
| mip4～11 | 1 / 1 | 真 | 真 | 真 | 1 |

mip0 的尺寸 128×128 超过 16×32 门槛，因此 `in_miptail[0]=0`。

第一个 0→1 转折发生在 mip3：

```text
in_miptail[3] ^ in_miptail[2] = 1 ^ 0 = 1
tail_mipid_raw = 3
```

再检查禁用 tail 的条件：

```text
maxmip == 0            → 假
(l2_ms_128B >> 1) == 0  → (9 >> 1) == 0 → 假

tail_mipid = 3
```

所以本例实际进入 tail 的是 mip3～mip11，共 9 个 mip。mip6 位于 tail 内。

## 6. S1/S2：计算各 mip 的计账块数和 mask

对应原文 L385～435。

`mipsize` 的选中路径为：

```text
mip_idx > tail_mipid  → 0
mip_idx == tail_mipid → 1
mip_idx < tail_mipid  → Wb_slice[mip_idx] × Hb[mip_idx]
```

代入：

| mip | 计算 | mipsize |
|---|---|---:|
| mip0 | 4×4 | 16 |
| mip1 | 2×2 | 4 |
| mip2 | 1×1 | 1 |
| mip3 | tail 首级计 1 | 1 |
| mip4～11 | tail 后续级计 0 | 0 |

后续求和涉及的 mip12～16 也为 0，并且不被有效 mip mask 选中。`mipsize` 在此是 XY 层面的块计账值，不是整个 3D mip 的总块数。

计算 mask：

```text
mip_mask = (1 << (mip_level + 1)) - 1
         = (1 << 7) - 1
         = 0x007F

maxmip_mask = (1 << (maxmip + 1)) - 1
            = (1 << 12) - 1
            = 0x0FFF

slice_input_en = maxmip_mask
               = 0x0FFF

mip_off_input_en = slice_input_en & ~mip_mask
                 = 0x0FFF & ~0x007F
                 = 0x0F80
```

`slice_input_en` 选择 mip0～11；`mip_off_input_en` 只选择当前 mip6 后面的 mip7～11。

## 7. S2：计算 pitch、slice 和 mip offset

对应原文 L419、L443～527。

```text
pitch = Wb[mip_level] << l2_blk_w
      = Wb[6] << 5
      = 1 << 5
      = 32
```

这是文档公式得到的对齐 pitch；mip6 的实际宽度仍然是 2。

文档将 mip offset 求和拆成高、低两段：

```text
高段：从 mip6～16 中选择 mip7～11，其 mipsize 全为 0
低段：mip1～5 均未被 mip_off_input_en 选中

mip_offset_in_blks = 0 + 0 = 0
```

Slice 求和：

```text
slice_b 高段 = mipsize[6] + ... + mipsize[11]
             = 0

slice_b 低段 = mipsize[0] + ... + mipsize[5]
             = 16 + 4 + 1 + 1 + 0 + 0
             = 22

slice_b = 22
```

模块输出：

```text
slice_out = slice_b << (l2_blk_w_slice + l2_blk_h)
          = 22 << (5 + 5)
          = 22 << 10
          = 22528
          = 0x5800

pitch_out = 32

mip_offset_b_out = mip_offset_in_blks << l2_mip_offset
                 = 0 << 8
                 = 0

mip_in_tail_out = mip_level - tail_mipid
                = 6 - 3
                = 3

l2_blk_width_out  = 5
l2_blk_height_out = 5
l2_blk_depth_out  = 4
l2_ms_out        = 16
```

`slice_out` 是 XY 元素位置数，`mip_offset_b_out` 的单位为 256B。此处 mip_in_tail=3 表示 mip6 是 tail 内从 0 编号的第 3 级，即第 4 个 mip。

## 8. 计算 tail 微块尺寸和 tail 原点

对应原文 L533～649。

进入 `calc_mip_inside_tail_xyz_orig`：

```text
l2_data_block_size_128B = 9
l2_data_block_size_256B = 9 - 1 = 8

num_mips_in_tail = 10
mip_in_tail     = 3

l2_ms_odd = l2_ms[0]
          = 16 的最低位
          = 0
```

微块尺寸公式：

```text
block_bits = 8 - (l2_eb + l2_ns)
           = 8 - (2 + 0)
           = 6
```

查 `case(block_bits)`：

```text
q_3 = 2
r_3 = 0
```

选择 3D 分支：

```text
l2_ublk_w = q_3 + (r_3 > 1) = 2 + 0 = 2
l2_ublk_h = q_3             = 2
l2_ublk_d = q_3 + (r_3 > 0) = 2 + 0 = 2
```

所以微块尺寸为 4×4×4。

计算反向 tail 序号：

```text
mip_in_tail_reverse
    = num_mips_in_tail - (mip_in_tail + 1)
    = 10 - (3 + 1)
    = 6
```

它非负，且不大于 6，因此选择文档最后一个分支：

```text
byte_offset = mip_in_tail_reverse << 8
            = 6 << 8
            = 0x600
```

按文档的 12 位 X/Y 交织拆位，高位不足处补 0：

```text
{x5,y5,x4,y4,x3,y3,x2,y2,x1,y1,x0,y0}
    = byte_offset[19:8]
    = 12'b0000_0000_0110
```

这里的 x/y 是 `x/y_mip_micro_block`。非零位为：

```text
x_mip_micro_block[0] = 1
y_mip_micro_block[1] = 1

x_mip_micro_block = 1
y_mip_micro_block = 2
```

`l2_ms_odd=0`，不交换 X/Y：

```text
x_mip_micro_block_final = 1
y_mip_micro_block_final = 2
```

最后按原文的 10 位输出计算；本例不会发生截断：

```text
x_mip_in_tail_orig = 10'(1 << l2_ublk_w) = 1 << 2 = 4
y_mip_in_tail_orig = 10'(2 << l2_ublk_h) = 2 << 2 = 8
z_mip_in_tail_orig = 0
```

Tail 原点为 **(4,8,0)**。

## 9. 补上坐标连接，计算 blk_offset

将原始访问坐标加上 tail 原点。此连接是本文明确补足的接口约定，原文没有写出这三行连线：

```text
x = x_in + x_mip_in_tail_orig = 1  + 4 = 5
y = y_in + y_mip_in_tail_orig = 1  + 8 = 9
z = z_in + z_mip_in_tail_orig = 17 + 0 = 17
```

按原文 L750 的 `SW_64KB_3D、AA_1X、BPE_4` 位表：

```text
blk_offset = {
    x[4], y[4], z[3], x[3],
    y[3], z[2], x[2], y[2],
    z[1], y[1], z[0], x[1],
    y[0], x[0], 1'b0, 1'b0
}
```

坐标的二进制表示：

```text
x =  5 = 5'b00101
y =  9 = 5'b01001
z = 17 = 5'b10001
```

逐组代入：

| 地址位 | 来源 | 代入结果 |
|---|---|---|
| [15:12] | {x[4],y[4],z[3],x[3]} | 0000 |
| [11:8] | {y[3],z[2],x[2],y[2]} | 1010 |
| [7:4] | {z[1],y[1],z[0],x[1]} | 0010 |
| [3:0] | {y[0],x[0],0,0} | 1100 |

因此：

```text
blk_offset = 16'b0000_1010_0010_1100
           = 0x0A2C
```

`z[4]` 没有进入块内位表，它由宏块 Z 索引处理。

## 10. 计算 base 和 mip base

对应原文 L763～767。

先转成 256B 单位：

```text
baseAddr256B_in = Base address >> 8
                = 0x10000000 >> 8
                = 0x100000
```

按文档提取 base swizzle：

```text
blk_bit_mask_128B >> 1 = 0x1FF >> 1
                       = 0xFF

swizzle_bits_256B
    = baseAddr256B_in & (blk_bit_mask_128B >> 1)
    = 0x100000 & 0xFF
    = 0
```

需要清除的低位原本就是 0，因此文档的清位拼接得到：

```text
baseAddr256B_out = 0x100000
```

再加上 mip 宏块偏移：

```text
mipoffset_BaseAddr256B_out
    = baseAddr256B_out + mip_offset_b_in
    = 0x100000 + 0
    = 0x100000
```

## 11. 按 block_index_calc 计算宏块字节偏移

对应原文 L773～839。

模块输入：

```text
x = 5
y = 9
z = 17

pitch = pitch_out = 32
slice = slice_out = 22528

log2_blk_width       = 5
log2_blk_width_slice = 5
log2_blk_height      = 5
log2_blk_depth       = 4

l2_ms       = 16
l2_ms_slice = (16 < 8) ? 8 : 16
            = 16
```

代入公式：

```text
log2_blk_slice = log2_blk_width_slice + log2_blk_height
               = 5 + 5
               = 10

pitch_b = pitch >> log2_blk_width
        = 32 >> 5
        = 1

slice_b = slice >> log2_blk_slice
        = 22528 >> 10
        = 22
```

这里的 slice_b 是 block_index_calc 模块内由 slice 输入还原的块计数，与前面求和模块的 slice_b 数值相同。

坐标转宏块索引：

```text
xb = x >> log2_blk_width  = 5  >> 5 = 0
yb = y >> log2_blk_height = 9  >> 5 = 0
zb = z >> log2_blk_depth  = 17 >> 4 = 1
```

文档拆分的乘法：

```text
slice_times_z_l = slice_b[15:0] × zb
                = 22 × 1
                = 22

slice_times_z_h = slice_b[SLICE_WIDTH_B-1:16] × zb
                = 0 × 1
                = 0

pitch_times_y = pitch_b × yb
              = 1 × 0
              = 0
```

合并：

```text
blk_index_pitch = pitch_times_y + xb
                = 0 + 0
                = 0

blk_index_slice = slice_times_z_l + (slice_times_z_h << 16)
                = 22 + (0 << 16)
                = 22
```

最后转成字节偏移：

```text
blk_index = (blk_index_pitch << l2_ms)
          + (blk_index_slice << l2_ms_slice)

          = (0 << 16) + (22 << 16)
          = 0x160000
```

文档这个输出 blk_index 已经是字节偏移，不能再乘一次 64KB。

## 12. 按文档最后几行计算最终地址

对应原文 L855～867。

```text
ms_mask_256B = ms_mask_128B >> 1
             = 0x1FF >> 1
             = 0xFF
```

因为 linear=0，选择 tiled 分支；`micro_offset_linear` 分支不参与本例：

```text
blk_offset_final = blk_offset
                 = 0x0A2C
```

文档这里的 swizzle_bits 来自块内偏移，与前面来自 base 的 swizzle_bits_256B 是不同变量：

```text
swizzle_bits = (blk_offset >> 8) & ms_mask_256B
              = (0x0A2C >> 8) & 0xFF
              = 0x0A
```

按原文的 OR 公式：

```text
addr_offset = blk_index | (swizzle_bits << 8) | blk_offset_final

            = 0x160000 | 0x000A00 | 0x000A2C
            = 0x160A2C
```

最后把 256B 单位的 base 还原成字节地址：

```text
address_final
    = {mipoffset_BaseAddr256B_out, 8'd0} + addr_offset

    = (0x100000 << 8) + 0x160A2C
    = 0x10000000 + 0x160A2C
    = 0x10160A2C
```

## 13. 关键结果与验证范围

| 变量 | 结果 |
|---|---|
| tail_mipid | 3 |
| mip_in_tail | 3 |
| pitch_out | 32 |
| slice_out | 22528 = 0x5800，XY 元素位置数 |
| mip_offset_b_out | 0，256B 单位 |
| byte_offset | 0x600，用于生成 tail 原点 |
| tail 原点 | (4,8,0) |
| 查位表坐标 | (5,9,17) |
| 宏块坐标索引 xb/yb/zb | (0,0,1) |
| blk_index | 0x160000，字节偏移 |
| blk_offset | 0x0A2C，块内字节偏移 |
| addr_offset | 0x160A2C |
| address_final | **0x10160A2C** |

以上中间量已经按文档公式用脚本复算；这不是完整 RTL 仿真。

`byte_offset=0x600` 已通过 tail 原点进入位表，不能重复加到最终地址。如果查表时直接使用原始 `(1,1,17)`、漏加原点，则块内偏移会变成 `0x002C`，最终错误地得到 `0x1016002C`。

本例 base swizzle 为 0，因此不触发此前指出的非零 base swizzle 丢失问题；不能用本例通过来证明文档的非零 base swizzle 路径正确。
