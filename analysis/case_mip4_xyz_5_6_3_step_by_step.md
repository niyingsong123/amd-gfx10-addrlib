# 用例3：按当前本地 ADDRLIB.md 逐段复算

## 结论

```text
address_final        = 0x30008175 = 805339509
mipid_in_tail        = 1       // 顶层布尔输出
mip_in_tail          = 1       // 当前 mip 在 tail 中的编号
tail_mipid           = 3
mip_offset_b         = 0       // 256B 单位
byte_offset          = 0x2000  // 用于生成 tail origin
tail origin          = (32, 0, 0)
查表坐标             = (37, 6, 3)
blk_index            = 0
blk_offset           = 0x8175
```

## 0. 来源、计算口径与必要假设

- 唯一算法来源：[本地 ADDRLIB.md](D:/project/addrlib/ADDRLIB.md)。
- 源文件修改时间：2026-09-16 14:35:02。
- SHA256：`EDE4CEBA021D7C0A7F1D143CF01D847BDE941FE50AFA8EBB8B873E3CFE8F6187`。
- 本次执行了按文档公式转写的整数计算模型；位映射直接从源文件对应表项提取。没有编译或仿真 RTL，没有使用其他 AddrLib 版本替换公式。
- 保留文档现有 tail 算法、3D 表格、掩码和最终 OR 合成；未暗中修正此前发现的算法问题。
- 输入沿用指定坐标的用例3其余条件：256³、SW_256KB_3D、1X、1BPE、mip4、maxmip=12、示例字节基址 0x30000000。
- 将输入 x/y/z 解释为当前 mip 的局部坐标，直接使用 (5,6,3)，不再右移 mip_level。mip4 的逻辑大小为16³。
- maxmip=12 表示级别0至12；本次保留该输入，不改成8，也不判断图形API合法性。
- 文档未定义 MAXMIP；依据求和显式覆盖0至16，本次取 MAXMIP=17。它与输入 maxmip=12 不同。
- 未给出的位宽按足宽、零扩展求值，避免截断有效数据。具体基址拆分取48位字节地址、40位256B基址、BLK_256B_WIDTH=12；tail交织字段取 BYTE_OFFSET_IN_MIPTAIL_WIDTH=20，MAXMIP_WIDTH=5。这些是复算假设，不是原文件已经给出的参数。
- Wb0/Hb0 的存储宽度须足以表示4；PAD宏超过有效位的部分按0处理。本例取任何足够的宽度，所列向上取整结果相同。
- 表内 x/y/z 使用 x_in_sheet/y_in_sheet/z_in_sheet；block_index_calc 使用原始 (5,6,3)。若后者改用 (37,6,3)，本例也都小于64，因此块索引仍为0。
- 将 return 解释为原点计算段结束；其后的坐标相加视为顶层连接。函数内部 l2_blk_w/h/d 是局部微块结果，不覆盖第一模块的宏块尺寸。
- pipeBankXor 不是当前顶层单独声明的 input；基地址中的 swizzle 值直接由文档公式提取，本例算得0。

## 1. 顶层输入（第7行起）

| 输入 | 代入值 |
|---|---:|
| x / y / z | 5 / 6 / 3 |
| s | 0 |
| map0_w_minus_1 / map0_h_minus_1 / map0_d_minus_1 | 255 / 255 / 255 |
| sw_mode | SW_256KB_3D |
| log2_num_samples | 0 |
| log2_element_bytes | 0 |
| mip_level | 4 |
| maxmip | 12 |
| baseAddr256B | 0x00300000 |

基址输入的单位是256B：
```text
baseAddr256B = 0x30000000 >> 8 = 0x00300000
```

## 2. 尺寸恢复与输入别名（第91行起）

```text
map0_w = 255 + 1 = 256
map0_h = 255 + 1 = 256
map0_d = 255 + 1 = 256
l2_eb  = log2_element_bytes = 0
l2_ns  = log2_num_samples   = 0
```

l2_eb 的对应关系来自该段注释。map0_d 在本文后续公式中没有被使用，不另加深度计算。

## 3. sw_mode_dec（第123行起）

查询 SW_256KB_3D 行：
```text
blk_type = SZ_256KB
sw_type  = SW_S_3D
linear   = (SW_S_3D == SW_L) = 0
```

## 4. macro_blk_size_calc（第142行起）

