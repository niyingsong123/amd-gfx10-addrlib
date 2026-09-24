# GFX12 模块的 RTL 时序分析

## 当前结论

[ADDRLIB_GFX12.md](../ADDRLIB_GFX12.md) 是已经做过百万组功能比较的算法版本，不是可直接交给综合工具的完整 RTL。去掉乘除法的等价写法有助于控制逻辑复杂度，但不能据此认定 timing 最优。

本次检查未在当前项目源文件中发现 .v/.sv、SDC/XDC、工艺 .lib 或 FPGA 工程；PATH 中未发现 Yosys、Vivado、Quartus、OpenSTA、Design Compiler 或 Genus。该检查不能排除其他目录或远程服务器上存在工具。

文档的 S0/S1/S2 是计算阶段说明，没有 clk/reset、寄存器语句或 valid/ready 协议，不能直接当成已实现的三级流水。目标 ASIC/FPGA、器件/工艺、频率、延迟和吞吐量要求尚待明确。因此当前没有综合网表、WNS/TNS、面积或 Fmax 实测结果。

## 1. 应优先检查的依赖路径

以下是根据公式作出的结构推断，实际关键路径以 STA 报告为准。

| 路径 | 可能的问题 | 优先尝试的结构 |
| --- | --- | --- |
| 各级 mipsize → slice 累加 → 新增裁剪减法 → 单位移位 | 总和之后再接一次宽位减法，可能延长原有末级路径 | 提前算裁剪条件和数量；比较“先修正 mip0 贡献再入树”及“负修正项参与压缩树”，避免只在末端追加运算 |
| tail 判定 → 编码 → k 减法 → 指数减法/比较 → pitch 译码 | 控制依赖连续，软件公式较短不代表门级路径浅 | T/U/limit 前移到模式解码阶段；比较预计算 base/stop 或对 tail 等级直接译码 |
| 多项 mipsize 累加 | 文本加法顺序不保证综合后就是理想加法树 | 观察网表；比较平衡加法树、压缩树，以及在现有阶段边界切分 |
| tail_mipid 编码与大量选择器控制 | 编码优先链、控制扇出可能进入关键路径 | 利用单调 tail 位图并行产生 one-hot，再做 OR 编码；评估实际扇出与布线 |

当前 slice 的公式依赖如下；图中不代表已存在寄存器：

~~~mermaid
flowchart LR
    A["各级 mipsize"] --> B["slice_b 累加"]
    B --> C["slice_b - drop"]
    D["Linear、层数、宽度奇偶、高度"] --> E["drop"]
    E --> C
    C --> F["单位左移"]
    F --> G["slice"]
~~~

将修正前移不保证一定更快：提前修正 mip0 也可能把减法放到乘法之后，成为另一条长路径。候选应在相同工艺、约束、流水延迟和负载下比较。使用补码将 -drop 并入压缩树时，还必须正确处理符号扩展、补偿进位和最终非负范围。

## 2. 可提前计算的 Linear 条件

令 Wm1=map0_w_minus_1、b=7-l2_eb，Linear 模式下：

~~~text
Wb[0] = ceil((Wm1+1)/2^b) = (Wm1 >> b) + 1
Wb[0][0] = ~Wm1[b]              // 仅对该位取反
map0_d == 1  <=>  map0_d_minus_1 == 0

trim_en = linear
       && (map0_d_minus_1 == 0)
       && !map0_w_minus_1[b]
~~~

这样 trim_en 可直接由输入和模式解码产生，不依赖完整 Wb[0] 的对齐加法结果。b 只取 3～7，取位可实现为小选择器；是否优于工具自动优化仍需测量。

令 Hm1=map0_h_minus_1：

~~~text
floor(map0_h/2) = (Hm1 >> 1) + Hm1[0]
drop = trim_en ? floor(map0_h/2) : 0
~~~

高度为 65536 时，右式为 32767+1=32768，结果必须保留 16 位；不能把 15 位切片加法的溢出截掉。实际 map0_h 本身需要能表示 65536。BigInt 模型的足宽计算要求不能直接等同于“RTL 所有信号都用 64 位”，应逐信号证明范围后定宽。

## 3. 缩短 tail pitch 的末级依赖

现有等价式：

