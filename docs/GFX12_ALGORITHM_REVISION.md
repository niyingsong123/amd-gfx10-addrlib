# ADDRLIB.md 的 GFX12 算法修订与百万组比较

## 1. 结论与版本

新公式依据 AMD PAL 的公开 GFX12 C++ 算法，经过等价化简后写成适合 RTL 描述的形式。**100 万组随机配置、3,365,705 个 mip、30,291,345 次字段比较，九个输出未发现差异。** 另外 610 组定向配置、2,282 个 mip 也无差异。160 组超出参考契约的探测单独分类，不计入通过率。

这是单 Node.js 进程中的整数功能计算比较，不是 RTL 仿真，也没有编译完整 AddrLib。参考端是独立的 C++ 算法转写；结论为“在声明范围和本次样本中未发现差异”，不是全部输入域的正确性证明。

| 文件或版本 | 标识 |
| --- | --- |
| 原文 | [字节快照](baselines/ADDRLIB_pre_gfx12_20260924.md)，修改前提交 1b6fa4a |
| 原文 SHA256 | 537CFA6D9FAFBAF3601B219B686D94CAA4B7C69FDFE89005DFF36A0B4CB6D3BB |
| 当前 ADDRLIB.md SHA256 | A6864BD26943078ADD333142BB40B87A9600B106572928F8B94621522CCACD8C |
| PAL 提交 | c5e800072a32f68b6ccc4422936d96167c6e0728 |
| GFX12 分支 | ADDR_GFX12_SHARED_BUILD=0 |

主文档保持 UTF-8 无 BOM、LF；未改写无关研究正文。[可信清单](TRUSTED_BASELINE.json)仍保存原哈希和可信声明，没有被新测试结果自动替换。

## 2. GFX12-01：Linear mip0 的 slice 裁剪

GFX12 在非 3D、单层 Linear 资源中，将 mip0 的分配量由“每行按 256B 对齐后乘高度”改成“128B rendering pitch 乘高度后，整体按 256B 对齐”。

令 n=Wb[0]，即 mip0 宽度占用的 128B 单位数，H=map0_h。两种分配量都用 256B 为单位：

~~~text
旧 mip0 贡献 = ceil(n/2) × H
GFX12 贡献   = ceil(n×H/2)
应减数量    = (n 为奇数) ? floor(H/2) : 0
~~~

证明：n 为偶数时两者相等；n=2a+1 时，差值为 H-ceil(H/2)=floor(H/2)。因此不必在 RTL 中重新做大乘法、字节对齐和单位换算。

正文采用：

~~~text
linear_can_trim_mip0 = linear && (map0_d == 1)
slice_b_drop = (linear_can_trim_mip0 && Wb[0][0]) ? (map0_h >> 1) : 0
slice_b_gfx12 = slice_b - slice_b_drop
slice = slice_b_gfx12 << (l2_blk_w_slice + l2_blk_h)
~~~

新增逻辑为条件判断、取最低位、固定移位和一次减法，不新增乘法器或除法器。原 slice 累加和最终单位移位继续使用。

**修正 mip0 的贡献，但不以当前查询 mip_level==0 为条件。** slice 是整条链的大小；查询任何 mip 都要得到同一个修订后总量。多层 Linear 不裁剪，其他 mip 的 256B 对齐规则不变。宏块偏移只累加当前 mip 之后的贡献，不包含 mip0，所以偏移公式无需修改。

依据：[GetMipOffset](../scripts/mipmap_compare/upstream/src/gfx12/gfx12addrlib.cpp) 第 450～505 行；[CanTrimLinearPadding](../scripts/mipmap_compare/upstream/src/core/addrlib3.cpp) 第 1007～1014 行。

## 3. GFX12-02：tail pitch 的指数计算

GFX12 从 tail 的最大宽度开始，每经过一个 tail mip 将宽度减半，再对齐到 256B micro block 的宽度：

~~~text
k = mip_level - tail_mipid
pitch = AlignUp(max(w_tail_sz >> k, 1), micro_width)
~~~

不是用实际 mip 的逻辑宽度来代替 w_tail_sz。令 w_tail_sz=2^T、micro_width=2^U，因为二者都是二次幂：

~~~text
pitch = 2^max(T-k, U)
~~~

U 直接由五项表给出：

| 元素字节数 | 1 | 2 | 4 | 8 | 16 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2D micro 宽度 log2 | 4 | 4 | 3 | 3 | 2 |
| 3D micro 宽度 log2 | 3 | 2 | 2 | 2 | 1 |

表项来自 HwlGetMicroBlockSize 中 blockBits=8-l2_eb 的 /2、/3 与余数公式；它们已在文档中预先化成常数，不要求 RTL 实现除法或求余。

正文采用：

~~~text
T = l2_blk_w - (y_bias ? 0 : 1)
U = 上表的结果
k = mip_level - tail_mipid
limit = T - U
l2_pitch_tail = (k < limit) ? (T-k) : U
pitch = 1 << l2_pitch_tail
~~~

