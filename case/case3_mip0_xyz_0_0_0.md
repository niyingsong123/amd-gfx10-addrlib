# case3：Linear 1×2 的 mip0 slice 差异

## 0. 状态、来源与计算范围

- 可信状态：**手工公式推导，待独立确认；未加入可信基准。** 放入 case/ 不表示已获用户确认或完成算法验证。
- 整理日期：2026-09-24。
- 对比对象：当前文档的 mipmap_param_calc_core_gc 与公开 GFX12 非 shared 实现。
- AMD PAL 固定提交：`c5e800072a32f68b6ccc4422936d96167c6e0728`，分支条件 `ADDR_GFX12_SHARED_BUILD=0`。
- 默认普通格式、二维单层资源、单采样；无 custom pitch/height，denseSliceExact=0。
- 本例尺寸和布局参数对应已归档 Linear 缩减反例的关键输入；坐标统一选为 (0,0,0)，仅研究布局模块。
- 本文记录公式代入结果，没有执行模型、随机测试、完整 C++ 或 RTL 仿真；不计算最终 texel 地址，也不修改可信原文。

| 源文件 | SHA256 |
| --- | --- |
| [ADDRLIB.md](../ADDRLIB.md) | `537CFA6D9FAFBAF3601B219B686D94CAA4B7C69FDFE89005DFF36A0B4CB6D3BB` |
| [gfx12addrlib.cpp](../scripts/mipmap_compare/upstream/src/gfx12/gfx12addrlib.cpp) | `9210BB10078C48A3757E1F1A2F9483D5A355B04D83FBCA19A65485938B1DA8DB` |
| [addrlib3.cpp](../scripts/mipmap_compare/upstream/src/core/addrlib3.cpp) | `068C124EF619AAD4D83F636BEE425146B9BF590E47D899F7C751A1736676A8FD` |

源码位置：ADDRLIB.md 第 123–240、320–339、411–559 行；gfx12addrlib.cpp 的 GetMipOffset 第 450–545 行；addrlib3.cpp 的 CanTrimLinearPadding 第 1007–1014 行。汇总背景见 [GFX12 差异分析](../regression_0924/GFX12_MATCHING_ANALYSIS.md)。

位宽约定：MAXMIP=17；采用足宽非负整数完成尺寸、乘法、移位和掩码运算，负数中间量保留符号；只执行文档明确给出的位切片和掩码，不自行截断未知 RTL 位宽。

单位：pitch 为元素数，slice 为模块的元素面积；本例每元素 1B、单采样、二维，所以 slice 的数值等于字节数。mip_offset_b 为 256B 单位。记 AlignUp(v,a)=ceil(v/a)×a。

## 1. 全部 12 个输入

~~~text
x = 0
y = 0
z = 0
s = 0
map0_w_minus_1 = 0
map0_h_minus_1 = 1
map0_d_minus_1 = 0
sw_mode = SW_LINEAR
log2_num_samples = 0
log2_element_bytes = 0
mip_level = 0
maxmip = 0
~~~

恢复尺寸及 GFX12 输入语义：

~~~text
map0_w = 0 + 1 = 1
map0_h = 1 + 1 = 2
map0_d = 0 + 1 = 1
l2_eb = 0，element_bytes = 2^0 = 1B
l2_ns = 0，numSamples = 2^0 = 1
numMipLevels = maxmip + 1 = 1

GFX12 resourceType = 2D
GFX12 swizzleMode = ADDR3_LINEAR
GFX12 bpp = 8
GFX12 numSlices = 1
~~~

x/y/z/s 不参与本模块公式，也不作为表面布局接口的坐标输入。文档不使用 map0_d；GFX12 的 numSlices 则参与本例裁剪条件。

## 2. 文档 S0：模式、块尺寸和对齐

~~~text
SW_LINEAR → blk_type=SZ_LIN，sw_type=SW_L
linear = 1
dim3D = 0
msaa = 0

l2_ms = 7
l2_ms_128B = 0
ms_mask_128B = 0
block_size_elements = 7 - (0 + 0) = 7

l2_blk_w = 7
l2_blk_h = 0
l2_blk_d = 0
rendering 块尺寸 = 128×1×1 元素

l2_blk_w_slice = 8 - l2_eb = 8
slice 宽度对齐单位 = 256 元素

l2_ms_256B = 0
l2_mip_offset = 0
~~~

文档同时保留两种尺度：128B 用于 pitch，256B 用于普通 slice 计算。此处不能把它们当成同一个宽度。

## 3. 文档 S1：padding 和 tail

~~~text
Wb[0]       = ceil(1 / 128) = 1
Hb[0]       = ceil(2 / 1)   = 2
Wb_slice[0] = ceil(1 / 256) = 1
~~~

Linear 对应 num_mips_in_tail=1，mips_outside_tail=0-1=-1，y_bias=0；但最终 tail_mipid 有模式覆盖条件：

~~~text
maxmip == 0                     → 真
(l2_ms_128B >> 1) == 0          → 真
tail_mipid = MAXMIP = 17
~~~