~~~text
T = log2(tail 最大宽度)
U = log2(micro 宽度)
k = mip_level - tail_mipid
pitch_exp = (k < T-U) ? T-k : U
~~~

T、U、T-U 只依赖模式和元素大小，可尝试与模式解码一起计算，在需要的位置寄存。另一种候选是：

~~~text
base = tail_mipid + T
stop = base - U
pitch_exp = (mip_level < stop) ? (base - mip_level) : U
pitch = 1 << pitch_exp
~~~

若 base/stop 能在前一级准备好，末级不必先算 k 再作后续运算。但该方案会增加前一级的工作，是否适合现有阶段边界必须由各级时序决定。tail 分支内计算，保留无 tail 和 tail 外分支；base/stop 在本域至少保留 5 位无符号数。

pitch 的指数范围很小，可以比较显式 one-hot 译码与移位写法的映射结果；不能仅凭 RTL 中出现 << 就认定会产生昂贵桶形移位器，也不能认定综合器必然给出最优实现。

## 4. tail 编码与流水边界

合法输入下，各级尺寸随 mip 增大不增，剩余级数条件也只会从不满足变成满足，因此 in_miptail 是单调位图。可以由：

~~~text
first_hot[0] = in_miptail[0]
first_hot[m] = in_miptail[m] && !in_miptail[m-1]
~~~

并行构造 one-hot，再对编码位做 OR 归约。无命中输出 17；Linear、256B 和单 mip 的强制无 tail 规则继续保留。这个推导依赖位图单调性，不能当作任意非单调位图的通用优先编码器。

若允许增加流水级，可以把乘法、压缩累加和最终结果整理拆开；如果总延迟固定，则先尝试在已有阶段间移动解码和小位宽计算。所有九个输出及 valid、模式、mip 和请求标签必须保持同一请求的周期对齐。增加流水通常以额外延迟和控制开销换取更短的单级路径，见 [AMD UG949 流水化说明](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Pipelining-Considerations)。

## 5. 已完成验证与后续综合条件

以上候选仍是实现分析，未写入已验证算法正文或改变流水接口。运行 [check_rtl_rewrites.cjs](../scripts/mipmap_compare/check_rtl_rewrites.cjs)，完成：

| 等价检查 | 数量 | 结果 |
| --- | ---: | --- |
| 1～65536 宽度、五种元素大小，直接取位与 Wb[0] 奇偶一致 | 327,680 | 通过 |
| 1～65536 高度，从减一编码求 floor(H/2) | 65,536 | 通过 |
| 六种有 tail 模式、五种元素大小、合法 mip 索引下的 base/stop 改写 | 4,080 | 通过 |
| 17 位单调 tail 位图的全部 18 种形式 | 18 | 通过 |

[机器结果](gfx12_rtl_structure_checks.json)记录源哈希和边界假设。这 397,314 次是整数恒等关系检查，不是综合、仿真、STA，也不能证明任意流水实现正确。

~~~sh
node scripts/mipmap_compare/check_rtl_rewrites.cjs --out build/gfx12_rtl_structure_checks.json
~~~

实际综合流程需要确定：

- ASIC：目标标准单元库、PVT corner、综合/STA 工具及可用运行环境；FPGA：具体器件和工具。
- 时钟周期、输入输出延迟、时钟不确定度、输入驱动和输出负载。
- 允许的流水延迟、每拍吞吐量、复位和 valid/ready 协议、端口位宽。
- 若需布局布线后结果，还需要相应物理实现环境和寄生信息。

在这些条件下可以建立“可综合 RTL → 功能/形式等价检查 → 综合映射 → STA → 关键路径反馈 → 再优化”的流程，并统一比较延迟、面积和寄存器开销。Yosys 支持按 Liberty 标准单元库或 FPGA LUT 进行映射；OpenSTA 使用网表、Liberty 和 SDC 等资料做门级时序分析，并支持寄生信息。[Yosys 官方说明](https://yosyshq.readthedocs.io/projects/yosys/en/stable/using_yosys/synthesis/abc.html)、[OpenSTA 官方说明](https://github.com/The-OpenROAD-Project/OpenSTA)。

未绑定实际工艺的逻辑级数评估，可以辅助比较结构；综合前估计、综合后 STA 和布局布线后 STA 应分别标注，不能把无布线结果当作最终 timing。
