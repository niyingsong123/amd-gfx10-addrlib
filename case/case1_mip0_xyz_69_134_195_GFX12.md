# case1_GFX12：mip0 的 (69,134,195)，修订后布局计算

## 0. 版本、可信状态与范围

- 版本：2026-09-24 的 ADDRLIB_GFX12.md GFX12 修订稿。此文件与原 case 分开保存。
- 状态：已完成本轮定向功能复算，与独立 GFX12 转写的九字段同口径结果一致；未获独立可信确认，未加入 TRUSTED_BASELINE.json。
- 原用例：[case1_mip0_xyz_69_134_195.md](case1_mip0_xyz_69_134_195.md)，原文件 SHA256：DC282D50A42228AFA35B6700EC45E5F31538F32CC9CC47F145CEDFAA62FFF407。
- 计算依据：[ADDRLIB_GFX12.md](../ADDRLIB_GFX12.md)，SHA256：A6864BD26943078ADD333142BB40B87A9600B106572928F8B94621522CCACD8C。
- GFX12 参考：AMD PAL c5e800072a32f68b6ccc4422936d96167c6e0728，ADDR_GFX12_SHARED_BUILD=0；源位置与比对说明见 [修订报告](../docs/GFX12_ALGORITHM_REVISION.md)。
- 只重新计算 mipmap_param_calc_core_gc 的十二输入、九输出及 pitch_b 接入；不把原用例的最终 texel 地址当成本次已重算结果。
- 使用足宽整数和 BigInt，MAXMIP=17；范围按修订稿的资源约定、默认 flags、mip 0～15 执行。没有编译完整 C++ 或进行 RTL 仿真。

pitch 以元素计；slice 为整条 mip 链的 XY 元素面积，乘元素大小及有效采样数得到对照字节数；三维厚度不再次乘入该 slice 对照。mip_offset_b 为 256B 单位，tail 内部偏移不包含在其中。

## 1. 全部输入与尺寸恢复

~~~text
x = 69
y = 134
z = 195
s = 0
map0_w_minus_1 = 255
map0_h_minus_1 = 255
map0_d_minus_1 = 255
sw_mode = SW_256KB_3D
log2_num_samples = 0
log2_element_bytes = 0
mip_level = 0
maxmip = 12

map0_w / map0_h / map0_d = 256 / 256 / 256
element_bytes = 2^0 = 1B
numSamples = 2^0 = 1
numMipLevels = 12 + 1 = 13
~~~

x/y/z/s 不参与布局公式；Linear 的 map0_d 作为非 3D 资源的层数参与单层裁剪条件。

## 2. 模式、块尺寸和 tail 容量

~~~text
linear = 0, dim3D = 1, msaa = 0
l2_ms = 18
block_size_elements = 18 - (0 + 0) = 18
l2_blk_w / l2_blk_h / l2_blk_d = 6 / 6 / 6
macro block = 64 x 64 x 64 elements
l2_blk_w_slice = 6
l2_mip_offset = max(18 - 8, 0) = 10
num_mips_in_tail = 11
mips_outside_tail = 12 - 11 = 1
y_bias = 1
w_tail_sz / h_tail_sz = 64 / 32
~~~

宏块宽、高、深使用原文三维表项；micro block 指数在 pitch 分支中另算，不覆盖这里的宏块指数。

## 3. 各 mip 块数及首个 tail

Wb[m]、Hb[m]、Wb_slice[m] 均由 mip0 的块数右移并按余数向上取整。下表覆盖请求的完整 mip 链：

| mip | 逻辑宽×高 | Wb | Hb | Wb_slice | mipsize（分配贡献） | 新 pitch |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 256×256 | 4 | 4 | 4 | 16 | 256 |
| 1 | 128×128 | 2 | 2 | 2 | 4 | 128 |
| 2 | 64×64 | 1 | 1 | 1 | 1 | 64 |
| 3 | 32×32 | 1 | 1 | 1 | 1 | 64 |
| 4 | 16×16 | 1 | 1 | 1 | 0 | 32 |
| 5 | 8×8 | 1 | 1 | 1 | 0 | 16 |
| 6 | 4×4 | 1 | 1 | 1 | 0 | 8 |
| 7 | 2×2 | 1 | 1 | 1 | 0 | 8 |
| 8 | 1×1 | 1 | 1 | 1 | 0 | 8 |
| 9 | 1×1 | 1 | 1 | 1 | 0 | 8 |
| 10 | 1×1 | 1 | 1 | 1 | 0 | 8 |
| 11 | 1×1 | 1 | 1 | 1 | 0 | 8 |
| 12 | 1×1 | 1 | 1 | 1 | 0 | 8 |

