# 大坐标用例：按当前 ADDRLIB.md 计算 mip0 的 (69,134,195)

## 结论

```text
address_final = 0x31440175 = 826540405
mipid_in_tail = 0

tail_mipid = 3
mip_in_tail = 17           // MAXMIP，无tail编号标记
tail origin = (0,0,0)
块坐标 = (1,2,3)
块内坐标 = (5,6,3)

pitch = 256
slice = 90112 = 0x16000
pitch_b = 4
slice_b = 22

mip_offset_in_blks = 6
mip_offset_b = 0x1800     // 256B单位
mip_offset_bytes = 0x180000
blk_index = 0x012C0000    // 公式已左移，单位为字节
blk_offset = 0x175
blk_offset_final = 0x75   // 当前版本仅取低8位
swizzle_bits = 1
addr_offset = 0x012C0175
```

## 0. 计算依据与解释

- 唯一算法来源：[D:/project/addrlib/ADDRLIB.md](D:/project/addrlib/ADDRLIB.md)。
- 修改时间：2026-09-16 16:50:47。
- SHA256：`216C030D9A6F2CF1E3AE88039F0C566A3484B16026FB496DFFEAFA4D0253E73B`。
- 执行的是按当前文档分支和公式转写的整数计算；位映射直接从当前源文件表项提取，不是RTL编译或硬件验证。
- 当前文件已经明确定义 MAXMIP=17，本次不再把它列为假设。
- 当前文件已将非linear的 blk_offset_final 改为 blk_offset[7:0]，采用这个新公式，不沿用旧版完整offset。
- x/y/z作为当前mip的局部坐标。非tail origin计算按文档负数分支执行，不额外强行置零。
- 对未定义位宽采用足宽求值。本例具体补充 MAXMIP_WIDTH=5，因此reverse按7位补码取符号位；BYTE_OFFSET_IN_MIPTAIL_WIDTH=20；基址按40位256B地址、12位低字段拆分，其余宽度足够容纳所列值。
- return解释为原点计算段结束，后面坐标相加属于顶层连接；函数内的微块尺寸局部变量不覆盖外层宏块尺寸。
- 按现有公式计算slice、mip偏移及最终OR，不替换成其他地址库的布局公式。maxmip=12输入原样保留。
- 本次未修改源文件。

## 1. 顶层输入

```text
sw_mode = SW_256KB_3D
log2_num_samples = 0
log2_element_bytes = 0
map0_w_minus_1 = 255
map0_h_minus_1 = 255
map0_d_minus_1 = 255
mip_level = 0
maxmip = 12
x = 69
y = 134
z = 195
s = 0
字节基址 = 0x30000000
baseAddr256B = 0x00300000
```

## 2. 输入转换

```text
map0_w = map0_h = map0_d = 255 + 1 = 256
l2_eb = 0
l2_ns = 0
```

map0_d在后续文档公式中未被使用，本次不擅自增加深度因子。

## 3. sw_mode_dec

```text
SW_256KB_3D → blk_type=SZ_256KB，sw_type=SW_S_3D
linear = 0
```

## 4. macro_blk_size_calc

```text
l2_ms = 18
l2_ms_128B = 11
ms_mask_128B = 0x7FF
macro block bytes = 1 << 18 = 0x40000
```

## 5. macro_block_dim_calc

```text
dim3D = 1
msaa = 0
block_size_elements = 18 - (0+0) = 18
3D查表索引：(l2_ms[4:1], l2_eb) = (9,0)
l2_blk_w/h/d = 6/6/6
macro block = 64×64×64
```

2D与linear分支本次不执行。

## 6. 256B对齐辅助量

```text
l2_blk_w_slice = 6
l2_ms_256B = 11 - 1 = 10
l2_mip_offset = 18 - 8 = 10
```

## 7. al_num_mips_inside_tail

```text
is_3d_blk_size = 1
l2_ms_256B = 10 → l2_ms_256B_3d = 7
l2_ms_256B_eff = 7
num_mips_in_tail = 7 + 4 = 11
```

