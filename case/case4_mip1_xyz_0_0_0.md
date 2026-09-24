# case4：4KB 二维 64×64 的 mip1 tail pitch 差异

## 0. 状态、来源与计算范围

- 可信状态：**手工公式推导，待独立确认；未加入可信基准。**
- 整理日期：2026-09-24。
- 对比对象：当前文档的 mipmap_param_calc_core_gc 与公开 GFX12 非 shared 实现。
- AMD PAL 固定提交：`c5e800072a32f68b6ccc4422936d96167c6e0728`，分支条件 `ADDR_GFX12_SHARED_BUILD=0`。
- 本例为便于手算构造的简单输入，不冒充已有云端样本编号或新增运行结果。
- 默认普通格式、二维单层资源、单采样、无自定义 pitch/height。
- 只分析布局模块的九个输出，不计算 tail 内原点和最终 texel 地址。没有执行模型、随机测试、完整 C++ 或 RTL 仿真，没有修改可信原文。

| 源文件 | SHA256 |
| --- | --- |
| [ADDRLIB.md](../ADDRLIB.md) | `537CFA6D9FAFBAF3601B219B686D94CAA4B7C69FDFE89005DFF36A0B4CB6D3BB` |
| [gfx12addrlib.cpp](../scripts/mipmap_compare/upstream/src/gfx12/gfx12addrlib.cpp) | `9210BB10078C48A3757E1F1A2F9483D5A355B04D83FBCA19A65485938B1DA8DB` |

源码位置：ADDRLIB.md 第 123–559 行，特别是第 387–399 行的 next-in-tail 判断及第 459 行的 pitch 输出；gfx12addrlib.cpp 的 GetMipOrigin 第 329–395 行、GetMipOffset 第 433–608 行、GetMaxNumMipsInTail 第 694–717 行、HwlGetMicroBlockSize 第 1810–1848 行、二维块与 tail 阈值公式第 2163–2248 行。背景见 [GFX12 差异分析](../regression_0924/GFX12_MATCHING_ANALYSIS.md)。

位宽约定：MAXMIP=17；足宽整数计算，保留负数中间量的符号；仅执行文档明确规定的位切片和掩码，不补设未知 RTL 截断。本例数值均可精确表示。

单位：pitch 为元素数，slice 为模块的元素面积；本例每元素 1B、单采样、二维，slice 数值等于字节数。mip_offset_b 为 256B 单位。AlignUp(v,a)=ceil(v/a)×a。

## 1. 全部 12 个输入

~~~text
x = 0
y = 0
z = 0
s = 0
map0_w_minus_1 = 63
map0_h_minus_1 = 63
map0_d_minus_1 = 0
sw_mode = SW_4KB_2D
log2_num_samples = 0
log2_element_bytes = 0
mip_level = 1
maxmip = 2
~~~

~~~text
map0_w = map0_h = 63 + 1 = 64
map0_d = 1
l2_eb = 0，element_bytes = 1B
l2_ns = 0，numSamples = 1
numMipLevels = maxmip + 1 = 3

GFX12 resourceType = 2D
GFX12 swizzleMode = ADDR3_4KB_2D
GFX12 bpp = 8
GFX12 numSlices = 1
~~~

x/y/z/s 不参与布局计算。这里使用包含 mip0、mip1、mip2 的截断 mip 链，重点比较 mip1 的输出。

| mip | 逻辑宽×高 | 从本级开始剩余 mip 数 |
| --- | --- | ---: |
| 0 | 64×64 | 3 |
| 1 | 32×32 | 2 |
| 2 | 16×16 | 1 |

## 2. 文档 S0：模式、宏块和对齐

~~~text
SW_4KB_2D → blk_type=SZ_4KB，sw_type=SW_D_2D
linear = 0
dim3D = 0
msaa = l2_ns = 0

l2_ms = 12
l2_ms_128B = 5
ms_mask_128B = 0x1F
block_size_elements = 12 - (0 + 0) = 12
~~~

二维块公式中的位切片：

~~~text
block_size_elements[4:1] = 6
block_size_elements[0] = 0
l2_eb[0] = l2_ns[0] = 0

l2_blk_w = 6 + (0 & (0 || 0)) = 6
l2_blk_h = 6
l2_blk_d = 0

宏块尺寸 = 64×64×1 元素
宏块大小 = 64×64×1B = 4096B
~~~

~~~text
l2_blk_w_slice = l2_blk_w = 6
l2_ms_256B = 5 - 1 = 4
l2_mip_offset = 12 - 8 = 4

is_3d_blk_size = 0
l2_ms_256B_eff = 4
num_mips_in_tail = 4 + 4 = 8

mips_outside_tail = maxmip - num_mips_in_tail = 2 - 8 = -6
in_tail_chk[m] = 1，m=0～16     // 负数符号分支为真
y_bias = 0                    // 二维模式
~~~

## 3. 文档 S1：块数和首个 tail，下标必须区分

mip0 的块数：