mipsize 在 tail 外为 Wb_slice×Hb，首个 tail 计一个宏块，之后的 tail mip 不重复分配。这里是裁剪前的累加贡献；Linear mip0 的裁剪在第 4 节单独替换。

首个 tail 为 mip3：逻辑尺寸 32×32 满足阈值 64×32，剩余 10 级不超过容量 11。

**下标关系：判断目标 mip k 时，原循环 m=k-1，读取上一 mip 的块数。**

~~~text
k = 3, m = 2
in_miptail[3] = (Wb[2] <= 2) && (Hb[2] <= 1) && in_tail_chk[3]
                = (1 <= 2) && (1 <= 1) && 1
                = 1
~~~

Wb[2]、Hb[2] 属于 mip2，不称为 mip3 的块数。计算当前 mip 的 pitch_block 时仍使用 Wb[mip_level]。

## 4. 整条链 slice：GFX12-01（RTL 等价式）

~~~text
slice_b = 16 + 4 + 1 + 1 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 = 22
linear_can_trim_mip0 = linear && (map0_d == 1) = 0
Wb[0] = 4, Wb[0][0] = 0
map0_h >> 1 = 256 >> 1 = 128
slice_b_drop = (linear_can_trim_mip0 && Wb[0][0]) ? (map0_h >> 1) : 0 = 0
slice_b_gfx12 = 22 - 0 = 22
slice = 22 << (6 + 6) = 90112
slice_bytes = 90112 × 1 = 90112B
~~~

Linear 旧 mip0 占用 ceil(Wb[0]/2)×H 个 256B 单位；GFX12 为 ceil(Wb[0]×H/2)。两者之差恰为 Wb[0] 为奇数时的 floor(H/2)，因此新逻辑不需要新增乘法器或除法器。

该修正只替换 mip0 的贡献，且对查询链中任意 mip 都生效；不以当前 mip_level==0 作为开关。

## 5. 当前 mip 的 pitch：GFX12-02（RTL 等价式）

~~~text
pitch_block = Wb[0] << 6 = 4 << 6 = 256
mip_level=0 < tail_mipid=3
pitch = pitch_block = 256
~~~

GFX12 原式为 AlignUp(max(tail_width >> k,1),micro_width)。两种宽度都是二次幂，等价于 1 << max(T-k,U)；正文用比较后选择避免无符号减法下溢，无 /3、%3 或通用对齐器。

该级 pitch：修订前 256 → GFX12 修订后 256 元素。

## 6. 宏块偏移、tail 编号及下游换算

~~~text
maxmip_mask = (1 << (12 + 1)) - 1 = 0x1fff
mip_mask = (1 << (0 + 1)) - 1 = 0x1
mip_off_input_en = maxmip_mask & ~mip_mask = 0x1ffe
mip_offset_in_blks = 后续 mip 的分配贡献之和 = 6
mip_offset_b = 6 << 10 = 6144
macro_offset_bytes = 6144 × 256 = 1572864B
mip_in_tail = 17
pitch_b_raw = 256 >> 6 = 4
pitch_b = (pitch_b_raw == 0) ? 1 : pitch_b_raw = 4
~~~

GFX12-03 在模块 pitch 的约定下，用零检测和选择器等价实现向上取整，恢复宏块跨度。tail 内的 macroBlockOffset 不包含 mipTailOffset，不代表最终纹素地址或 tail 内原点。

## 7. 九个输出与参考值

GFX12 栏已转换到模块单位：sliceSize 除以元素字节数及有效采样数，macroBlockOffset 除以 256；无 tail 为 17，l2 字段按本轮语义推导。

| 输出 | 修订前 | GFX12 修订稿 | GFX12 参考（同口径） |
| --- | ---: | ---: | ---: |
| pitch | 256 | 256 | 256 |
| slice | 90112 | 90112 | 90112 |
| mip_in_tail | 17 | 17 | 17 |
| mip_offset_b | 6144 | 6144 | 6144 |
| l2_ms | 18 | 18 | 18 |
| l2_blk_w | 6 | 6 | 6 |
| l2_blk_h | 6 | 6 | 6 |
| l2_blk_d | 6 | 6 | 6 |
| l2_blk_w_slice | 6 | 6 | 6 |

本输入已纳入本轮 610 组定向配置；本页提取时再次核对所选 mip 的九个输出，均一致。结果适用于所列单位与资源约定，不作为无限输入域证明，也不代表原用例最终地址已重新执行验证。