## 8. in_tail_chk

```text
mips_outside_tail = 12 - 11 = 1
符号位 = 0
in_tail_chk[m] = (m > 1)
m0、m1为0；m2至m16为1
```

## 9. y_bias

```text
sw_type = SW_S_3D
256KB按文档注释满足blk_type[0]=1
y_bias = 1
```

## 10. mip0尺寸padding

```text
pad_sz_mask = (1<<6)-1 = 0x3F
pad_out = (256>>6) + |(256 & 0x3F)
        = 4 + 0 = 4
Wb[0] = Wb0 = 4
Hb[0] = Hb0 = 4
Wb_slice[0] = Wb_slice0 = 4
```

## 11. pad_data_sz_w/h

```text
pad_data_sz_w = 1<<6 = 64
pad_data_sz_h = 1<<6 = 64
```

## 12. W_H_block_calc及PAD宏

```text
m=1：(4>>1)+低1位是否非零 = 2+0 = 2
m=2：(4>>2)+低2位是否非零 = 1+0 = 1
m≥3：(4>>m)+低m位是否非零 = 0+1 = 1
```

三个数组均为：
```text
[4,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
```

PAD宏将切片限制在有效存储宽度内，4只有bit2为1，高位补0，不改变上述结果。

## 13. mip0是否在tail

```text
w_tail_sz = 64
h_tail_sz = 32
in_miptail[0] = (256<=32) & (256<=64) & in_tail_chk[0] = 0
```

## 14. CHK_NEXT_IN_MIPTAIL

| 循环m | Hb[m]<=1 | Wb[m]<=2 | in_tail_chk[m+1] | in_miptail[m+1] |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 1 | 1 | 0 |
| 2 | 1 | 1 | 1 | 1 |
| 3至15 | 1 | 1 | 1 | 1 |

因此mip0至mip2不在tail；mip3起为tail标志1。请求范围只到mip12。

## 15. tail_mipid_calc

```text
tail_mipid_raw初始17
i=3：in_miptail[3] ^ in_miptail[2] = 1 → 更新为3
其余位置不更新
maxmip==0：否
(l2_ms_128B>>1)==0：5==0，否
tail_mipid = tail_mipid_raw = 3
```

## 16. 高mip的mipsize

```text
mip_idx=16…6均大于tail_mipid=3
mipsize[6…16]=0
```

## 17. mip_mask、maxmip_mask及使能

```text
mip_mask = (1<<(0+1))-1 = 0x00001
maxmip_mask = (1<<(12+1))-1 = 0x01FFF
slice_input_en = 0x01FFF
mip_off_input_en = 0x01FFF & ~0x00001 = 0x01FFE
```

slice选择mip0至12；mip offset选择mip1至12。

## 18. S2 pitch

```text
pitch = Wb[0] << 6 = 4<<6 = 256
```

## 19. 低mip的mipsize

```text
mipsize[5]=0
mipsize[4]=0
mipsize[3]=1         // 首个tail mip记1
mipsize[2]=1×1=1
mipsize[1]=2×2=4
mipsize[0]=4×4=16
```

## 20. 分组求和

```text
高组mip6至16：
mip_offset_in_blks_high = 0
slice_b_high = 0

低组：
mip_offset_in_blks_low = 4+1+1+0+0 = 6
slice_b_low = 16+4+1+1+0+0 = 22

mip_offset_in_blks = 6
slice_b = 22
```

### 完整数组

| mip | Wb | Hb | Wb_slice | in_tail_chk | in_miptail | mipsize | slice_en | offset_en |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 4 | 4 | 0 | 0 | 16 | 1 | 0 |
| 1 | 2 | 2 | 2 | 0 | 0 | 4 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 |
| 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 4 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
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

## 21. 第一模块输出