~~~text
Wb[0]       = ceil(64 / 64) = 1
Hb[0]       = ceil(64 / 64) = 1
Wb_slice[0] = ceil(64 / 64) = 1
~~~

后续级别按文档的右移加余数归约计算，相当于对块数向上取整：

~~~text
Wb[m]       = ceil(Wb[0] / 2^m)
Hb[m]       = ceil(Hb[0] / 2^m)
Wb_slice[m] = ceil(Wb_slice[0] / 2^m)
~~~

因此请求范围内：

| mip | Wb[m] | Hb[m] | Wb_slice[m] |
| --- | ---: | ---: | ---: |
| 0 | 1 | 1 | 1 |
| 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 |

### 3.1 mip0 是否在 tail：直接检查 mip0 元素尺寸

~~~text
w_tail_sz = 64 >> 1 = 32
h_tail_sz = 64

in_miptail[0] = (map0_w <= 32) && (map0_h <= 64) && in_tail_chk[0]
             = (64 <= 32) && (64 <= 64) && 1
             = 0
~~~

### 3.2 mip1 是否在 tail：使用 mip0 的块数判断下一级

**Wb[0]、Hb[0] 是 mip0 的值，不能称作 mip1 的块数。** 原文循环的输入下标为 m，而输出下标为 m+1：

~~~text
// y_bias=0，原文 next-in-tail 公式
in_miptail[m+1] =
    (Wb[m] <= 1) &&
    (Hb[m] <= 2) &&
    in_tail_chk[m+1]
~~~

如果用 k 表示“正在判断的目标 mip”，应写为：

~~~text
// k=m+1，适用于 k=1～16
in_miptail[k] =
    (Wb[k-1] <= 1) &&
    (Hb[k-1] <= 2) &&
    in_tail_chk[k]
~~~

检查 mip1 时，k=1、原循环变量 m=0，逐项代入：

~~~text
in_miptail[1] =
    (Wb[0] <= 1) &&
    (Hb[0] <= 2) &&
    in_tail_chk[1]

= (1 <= 1) && (1 <= 2) && 1
= 1
~~~

该条件已经把下一级尺寸减半的效果计入阈值：

| 上一级 mip0 的块数条件 | 对 mip0 元素尺寸的约束 | 推出 mip1 的尺寸约束 |
| --- | --- | --- |
| Wb[0] <= 1 | 宽度 <= 64 | 减半后宽度 <= 32 |
| Hb[0] <= 2 | 高度 <= 128 | 减半后高度 <= 64 |

本例 mip1 的实际尺寸为 32×32，符合 32×64 的 tail 阈值。

判断 mip2 时原循环 m=1，使用 Wb[1]、Hb[1]，结果同样为 1。其余候选级别也为 1，所以 in_miptail 在下标 1 处由 0 变 1：

~~~text
tail_mipid_raw = 1
maxmip != 0，且 (l2_ms_128B >> 1) = (5 >> 1) = 2 != 0
tail_mipid = 1
~~~

本例各级宏块数恰好都为 1，这不允许混用下标。**判断 mip1 是否在 tail 使用 Wb[0]；计算 mip1 的 pitch 使用 Wb[1]。** 两条公式用途不同。

## 4. 文档 S2：空间贡献、掩码及输出

首个 tail 只计入一个宏块，后续 tail mip 的空间已包含在该块内：

| mip | 计算分支 | mipsize |
| --- | --- | ---: |
| 0 | 小于 tail_mipid，Wb_slice[0]×Hb[0] | 1 |
| 1 | 等于 tail_mipid，整个 tail 计一个宏块 | 1 |
| 2 | 大于 tail_mipid，不重复分配 | 0 |

~~~text
maxmip_mask = (1 << (2 + 1)) - 1 = 0b111
mip_mask    = (1 << (1 + 1)) - 1 = 0b011

slice_input_en   = 0b111
mip_off_input_en = 0b111 & ~0b011 = 0b100

slice_b = mipsize[0] + mipsize[1] + mipsize[2]
        = 1 + 1 + 0
        = 2

mip_offset_in_blks = mipsize[2] = 0
~~~

计算当前 mip1 的输出：

~~~text
pitch = Wb[mip_level] << l2_blk_w
      = Wb[1] << 6
      = 1 << 6
      = 64 元素

slice = slice_b << (l2_blk_w_slice + l2_blk_h)
      = 2 << (6 + 6)
      = 8192 元素面积
      = 8192B

mip_offset_b = mip_offset_in_blks << l2_mip_offset
             = 0 << 4
             = 0
mip_offset_bytes = 0 × 256 = 0B

mip_in_tail = mip_level - tail_mipid = 1 - 1 = 0
~~~

slice 是一个二维 slice 的整条 mip 链分配量，不是单独 mip1 的逻辑面积。mipsize[2]=0 表示不再额外分配宏块，不表示 mip2 没有数据。

## 5. GFX12：同样的块尺寸、首 tail、slice 与宏块偏移

二维宏块公式：

