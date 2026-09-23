# GFX10 mip tail：真实布局、偏移与地址组合

本稿替换旧版正向“先Mip0再tail”的抽象，使用[AMD固定提交源码](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3801)。完整跨代差异见[审计表](addrlib_version_audit.md)。以下关注多mip、macro-tiled数据surface；metadata、linear、micro-tiled有各自路径。

## 1. tail的用途与条件

多个小mip共享宏块分配，避免每级独立占完整宏块。它们仍使用swizzle，不会因此改成linear。firstMipIdInTail同时受宽高阈值和剩余级数限制，不是只要足够小就能进入。

2D thin的阈值通常为blockWidth/2、blockHeight；特定Z-order/HTILE workaround会进一步调整。thick的阈值由blockSizeLog2%3决定。需要以实际swizzle和配置为准。[上游判定](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3843)

## 2. tail不是放在所有大mip之后

对单个2D slice，设first=K、块字节数B：
```text
低地址 -> [共享tail块] [Mip K-1] [Mip K-2] ... [Mip0] -> 高地址
```

当有tail时，普通mip累加器macroBlkOffset初始化为B，然后i=K-1递减到0，先写该级offset再增加该级尺寸；tail级macroBlockOffset=0。[上游循环](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3911)

因此旧稿tailOffset=Align(sum(non-tail mip sizes),tailAlignment)不是此GFX10路径。若给“tail region base”自定义一个名字，它在上述单slice示例中相对于slice base为0。数组/厚资源还有slice/group基址，不可直接将此0推广成整个资源任意切片的地址。

旧稿独立对齐算术也错：AlignUp(0x05523400,0x40000)=0x05540000，不是0x05600000。此算术例不作为GFX10 tail算法。

## 3. 三个offset字段不能互换

| 字段 | 在此路径中的含义 |
|---|---|
| macroBlockOffset | 普通mip宏块基址，tail级为0 |
| mipTailOffset | tail原点编码：(r>6)?16<<r:r<<8 |
| offset | pMipInfo暴露的mip偏移；tail时为mipTailOffset×tailMaxDepth |

其中r=C-1-(mip-first)。C是最大容量，tailMaxDepth为相应微块深度层数，thin时为1。字段offset不能在所有资源上简单等同于macroBlockOffset+mipTailOffset。[字段赋值](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3932)

## 4. 已平移坐标的swizzle不能再重复加tail offset

[GFX10 ComputeSurfaceAddrFromCoordMacroTiled的方程路径](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L4786)把tail原点加到坐标：
```text
x' = x + mipTailCoordX
y' = y + mipTailCoordY
z' = slice + mipTailCoordZ

blkOffset = Equation(x' << log2(BPE), y', z')
address = sliceSize * sliceId
        + macroBlockOffset
        + (blkIdx << blockSizeLog2)
        + (blkOffset XOR pipeBankXor)
```

这里address是相对资源基址的地址；如果需要GPU地址，再加资源base。
tail原点已进入Equation，不再额外加一次mipTailOffset。旧稿tailOffset+MipTailOffset+InTailSwizzledOffset如果后者使用了平移坐标，会重复计算。swizzle也不是一般可加的线性byte映射。

pipeBankXor在方程结果上应用；它并非另加一个任意bank偏移。图中的pipe/bank是AddrLib布局概念，不足以推导外部DRAM channel/bank拓扑。

## 5. 3D和数组

isThin决定sliceSize/sliceId的计算；thick要使用blockSlices及slice/blockSlices，surface占用包含深度对齐。z-origin=0只说明原点不沿Z平移，实际Z坐标仍进入方程。

整个tail在XY计账中合并为一个region，并不保证任意3D资源只消耗一个物理宏块。不要将2D的“一个tail块”未经限定推广到3D。

## 6. metadata范围

DCC、HTILE、CMASK/FMASK具有独立的支持条件和地址计算路径。本文数据surface的尾部公式不能直接复制为metadata实现，也不能仅从函数名称推定功能已实现。GFX10 HwlComputeHtileCoordFromAddr在本固定提交中是ADDR_NOT_IMPLEMENTED桩。

源码阅读顺序：ComputeSurfaceInfoMacroTiled → firstMipIdInTail/offset字段 → ComputeSurfaceAddrFromCoordMacroTiled → ComputeOffsetFromEquation。这条路径能直接核对布局和最终地址，避免以未定义的tailOffset替代真实字段。
