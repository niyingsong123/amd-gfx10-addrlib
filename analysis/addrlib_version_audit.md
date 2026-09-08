# ADDRLIB.md：GFX10 / GFX11 / GFX12 逐段版本核对

审计日期：2026-09-08。

## 结论与版本边界

当前片段的模式集合、128B pitch / 256B slice 分离及固定 256KB 3D 模式，整体指向 **GFX12**。它复用了多代相同的 mip-tail 数学，并带有旧 VAR/奇数块尺寸处理痕迹。它不是已证明来自某一个发布版的完整可编译源码；不能把所有段落统一标为 GFX10，也不能把代码相似性当成来源证明。

本次固定对照 AMD 官方 GPUOpen-Drivers/pal 提交 `c5e800072a32f68b6ccc4422936d96167c6e0728`（2025-04-29），使用其中完整的 AddrLib GFX10、GFX11、GFX12 及公共层、GFX12 shared 参考模型。这里的“版本”指 GPU 代际加该固定软件提交，**没有证据将用户片段精确归属到 Mesa 某个发布号**。旧文档的 Mesa 26.2.2 只是研究目标，仓库没有该源码快照，不能作为已核验来源。

用户片段保持原样，行号对应 blob `469fcd54e79ebb33b0076cbd2f9dbb575fb96e77`。表中“相同”指所述算法/数值及限定配置相同，不表示 API、有效模式或所有边界行为相同。GFX12 的 shared 和非 shared 两条路径均已阅读。

## 逐段表（覆盖全部 359 行）