合法 tail 模式中 T>=U。比较后选择避免无符号下溢；只需小表、少量小位宽减法和比较、单热译码，不需要通用 AlignUp 数据通路。tail 外继续输出 Wb[mip_level]<<l2_blk_w。宏块 l2_blk_w/h/d、首 tail 判定、tail 容量和偏移公式保持原样。

**next-in-tail 下标不变：用第 m 级的 Wb[m]/Hb[m] 判断第 m+1 级能否进入 tail。** Wb[0]/Hb[0] 始终属于 mip0。

依据：[GetMipOrigin](../scripts/mipmap_compare/upstream/src/gfx12/gfx12addrlib.cpp) 第 329～395 行；同文件 HwlGetMicroBlockSize 第 1810～1848 行。以上是代数和结构简化，没有进行综合、时序或面积测量。

## 4. GFX12-03：保留原宏块寻址跨度

tail pitch 可能小于宏块宽度，原先直接右移会得到 0。下游改为：

~~~text
pitch_b_raw = pitch >> l2_blk_w
pitch_b = (pitch_b_raw == 0) ? 1 : pitch_b_raw
~~~

例：pitch=32、宏块宽度=64，则右移为 0，选择器恢复为 1。

这一步是本项目为输出语义调整所做的接入适配，不是照抄 GFX12 的同名公式。成立条件是：tail 外 pitch 已按宏块对齐；tail 内 0<pitch<=宏块宽度。因此零检测和选择器等价于 ceil(pitch/宏块宽度)，不需要一般的向上取整加法器。

百万组的 3,365,705 个 mip 均检查了新旧宏块跨度一致。另在定向复算中比较 4,564 个新旧 block_index 值，未发现差异。Linear 裁剪只发生在单层资源，有效 z=0，slice×z 项不受影响。此处没有验证完整纹素地址链路。

## 5. 输入、输出和适用域

保留 12 个输入、9 个输出。输入尺寸从 minus_1 编码恢复；maxmip+1 是 mip 数量；元素大小为 2^l2_eb，采样数为 2^l2_ns。x/y/z/s 坐标不参与布局计算。修订后的 map0_d 在 Linear 模式用于判断是否单层；不能再将该输入一概视为无关输入。

| 模块输出 | GFX12 对照口径 |
| --- | --- |
| pitch | pMipInfo[m].pitch，单位为元素；tail 内也逐值比较，不豁免表示差异 |
| slice | 乘元素字节数、有效采样数，与整条链 sliceSize 比较；不再次乘资源深度 |
| mip_in_tail | 从 firstMipIdInTail 推导相对级别，无 tail 统一为 17 |
| mip_offset_b | 乘 256，对比 macroBlockOffset；不混入 mipTailOffset |
| l2_ms | tiled 对应物理块 log2；Linear 是 128B rendering 尺度的推导值 7 |
| l2_blk_w/h/d | tiled 对应块尺寸 log2；Linear 宽度用 rendering 对齐推导，原始物理 blockExtent 仍为 256B |
| l2_blk_w_slice | 原 slice 宽度对齐指数；Linear 为 8-l2_eb，其他模式为块宽指数 |

参考接口没有直接暴露的 l2 字段明确作为推导值；原始物理块尺寸与换算值分别保留。模式显式映射见独立参考的 MAP：Linear、256B 2D、4KB/64KB/256KB 的 2D/3D，共八种；本次使用 GFX12 固定 256KB 模式，没有使用 GFX10 VAR 代替。

适用域：

- mip 索引 0～15；MAXMIP=17 仅保留内部数组和无 tail 哨兵意义。
- 元素大小 1/2/4/8/16B；采样数 1/2/4/8，MSAA 只用于单 mip 的二维 tiled 资源。
- Linear 按非 3D 资源处理，map0_d 是层数；二维 swizzle 配二维资源，三维 swizzle 配三维资源。Linear 3D、三维资源使用二维 swizzle 不在该接口约定中。
- 普通未压缩元素、默认 flags；无自定义 pitch/height、denseSliceExact、压缩格式预处理。
- 乘积、掩码和偏移使用 BigInt；小尺寸和指数用精确整数 Number。未知 RTL 截断不自行添加，负数 tail 判断保留符号。

## 6. 百万组结果与覆盖

入口：[verify_gfx12_revision.cjs](../scripts/mipmap_compare/verify_gfx12_revision.cjs)；完整计数、源码哈希、输入输出样例和有限反例槽位见 [机器结果](gfx12_million_results.json)。

文档端复用已核对的未修改阶段，并单独实现本轮两个模块改动及 pitch_b 适配；GFX12 端使用独立的 [公开 C++ 算法转写](../regression_0924/cloud/scripts/mipmap_compare/gfx12.cjs)，不调用文档模型的逻辑。旧模型和归档资料保持原样。

