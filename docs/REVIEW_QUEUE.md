# 待核实清单

本表记录当前观察与尚未完成的验证，不预判旧资料有错。三个用户确认文件的可信地位不因版本差异而被撤销。

| ID | 状态 | 对象 / 观察 | 后续检查与完成条件 |
| --- | --- | --- | --- |
| R01 | 待核实 | 当前主文档与两个用例所记源哈希不同；mip6 源哈希匹配 backup/ADDRLIB.md | 比较源版本语义差异，记录用例适用范围；不能仅因字节不同否定用例 |
| R02 | 待核实 | analysis/case_mip4_xyz_5_6_3_step_by_step.md 未被列为可信 | 明确源版本、假设与输入，逐步复算并记录结论 |
| R03 | 待核实 | analysis/addrlib_version_audit.md、three_address_calculation_examples.md、verify_version_audit.ps1 | 检查旧行号、固定来源、算法假设及脚本覆盖；脚本通过不代表当前主文档已验证 |
| R04 | 待核实 | analysis/gfx10_64kb.md、gfx10_64kb_swizzle_deepdive.md、gfx10_addrlib_深入浅出总览.md、gfx10_mip_tail_and_tail_offset.md、mip_tail_gfx10_analysis.md | 逐项对照可信基准，区分其他代际背景与当前规则 |
| R05 | 待核实 | analysis/GFX12对比/ 下两个文件，backup/ 下两个文件 | 记录与主文档差异及来源；“对照原文”和“filled”名称不能证明正确 |
| R06 | 待核实 | upstream/README.md、verilog/README.md 的历史声明 | 开展相关工作时固定实际来源并验证；当前没有源码快照或完整模型 |
| R07 | 部分处理 | 旧入口链接缺失的 ADDRLIB_comment.md；可信用例存在旧路径 | 两个导航 README 已重写；原始用例与旧分析保留，后续引用使用有效相对路径，必要时追查缺失原稿 |

关闭问题时补充验证日期、方法、源版本、结果和相关提交。仅有推测或旧文档自述不足以关闭问题。
