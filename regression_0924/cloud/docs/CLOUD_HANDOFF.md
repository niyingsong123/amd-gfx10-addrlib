# 云端续做：mipmap 参数算法比较

先读 PROJECT_CONTEXT.md 和根目录 AGENTS.md。可信原文保持字节不变，backup/ 默认不读。本文件记录尚未完成的任务，不是验证报告。

## 当前边界

只验证 mipmap_param_calc_core_gc。公开 GFX10 为主要参考，GFX12 用于判断各阶段的规则归属；没有证据时不把公开 GFX10 称为精确 GFX10.2。其他地址计算模块、最终地址及旧 mip0 测试结论不在本次验证范围。

**用户最新要求：先完成小规模测试，一起查看结果，再决定是否执行百万组。未经用户进一步决定，不运行百万组。** 建议小规模为固定种子 0x20260922、100 个参数组合各 100 组，另加定向边界和三个可信用例。

## 现有实现与待完成内容

scripts/mipmap_compare/ 下已有三个独立功能模型 document.cjs、gfx10.cjs、gfx12.cjs，以及 generate.cjs、compare.cjs 草稿。它们尚未完成系统核验，不是已经验证正确的参考实现；不能把函数存在或语法通过当成算法通过。

云端需要先逐式审查模型，补齐统一 run.cjs 入口、自检、统计、摘要哈希、输入不变性检查和限量反例输出，然后运行小规模并提交中文报告。保留输入、文档原始输出、参考原始量、单位换算值、分类、种子、配置编号、mip 编号；支持种子和编号重放。阶段输入固定后的结果只用于定位，不算整体通过。

已下载的 AMD PAL 固定提交为 c5e800072a32f68b6ccc4422936d96167c6e0728。scripts/mipmap_compare/upstream/ 保留与转写有关的原始文件，provenance.json 记录 Git blob 和 SHA256。不要编译完整 AddrLib。GFX12 参考选取 ADDR_GFX12_SHARED_BUILD=0 分支。模型不得共享彼此的公式实现。

重点审查：

- 12 个输入、9 个输出的逐项口径；尺寸减一恢复，maxmip+1 是 mip 总数。
- slice 是 XY 元素位置数，乘元素字节数和有效 samples 与链 sliceSize 比较；厚块深度用于宏块偏移的 slab 单位，不能再乘整个资源深度。
- mip_offset_b 乘 256 比 macroBlockOffset，不混用 tail 内 mipTailOffset。
- 无 tail 归一为 17；文档可能计算出请求链以外的潜在首 tail，要保留原值并区分。
- tail 内 pitch 表示差异单列，不能自动计作数值相同。
- GFX10 Linear 是 256B 对齐；GFX12 渲染 pitch 为 128B、slice pitch 为 256B，单层资源的末端裁剪会影响 sliceSize。
- GFX10 的 64KB 二维布局暂映射到 ADDR_SW_64KB_R_X，以检查 MSAA；这只是布局算法映射，不宣称地址 swizzle 等价。256B/4KB D 模式不支持 MSAA；固定 256KB 不替换成 VAR。
- 两版公开源码的 MaxMipLevels=16，文档 MAXMIP=17。第 16 号 mip 是参考契约之外的边界，不能算通过。
- GFX10 MicroTiled 多 mip 的部分乘法在 C++ 中先以 UINT_32 运算，再累加到 UINT_64。检查极限尺寸的溢出语义；当前足宽草稿尚未模拟该处截断。
- x/y/z/s 坐标和文档未使用的深度输入要做单变量扰动。未知 RTL 位宽列为假设，不擅自截断或修改文档来匹配。

## 后续完整规模（等待用户决定）

4 个二维模式 × 5 个元素大小 × 4 个采样数，另加 3 个三维模式 × 5 个元素大小、Linear × 5，合计 100 个组合。每组合 10,000 组即百万组，每组检查全部请求 mip。宽高 1～16384，三维深度 1～2048，混合普通随机、二次幂、块边界、tail 阈值的 ±1；定向包含 65536、单级/完整/截断链、首级入 tail、无 tail 和相邻级别。MSAA 主测试使用单级，MSAA+mip 作为额外非法探测。

分类至少包括：一致、数值差异、表达口径不同、无等价模式、参考契约拒绝、模型假设未明确。后面三类排除在可比分母外，绝不能算通过。全部 9 字段一致才算整体匹配；随机通过不构成无限输入域的数学证明。

## 云端环境

使用 Node.js 20 或更新版本，无 npm 依赖，无 C++ 编译工具要求。从仓库根目录执行：

```sh
node scripts/verify_trusted_baseline.cjs
```

Windows 的原校验入口 scripts/verify_trusted_baseline.ps1 保留。完成修改后校验可信文件、检查 git diff/status 并提交。仅保存限量反例和统计；大批样本放忽略目录，不逐一写入 case/ 或上下文。