因此本例不使用 tail。内部对其他级别计算的 tail 候选量不改变该输出，且 maxmip=0 会屏蔽全部高于 mip0 的空间贡献。

## 4. 文档 S2：pitch、slice 和宏块偏移

~~~text
mipsize[0] = Wb_slice[0] × Hb[0]
           = 1 × 2
           = 2

maxmip_mask = (1 << (0 + 1)) - 1 = 0b1
mip_mask    = (1 << (0 + 1)) - 1 = 0b1

slice_input_en   = 0b1
mip_off_input_en = 0b1 & ~0b1 = 0

slice_b = mipsize[0] = 2
mip_offset_in_blks = 0
~~~

~~~text
pitch = Wb[0] << l2_blk_w
      = 1 << 7
      = 128 元素

slice = slice_b << (l2_blk_w_slice + l2_blk_h)
      = 2 << (8 + 0)
      = 512 元素面积
      = 512B

mip_offset_b = 0 << l2_mip_offset = 0
mip_offset_bytes = 0 × 256 = 0B

mip_in_tail = 17                 // mip_level=0 < tail_mipid=17
~~~

## 5. GFX12：从普通 slice 到 mip0 裁剪

GFX12 的物理 blockExtent 为 256×1×1 元素；rendering pitch 仍按 128B 对齐。

~~~text
pitchImgData   = AlignUp(1, 128 / 1) = 128 元素
pitchSliceSize = AlignUp(128, 256 / 1) = 256 元素
height = AlignUp(2, 1) = 2
depth  = 1

sizeExceptPitch = height × numSamples × element_bytes
                = 2 × 1 × 1
                = 2

普通 sliceSize = pitchSliceSize × sizeExceptPitch
               = 256 × 2
               = 512B

sliceDataSize = AlignUp(pitchImgData × sizeExceptPitch, 256)
              = AlignUp(128 × 2, 256)
              = 256B
~~~

**分歧发生在 GetMipOffset 的 mip0 裁剪分支。** CanTrimLinearPadding 的实际条件为：

~~~text
resourceType 不是 3D  → 真
numSlices <= 1       → 真
Linear               → 真
当前 mipIdx == 0     → 真
~~~

无自定义高度，所以执行：

~~~text
pitchSliceSize = pitchImgData = 128
sliceSize = sliceDataSize = 256B
hwSliceSize = 256B
~~~

只有一个 mip，最终原始 GFX12 布局字段为：

~~~text
pMipInfo[0].pitch = 128 元素
pMipInfo[0].pitchForSlice = 128 元素
pMipInfo[0].macroBlockOffset = 0B
sliceSize = 256B
blockExtent = (256, 1, 1)
firstMipIdInTail = 1             // 等于 numMipLevels，表示无 tail
~~~

## 6. 九个输出及差异解释

GFX12 栏采用本轮比较口径：sliceSize 换为模块元素面积，macroBlockOffset 除以 256，无 tail 统一为哨兵 17。l2 字段为语义推导，不能当成官方 API 的同名输出。

| 模块输出 | 当前文档 | GFX12 同口径值 | 解释 |
| --- | ---: | ---: | --- |
| pitch | 128 | 128 | rendering pitch 一致 |
| slice | **512** | **256** | mip0 裁剪产生数值差异 |
| mip_in_tail | 17 | 17 | 均无 tail |
| mip_offset_b | 0 | 0 | 唯一 mip 的宏块偏移为 0 |
| l2_ms | 7 | 7 | rendering 对齐尺度 |
| l2_blk_w | 7 | 7 | rendering 宽度指数 |
| l2_blk_h | 0 | 0 | 高度对齐为 1 |
| l2_blk_d | 0 | 0 | 深度对齐为 1 |
| l2_blk_w_slice | 8 | 8 | 普通 slice 对齐尺度；mip0 裁剪单独覆盖其贡献 |

Linear 的 GFX12 原始物理块宽为 256，物理块大小指数为 8；表中 7 对应 rendering 尺度，不能声称原始 blockExtent 与文档块宽相同。

| 路径 | 本例计算 |
| --- | --- |
| 文档普通 slice | 256×2=512B |
| GFX12 mip0 裁剪 | AlignUp(128×2,256)=256B |

两边 pitch 都是 128 元素；差异改变的是分配量。单层非 3D Linear 才满足此裁剪条件，即使资源包含多个 mip，也只替换 mip0 的贡献。不能把全部 mip 的 l2_blk_w_slice 从 8 改成 7。

## 7. 建议及验证状态

候选改动是在满足上述条件时，用裁剪贡献替换普通 mip0 贡献：

~~~text
slice_bytes_new = slice_bytes_old
                - ordinary_mip0_bytes
                + AlignUp(rendering_pitch0 × height0 × element_bytes, 256)
~~~

本例得到 512-512+256=256B。当前 mip 后面没有其他 mip，所以宏块偏移仍为 0。

本例只完成源文件核对和手工代入；未实施候选修改，未重新运行云端样本，未宣称修改后全部匹配。可信状态需独立确认。