~~~text
log2Width  = (12 >> 1) - (0 >> 1) - (0 >> 1) - (0 & 0 & 1) = 6
log2Height = (12 >> 1) - (0 >> 1) - (0 >> 1) - ((0 | 0) & 1) = 6
blockExtent = (64, 64, 1)
~~~

tail 最大尺寸为 32×64；最大容量为 effectiveLog2-4=12-4=8 个 mip：

~~~text
mip0：64×64，宽度超过 32，不能进入 tail
mip1：32×32，尺寸满足，剩余 2 级 <= 8，是首个 tail
firstMipIdInTail = 1
~~~

GetMipOffset 先累加 mip0，再为整个 tail 加一个宏块：

~~~text
mip0 sliceSize = AlignUp(64,64) × AlignUp(64,64) × 1B
               = 4096B

整个 tail 的贡献 = blockSize / blockExtent.depth
                 = 4096 / 1
                 = 4096B

总 sliceSize = 4096 + 4096 = 8192B
~~~

tail 位于前一个宏块，mip0 位于其后：

| 宏块字节范围 | 内容 |
| --- | --- |
| 0～4095 | mip1、mip2 共用的 tail |
| 4096～8191 | mip0 |

mip1 的 macroBlockOffset=0B，与模块 mip_offset_b×256=0B 一致。宏块偏移为零不意味着两个 tail mip 的内部原点相同；mipTailOffset 和 tail 坐标不在本模块九个输出中。

## 6. 关键差异：tail 内 pitch 从哪里取得

文档不对 tail 单独选择 pitch 公式：

~~~text
pitch_document[mip1] = Wb[1] << 6 = 64
~~~

GFX12 的 GetMipOrigin 从 tailMaxDim.width 开始，用 micro block 宽度对齐后输出，再为下一 mip 将候选宽度减半。

先计算 256B micro block：

~~~text
blockBits = 8 - log2_element_bytes = 8

micro_width_log2  = (8 >> 1) + (8 & 1) = 4
micro_height_log2 = (8 >> 1) = 4

microBlockExtent = (16, 16, 1)
16×16×1B = 256B
~~~

再计算 tail pitch：

~~~text
初始候选宽度 p = tailMaxDim.width = 32

mip1：
    输出 pitch = AlignUp(p,16) = AlignUp(32,16) = 32
    下一 mip 的候选宽度 p = max(32 >> 1,1) = 16

mip2：
    输出 pitch = AlignUp(p,16) = AlignUp(16,16) = 16
    下一 mip 的候选宽度 p = max(16 >> 1,1) = 8
~~~

| mip | 当前文档 pitch | GFX12 pitch | 分歧位置 |
| --- | ---: | ---: | --- |
| 0 | 64 | 64 | tail 外，宏块对齐 |
| 1 | **64** | **32** | 首 tail，文档仍用宏块跨度；GFX12 用 tail 候选宽度 |
| 2 | **64** | **16** | GFX12 候选宽度继续减半并按 micro block 对齐 |

宽度取自 tail 阈值，不是一般性地将实际 mip 宽度按 micro block 对齐；本例 mip1 的实际宽度恰好等于 tail 阈值。

**差异发生在 pitch 输出方式，不在首 tail 判定。** 两边的 tail 都占一个 4KB 宏块，总 slice 都为 8192B。不能把全局 l2_blk_w 改成 5 来强行得到 pitch=32，那会同时改变宏块语义。

## 7. mip1 的九个输出

GFX12 栏按本轮规则换算：sliceSize 转换为模块元素面积，macroBlockOffset 除以 256，由 firstMipIdInTail 推导相对 tail 编号；l2 字段为源码维度的推导值，不是伪造同名 API 输出。

| 模块输出 | 当前文档 | GFX12 同口径值 |
| --- | ---: | ---: |
| pitch | **64** | **32** |
| slice | 8192 | 8192 |
| mip_in_tail | 0 | 0 |
| mip_offset_b | 0 | 0 |
| l2_ms | 12 | 12 |
| l2_blk_w | 6 | 6 |
| l2_blk_h | 6 | 6 |
| l2_blk_d | 0 | 0 |
| l2_blk_w_slice | 6 | 6 |

GFX12 原始字段中，blockExtent=(64,64,1)、sliceSize=8192B、firstMipIdInTail=1、pMipInfo[1].pitch=32、pMipInfo[1].macroBlockOffset=0B。

## 8. 建议及验证状态

若要求九个输出采用相同语义，应为 tail 内 pitch 增加独立分支：

~~~text
if mip_level < tail_mipid:
    pitch = Wb[mip_level] << l2_blk_w
else:
    k = mip_level - tail_mipid
    pitch = AlignUp(max(tail_max_width >> k,1), micro_block_width)
~~~

在本例，k=0，所以 pitch=AlignUp(32,16)=32。首 tail、slice、宏块尺寸和宏块偏移无需为此改变。下游若依赖原宏块跨度，应保留独立内部量并检查连接，不能直接假定修改输出不影响完整地址链路。

本例仅完成源文件核对和手工代入；没有实施候选算法，没有重新运行云端样本或验证完整地址。可信状态需独立确认。
