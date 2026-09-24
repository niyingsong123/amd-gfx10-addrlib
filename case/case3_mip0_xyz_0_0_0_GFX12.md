# case3_GFX12：mip0 的 (0,0,0)，修订后布局计算

## 0. 版本、可信状态与范围

- 版本：2026-09-24 的 ADDRLIB_GFX12.md GFX12 修订稿。此文件与原 case 分开保存。
- 状态：已完成本轮定向功能复算，与独立 GFX12 转写的九字段同口径结果一致；未获独立可信确认，未加入 TRUSTED_BASELINE.json。
- 原用例：[case3_mip0_xyz_0_0_0.md](case3_mip0_xyz_0_0_0.md)，原文件 SHA256：F23084410CE61135758F1E2546254AD9D2D251E2C7CD43AE430B48881D9BB713。
- 计算依据：[ADDRLIB_GFX12.md](../ADDRLIB_GFX12.md)，SHA256：A6864BD26943078ADD333142BB40B87A9600B106572928F8B94621522CCACD8C。
- GFX12 参考：AMD PAL c5e800072a32f68b6ccc4422936d96167c6e0728，ADDR_GFX12_SHARED_BUILD=0；源位置与比对说明见 [修订报告](../docs/GFX12_ALGORITHM_REVISION.md)。
- 只重新计算 mipmap_param_calc_core_gc 的十二输入、九输出及 pitch_b 接入；不把原用例的最终 texel 地址当成本次已重算结果。
- 使用足宽整数和 BigInt，MAXMIP=17；范围按修订稿的资源约定、默认 flags、mip 0～15 执行。没有编译完整 C++ 或进行 RTL 仿真。

pitch 以元素计；slice 为整条 mip 链的 XY 元素面积，乘元素大小及有效采样数得到对照字节数；三维厚度不再次乘入该 slice 对照。mip_offset_b 为 256B 单位，tail 内部偏移不包含在其中。

## 1. 全部输入与尺寸恢复

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

map0_w / map0_h / map0_d = 1 / 2 / 1
element_bytes = 2^0 = 1B
numSamples = 2^0 = 1
numMipLevels = 0 + 1 = 1
~~~

x/y/z/s 不参与布局公式；Linear 的 map0_d 作为非 3D 资源的层数参与单层裁剪条件。

## 2. 模式、块尺寸和 tail 容量

~~~text
linear = 1, dim3D = 0, msaa = 0
l2_ms = 7
block_size_elements = 7 - (0 + 0) = 7
l2_blk_w / l2_blk_h / l2_blk_d = 7 / 0 / 0
macro block = 128 x 1 x 1 elements
l2_blk_w_slice = 8
l2_mip_offset = max(7 - 8, 0) = 0
num_mips_in_tail = 1
mips_outside_tail = 0 - 1 = -1
y_bias = 0
w_tail_sz / h_tail_sz = 64 / 1
~~~

Linear 使用 128B rendering 尺度，普通 slice 宽度仍按 256B 对齐。该模式最终强制 tail_mipid=17；GFX12 原始物理 blockExtent 的宽度为 256/element_bytes，不与 rendering 块宽混用。

## 3. 各 mip 块数及首个 tail

Wb[m]、Hb[m]、Wb_slice[m] 均由 mip0 的块数右移并按余数向上取整。下表覆盖请求的完整 mip 链：

| mip | 逻辑宽×高 | Wb | Hb | Wb_slice | mipsize（分配贡献） | 新 pitch |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 1×2 | 1 | 2 | 1 | 2 | 128 |

mipsize 在 tail 外为 Wb_slice×Hb，首个 tail 计一个宏块，之后的 tail mip 不重复分配。这里是裁剪前的累加贡献；Linear mip0 的裁剪在第 4 节单独替换。

请求链中没有 tail；tail_mipid=17，对外无 tail 标记为 17。

## 4. 整条链 slice：GFX12-01（RTL 等价式）

~~~text
slice_b = 2 = 2
linear_can_trim_mip0 = linear && (map0_d == 1) = 1
Wb[0] = 1, Wb[0][0] = 1
map0_h >> 1 = 2 >> 1 = 1
slice_b_drop = (linear_can_trim_mip0 && Wb[0][0]) ? (map0_h >> 1) : 0 = 1
slice_b_gfx12 = 2 - 1 = 1
slice = 1 << (8 + 0) = 256
slice_bytes = 256 × 1 = 256B
~~~

Linear 旧 mip0 占用 ceil(Wb[0]/2)×H 个 256B 单位；GFX12 为 ceil(Wb[0]×H/2)。两者之差恰为 Wb[0] 为奇数时的 floor(H/2)，因此新逻辑不需要新增乘法器或除法器。

该修正只替换 mip0 的贡献，且对查询链中任意 mip 都生效；不以当前 mip_level==0 作为开关。

## 5. 当前 mip 的 pitch：GFX12-02（RTL 等价式）

~~~text
pitch_block = Wb[0] << 7 = 1 << 7 = 128
mip_level=0 < tail_mipid=17
pitch = pitch_block = 128
~~~

GFX12 原式为 AlignUp(max(tail_width >> k,1),micro_width)。两种宽度都是二次幂，等价于 1 << max(T-k,U)；正文用比较后选择避免无符号减法下溢，无 /3、%3 或通用对齐器。

该级 pitch：修订前 128 → GFX12 修订后 128 元素。

## 6. 宏块偏移、tail 编号及下游换算

~~~text
maxmip_mask = (1 << (0 + 1)) - 1 = 0x1
mip_mask = (1 << (0 + 1)) - 1 = 0x1
mip_off_input_en = maxmip_mask & ~mip_mask = 0x0
mip_offset_in_blks = 后续 mip 的分配贡献之和 = 0
mip_offset_b = 0 << 0 = 0
macro_offset_bytes = 0 × 256 = 0B
mip_in_tail = 17
pitch_b_raw = 128 >> 7 = 1
pitch_b = (pitch_b_raw == 0) ? 1 : pitch_b_raw = 1
~~~

GFX12-03 在模块 pitch 的约定下，用零检测和选择器等价实现向上取整，恢复宏块跨度。tail 内的 macroBlockOffset 不包含 mipTailOffset，不代表最终纹素地址或 tail 内原点。

## 7. 九个输出与参考值

GFX12 栏已转换到模块单位：sliceSize 除以元素字节数及有效采样数，macroBlockOffset 除以 256；无 tail 为 17，l2 字段按本轮语义推导。

| 输出 | 修订前 | GFX12 修订稿 | GFX12 参考（同口径） |
| --- | ---: | ---: | ---: |
| pitch | 128 | 128 | 128 |
| slice | 512 | 256 | 256 |
| mip_in_tail | 17 | 17 | 17 |
| mip_offset_b | 0 | 0 | 0 |
| l2_ms | 7 | 7 | 7 |
| l2_blk_w | 7 | 7 | 7 |
| l2_blk_h | 0 | 0 | 0 |
| l2_blk_d | 0 | 0 | 0 |
| l2_blk_w_slice | 8 | 8 | 8 |

本输入已纳入本轮 610 组定向配置；本页提取时再次核对所选 mip 的九个输出，均一致。结果适用于所列单位与资源约定，不作为无限输入域证明，也不代表原用例最终地址已重新执行验证。
