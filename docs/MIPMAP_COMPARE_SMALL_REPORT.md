# mipmap_param_calc_core_gc 小规模算法对比报告

## 范围与结论

本轮只复算 `mipmap_param_calc_core_gc` 文档算法，并与 AMD PAL 固定提交
`c5e800072a32f68b6ccc4422936d96167c6e0728` 中的公开 GFX10 实现比较；GFX12 非 shared 分支只用于定位规则来源。
没有证据把该公开实现精确称为 GFX10.2。本轮不是 RTL 仿真，也没有执行百万组。

小规模结果已经给出否定“模块对公开 GFX10 完全匹配”的明确反例：Linear 的宏块尺度和 pitch、奇数
`log2_num_samples` 的 GFX10 MSAA 二维块方向，以及 MicroTiled 极端多 mip 的 C++ `UINT32` 中间乘积回绕均可造成数值差异。
另一方面，宏块模式的 tail 容量、首 tail mip、各级逻辑尺寸和宏块偏移在本轮全部可比样本中未发现差异；这些是有限样本结论，不是数学证明。

## 复核依据与模型边界

- 参考源码来自仓库内 `scripts/mipmap_compare/upstream/`；运行前按 `provenance.json` 同时核对 SHA-256 和 Git blob。
- GFX10 转写逐阶段对应 `ComputeThinBlockDimension`、`ComputeThickBlockDimension`、`GetMipTailDim`、
  `GetMaxNumMipsInTail`、`ComputeSurfaceInfoMicroTiled`、`ComputeSurfaceInfoMacroTiled` 和
  `HwlComputeSurfaceInfoLinear`。MicroTiled 多 mip 的 `pitch * height * elementBytes` 按 C++ 的
  `UINT_32` 中间表达式取低 32 位，再累加到 `UINT_64`。
- GFX12 转写选择 `ADDR_GFX12_SHARED_BUILD=0`；两个参考模型都不导入或调用文档模型。
- 文档模型尺寸和指数使用可精确表示当前范围的 JavaScript `Number`，乘积、mask 和 offset 使用 `BigInt`。
  未定义的 RTL 位宽没有被猜测或截断，因此结果是文档算法复算，不是 RTL 行为保证。
- 输入的减一尺寸先加 1；`maxmip + 1` 是 mip 数量。`slice` 从文档 XY 元素位置数换算为字节；
  `mip_offset_b * 256` 只与 `macroBlockOffset` 比较，不加入 tail 内偏移。无 tail 统一为 17。
  参考接口没有直接返回的对齐指数均明确作为从块尺寸推导的量。
- 固定 256KB 没有映射成 GFX10 VAR；它在 GFX10 统计中属于“无等价模式”。GFX10 64KB 二维暂映射
  `ADDR_SW_64KB_R_X` 以检查布局/MSAA 规则，不声称地址 swizzle 等价。
- PAL `MaxMipLevels=16` 仅允许索引 0～15；文档 `MAXMIP=17` 的索引 16 单列为参考拒绝，未计作通过。

## 输入与实际规模

统一入口使用种子 `0x20260922`，100 个模式/元素大小/采样数组合各生成 100 个随机配置，共 10,000 个；
另加入 670 个定向配置。合计：

| 项目 | 数量 |
|---|---:|
| 配置 | 10,670 |
| 请求范围内 mip | 36,607 |
| 两个参考、9 字段的分类次数 | 658,926 |
| 不变性扰动 | 500 |

覆盖 8 种文档模式、元素字节指数 0～4、二维采样指数 0～3；普通单采样包含单级、完整链和截断链，
多采样主样本为单级，另有多采样多 mip 拒绝探测。随机范围为宽高 1～16384、3D 深度 1～2048；
定向加入二次幂、块/tail 阈值 ±1、65536 尺寸、mip 16、首级入 tail、无 tail、tail 前后相邻级和 Linear 末端裁剪。

## 模块整体分类

下表是“配置”分类；一个可比配置只要任一请求 mip 有数值差异就归数值差异，其次才归表达口径不同。
拒绝、无等价和假设未明确绝不计作通过。

| 参考 | 一致 | 数值差异 | 表达口径不同 | 无等价模式 | 参考拒绝 | 假设未明确 |
|---|---:|---:|---:|---:|---:|---:|
| 公开 GFX10 | 2,688 | 1,169 | 938 | 2,665 | 3,210 | 0 |
| GFX12 辅助 | 8,919 | 127 | 1,464 | 0 | 160 | 0 |