```text
pitch = 256
slice = 22<<(6+6) = 90112 = 0x16000
mip_offset_b = 6<<10 = 6144 = 0x1800       // 256B单位
mip_offset_bytes = 0x1800<<8 = 0x180000
mip_in_tail = (0<3) ? MAXMIP : ... = 17
l2_ms = 18
l2_blk_w/h/d = 6/6/6
l2_blk_w_slice = 6
l2_blk_width/height/depth别名 = 6/6/6
```

mip0偏移不为0是当前文档“累加后续mip”的公式结果。17不是第17个tail mip，而是不在tail的标记。

## 22. 模块间辅助值

```text
l2_block_ms = 18
l2_ms_odd = 18[0] = 0
l2_block_ms_128B = 18-7 = 11
```

## 23. tail模块准备

```text
输入mip_in_tail=17，l2_ms_odd=0，l2_eb=0，l2_ns=0，sw_type=SW_S_3D
l2_data_block_size_256B = 11-1 = 10
num_mips_in_tail = 11
```

## 24. micro_block_dim_calc

```text
block_bits = 8-(0+0)=8
2D候选：l2_2d_blk_w=4，l2_2d_blk_h=4
case(8)：q_3=2，r_3=2
3D候选：
l2_3d_blk_d=2+1=3
l2_3d_blk_w=2+1=3
l2_3d_blk_h=2
选择3D：
l2_ublk_w/h/d=3/2/3
micro block=8×4×8
```

## 25. mip_in_tail_reverse

```text
reverse = 11-(17+1) = -7
```

按本次MAXMIP_WIDTH=5，结果宽度为7位：
```text
-7 → 7'b1111001
reverse[6] = 1
```

## 26. byte_offset分支

符号位为1，直接命中第一分支：
```text
byte_offset = 0
```

不执行reverse>6分支，也不执行reverse<<8分支。这里必须先看符号位，不能把补码121当成正数进入大偏移计算。

## 27. microblock坐标拆位

```text
byte_offset[19:8] = 0
x_mip_micro_block = 0
y_mip_micro_block = 0
```

## 28. 奇偶交换

```text
l2_ms_odd=0，不交换
x_mip_micro_block_final=0
y_mip_micro_block_final=0
```

## 29. tail origin输出

```text
x_mip_in_tail_orig=0<<3=0
y_mip_in_tail_orig=0<<2=0
z_mip_in_tail_orig=0
```

本例非tail时origin为0，是文档负数分支实际算出的结果。

## 30. 查表坐标

```text
x_in_sheet=0+69=69
y_in_sheet=0+134=134
z_in_sheet=0+195=195
```

此3D表只读取坐标bit0至bit5，等价于取模64：
```text
x低6位=5=000101b
y低6位=6=000110b
z低6位=3=000011b
```

更高位进入块索引计算，并未丢失。

## 31. blk_offset位映射

```text
blk_offset[17:0] =
{y5,z5,x5,y4,z4,x4,y3,z3,x3,y2,z2,x2,z1,y1,y0,z0,x1,x0}
```

| 地址位 | 来源坐标位 | 值 |
|---:|---|---:|
| 17 | y[5] | 0 |
| 16 | z[5] | 0 |
| 15 | x[5] | 0 |
| 14 | y[4] | 0 |
| 13 | z[4] | 0 |
| 12 | x[4] | 0 |
| 11 | y[3] | 0 |
| 10 | z[3] | 0 |
| 9 | x[3] | 0 |
| 8 | y[2] | 1 |
| 7 | z[2] | 0 |
| 6 | x[2] | 1 |
| 5 | z[1] | 1 |
| 4 | y[1] | 1 |
| 3 | y[0] | 0 |
| 2 | z[0] | 1 |
| 1 | x[1] | 0 |
| 0 | x[0] | 1 |

```text
置位地址位：8、6、5、4、2、0
blk_offset=0x100+0x40+0x20+0x10+0x4+0x1
          =0x175=373
```

## 32. 基地址swizzle提取与清理

```text
baseAddr256B[11:0] = 0
(ms_mask_128B>>1)[11:0] = 0x3FF
swizzle_bits_256B = 0 & 0x3FF = 0

baseAddr256B_out = 0x00300000
mipoffset_BaseAddr256B_out
= 0x00300000 + 0x1800
= 0x00301800
```

