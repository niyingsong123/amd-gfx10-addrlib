# 项目上下文

## 当前状态

项目用于研究 AddrLib 地址计算。ADDRLIB.md 已按用户要求改为 GFX12 算法，并用适合 RTL 描述的等价式实现 Linear mip0 slice 裁剪、tail pitch 和下游宏块跨度适配。修改位置标记为 GFX12-01/02/03。

当前验证入口为 scripts/mipmap_compare/verify_gfx12_revision.cjs。固定 PAL c5e800072a32f68b6ccc4422936d96167c6e0728、GFX12 非 shared 分支；百万随机配置（100 个组合各 10,000 组）、3,365,705 个 mip 的九字段对比无差异，另有 610 组定向通过，160 组域外探测明确排除。详见 GFX12_ALGORITHM_REVISION.md 和 gfx12_million_results.json。这是独立算法转写的功能比较，不是 RTL 仿真或编译 C++ 对比。

范围为普通格式、默认 flags、mip 0～15；Linear 非 3D，2D/3D swizzle 对应同维资源，MSAA 仅用于单 mip 的二维 tiled。无自定义 pitch、denseSliceExact 或完整地址链路验证。随机通过不表示全部输入域已经证明。

原可信清单 TRUSTED_BASELINE.json 未改；修订前原文保存于 baselines/ADDRLIB_pre_gfx12_20260924.md，字节与原哈希一致。旧基准校验会如实报告当前 ADDRLIB.md 已变化，原三个可信 case 仍通过。case0～case4 原文件不变，新计算单独保存为对应 _GFX12.md，不自动成为可信基准。源哈希不同不能单凭此判断历史用例错误。

## 目录与使用范围

- ADDRLIB.md、case/：当前算法与用例；用例导航和命名规则见 case/README.md。
- ADDRLIB_MAS.md：讲解稿，不属于可信基准，尚未随本轮公式修订；图和 Mermaid 源码在 assets/addrlib_mas/，原稿保存于提交 669bb67。
- docs/：当前上下文、原可信清单、修订报告与紧凑结果。
- scripts/：校验与功能比较入口、固定版本参考源码；旧 document.cjs 和 smoke.cjs 不能用于验证当前公式。
- regression_0924/：修订前云端比较报告与模型的原样归档。
- backup/：仅作备份，默认不读、不搜索、不作为依据。

Git 目标为 niyingsong123/amd-gfx10-addrlib，主分支 main。跨平台运行使用 Node.js 20+，无需 npm 或完整 AddrLib 编译。新增 case 按已有最大编号加 1；详细历史由 Git 保存。