GFX10 的 22,654 个可比 mip 中，14,684 个九字段全同，4,103 个有数值差异，3,867 个只有 tail 内
pitch 表达不同。GFX12 的 34,607 个可比 mip 中，相应数字为 27,198、830、6,579。

## 字段与阶段定位

### 更符合 GFX12 的部分

- 除 Linear 物理 slice block 的口径外，文档的块指数、tail 容量、首 tail、各级尺寸、宏块偏移均与
  GFX12 可比结果一致。固定 256KB 模式也有直接 GFX12 对应。
- GFX12 的 550 个 `block_dimensions` 差异全部来自 Linear：文档输出的是 128B rendering pitch 指数，
  GFX12 物理 slice block 是 256B；归一后的 9 输出对齐指数按接口语义比较为一致。
- GFX12 的 127 个配置/830 个 mip 仅在 `slice` 数值上不同，来源是单层 Linear 的末端 256B 裁剪；
  使用相同参考块、容量和首 tail 后，非 Linear 的 slice 累加与逐级贡献未发现差异。

### 符合公开 GFX10 的部分

- 所有 4,795 个 GFX10 可比配置的首 tail 判定均一致；有 tail 容量计算的 3,705 个配置也全部一致。
- 所有 22,654 个 GFX10 可比 mip 的逻辑尺寸、归一 tail 相对编号和宏块字节偏移均一致。
- 强制双方使用相同参考块、tail 容量和首 tail 后，tail 外 pitch 15,087 次全部一致；这说明大量 pitch
  差异来自更早的块形状规则，而非后续 pitch 对齐公式。

### 不符合公开 GFX10 或不完全符合两者的部分

- GFX10 有 1,168 个可比配置块形状不同，集中于 Linear 的 256B 对齐口径及 MSAA 二维块宽高方向。
  例如缩减反例 `SW_64KB_2D`、8bpp、8 samples、`1×126`：文档块为 `128×64`，公开 GFX10 为
  `64×128`，导致 slice 分别为 131072B 和 65536B。
- 最小 Linear 反例 `SW_LINEAR`、8bpp、`1×1`：文档 pitch 128、`l2_ms=7`，公开 GFX10 pitch 256、
  `l2_ms=8`；slice 都是 256B。它说明 Linear 并非完整 GFX10 匹配。
- GFX10 MicroTiled 多 mip 的极端 65536 维度触发 `UINT32` 乘积回绕。隔离阶段仍有 1 个配置的
  slice 累加/逐级贡献不同，这是有意保留 C++ 整数语义后的真实差异，而不是用足宽 `BigInt` 掩盖。
- Linear 同时体现“更像 GFX12 的 128B rendering pitch”和“文档固定 256B slice pitch”；但 GFX12
  单层末端会裁剪，文档不会。因此不能笼统称 Linear 完全匹配 GFX12，更不能称其匹配 GFX10。

tail 内 pitch 在两边代表方式不同，共有 GFX10 3,867、GFX12 6,579 个 mip 被单独归为“表达口径不同”，
没有伪装成数值一致。`mip_offset_b` 只比较宏块偏移，所有可比项一致；tail 内 `mipTailOffset` 未混入。

## 不变性与限制

对前 100 个随机配置分别扰动 x、y、z、sample 坐标和深度输入，共 500 次。文档模型及 GFX10 可比模型
未发现输出变化；GFX12 有 1 次深度从 1 变 2 后变化，因为其单层 Linear 末端裁剪条件依赖层数。
这不是坐标进入 mip 参数运算，而是参考 API 的资源层数语义差异。

结果文件只保存汇总、可信用例回归和每类限量代表性反例（含双方原始量、换算量及有界贪心缩减），
不保存整批逐样本日志。输入摘要 SHA-256 为
`3b480db81b8a2bda35b49f0b213973a75badc61003083ff2a0d892da54fb4419`，输出汇总 SHA-256 为
`9be204580dbdde236ec7cda08a77089c1c3a8773f2423bbab889a07d307d89e5`。

本轮没有证明无限输入域上的等价性，没有验证未知 RTL 位宽，也没有把阶段通过计作模块整体通过。
需与用户讨论后再决定是否扩展至百万组。

## 运行与重放

```sh
# 本报告的小规模运行
node scripts/mipmap_compare/run.cjs --seed 0x20260922 --config-count 10000 \
  --out docs/mipmap_compare_small_results.json

# 随机配置编号 48 的全部请求 mip
node scripts/mipmap_compare/run.cjs --seed 0x20260922 --config-number 48 --no-directed

# 随机配置编号 48 的 mip 0
node scripts/mipmap_compare/run.cjs --seed 0x20260922 --config-number 48 --mip 0 --no-directed
```