清理时按12位低字段拆分，原基址低字段全0，因此本例清理不改变基址。mip偏移在提取swizzle之后加入，不能再把新增0x1800当基地址swizzle提取一次。

## 33. block_index_calc：块单位换算

```text
log2_blk_slice = 6+6=12
pitch_b=256>>6=4
slice_b=90112>>12=22
xb=69>>6=1
yb=134>>6=2
zb=195>>6=3
```

三个方向的块编号都非0。特别注意，slice_b是22，来自当前文档累计mipsize的公式，不是仅计算mip0平面的4×4=16。

## 34. 分段乘法与块索引

```text
slice_times_z_l = slice_b[15:0] * zb = 22*3=66
slice_times_z_h = slice_b的高位 * zb = 0*3=0
pitch_times_y = 4*2=8
blk_index_pitch = 8+1=9
blk_index_slice = 66+(0<<16)=66

l2_ms_slice=18
blk_index=(9<<18)+(66<<18)
         =0x00240000+0x01080000
         =0x012C0000
         =19660800
```

这是75个宏块对应的字节偏移。这里按原文执行加法，不把块索引公式改写成OR。

## 35. slice对齐与linear候选

```text
l2_ms_slice=(18<8)?8:18=18
micro_offset_linear=69[6:0]<<0=69=0x45
```

linear=0，linear候选不被选中。

## 36. 当前版本的XOR与低位候选

```text
ms_mask_256B=0x7FF>>1=0x3FF

blk_offset_final
= linear ? ... : blk_offset[7:0]
= 0x75

swizzle_bits
= (blk_offset高于bit7的部分 & ms_mask_256B) ^ swizzle_bits_256B
= (0x1 & 0x3FF) ^ 0
= 1
```

当前版本用低8位作为blk_offset_final，不能把旧版完整0x175仍记为该变量值。

## 37. addr_offset合成

```text
blk_index[47:0] = 0x012C0000
(swizzle_bits<<8)[19:0] = 0x100
blk_offset_final[45:0] = 0x75    // 按足宽零扩展

addr_offset=0x012C0000 | 0x100 | 0x75
           =0x012C0175
```

本例三项置位区域不重叠，OR得到上述值。这里不将最终OR改成新的算法。

## 38. 顶层输出

```text
{mipoffset_BaseAddr256B_out,8'd0}
=0x00301800<<8
=0x30180000

address_final=0x30180000+0x012C0175
             =0x31440175
             =826540405

mipid_in_tail=(mip_in_tail!=MAXMIP)
              =(17!=17)
              =0
```

## 39. 独立算术交叉核对及关键区别

将同一路径重新按“宏块数量+块内偏移”合并：

```text
相对原始surface base的宏块数
= mip_offset_in_blks + zb*slice_b + yb*pitch_b + xb
= 6 + 3*22 + 2*4 + 1
= 81

最终地址
=0x30000000 + 81*0x40000 + 0x175
=0x30000000 + 0x01440000 + 0x175
=0x31440175
```

与逐段结果一致。

| 量 | 本例值 | 含义 |
|---|---:|---|
| tail_mipid | 3 | 整个资源第一个tail mip |
| mip_in_tail | 17 | 当前mip0不在tail的标记 |
| byte_offset | 0 | 原点生成中间量 |
| mip_offset_b | 0x1800 | 256B单位的mip偏移 |
| blk_index | 0x012C0000 | 已含Z/Y/X块位置的字节偏移 |
| blk_offset | 0x175 | 块内位映射完整结果 |
| blk_offset_final | 0x75 | 最终合成用低8位 |
| swizzle_bits<<8 | 0x100 | 最终合成用高位部分 |

本例验证了当前文档输入到输出的这条计算路径；没有据此宣称与上游完整AddrLib或硬件布局一致。基地址swizzle=0，本例不构成非零swizzle的测试。