查询 SZ_256KB 行：
```text
l2_ms        = 18
l2_ms_128B   = 11
ms_mask_128B = 0x7FF
block bytes = 2^18 = 262144
```

## 5. macro_block_dim_calc（第154行起）

```text
dim3D = 1
msaa = (dim3D | linear) ? 0 : l2_ns = 0
block_size_elements = 18 - (0 + 0) = 18
```

进入3D查表分支，索引 l2_ms[4:1]=9、l2_eb=0：
```text
l2_blk_w = 6
l2_blk_h = 6
l2_blk_d = 6
macro block = 64 × 64 × 64
```

本次不执行2D分支或linear分支。18是元素数量的log2，不是18个元素。

## 6. 256B 对齐辅助量（第234行起）

```text
l2_blk_w_slice = linear ? ... : l2_blk_w = 6
l2_ms_256B = 11 - 1 = 10
l2_mip_offset = 18 - 8 = 10
```

linear条件为0，因此不进入其特殊对齐分支。

## 7. al_num_mips_inside_tail（第246行起）

```text
is_3d_blk_size = 1
l2_ms_256B = 10 → case选择 l2_ms_256B_3d = 7
l2_ms_256B_eff = 7
num_mips_in_tail = 7 + 4 = 11
```

11是容量上限，不代表当前资源恰好有11级位于tail。

## 8. tail 数量限制（第292行起）

```text
mips_outside_tail = maxmip - num_mips_in_tail
                  = 12 - 11 = 1
mips_outside_tail[msb] = 0
in_tail_chk[m] = (m > 1)
```

所以 m=0、1 时为0，m=2至16时为1。

## 9. y_bias（第310行）

按文件注释，256KB满足 blk_type[0]=1：
```text
y_bias = (SW_S_3D == SW_S_3D) & 1 = 1
```

## 10. pad_to_log2sz_gc 与 mip0 块数（第318行起）

宽、高及slice宽的对齐指数均为6：
```text
pad_sz_mask = (1 << 6) - 1 = 63 = 0x3F
dim_in >> 6 = 256 >> 6 = 4
dim_in & pad_sz_mask = 256 & 63 = 0
|(dim_in & pad_sz_mask) = 0
pad_out = 4 + 0 = 4

Wb[0]       = Wb0       = 4
Hb[0]       = Hb0       = 4
Wb_slice[0] = Wb_slice0 = 4
```

pad_out 是对齐后块数，不是texel宽度。

## 11. 单块宽高（第341行起）

```text
pad_data_sz_w = 1 << 6 = 64
pad_data_sz_h = 1 << 6 = 64
```

## 12. W_H_block_calc 与 PAD 宏（第363行起）

三个数组的初值均为4，计算规则相同：
```text
m=1: (4 >> 1) + |4[0:0] = 2 + 0 = 2
m=2: (4 >> 2) + |4[1:0] = 1 + 0 = 1
m≥3: (4 >> m) + |低m位 = 0 + 1 = 1
```

PAD_W_MSB/PAD_H_MSB 把低位选取范围限制在存储宽度内；4的唯一置位在bit2，以上结果不受更高零位影响。

```text
Wb[0..16]       = [4,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
Hb[0..16]       = [4,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
Wb_slice[0..16] = [4,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
```

## 13. mip0 是否在 tail（第375行起）

```text
w_tail_sz = 64
h_tail_sz = 64 >> 1 = 32
in_miptail[0] = (256 <= 32) & (256 <= 64) & in_tail_chk[0]
              = 0 & 0 & 0 = 0
```

## 14. CHK_NEXT_IN_MIPTAIL（第385行起）

y_bias=1，故：
```text
height_in_tail = (Hb[m] <= 1)
width_in_tail  = (Wb[m] <= 2)
next_in_tail[m+1] = height_in_tail && width_in_tail && in_tail_chk[m+1]
```

| 循环m | Hb[m] | Wb[m] | height_in_tail | width_in_tail | in_tail_chk[m+1] | in_miptail[m+1] |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 4 | 0 | 0 | 0 | 0 |
| 1 | 2 | 2 | 0 | 1 | 1 | 0 |
| 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3至15 | 1 | 1 | 1 | 1 | 1 | 1 |

所以 mip2 虽通过数量检查，仍未通过尺寸检查；首个tail mip为3。

