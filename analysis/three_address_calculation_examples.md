# GFX12 AddrLib：两个地址例子与一个tail原点例子

依据[固定GFX12模式表](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12SwizzlePattern.h)、[布局/地址实现](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp)和[shared参考模型](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp)。这些SW_*_2D/3D名称属于GFX12模式集合，不能称为GFX10实例。前两例byte-in-element=0，例2明确令pipeBankXor=0；例3只计算布局原点，没有指定texel坐标，不能声称得出了最终地址。

## 1. SW_256B_2D，1X，1BPE，64×64，mip0

base=0x10000000，x=20，y=18，单mip。
block=16×16，元素pitch=64，pitchInBlocks=4（旧稿把4直接称为pitch，单位不清）。
xb=1，yb=1，blockIndex=1×4+1=5，macroOffset=0x500。

PATINFO选nibble1[0]，按低位到高位：
```text
A[0..7] = X0, X1, Y0, X2, Y1, Y2, X3, Y3
```

块内x=4、y=2，使A3=A4=1，blkOffset=0x18；256B不应用base-address XOR。
最终地址=0x10000000+0x500+0x18=**0x10000518**。[表项](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12SwizzlePattern.h#L40)

## 2. SW_64KB_2D，4X，4BPE，1024×1024，mip0

base=0x20000000，x=130，y=70，sample=2，单mip，pipeBankXor=0。
blockLog2=16，e=2，s=2；block=64×64，64×64×4×4=65536B。
元素pitch=1024，pitchInBlocks=16；xb=2，yb=1，blockIndex=18，macroOffset=0x120000。
块内坐标为x=2、y=6。

上游PATINFO[4BPE]选择nibble1[12]、nibble2[5]、nibble3[5]。按**低位到高位**展开：
```text
A[0..15] =
0, 0, S0, S1, X0, Y0, X1, Y1,
Y2, X2, Y3, X3, Y4, X4, Y5, X5
```

置位：A3（S1）、A6（X1）、A7（Y1）、A8（Y2）。
blkOffset=0x8+0x40+0x80+0x100=**0x1C8**。
最终地址=0x20000000+0x120000+0x1C8=**0x201201C8**。[PATINFO](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12SwizzlePattern.h#L130)；[nibble数组](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12SwizzlePattern.h#L211)

旧稿0x1340既不是正确上游映射结果，也不是其自身所列映射的结果（原排列实际给0x2C8）。不得保留旧值作为验证基准。非零pipeBankXor需要在blkOffset上异或，再组合最终地址。

## 3. SW_256KB_3D，1X，1BPE，256³，maxmip=12，mip4

本例按原始给定的maxmip=12复算片段数学。256³通常完整mip链至mip8；12意味着继续请求1尺寸级，这里不声称该参数组合满足所有图形API的合法性规则。

block=64×64×64=256KB。
E=18-floor((18-8)/3)=15，所以C=11。
3D 256KB减半高度：tail阈值为**64×32**。

| mip | 宽×高 | 剩余级数13-m | 数量<=11 | 尺寸满足64×32 | 进入tail |
|---:|---|---:|---|---|---|
| 1 | 128×128 | 12 | 否 | 否 | 否 |
| 2 | 64×64 | 11 | 是 | 否 | 否 |
| 3 | 32×32 | 10 | 是 | 是 | 是 |
| 4 | 16×16 | 9 | 是 | 是 | 是 |

因此**first=3**，不是2。旧稿只检查maxmip-C=1的数量边界，漏了高度条件；“上次已纠正为mip2”的结论应撤销。

mip4的t=4-3=1，reverse=11-1-1=9。
byte_offset=16<<9=**0x2000**。

```text
byte_offset >> 8 = 0x020
X取原offset的9,11,13,15,17,19位 -> Xmicro=4
Y取原offset的8,10,12,14,16,18位 -> Ymicro=0
```

L=18为偶数，无swap。
1BPE 3D微块=8×4×8，所以origin=(4×8,0×4,0)=**(32,0,0)**。

mip4 texel坐标(x,y,z)将变成(x+32,y,z)；逻辑16³范围映射到x=32..47、y=0..15、z=0..15，仍在64³块内。实际byte地址还需具体texel坐标、3D pattern及XOR输入。

另一个独立位拆解错误：即使假设offset=0x1000，offset>>8=0x010也应给Xmicro=0、Ymicro=4、origin=(0,16,0)，不是旧稿(0,32,0)。

## 汇总

| 例子 | 已复算结果 | 范围 |
|---|---|---|
| 1 | 0x10000518 | 完整指定坐标的地址 |
| 2 | 0x201201C8 | pipeBankXor=0、byte-in-element=0 |
| 3 | first=3，offset=0x2000，origin=(32,0,0) | tail布局中间结果，不是最终地址 |

复算脚本：[verify_version_audit.ps1](verify_version_audit.ps1)。它检验文档公式和上游提取的pattern，不替代完整驱动或RTL仿真。
