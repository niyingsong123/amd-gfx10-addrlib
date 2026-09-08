# ADDRLIB.md 的 mip-tail 注释（经源码核对）

核对来源：AMD PAL 固定提交 `c5e800072a32f68b6ccc4422936d96167c6e0728`。详细的行号、三代差异及片段缺陷见[逐段版本审计](analysis/addrlib_version_audit.md)。

## 1. 版本与输入语义

此伪RTL的模式和linear对齐策略主要对应GFX12；tail数学在GFX10/11/12中有共用部分，不能统一冠以GFX10。本文保留原片段，解释其算法意图；它缺少位宽、接口预处理和完整语法，不是已验证RTL。

设C=num_mips_in_tail（最大容量），first=tail_mipid，mip为当前级，maxmip为末级ID。实际tail级数T=maxmip-first+1，可以小于C。

有效tail的相对编号t=mip-first，reverse=C-1-t。reverse=0是最大容量布局的最后位置，**实际链的最后一级不一定达到0**。例如64KB 2D，C=12，实际仅6级tail：reverse为11..6，不是5..0。[上游GFX10循环](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3938)

## 2. reverse 到 byte_offset

```text
r = C - 1 - t
r < 0: byte_offset = 0
0 <= r <= 6: byte_offset = r * 256
r > 6: byte_offset = 16 * 2^r
```

GFX12通过将负r钳位到0处理非tail哨兵，与上述输出一致。GFX10/11则在合法tail循环中计算此式。[GFX12参考函数](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L483)

| r | byte_offset（B） |
|---:|---:|
| 0 | 0 |
| 1 | 256 |
| 2 | 512 |
| 3 | 768 |
| 4 | 1024 |
| 5 | 1280 |
| 6 | 1536 |
| 7 | 2048 |
| 8 | 4096 |
| 9 | 8192 |
| 10 | 16384 |
| 11 | 32768 |

r>6仍可为tail内的较大mip，不能称为“tail外”。r=6的offset确为1536B，不能用16×2^6替代。

## 3. offset、占用与分配

256B是上述低区间**原点偏移的步长**，不是证明每个mip固定占256B。更不能从6个原点推出总tail footprint=1536B。二维宏块级布局会为整个tail计一个当前swizzle块；64KB模式为64KB。三维slice统计按blockSize/blockDepth计算，完整深度占用还涉及对齐切片数。

byte_offset不是mip自己的size，也不一定等于pMipInfo.offset：厚模式中后者还乘tailMaxDepth。[GFX10布局和字段赋值](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3874)；[GFX12对应代码](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L340)

## 4. 从byte_offset拆出XY微块索引

```text
X[j] = byte_offset[9 + 2*j]    (j=0..5)
Y[j] = byte_offset[8 + 2*j]    (j=0..5)
```

先去掉低8位，再取12位交错位；不可漏掉右移8这一步。

| byte_offset | byte_offset >> 8 | Xmicro | Ymicro |
|---|---|---:|---:|
| 0x1000 | 0x010 | 0 | 4 |
| 0x2000 | 0x020 | 4 | 0 |

这只是tail原点的布局编码，不是所有texel的通用Morton地址公式。[上游位拆解](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L367)

## 5. 奇数块指数

GFX12合法tiled块指数8/12/16/18均为偶数，此交换分支不启用。GFX10/11公开泛化代码对于奇数L先交换XY，还在e=log2(BPE)为奇数时执行：

```text
Y = (Y << 1) | (X & 1)
X = X >> 1
```

当前片段漏了后一步，不能证明其兼容旧VAR模式。三目式的分隔符也应为冒号，且micro_block/micro_blocks混名需要完整代码确认。[GFX10源码](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3963)

## 6. 微块尺寸与坐标缩放

上游tail微块令b=8-e：
2D：w=ceil(b/2)，h=floor(b/2)，d=0。
3D：q=floor(b/3)，r=b mod3，w=q+[r>1]，h=q，d=q+[r>0]。

这些w/h/d是log2尺寸。当前片段用8-e-s，多减了samples指数；仅s=0时可据此匹配所对照函数。linear在上游还有单独分支。[getMicroBlockSize](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L539)

```text
originX = Xmicro * 2^w
originY = Ymicro * 2^h
originZ = 0
```

z原点为0不代表3D深度不参与最终地址。每个texel仍需加原点后进入对应swizzle方程，并处理slice、macroBlockOffset与pipeBankXor。

## 7. surface级mipsize与输出单位

原片段：
tail前mipsize=Wb_slice×Hb；tail首级计1；其后计0。这是避免重复计算共享tail的**XY块统计**，不是每一级真实texel字节数。

slice_b是该统计的和；slice_out乘XY块尺寸后为元素位置数，转换字节还要BPE和samples，不能忽略3D slice/depth语义。mip_offset_in_blks选择当前mip之后的级数，符合倒序布局。

mip_offset_b_out=mip_offset_in_blks×2^max(L-8,0)使用256B单位；不是直接byte数。输入minus-one与输出减一注释和公式存在冲突，详见审计表，不将推测的接口行为写成事实。