## 15. tail_mipid_calc（第409行起）

```text
tail_mipid_raw 初始值 = MAXMIP = 17
i=0: in_miptail[0]=0，不更新
i=1,2: 相邻标志未变化，不更新
i=3: in_miptail[3] ^ in_miptail[2] = 1 ^ 0 = 1 → 更新为3
i=4至16: 相邻标志均为1，不更新
tail_mipid_raw = 3

maxmip == 0                  → 0
(l2_ms_128B >> 1) == 0       → (11 >> 1)==0 → 5==0 → 0
tail_mipid = tail_mipid_raw = 3
```

实际请求的tail级别为mip3至mip12，共10级。

## 16. 高 mip 的 mipsize 计算（第423行起）

对 mip_idx=16至6，均满足 mip_idx > tail_mipid：
```text
mipsize[6..16] = 0
```

即使 mip_idx=16 也先命中此分支，不会执行后面的“最后一级设为1”。

## 17. 求和使能掩码（第445行起）

```text
mip_mask = (1 << (4 + 1)) - 1 = 0x0001F
maxmip_mask = (1 << (12 + 1)) - 1 = 0x01FFF
slice_input_en = 0x01FFF           // 选择0至12
mip_off_input_en = 0x01FFF & ~0x0001F
                 = 0x01FE0        // 选择5至12
```

## 18. S2 pitch（第457行）

```text
pitch = Wb[4] << l2_blk_w = 1 << 6 = 64
```

单位为元素。mip4逻辑宽度16与补齐后的pitch 64是不同的量。

## 19. 低 mip 的 mipsize 计算（第461行起）

```text
mipsize[5] = 0      // 5 > 3
mipsize[4] = 0      // 4 > 3
mipsize[3] = 1      // 第一个tail mip
mipsize[2] = Wb_slice[2] * Hb[2] = 1 * 1 = 1
mipsize[1] = 2 * 2 = 4
mipsize[0] = 4 * 4 = 16
```

这里只按文件的二维乘积公式计算，不另乘深度。

## 20. 分组求和（第481行起）

```text
高组6至16:
mip_offset_in_blks_high = 0
slice_b_high = 0

低组:
mip_offset_in_blks_low = Σ(i=1..5, offset_en[i] * mipsize[i])
                       = mipsize[5] = 0
slice_b_low = 16 + 4 + 1 + 1 + 0 + 0 = 22

最终:
mip_offset_in_blks = 0
slice_b = 22
```

没有在此处额外加入byte_offset；原文也没有这样的加法。

### 完整数组与掩码逐项结果

| mip | Wb | Hb | Wb_slice | in_tail_chk | in_miptail | mipsize | slice_en | offset_en |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 4 | 4 | 0 | 0 | 16 | 1 | 0 |
| 1 | 2 | 2 | 2 | 0 | 0 | 4 | 1 | 0 |
| 2 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 |
| 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| 4 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 |
| 5 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 6 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 7 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 8 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 9 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 10 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 11 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 12 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 13 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 14 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 15 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 16 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |

mip13至16是MAXMIP计算范围内的数组元素，但不在maxmip=12请求范围内，故求和使能为0。

## 21. 第一模块输出（第553行起）

```text
slice = slice_b << (l2_blk_w_slice + l2_blk_h)
      = 22 << 12
      = 90112 = 0x16000
pitch = 64
mip_offset_b = 0 << 10 = 0
mip_in_tail = 4 < 3 ? 17 : 4 - 3 = 1

l2_ms = 18
l2_blk_w / l2_blk_h / l2_blk_d = 6 / 6 / 6
l2_blk_w_slice = 6
l2_blk_width / l2_blk_height / l2_blk_depth = 6 / 6 / 6
```

slice是当前公式累计各级后得到的元素计数，不是单独mip4的64×64，也不是纹理总字节数。mip_offset_b在后面与256B基址相加，因此这里单位为256B。

## 22. 模块间辅助量（第573行起）

```text
l2_block_ms = l2_ms = 18
l2_ms_odd = l2_block_ms[0] = 0
l2_block_ms_128B = 18 - 7 = 11
```

按信号依赖关系求值，赋值在文档中的先后不作为顺序程序执行顺序。

## 23. tail 原点模块的输入及容量（第581行起）

