# ADDRLIB mip 参数计算：跨代算法与RTL片段边界

本文件更正旧稿把整段片段称为GFX10的归属。模式/linear策略主要是GFX12，容量和布局数学多代共用。依据见[完整逐段审计](addrlib_version_audit.md)。

## 1. 参数和block几何

所有log2宽高深度均以element为坐标，BPE是每element的byte数；压缩格式需先由格式层变换。resourceType=3D不意味着一定使用3D swizzle。公开GFX10按标准/显示swizzle判thick，GFX12按SW_S_3D计算这里的3D表。

L是log2(block bytes)，e是log2(BPE)，s是log2(samples)。GFX12 fixed tiled L=8/12/16/18：
2D的w=ceil((L-e-s)/2)、h=floor((L-e-s)/2)，d=0。
3D的维度见原文表及审计，上游不支持3D swizzle MSAA。

linear渲染pitch为128B对齐，slice计算的pitch为256B对齐；这不能当作GFX10常规linear策略。

## 2. 尺寸输入与ceil

对真实正尺寸D：
```text
blocks(D,k) = (D >> k) + ((D & ((1<<k)-1)) != 0)
Wb[m] = ceil(Wb[0] / 2^m)
```

ceil(ceil(D/2^k)/2^m)=ceil(D/2^(k+m))，故先求块数再ceil缩小具有数学依据。[GFX12 shift_ceil/getMipSize2dCompute](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L211)

但ADDRLIB.md输入写minus-one，接口恢复没有展示。若Dminus1传入上述公式，真实宽1会给0块；必须先恢复D或使用适合minus-one的式子。原注释“至少一块”也不适用于未经clamp的0输入。

公开内部GetMipSize使用ceil；不要据此把图形API的所有mip/压缩格式尺寸规则统一改成ceil，格式预处理是另一层。

## 3. tail容量

```text
E = L                       // 2D swizzle
E = L - floor((L-8)/3)       // 3D swizzle
C = 1                       // E<=8，仅内部占位
C = 1 + 2^(E-9)             // 9<=E<=11
C = E-4                     // E>11
```

| block | 2D容量C | 3D容量C | 3D的E-8 |
|---|---:|---:|---:|
| 4KB | 8 | 5 | 3 |
| 64KB | 12 | 10 | 6 |
| 256KB | 14 | 11 | 7 |

旧稿将256KB的case输入抄成12，应为10（18-8）。上游解释3D修正来自tail原点不使用Z项，不仅是mip体积缩小。[getNumMipsInTail](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L514)

## 4. tail条件必须合取

```text
count_ok(m) = (maxmip + 1 - m <= C)
size_ok(m)  = (W[m] <= tailW) && (H[m] <= tailH)
in_tail(m)  = count_ok(m) && size_ok(m) && supports_tail
```

maxmip是末级ID，numMipLevels=maxmip+1。
B=maxmip-C是**数量限制产生的排除边界**。m>B只是候选；真正first还可能被尺寸推迟。
RTL形式为(m>B) OR B[msb]，只取符号位，不能OR整个多位B。

GFX12 2D减半block宽；3D 4KB/256KB减半高、64KB减半宽。[getMipInTaleMaxSize](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L118)
blk_type[0]能否实现该选择需枚举定义证明；源码注释SW_TYPE[0]不是实际表达式。

用上一mip块数判断下一mip：
X减半情况下Wb[m]<=1且Hb[m]<=2；Y减半时Wb[m]<=2且Hb[m]<=1。该变换依赖正尺寸和ceil递推；mip0仍须单独检查。

linear、256B、单mip不启用tail。无tail时RTL用MAXMIP哨兵，公开firstMipIdInTail字段用numMipLevels。

## 5. mipsize、倒序布局、单位

tail首级计一个XY块、后续tail级计0；普通级计Wb_slice×Hb。此为slice/XY层计账，不可等同完整3D分配。

当前mip偏移选择更高mip ID的尺寸，较小mip和tail位于低地址，大mip随后。普通mip的macroBlockOffset由小级向大级累加。[GFX10布局](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3911)

mip_mask覆盖0..current；maxmip_mask覆盖0..maxmip。意图为：
```text
maxmip_mask = (wide_one << (maxmip+1)) - 1
mip_off_input_en = maxmip_mask & ~mip_mask
```

原代码缺正确括号/完整位宽，且mip_off_en别名未定义，不是可直接编译的实现。

| 量 | 由片段公式可确定的语义 |
|---|---|
| Wb/Hb | XY方向块数 |
| mipsize/slice_b | XY块计数 |
| slice_out | XY元素位置数；字节需乘BPE和samples |
| mip_offset_b_out | 256B单位的偏移计数；64KB一块对应256，而非65536 |
| pitch_out | 按宏块宽还原的元素宽；原注释减一未实现，tail pitch亦需单独核对 |
| mip_in_tail_out | 相对tail级ID或哨兵 |

上游3D还处理对齐深度、blockSlices、sliceSize和macroBlockOffset；不要把mipsize=1误写成任意3D资源整个tail恰好只有一个物理块。

## 6. 示例纠正

256KB 3D、1BPE、256³、maxmip=12：
C=11；数量最早候选mip2，但tail阈值为64×32。
mip2=64×64不满足高度；mip3=32×32且剩10级，故first=3。
mip4：t=1，reverse=9，byte_offset=0x2000，origin=(32,0,0)。

完整位拆解见[计算例子](three_address_calculation_examples.md)。
