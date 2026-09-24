# 当前差异及与公开 GFX12 匹配的建议

## 结论

当前 `mipmap_param_calc_core_gc` 的已比较规则更接近 **公开 GFX12 非 shared 实现**。在云端保存的可比样本中，GFX12 的数值差异仅出现在 Linear 的 `slice`；tail 内 `pitch` 还有明确的输出表示差异。要让声明范围内的九个输出逐字段同口径比较，应处理这两项，并明确 Linear 块尺度、资源类型和 mip 上限；仅把差异分类改成“通过”不能说明原模块已经匹配。

本报告基于已接受的[云端报告](cloud/docs/MIPMAP_COMPARE_SMALL_REPORT.md)、[结果 JSON](cloud/docs/mipmap_compare_small_results.json)和固定提交的 C++ 公式做静态分析。**修改建议尚未实施，也没有新跑测试或验证“修后全部通过”。**

## 1. 已有结果到底说明什么

种子 `0x20260922`，10,000 个随机配置加 670 个定向配置，检查 36,607 个请求 mip。配置分类如下：

| 参考 | 九字段一致 | 数值差异 | 仅表达口径不同 | 无等价模式 | 参考模型拒绝 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 公开 GFX10 | 2,688 | 1,169 | 938 | 2,665 | 3,210 |
| GFX12 | 8,919 | 127 | 1,464 | 0 | 160 |

拒绝和无等价配置不进入匹配率分母；表达口径不同也不算九字段一致。GFX12 可比配置为 10,510 个、可比 mip 为 34,607 个。

| GFX12 输出 | 可比 mip 上的结果 | 说明 |
| --- | --- | --- |
| pitch | 28,028 一致；6,579 表达不同 | 差异在 tail 内 |
| slice | 33,777 一致；830 数值不同 | 127 个 Linear 配置的整条链 slice 被每个请求 mip 重复观察到 |
| mip_in_tail | 34,607 一致 | 将无 tail 统一为哨兵 17 后比较 |
| mip_offset_b | 34,607 一致 | 模块值乘 256 后对比 macroBlockOffset |
| l2_ms、l2_blk_w/h/d、l2_blk_w_slice | 每项 34,607 一致 | 按已声明的语义推导和归一；不是全部来自同名官方 API 字段 |

阶段检查中，GFX12 的 tail 容量、首 tail、各级逻辑尺寸、宏块偏移均未发现差异。块尺寸阶段的 550 个差异全部来自 Linear 的 128B rendering 尺度与 256B physical slice block 尺度，不代表二维 tiled 公式不匹配。

这些结果支持“已测范围内更符合 GFX12”，不能把模块简单定性为“纯 GFX10.2 算法”，也不能外推到未知 RTL 位宽或完整地址模块。

## 2. 必须处理的数值差异：Linear slice 的末端裁剪

云端保存的有界缩减反例为 `r2` 的缩减输入：

| 参数 | 值 |
| --- | --- |
| 模式 | SW_LINEAR |
| 宽×高、层数 | 1×2、1 层；适配为非 3D 资源 |
| 元素大小、采样数 | 1 BPE、1 sample |
| maxmip、mip_level | 0、0 |
| 双方 pitch | 128 元素 |
| 文档 slice | 512 元素位置，即 512B |
| GFX12 sliceSize | 256B |

文档用 256B 对齐的 slice pitch 累加，所以该例为 `256×2=512B`。GFX12 的 rendering pitch 同样是 128B，但允许最后一个 Linear 子资源裁掉多余尾部 padding，得到 `AlignUp(128×2,256)=256B`。

证据为 [gfx12addrlib.cpp](../scripts/mipmap_compare/upstream/src/gfx12/gfx12addrlib.cpp) 的 `GetMipOffset`，尤其第 450–505 行；完整裁剪条件在 [addrlib3.cpp](../scripts/mipmap_compare/upstream/src/core/addrlib3.cpp) 第 1007–1014 行：

~~~text
CanTrimLinearPadding =
    resourceType 不是 3D
    && numSlices <= 1
    && Linear

实际替换 slice 贡献的分支还要求 mipIdx == 0。
~~~

这里的“单层”指 array/slice 层数，不是“只有一个 mip”。有多级 mip 时也只替换 mip0 的贡献。不能将 mip0 的裁剪规则套给每一级。

### 建议的最小公式改动

以下只覆盖本轮默认参数：无 custom pitch/height，denseSliceExact=0，Linear 单采样；`AlignUp` 按字节或明确给定的元素单位计算。

~~~text
B = 1 << l2_eb                         // bytes per element
W0 = map0_w_minus_1 + 1
H0 = map0_h_minus_1 + 1
P128_0 = AlignUp(W0, 128 / B)          // 元素
P256_0 = AlignUp(P128_0, 256 / B)      // 元素