```text
输入:
l2_ms_odd = 0
mip_in_tail = 1
l2_eb = 0
l2_ns = 0
sw_type = SW_S_3D
l2_block_ms_128B = 11

l2_data_block_size_256B = 11 - 1 = 10
num_mips_in_tail = al_num_mips_inside_tail(10, SW_S_3D) = 11
```

## 24. micro_block_dim_calc（第609行起）

```text
block_bits = 8 - (0 + 0) = 8

先计算的2D候选:
l2_2d_blk_w = block_bits[3:1] + block_bits[0] = 4 + 0 = 4
l2_2d_blk_h = block_bits[3:1] = 4

case(8):
q_3 = 2
r_3 = 2

3D候选:
l2_3d_blk_d = 2 + (2 > 0) = 3
l2_3d_blk_w = 2 + (2 > 1) = 3
l2_3d_blk_h = 2

dim3D = 1 → 选择3D候选:
l2_ublk_w = 3
l2_ublk_h = 2
l2_ublk_d = 3
micro block = 8 × 4 × 8 = 256个1B元素
```

这里的微块尺寸不同于前面的64³宏块。

## 25. mip_in_tail_reverse（第651行）

```text
mip_in_tail_reverse = 11 - (1 + 1) = 9
符号位 = 0
```

## 26. byte_offset 分支（第653行起）

9非负且大于6，选择左移分支：
```text
byte_offset = 16 << 9 = 8192 = 0x2000
```

本次不执行“负数置0”或“reverse<<8”分支。

## 27. byte_offset 拆成 microblock 坐标（第665行起）

```text
byte_offset[19:8] = 0x020 = 0000_0010_0000b
```

按文件的交织顺序，x取原byte_offset的9、11、13、15、17、19位；y取8、10、12、14、16、18位。

0x2000只有bit13为1，该位对应x_mip_micro_block[2]：
```text
x_mip_micro_block = 1 << 2 = 4
y_mip_micro_block = 0
```

## 28. 奇偶交换（第689行起）

```text
l2_ms_odd = 0 → 不交换
x_mip_micro_block_final = 4
y_mip_micro_block_final = 0
```

## 29. tail origin（第693行起）

```text
x_mip_in_tail_orig = 4 << 3 = 32
y_mip_in_tail_orig = 0 << 2 = 0
z_mip_in_tail_orig = 0
```

本次结果为(32,0,0)，完全按当前文件计算。

## 30. 坐标相加（第701行起）

```text
x_in_sheet = 32 + 5 = 37
y_in_sheet = 0 + 6  = 6
z_in_sheet = 0 + 3  = 3
```

第708行明确说明，下方表格的x/y/z代表这组三个合成坐标。

## 31. blk_offset 位映射表（第799行）

选中 SW_256KB_3D、AA_1X、BPE_1 行，左侧是高位：
```text
blk_offset[17:0] =
{y5,z5,x5,y4,z4,x4,y3,z3,x3,y2,z2,x2,z1,y1,y0,z0,x1,x0}

x = 37 = 100101b
y =  6 = 000110b
z =  3 = 000011b
```

| 地址位 | 来源坐标位 | 值 | 贡献 |
|---:|---|---:|---:|
| 17 | y[5] | 0 | 0 |
| 16 | z[5] | 0 | 0 |
| 15 | x[5] | 1 | 0x8000 |
| 14 | y[4] | 0 | 0 |
| 13 | z[4] | 0 | 0 |
| 12 | x[4] | 0 | 0 |
| 11 | y[3] | 0 | 0 |
| 10 | z[3] | 0 | 0 |
| 9 | x[3] | 0 | 0 |
| 8 | y[2] | 1 | 0x100 |
| 7 | z[2] | 0 | 0 |
| 6 | x[2] | 1 | 0x40 |
| 5 | z[1] | 1 | 0x20 |
| 4 | y[1] | 1 | 0x10 |
| 3 | y[0] | 0 | 0 |
| 2 | z[0] | 1 | 0x4 |
| 1 | x[1] | 0 | 0 |
| 0 | x[0] | 1 | 0x1 |

```text
置位地址位 = {15,8,6,5,4,2,0}
blk_offset = 0x8000 + 0x100 + 0x40 + 0x20 + 0x10 + 0x4 + 0x1
           = 0x8175
           = 33141
```

文档标题“blk_offset[6:0] table”与该行实际18位宽度不同；本次按具体18位表项解释。