| 原文行号 | 段落 | GFX10 | GFX11 | GFX12 | 判定、限制和问题 | 固定源码证据 |
|---|---|---|---|---|---|---|
| [1–35](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L1-L35) | 模块接口、变量和 PAD_* 宏 | 接口不同 | 接口不同 | 概念对应，非原样源码 | 共享 C++ 没有该 RTL 模块/流水线。输入 minus-one 与正文实际尺寸混用；pitch/slice 注释说减一，输出未减一。位宽和 TC 预处理缺失，无法确认接口等价。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L211) |
| [36–42](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L36-L42) | S0 阶段说明 | 功能共有 | 功能共有 | 功能共有 | 阶段划分是 RTL 实现选择，不能作为版本证据。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L56) |
| [43–58](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L43-L58) | sw_mode_dec 模式表 | 不匹配 | 不匹配 | 明确匹配模式集合 | GFX10 使用 S/D/Z/R 与 VAR；GFX11 有 256KB_*_X；GFX12 为 ADDR3_*_2D/3D。SW_L 与 SW_LINEAR 名称须区分；blk_type 编码未给出。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L66) |
| [59–69](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L59-L69) | macro_blk_size_calc | 部分尺寸共有 | 部分尺寸共有 | 匹配 pitch 基准 | 7/8/12/16/18 与 GFX12 128B linear pitch 和固定块吻合；ms_mask 是 RTL 表示，不是公开 API 字段。linear slice 的块仍按 256B。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L98) |
| [70–74](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L70-L74) | dim3D、MSAA 与元素数指数 | 部分通用 | 部分通用 | 意图匹配 | block_size_elements 实为 log2 元素位置数；msaa 与 msaa_cnt 未连线。3D swizzle 不等于 3D resource。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L2097) |
| [75–93](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L75-L93) | 2D 宏块公式及全部示例 | 1X 等子集 | 1X 等子集 | 公式与表的数值匹配 | 固定偶数 L 下可化为 ceil((L-e-s)/2), floor((L-e-s)/2)。GFX10/11 在奇数 sample log2 时方向可能不同，且 256B/4KB 不支持本表 MSAA 用法。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L2163) |
| [94–106](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L94-L106) | 3D 4KB 五行表 | 匹配厚模式表 | 匹配厚模式表 | 匹配 S_3D | 相同数值不是 GFX10 独有；要选实际支持的 thick/swizzle。 | [G10](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L112) |
| [107–111](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L107-L111) | 3D 64KB 五行表 | 匹配厚模式表 | 匹配厚模式表 | 匹配 S_3D | 三代均可得到所列尺寸。 | [G11](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx11/gfx11addrlib.cpp#L111) |
| [112–117](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L112-L117) | 3D 256KB 五行表 | 无对应固定厚模式表 | 匹配 256KB 厚表 | 匹配 S_3D | GFX10 VAR 的大小数值可能为 256KB，不能据此认定有该 3D 模式。 | [G11](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx11/gfx11addrlib.cpp#L113) |
| [118–124](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L118-L124) | linear 一维块尺寸 | 形式共有 | 形式共有 | 结合 L=7 匹配 | 宽指数 L-e，高/深指数 0；GFX10/11 常规 linear pitch 为 256B，LINEAR_GENERAL 为例外。 | [G10](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L5033) |
| [125–132](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L125-L132) | 128B pitch、256B slice、偏移缩放 | 不匹配该策略 | 不匹配该策略 | 明确匹配 | mip_offset_in_blks << (L-8) 是 256B 单位的计数，不能称 byte offset；linear 按 256B slice 单位。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L450) |
| [133–153](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L133-L153) | tail 容量与 3D effective log2 | 支持尺寸上相同 | 支持尺寸上相同 | 支持尺寸上相同 | 2D 4/64/256KB 容量为 8/12/14；3D 为 5/10/11。<=256B 返回1只是内部占位，仍禁用 tail。旧 VAR 注释不是 GFX12 模式证据。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L514) |
| [154–162](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L154-L162) | mips_outside_tail 与 in_tail_chk | 相同数量条件 | 相同数量条件 | 相同数量条件 | m > maxmip-C 等价 numMipLevels-m <= C；maxmip 为末级 ID。maxmip-C 是数量条件的边界，不是实际 tail 起点。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L348) |
| [163–168](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L163-L168) | y_bias_intail | 4/64KB 子集相同 | 4/64/256KB 相同 | 固定块尺寸下匹配 | 3D 4KB/256KB 减半高度，64KB 减半宽度；blk_type[0] 仍需编码定义。注释 SW_TYPE[0] 与实际 blk_type[0] 不同。无法仅凭注释证明来自 GFX10.1。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L172) |
| [169–182](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L169-L182) | pad_to_log2sz_gc 与 Wb0/Hb0 | 向上取整共有 | 向上取整共有 | 向上取整共有 | 对实际正尺寸是 ceil(dim/2^k)；输入若真为 dim-1，要先恢复；dim=0 时原式不满足注释的至少一块。原片段括号有误。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L211) |
| [183–195](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L183-L195) | S1 说明及逐 mip block count | 条件匹配 | 条件匹配 | 条件匹配 | 正尺寸的嵌套 ceil 可合并；依赖正确的实际尺寸输入。循环缺少 m<MAXMIP。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L229) |
| [196–200](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L196-L200) | 尺寸阈值和数量条件合取 | 基本逻辑相同 | 基本逻辑相同 | 基本逻辑相同 | W/H 必须是 mip 元素尺寸；y_bias/pad_sz 别名缺失。未涵盖 GFX10/11 特定 Z-order HTILE 修正。 | [G10](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3843) |
| [201–211](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L201-L211) | 用上一 mip 的块数检查下一 mip | 条件下等价 | 条件下等价 | 条件下等价 | 对正尺寸、ceil 缩减和固定偶数宽高块，两个 <=1/<=2 条件等价；需另算 mip0，片段未明确连线。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L348) |
| [212–220](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L212-L220) | tail 首级和禁用逻辑 | 功能对应 | 功能对应 | CalcMipInTail 直接对应 | linear、256B、单 mip 不进入 tail；MAXMIP 为 RTL 哨兵，上游 firstMipIdInTail 无 tail 时为 numMipLevels。XOR 找转折依赖单调性。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L730) |
| [221–230](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L221-L230) | 高 mip 的 mipsize | 计账思路共有 | 计账思路共有 | 计账思路共有 | tail 首级计1、之后计0，是 XY block/slice 层统计；末硬编码级计1依赖最大输入尺寸。不能当完整 3D surfSize。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L437) |
| [231–236](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L231-L236) | mip/maxmip mask | 倒序累加对应 | 倒序累加对应 | 倒序累加对应 | 选择 current_mip 之后的级数；不是从 mip0 正向前缀求和。maxmip_mask 的括号与字面量需修正。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L538) |
| [237–248](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L237-L248) | S2 pitch 与低 mip mipsize | 部分对应 | 部分对应 | 部分对应 | 普通 mip pitch 公式可对应；tail pitch 上游另有 microblock 下限。不能把本输出直接等同于每级 pMipInfo.pitch。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L383) |
| [249–280](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L249-L280) | 高/低 mip offset 累加 | 功能对应 | 功能对应 | 功能对应 | 两段加法为时序拆分，无代际特征；mip_size/mipsize、mip_off_en/mip_off_input_en 混名。 | [G10](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3922) |
| [281–288](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L281-L288) | slice 全链累加 | 功能对应 | 功能对应 | 功能对应 | 加的是被 mask 选择的 XY 块计数，不能直接称 byte size。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L489) |
| [289–291](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L289-L291) | slice/pitch/mip_offset 输出 | 单位需转换 | 单位需转换 | 单位需转换 | slice_out 为 XY 元素位置数；字节还需 BPE、samples，3D 全表面另需深度。mip_offset_b_out 单位为256B，不是B。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L489) |
| [292–297](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L292-L297) | tail 相对 ID 和 log2 输出 | 概念对应 | 概念对应 | 概念对应 | 合法 tail index 为 mip-first；未在 tail 时为哨兵；无明确位宽，不能证明完整 RTL 正确。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L730) |
| [298–312](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L298-L312) | tail-origin 模块接口和参数换算 | 核心功能共有 | 核心功能共有 | 核心功能共有 | 公开上游是 C++ 函数，不是此 RTL 模块；num_mips_inside_tail 与 al_num_mips_inside_tail 混名。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L577) |
| [313–333](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L313-L333) | micro_block_dim_calc | 1X 子集匹配 | 1X 子集匹配 | 1X 子集匹配 | 公开 tail microblock 使用 8-e，当前代码使用8-e-s；s=0 相同，s>0 不可宣称相同。3D case 只覆盖4..8；linear 专门分支也缺失。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L539) |
| [334–340](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L334-L340) | reverse 与分段 byte_offset | 合法 tail 同式 | 合法 tail 同式 | 连同负数钳位匹配 | reverse>6 仍是 tail 内较大 offset，不是 tail 外。C 为最大容量，实际 tail 未填满时末级 reverse 不一定为0。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L483) |
| [341–352](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L341-L352) | offset[19:8] 拆 X/Y | 相同 | 相同 | 相同 | X取9/11/13/15/17/19，Y取8/10/12/14/16/18；右边位宽须为12。 | [G12](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/gfx12addrlib.cpp#L367) |
| [353–354](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L353-L354) | 奇数 L 的 XY 交换 | 不完整 | 泛化分支不完整 | 合法 tiled L 均偶数，此分支不启用 | GFX10/11 上游还在 e 为奇数时做坐标位调整。当前片段只有交换，不能宣称支持旧 VAR。 | [G10](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx10/gfx10addrlib.cpp#L3963) |
| [355–359](https://github.com/niyingsong123/amd-gfx10-addrlib/blob/b533fc8a3e51c1da4faf77c6cc3982d676b9b623/ADDRLIB.md#L355-L359) | microblock 坐标缩放、z=0 | 支持配置下相同 | 支持配置下相同 | 支持配置下相同 | 乘微块尺寸得 mip 原点，不是最终 texel 地址；z-origin=0 不代表 3D 深度无需处理。10位截断属 RTL 接口约束。 | [Shared](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L668) |

## 可复算的代际差异

设 L=log2(block bytes)，e=log2(BPE)，s=log2(samples)，N=L-e-s。

- GFX12 固定偶数 L 的 2D 块：w=ceil(N/2)，h=floor(N/2)。GFX10/11 公共薄块计算用 widthPrecedent=(s 为偶数)或(L 为奇数)，w=floor((N+widthPrecedent)/2)，h=N-w。例：64KB、1BPE、2X，GFX12 为256×128，GFX10/11 的薄块公式为128×256；合法模式仍需单独检查。
- 3D 表满足 w+h+d+e=L。4KB/64KB 的两组共10行与三代对应；256KB的5行对应GFX11/12，不是GFX10固定厚模式。
- tail 的有效指数 E：2D为L；3D为L-floor((L-8)/3)。E<=8时容量占位C=1，9..11时C=1+2^(E-9)，更大时C=E-4。
- 支持 tail 的 4KB、64KB、256KB，C分别为：2D 8/12/14；3D 5/10/11。linear和256B不因C=1而启用tail。
- 数量条件为 maxmip+1-m<=C；尺寸条件仍须同时满足。实际tail级数T=maxmip-first+1可以小于C，末级reverse=C-T，并不保证为0。
- offset计数乘2^(L-8)的结果以256B为单位：64KB的一块输出256，实际字节数65536。linear需用256B slice块而非128B pitch块。
- 3D有效指数减少来自tail原点不使用Z项的布局约束，不能仅用“体积每级缩为1/8”解释。参见 [getNumMipsInTail](https://github.com/GPUOpen-Drivers/pal/blob/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib/src/gfx12/shared/addr_shared.cpp#L514)。

## 已发现并修正的文档问题

| 文件 | 原问题 | 本次修正 |
|---|---|---|
| ADDRLIB_comment.md | 把6个offset槽推成1536B总tail；把reverse>6叫tail外；默认实际末级reverse=0 | 区分最大容量、实际级数、offset、XY块统计与3D占用；给出正确公式和来源 |
| analysis/mip_tail_gfx10_analysis.md | 整段归为GFX10；3D case抄成12而不是10；符号检查漏[msb]；偏移单位和倒序布局不清 | 改为跨代分析，修正公式、单位、尺寸编码和布局前提 |
| analysis/gfx10_mip_tail_and_tail_offset.md | 将tail放在大mip后；用Align(sum(non-tail))代表GFX10；重复加tail偏移与已平移坐标的swizzle | 按上游倒序macroBlockOffset和坐标平移路径重写；区分offset字段 |
| analysis/three_address_calculation_examples.md | 例2位排列及算术错误；例3漏尺寸检查、位拆解错误；标题声称三个完整地址 | 例1保留0x10000518；例2按固定GFX12表及pipeBankXor=0得0x201201C8；例3first=3、mip4 offset=0x2000、origin=(32,0,0)，明确仅算原点 |
| analysis/gfx10_64kb.md | 将PI枚举解码值当成完整支持；引用为不可访问会话标记 | 说明代码断言PI=256B，较大枚举值不代表swizzle支持；换固定源码链接 |
| analysis/gfx10_64kb_swizzle_deepdive.md | 会把X解释为普通元素坐标；缺PI有效配置限制 | 说明方程求值X是字节坐标、低e位为元素内字节位；补PI=256B限制和固定来源 |
| analysis/gfx10_addrlib_深入浅出总览.md | 将HTILE反向接口的存在当作功能实现；会话引用不可用 | 标明该函数是ADDR_NOT_IMPLEMENTED桩；替换来源并解释pipe/bank映射不等于DRAM拓扑 |
| README.md / analysis/README.md / upstream/README.md / verilog/README.md | 容易把研究计划当作已存在源码/RTL、把目标发行号当作已核验版本 | 更新实际内容、审计入口和固定来源；说明无完整上游快照/可编译RTL |

## 原始片段中的问题（保留原文，避免把推测写成原始源码）

1. 缺端口位宽、完整语法、资源类型、TC转换、宏定义及若干别名；本文件是伪RTL/笔记混排，不能宣称编译通过。
2. 输入minus-one编码与ceil公式不一致；例如真实宽1而输入0时，直接ceil会给0块。需查接口还原步骤。
3. pitch/slice的减一注释与实际输出冲突；mip_offset_b的字节命名与256B单位冲突。
4. maxmip_mask应表达(1 << (maxmip+1))-1，并采用足够宽常量；现有括号可能变成移位maxmip位。mip_level+1也要防止4位运算溢出。
5. 2D公式缺括号；msaa_cnt、mip_size、mip_off_en、y_bias、pad_sz_w/h、micro_blocks与对应已定义变量不统一；部分for语法/三目分隔符错误。
6. 3D tail判断依据swizzle，不是仅依据资源维度；z-origin=0不消除深度、切片数或macroBlockOffset的处理。
7. microblock函数减了samples，而所对照tail函数不减；奇数块尺寸交换还缺奇数BPE调整。这些不能悄悄当作已支持特性。
8. 原文“VAR sizes14..20”及“switch back to10.1”是历史注释，不能证明当前实现支持这些块或源自某个精确GFX10.1发行版。
9. Wb/Hb用于下一mip判断须保证实际正尺寸和ceil递推；mip0的in_miptail初始化、tail pitch及末硬编码级处理需完整接口补足。

## 验证范围

逐段静态对照、上游表项提取和算术反例验证。附带的verify_version_audit.ps1复算块尺寸、容量、offset单位、位拆解和三个例子；不是完整AddrLib/RTL端到端仿真。没有执行未提供的硬件RTL，也不声称审计覆盖整个GPU驱动或所有上游版本。所有结论仅针对本次固定来源与仓库文档。

本次复算结果：454项检查通过，包含80组2D配置、15行3D尺寸表、tail边界、偏移单位、嵌套ceil和三个例子。例2还直接从下载的固定GFX12源码nibble数组重建pattern，结果为0x1C8。32段行号连续覆盖1–359，无遗漏。完整AddrLib/RTL端到端测试未执行。