old_mip0_bytes = P256_0 * H0 * B
new_mip0_bytes = AlignUp(P128_0 * H0 * B, 256)

if CanTrimLinearPadding:
    slice_bytes_new = slice_bytes_old
                    - old_mip0_bytes
                    + new_mip0_bytes
else:
    slice_bytes_new = slice_bytes_old

slice_new = slice_bytes_new / B        // 保留模块原来的元素面积单位
~~~

应在汇总结果或独立的字节贡献支路中做该调整，不能一概把 `l2_blk_w_slice` 改成 `7-l2_eb`：未裁剪的其他 mip 和多层资源仍有 256B 的 slice pitch 规则。

`mip_offset_b` 的公式累计当前 mip 后面的贡献，从不包含 mip0，因此上述仅替换 mip0 贡献的修正不要求改变它。Linear 下仍保留 `l2_ms=7`、rendering 块宽指数 `7-l2_eb` 和默认 slice 对齐指数 `8-l2_eb`。

### 输入语义需要补齐

本轮适配把 Linear 和二维 swizzle 都视为二维资源，并把 `map0_d_minus_1+1` 映射为 `numSlices`。在这个明确限制下，裁剪条件可以简化为 `linear && map0_d_minus_1==0`。

如果模块还要支持“Linear 布局的三维资源”，仅凭 `sw_mode` 和深度值无法可靠区分二维单层与三维深度为 1 的资源。需要增加/传递资源类型，或者由调用接口明确保证不输入该情况；不能把“不是 3D swizzle”等同于“不是 3D 资源”。

当前公式完全不使用深度输入。若选择匹配上述 GFX12 API 行为，深度/层数不变性要求也要相应修改：x/y/z/sample 坐标仍不参与布局计算，但层数从 1 变 2 可以改变 Linear slice。这正是云端 500 次扰动中记录的唯一 GFX12 变化。

## 3. 若要九字段严格一致：tail 内 pitch 也要调整

云端代表项 `r29/mip6`：

| 参数或输出 | 文档 | GFX12 |
| --- | --- | --- |
| 共同输入 | SW_4KB_2D，1286×256，2 BPE，单采样，maxmip=10，mip=6 | 相同 |
| 首 tail mip | 6 | 6 |
| pitch | 64 元素 | 32 元素 |
| 换算后的 slice | 946176B | 946176B |
| 宏块字节偏移 | 0 | 0 |

原模块始终使用 `Wb[mip_level] << l2_blk_w`；入 tail 后仍保留 macro block 对齐跨度。GFX12 的 `GetMipOrigin` 则从 tail 最大宽度出发，逐级减半，再按 256B micro block 的宽度对齐。见 [gfx12addrlib.cpp](../scripts/mipmap_compare/upstream/src/gfx12/gfx12addrlib.cpp) 第 335–398 行；micro block 尺寸见第 1810–1848 行。

~~~text
if mip_level < first_tail:
    pitch_api = pitch_original
else:
    k = mip_level - first_tail
    pitch_api = AlignUp(max(tail_max_width >> k, 1), micro_block_width)
~~~

上式使用同一套 GFX12 tail 阈值，不能改成对该 mip 实际宽度随意作 micro block 对齐。单采样 tail 下，令 `b=8-l2_eb`：

~~~text
2D micro_block_width = 2 ^ ceil(b/2)
3D micro_block_width = 2 ^ (floor(b/3) + (b%3 > 1))
~~~

例如 r29 的 tail_max_width=32、micro_block_width=16，因此 GFX12 从首 tail 开始的 pitch 是 32、16、16……；文档保留 64。

建议区分 `pitch_block`（原内部宏块寻址跨度）与 `pitch_api`（对外 mip 信息）。若要求原模块九个输出本身匹配，就必须明确定义输出 `pitch` 采用后者，并检查下游 `block_index_calc` 的连接；只在比较器里转换或把分类记为通过，不能证明原模块输出已相同。有效 tail 坐标通常不跨 XY 宏块，但该条件不应未经检查就扩展到越界坐标和所有调用者。

这项修改会改变部分可信 tail 用例的布局输出预期。应把新行为作为独立 GFX12 版本/派生用例验证，保留现有 case0/case2 及其源哈希，不覆盖原证据。

## 4. 已经符合 GFX12 的部分应保留

### 二维块宽高公式具有明确的恒等关系

在本文 tiled 范围，`L=l2_ms∈{8,12,16,18}` 是偶数，`e=l2_eb=2a+p`、`s=l2_ns=2b+q`，其中 `p,q∈{0,1}`。令 `A=L/2-a-b`。

文档中的 `n=L-e-s` 满足：

