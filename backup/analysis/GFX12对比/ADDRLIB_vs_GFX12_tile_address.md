**结论：ADDRLIB.md 的 95 条 tiled 块内位排列全部与本次 GFX12 开源基准一致。主要差异位于 base swizzle、mip-tail 坐标接入，以及输入输出的定义；不能据此把它判定为另一代 GPU 的 tile 算法。**

本次按“GFX12 开源寻址实现”理解“开源协议”，只检查 tile address 路径及它直接依赖的尺寸、tail 原点和 swizzle 处理。未审查许可条款，也未通读整个 AddrLib。

对照对象：

- 文档：找到的 873 行完整版，保存为 [ADDRLIB 对照原文](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md)。它与此前解压目录里的同名文件 SHA-256 一致：`05D4519FBF57BB516590AE397DD67EDB2FE6FF7A09570325D033A3D73702216D`。下文行号均指此文件。
- 开源基准：AMD 官方 GPUOpen-Drivers/pal 固定提交 `c5e800072a32f68b6ccc4422936d96167c6e0728`。本次重新获取该提交的源码，主要对照 [gfx12addrlib.cpp 的 tiled 地址函数](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L833-L954)、[块内位表](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12SwizzlePattern.h#L40-L290) 和 shared 辅助函数。结论绑定此提交，不声称覆盖所有版本。

**1. 提取出来的 base swizzle 没有进入最终地址——按文档的完整地址职责，这是明确的逻辑缺失。**

文档 [L763](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:763) 提取 `swizzle_bits_256B`，L765 又从 base 中清除这些位，但后续没有使用这个提取结果。

文档 [L859–863](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:859) 对 tiled 路径实际执行的是：

```text
blk_offset_final = blk_offset
swizzle_bits = (blk_offset >> 8) & ms_mask_256B
addr_offset = blk_index | (swizzle_bits << 8) | blk_offset
```

`swizzle_bits << 8` 只是 `blk_offset` 中已有位的子集，OR 回去没有作用。因此这几行等价于：

```text
addr_offset = blk_index | blk_offset
```

非零 base swizzle 被丢掉了。GFX12 上游明确保留 base-address XOR 功能，并有独立的 [HwlComputePipeBankXor](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L1191-L1206)。按照文档自己的“从 base 提取 swizzle”约定，块内偏移应体现如下关系，具体 mask 和位宽需与接口定义一致：

```text
tile_offset_final = tile_offset ^ (base_swizzle_in_256B_units << 8)
```

可复算例：`SW_4KB_2D、1×AA、4 BPE、(x,y)=(8,8)` 的原始块内偏移为 `0x300`。若有效 base swizzle 在字节地址上为 `0x100`，XOR 后应为 `0x200`；文档仍输出 `0x300`。这里假设启用了相应 swizzle，且其他基址、mip 和宏块偏移相同。

需要区分 API 层级：本次上游 `HwlComputeSurfaceAddrFromCoordTiled` 自身计算相对 surface 的地址，没有在该函数里读取绝对 base 或应用 base seed。因此，这一项不是声称“上游该函数有一行 XOR，而文档抄漏了”，而是文档扩展到 `address_final` 后，没有完成它自己声明的 base swizzle 数据流。

**2. XOR 的使能模式说明沿用了旧命名。**

文档 [L849](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:849) 写着只对 `SW_*_X`、`SW_*_T` 开启 XOR。该 GFX12 的 [模式表](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L67-L76) 没有这些后缀；[实际条件](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L1196-L1206) 为硬件配置支持 swizzle，且模式既非 Linear、也非 256B，即对应 4KB、64KB、256KB 的 2D/3D 模式。

这是确定的说明差异；文档没有写出相应使能电路，所以不能进一步断言真实 RTL 已按错误注释实现。

此外，文档的 swizzle 按 256B 单位表达；公开 API 的 `pipeBankXor` 还关联 `m_pipeInterleaveLog2` 和硬件允许的 swizzle 位数。上游 [L1379–1399](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L1379-L1399) 读取这些配置，[L1661](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L1661) 按 pipe-interleave 位数换算。两种表示需先统一单位；文档中的固定 `<< 8` 本身不足以证明它只支持一种硬件配置。`blk_bit_mask_128B` 与 `ms_mask_128B` 的关系也尚未定义。

**3. mip-tail 原点算出来了，但没有写出接入位表的步骤——属于连接缺失。**

文档 [L645–649](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:645) 计算了 `x/y/z_mip_in_tail_orig`，后面的位表直接使用 `x/y/z`，没有说明它们是否已经加上原点。

上游 [L926–939](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L926-L939) 和 shared 的 [getXYZoffsets](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L670-L685) 都明确先加原点，再计算块内地址：

```text
x_for_pattern = x_in + x_mip_in_tail_orig
y_for_pattern = y_in + y_mip_in_tail_orig
z_for_pattern = z_in + z_mip_in_tail_orig
```

例：`SW_64KB_2D、4 BPE、1×AA、256×256、9 个 mip`，首个 tail mip 为 mip2；mip4 的 tail 原点为 `(32,0,0)`。访问该 mip 的 `(0,0)` 时，正确块内偏移为 `0x2000`，未加原点则为 `0`。

若外部连接已经完成这次加法，位表不需要修改；否则 tail 地址会错。现有文档只能证明这一步没有交代，不能证明外部模块不存在。

**4. `pitch/slice` 的“减一”注释与实际公式冲突——需要统一接口约定。**

文档 [L63–65](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:63) 声称 `pitch`、`slice` 为实际数量减一，但 [L419](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:419)、[L513](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:513) 输出实际数量；[L809–811](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:809) 也直接右移，没有先加一。上游 [L911–914](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L911-L914) 使用实际 pitch。

例如块宽 128、实际 pitch 256，正确每行有 `256 >> 7 = 2` 个块。如果按注释传入 255，文档会算成 1 个块。`map0_*_minus_1` 输入与 `map0_w/h` 的转换也没有明确给出。

因此不能笼统认定块索引公式错误：以实际数量为输入时，其基本结构是对的；按注释传入减一编码时则会错。

**5. 有几处只是表示方式不同，换算后应当一致。**

| 项目 | ADDRLIB.md | 上游 GFX12 | 判断 |
|---|---|---|---|
| 宏块位置 | L833 的 `blk_index` 已经左移 `l2_ms`，是字节偏移 | tiled 函数的 `blkIdx` 先保留块编号，在 L942 才左移 | 命名、流水线位置不同，不能再给文档的 `blk_index` 乘一次块大小 |
| mip 宏块偏移 | L517 的 `mip_offset_b_out` 为 256B 单位；L767、L867 合入基址后再乘 256 | `macroBlockOffset` 为字节 | 应比较 `mip_offset_b_out << 8` 与 `macroBlockOffset` |
| slice | 文档由 XY 块数还原为 XY 元素位置数 | `sliceSize` 为字节，3D 再乘 block depth 得 HW slice 步长 | 在对应 tiled 布局下，还需考虑 BPE、sample 数和 block depth |
| 最终结果 | `address_final` 包含 base | `pOut->addr` 是相对 surface 起点的地址 | 比较前应统一绝对/相对地址语义 |

上游依据为 [HW slice、块编号和最终求和](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L904-L943) 及 [slice 大小计算](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L478-L509)。

对合法 tiled 地址，宏块字节偏移的低 `L=log2(blockBytes)` 位为零，而块内偏移只占这低 L 位。因此文档用 OR 合并这两项、上游用加法合并，可以等价。这种 OR 与第 1 项中应作用于重叠位的 base XOR 是两回事。

**6. tail 微块公式有形式差异，但在本次上游支持的 mip-tail 配置中不构成实际差异。**

文档 [L565](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:565) 为 `8 - log2(BPE) - log2(samples)`；上游 [getMicroBlockSize](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L539-L575) 为 `8 - log2(BPE)`。

但上游 [参数检查](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L2494-L2508) 不接受 MSAA 与 mipmap 同时存在，也不接受 3D MSAA。因此有效 tail 路径中 `samples=1`，两式一致。不能将这项写成“合法 MSAA mip-tail 地址错误”。

另外，文档 [L654](D:/project/no_preject/2026-09-16/addrlib-md-gfx12-tile-address-2/outputs/ADDRLIB_对照原文.md:654) 的标题 `blk_offset[6:0] table` 不符合表格内容：tiled 表覆盖 8、12、16、18 位块内字节偏移，应改为与块大小对应的范围。仅凭标题不能断言实际硬件只保留 7 位。

**已核对的一致部分和验证范围。**

- 将官方 `PATINFO` 指向的四段 NIBBLE 位表，按 [上游拼表顺序](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.h#L204-L222) 重建为完整位排列，再与文档 Verilog 拼接的反向位序逐位比较：80 条 2D、15 条 3D，95/95 一致。1×/2×/4×/8× AA 的 sample 位也在比较范围内。
- 80 组 2D 块宽高公式与上游公式一致。
- 上述 swizzle `0x300 → 0x200` 和 tail `0 → 0x2000` 算例均已复算。它们分别依赖文中列出的 swizzle 使能条件、以及“原点尚未在外部加入”的条件。
- 本次没有编译 RTL 或运行完整 AddrLib 端到端测试；结论为源码公式、位表和可复算算例的对比。

建议优先补全 base swizzle 的数据流，然后明确 tail 坐标接入及所有数量/单位约定。95 条 tiled 位表无需因本次对比而修改。
