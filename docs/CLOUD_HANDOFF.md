# 云端继续使用说明

先读 [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) 与根目录 AGENTS.md。当前目标和证据已更新为 GFX12 修订算法；修订前 GFX10/GFX12 比较保存在 regression_0924/，不回写归档。

ADDRLIB_GFX12.md 的百万组功能比较已经完成，结论、范围与剩余限制见 [GFX12_ALGORITHM_REVISION.md](GFX12_ALGORITHM_REVISION.md)。用一个 Node.js 进程比较文档公式与独立的公开 GFX12 C++ 算法转写，不进行 RTL 仿真，不编译完整 AddrLib。

Node.js 20+，无 npm 依赖，从仓库根目录执行：

~~~sh
node scripts/mipmap_compare/verify_gfx12_revision.cjs --directed-only
node scripts/mipmap_compare/verify_gfx12_revision.cjs --count 1000000 --seed 0x20260922 --out build/gfx12_million_results.json
node scripts/mipmap_compare/verify_gfx12_revision.cjs --seed 0x20260922 --replay 999999 --mip 0
~~~

使用报告和 JSON 即可查看已经完成的结果，无需为查看而重新运行。今后修改算法时先核对源码与接口契约，再更新验证入口的源哈希约束；不得只改哈希跳过审查。大批样本不加入 case/ 或上下文。

原可信清单保持不变：ADDRLIB.md 保存原版并通过基准校验，ADDRLIB_GFX12.md 保存修订版；原文快照也保留。smoke.cjs 和 document.cjs 对应原版，新比较入口读取 GFX12 版。新 _GFX12 用例与原用例分开，独立标注可信状态。

尚未验证完整地址流水线、RTL 实际位宽/时序/综合、Linear 3D、三维资源采用二维 swizzle 以及自定义 pitch/压缩格式。公开 GFX10 的精确 GFX10.2 归属没有新增证据，不据此扩大版本结论。