~~~text
floor(n/2) = A - (p OR q)
n%2 = p XOR q

doc_l2_blk_h = A - (p OR q)
doc_l2_blk_w = A - (p OR q) + (p XOR q)
             = A - (p AND q)
~~~

这正是公开 GFX12 `HwlCalcBlockSize` 的两条公式，见 [gfx12addrlib.cpp](../scripts/mipmap_compare/upstream/src/gfx12/gfx12addrlib.cpp) 第 2162–2181 行。当前指数范围下，文档位切片没有截去有效高位。

因此不需要照 GFX10 的 2/8 samples 方向规则交换块宽高。三维尺寸查表、tail 容量、首 tail 条件和宏块偏移也没有本轮 GFX12 数值差异证据，应先保留。

### Linear 的两个块尺度不能混为一谈

GFX12 同时有 128B rendering pitch 和 256B slice block。API 的 `blockExtent` 对应后者；文档 `l2_ms=7/l2_blk_w=7-e` 对应前者。本轮比较器明确进行了语义推导，并没有把原始 256B blockExtent 伪装成 128B。

若未来目标改为逐字比较 API 的物理 blockExtent，就需要另行导出 `8/8-e/0/0`，而不是破坏当前内部 rendering 尺度。九个模块输出与 API 并非九个同名字段；单位转换和派生口径必须随验证保留。

## 5. GFX10 的差异为何不能当作 GFX12 的修改清单

| 差异 | 公开 GFX10 的情况 | 对齐 GFX12 的处理 |
| --- | --- | --- |
| Linear pitch/block | 1×1、1 BPE 时文档 pitch=128、GFX10=256 | 保留 GFX12 的 128B rendering pitch |
| 奇数采样指数 | 如 64KB、1 BPE、8 samples 时文档 128×64，GFX10 64×128 | 当前二维公式与 GFX12 恒等，不交换 |
| 固定 256KB | 没有直接等价模式；不能替换成 VAR | 保留 GFX12 的固定 256KB 模式 |
| MicroTiled 大尺寸乘积 | 旧 GFX10 C++ 中间 UINT32 乘法可能回绕 | 不为 GFX12 引入该回绕；GFX12 源码先转 UINT64 |
| tail 内 pitch | 也存在 macro/micro 表示差异 | 按 GFX12 的具体 API pitch 规则处理 |

GFX10 的 1,169 个数值差异配置与 GFX12 的 127 个不能直接相减或当作同一套失败输入：两边的可比模式和拒绝范围不同。

## 6. 建议的实现与验收顺序

1. 固定目标为本轮 PAL 提交的 GFX12 非 shared 分支，使用普通格式、默认 flags、无自定义 pitch/height；明确 Linear 的资源类型和层数映射。
2. 在独立候选版本中增加 Linear mip0 的 slice 裁剪，保持其他 mip 的贡献和宏块偏移规则。
3. 如要求九输出逐字段同口径，将 tail pitch 输出改为 GFX12 的 micro block 对齐表示；内部需要时保留原宏块跨度。
4. 对外验证范围限制为 `0 <= mip_level <= maxmip <= 15`，维持合法资源/采样约束。内部可以保留数组长度 17 和哨兵 17；索引 16 属于扩展域，不应伪造 PAL 对照输出。
5. 后续经用户同意再验证：先使用已保存的 Linear 1×2、D=1/D=2，以及 tail 首级/后续级反例；再做原小规模集合和受影响的地址链路回归。原样本未保存逐条输入，完整集合需要依种子重建。本次没有执行此步骤。

未来的合格结论应是：在明确的输入域、单位转换和 API 字段推导下，九个可比输出未发现差异。只有修改后验证才能给出这个结论；随机通过仍不是无限输入域的数学证明。

## 7. 本次整理的证据和限制

- 云端最新补丁中的 9 个变更文件已逐个恢复，并与补丁的完整 Git blob SHA-1 一致；原始报告与 JSON 保持原字节。
- 本次只复核保存结果的计数、输出汇总哈希及源码公式。没有重新生成随机输入、调用模型、编译 C++ 或做 RTL 仿真。
- 当前结果的“参考拒绝”来自参考模型的 eligibility 规则，不是本次真实 API 调用返回；自定义布局、压缩格式、更多资源类型等不在本轮声明范围。
- 代表项可能保留超出某 mip 逻辑范围的坐标；坐标不参与本模块计算，所以这些是布局反例，不是有效 texel 地址访问用例。
- isolated 阶段的 notApplicable 保留云端计数方式：Linear 整配置跳过记一次，部分 tail pitch 跳过按 mip 记数；不能直接混用这些数求总体通过率。
- 归档来源、哈希和派生文件列表见 [manifest](provenance/manifest.json)。可信原文和三个用例保持不变。