种子 0x20260922。100 个模式/元素/采样组合各 10,000 组，每组检查所有请求 mip。宽高为 1～16384，3D 深度为 1～2048，混合普通随机、二次幂、块对齐边界和 tail 阈值附近尺寸。

| 模式 | 随机配置 | mip | 差异 mip |
| --- | ---: | ---: | ---: |
| Linear | 50,000 | 341,772 | 0 |
| 256B 2D | 200,000 | 490,958 | 0 |
| 4KB 2D | 200,000 | 492,992 | 0 |
| 64KB 2D | 200,000 | 497,338 | 0 |
| 256KB 2D | 200,000 | 499,476 | 0 |
| 4KB 3D | 50,000 | 348,079 | 0 |
| 64KB 3D | 50,000 | 346,073 | 0 |
| 256KB 3D | 50,000 | 349,017 | 0 |
| 合计 | 1,000,000 | 3,365,705 | 0 |

九个字段各比较 3,365,705 次，差异均为 0；合计 30,291,345 次。块尺寸、tail 容量、有效首 tail、各级尺寸、pitch、每级 slice 贡献、宏块偏移等阶段均未发现差异。

随机覆盖中：600,000 组 MSAA；743,923 组单级、144,529 组完整链、111,548 组截断链；141,458 组存在 tail，其中 2,410 组首级入 tail；25,138 组单层 Linear，12,120 组实际触发分配量变化。单采样完整链由最大维度确定；三维尺寸包含深度。

额外的 [610 组定向输入](gfx12_revision_inputs.json) 覆盖 65536 尺寸、mip15、tail 边界±1 和五个 case，结果为 2,282 个 mip、20,538 次字段比较无差异，见 [定向结果](gfx12_revision_results.json)。简化前后在同一输入集的计算摘要完全一致，说明 RTL 等价改写未改变这批结果。

160 组额外探测因 mip16 或 MSAA 多 mip 超出参考契约而被拒绝。全部 1,000,770 组输入都有分类；可比配置为 1,000,610 组，总计 3,367,987 个 mip、30,311,883 次字段比较。没有将拒绝或跳过计为通过，也没有为了统计一致而豁免 tail pitch。

对 100 个参数组合逐一扰动 x/y/z/s，完成 12,420 次九输出字段检查；95 个非 Linear 组合另做深度扰动，完成 2,763 次字段检查，均保持不变。Linear 的层数属于有效条件，未错误纳入深度不变性声明。

本机 Node.js v24.19.0、Windows x64，批量计算耗时约 89.50 秒；不包含资料整理时间。循环内无子进程，也不逐条保存百万样本。输入由种子和编号重建，保存汇总与少量完整原始/换算输出。

汇总 SHA256（包含定向、拒绝探测及随机输入输出，编码格式见 JSON）：

~~~text
350d9101096b7df4456d5a1e9aebac01e1e6fd4f5b1e3293be7c25ce9b262173
~~~

## 7. 复现与用例

从仓库根目录，Node.js 20+，无 npm 依赖：

~~~sh
# 完整百万组；另含 610 组定向与 160 组契约探测
node scripts/mipmap_compare/verify_gfx12_revision.cjs --seed 0x20260922 --count 1000000 --out build/gfx12_million_results.json

# 只检查定向集合和契约探测
node scripts/mipmap_compare/verify_gfx12_revision.cjs --directed-only --out build/gfx12_directed_results.json

# 按零起始随机配置编号重放全部 mip，或指定一个 mip
node scripts/mipmap_compare/verify_gfx12_revision.cjs --seed 0x20260922 --replay 999999
node scripts/mipmap_compare/verify_gfx12_revision.cjs --seed 0x20260922 --replay 999999 --mip 0
~~~

入口会核对当前主文档、原模型、参考转写和固定 C++ 文件的哈希，防止源版本改变后仍套用本次结论。重放返回全部 12 个输入、模块原始九输出、参考原始量及换算结果。

原 case0～case4 保持不变，新公式的五份用例单独使用 _GFX12 后缀保存，见 [用例索引](../case/README.md)。主要变化：case0 的 pitch 64→32；case2 的 pitch 32→4；case3 的 slice 512→256；case4 的 pitch 64→32；case1 九输出不变。新用例没有自动取得可信基准身份，也没有宣称重算完整最终地址。

## 8. 基准与限制

规定的 verify_trusted_baseline.ps1 仍按原可信清单检查：三个可信 case 通过，ADDRLIB.md 因用户授权的算法修改而报告 CHANGED。原文快照的 SHA256 和长度与原清单完全一致；没有通过更新旧哈希掩盖变化。

新结果支持本轮声明域内的算法匹配；未知 RTL 位宽、硬件综合与时序、域外资源、完整地址流水线仍未验证。两处代数恒等关系有推导依据，但百万随机通过不构成整个模块的无限输入域证明。

旧 document.cjs 与 smoke.cjs 仍属于原文模型与原基准校验；验证当前算法应使用本报告的新入口。旧云端结果保留在 regression_0924/，本轮没有改写其内容或结论。
