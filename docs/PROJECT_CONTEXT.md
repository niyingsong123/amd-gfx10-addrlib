# 项目上下文

## 当前状态

项目用于研究 AddrLib 地址计算。ADDRLIB.md 保存原始算法及用户补充的拍次标注，ADDRLIB_GFX12.md 保存适配 GFX12 的算法，并用适合 RTL 描述的等价式实现 Linear mip0 slice 裁剪、tail pitch 和下游宏块跨度适配。修改位置标记为 GFX12-01/02/03。

当前验证入口为 scripts/mipmap_compare/verify_gfx12_revision.cjs。固定 PAL c5e800072a32f68b6ccc4422936d96167c6e0728、GFX12 非 shared 分支；百万随机配置（100 个组合各 10,000 组）、3,365,705 个 mip 的九字段对比无差异，另有 610 组定向通过，160 组域外探测明确排除。详见 GFX12_ALGORITHM_REVISION.md 和 gfx12_million_results.json。这是独立算法转写的功能比较，不是 RTL 仿真或编译 C++ 对比。

范围为普通格式、默认 flags、mip 0～15；Linear 非 3D，2D/3D swizzle 对应同维资源，MSAA 仅用于单 mip 的二维 tiled。无自定义 pitch、denseSliceExact 或完整地址链路验证。随机通过不表示全部输入域已经证明。

原可信清单 TRUSTED_BASELINE.json 未改；baselines/ADDRLIB_pre_gfx12_20260924.md 保存原始字节。当前 ADDRLIB.md 已由用户补充 stage 注释，文件哈希不再等于原基准；移除 stage 标记并忽略空白后与快照一致。三个原可信 case 保持原样。GFX12 版独立保留修订字节和哈希。case0～case4 原文件不变，新计算单独保存为对应 _GFX12.md，不自动成为可信基准。源哈希不同不能单凭此判断历史用例错误。

RTL 时序分析见 GFX12_RTL_TIMING.md：先评估 slice 累加后的减法和 tail 控制路径，397,314 次候选恒等关系检查通过，但尚无综合或 STA 结果。项目尚缺可综合 RTL、目标器件/工艺、时钟和流水约束；实际优化需以同约束下的时序报告比较。

## 目录与使用范围

- ADDRLIB.md、ADDRLIB_GFX12.md、case/：原版、GFX12 版和用例；用例导航和命名规则见 case/README.md。
- ADDRLIB硬件算法.md：按当前 ADDRLIB.md 算法和 S0～S8 拍次重写的讲解稿，不属于可信基准，也不混入 GFX12 修订公式；图在 assets/addrlib_mas/。当前备份与核对记录见 ADDRLIB_MAS_SIX_CHAPTER_REWRITE.md。
- ADDRLIB硬件算法.md 的正文与配图只呈现技术内容，不出现来源、引用关系、路径式标注或优化、修订痕迹；保留必要的单位、位宽及适用条件。讲解稿及配图将 KiB 统一标为 KB，容量数值仍按原有二进制含义计算。溯源与修订记录放在独立的项目管理文件或配图资料中。
- 讲解稿使用 Markdown；正文为用途、概念、内存布局、S0～S8 概览、单一三维算例、通用公式六章，每章 3～4 小节，开头先定义 mipmap level，再讲纹理缩小与放大；LOD 首次出现时解释含义和用途；2.2 分为层次关系、Standard/Z-order、Morton 规则、三维实例四个子小节，区分概念排布与实际 swizzle 位序。完整数值计算集中第五章，查表放附录；独立提纲见 ADDRLIB_MAS_OUTLINE.md。
- 主例为 250×180×1537、SW_256KB_3D、1 BPE、单采样、mip0～10，访问 mip4 的 (5,6,69)；该点位于 tail，blk_index=0x480000 B，最终地址 0x304881D5。复算入口 scripts/verify_mas_3d_walkthrough.cjs；148,630 个有效 tail 地址无重叠，354 个普通宏块的 2,784 个边界点核对通过。仅限该配置的功能检查，无 RTL 或上游完整地址验证。正文共十三张图；2.2 使用层次图35、Standard/Z-order 图11/12及实际三维位表图32。补入接口、采样复用、实际位表的块层次、同一 Z 分组内的 tail 打包及地址合成；仍只用一个完整算例。正文/图检查入口 scripts/check_mas_document.py，统一绘图入口 scripts/render_mas_3d_walkthrough.py；补图数据见 ADDRLIB_MAS_SUPPLEMENT_CHECK.json。
- 地址计算从 S0 输入到 S8 最终输出计 8 拍：S0→S3 为前 3 拍，S3→S8 为后 5 拍；S0 为输入及同拍计算起点。变量 stage 归属保持原标注。
- stage 注释：行尾只指定对应变量；独立行指定后续变量的默认拍次，延续到下一个独立 stage 标记，单变量标记不改变默认段。大小写及空格/下划线写法等价；模块边界本身不改变段标记。同名变量按所属模块区分，明确的单变量标记优先。当前 `//S2 ->S3` 按转入 S3 解释；未定义的寄存器传递及握手不自行补设。
- 多 mipmap 内存分布图见 assets/addrlib_mas/MIPMAP_MEMORY_LAYOUT.md；按原版算法区分 Z 分组、宏块补齐和 tail 原点，包含原图构图扩展的三维 mip 综合图，绘图入口见配图说明，非新增可信用例。
- docs/：当前上下文、原可信清单、修订报告与紧凑结果。
- scripts/：校验与功能比较入口、固定版本参考源码；document.cjs 和 smoke.cjs 对应原版；verify_gfx12_revision.cjs 对应 GFX12 版。
- regression_0924/：修订前云端比较报告与模型的原样归档。
- backup/：仅作备份，默认不读、不搜索、不作为依据。

Git 目标为 niyingsong123/amd-gfx10-addrlib，主分支 main。跨平台运行使用 Node.js 20+，无需 npm 或完整 AddrLib 编译。新增 case 按已有最大编号加 1；详细历史由 Git 保存。