## 32. 基地址 swizzle 提取与清理（第817行起）

```text
ms_mask_128B >> 1 = 0x7FF >> 1 = 0x3FF
swizzle_bits_256B = 0x00300000 & 0x3FF = 0

baseAddr256B_out = 0x00300000
mipoffset_BaseAddr256B_out = baseAddr256B_out + mip_offset_b
                          = 0x00300000 + 0
                          = 0x00300000
```

按本次12位低字段拆分，基址低12位为0，清理表达式不会改变基址。这里保留原文的取反/右移顺序，没有改写它。

## 33. block_index_calc：换算块单位（第861行起）

输入取原始局部坐标(5,6,3)，宏块尺寸指数仍是6/6/6：
```text
log2_blk_slice = l2_blk_w_slice + l2_blk_h = 6 + 6 = 12
pitch_b = 64 >> 6 = 1
slice_b = 90112 >> 12 = 22
xb = 5 >> 6 = 0
yb = 6 >> 6 = 0
zb = 3 >> 6 = 0
```

即使坐标改为(37,6,3)，三项右移结果也仍为0；这使本例不受该端口连接歧义影响。

## 34. block_index_calc：分段乘法与合成（第877行起）

```text
slice_b[15:0] = 22
slice_b 高于bit15的部分 = 0

slice_times_z_l = 22 * 0 = 0
slice_times_z_h = 0 * 0 = 0
pitch_times_y = 1 * 0 = 0
blk_index_pitch = 0 + 0 = 0
blk_index_slice = 0 + (0 << 16) = 0

l2_ms_slice = max(18,8) = 18
blk_index = (0 << 18) + (0 << 18) = 0
```

该变量虽然命名为blk_index，但最后的移位表达式已把结果转换为字节偏移。

## 35. slice 对齐与 linear 候选（第893行起）

```text
l2_ms_slice = (18 < 8) ? 8 : 18 = 18
micro_offset_linear = x[6:0] << l2_eb = 5 << 0 = 5
```

linear=0，因此micro_offset_linear仅为未选中的候选，不参与本例结果。

## 36. XOR swizzle 与最终块内候选（第909行起）

```text
ms_mask_256B = 0x7FF >> 1 = 0x3FF
blk_offset_final = linear ? micro_offset_linear : blk_offset
                 = 0x8175

blk_offset 高于bit7的部分 = 0x81
swizzle_bits = (0x81 & 0x3FF) ^ 0
             = 0x81
swizzle_bits << 8 = 0x8100
```

本例基地址swizzle为0，故异或不会翻转任何位。保留文档现有OR公式，并不表示该公式对非零swizzle也正确。

## 37. addr_offset（第917行）

按文件当前的截取和OR：
```text
blk_index[47:0] = 0
(swizzle_bits << 8)[19:0] = 0x8100
blk_offset_final[45:0] = 0x8175

addr_offset = 0 | 0x8100 | 0x8175
            = 0x8175
```

0x8100中的置位已包含在0x8175中，OR结果仍为0x8175。这里没有把OR改成加法，也没有应用此前建议的修正公式。

## 38. 顶层两个输出（第921行起）

```text
{mipoffset_BaseAddr256B_out, 8'd0}
    = 0x00300000 << 8
    = 0x30000000

address_final = 0x30000000 + 0x8175
              = 0x30008175
              = 805339509

mipid_in_tail = (mip_in_tail != MAXMIP)
              = (1 != 17)
              = 1
```

## 39. 三个偏移的区别与结果适用范围

| 变量 | 本例值 | 在当前文档中的用途 |
|---|---:|---|
| mip_offset_b | 0 | 以256B为单位加到清理后的基地址 |
| byte_offset | 0x2000 | 拆位生成tail origin |
| blk_offset | 0x8175 | 用加入origin后的坐标查表，参与最终地址 |

byte_offset不是该代码路径中要额外加到最终地址上的另一项。本次0x2000经原点变换与3D映射后，原点自身贡献的是地址bit15（0x8000）；局部坐标(5,6,3)贡献0x175，合计0x8175。

本结果是“当前本地文档在上述明确输入及解释下的输出”。它不等同于完整硬件/上游AddrLib一致性验证；尤其本例swizzle=0，无法用来验证非零swizzle时的OR覆盖问题。

