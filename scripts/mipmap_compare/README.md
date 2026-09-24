# mipmap 算法比较工具

当前 GFX12 修订版入口为 verify_gfx12_revision.cjs；公式、单位、来源和已完成的百万组结果见 [报告](../../docs/GFX12_ALGORITHM_REVISION.md)。这是单 Node.js 进程中的功能计算比较，不是 RTL 仿真或编译 C++ 对比。

Node.js 20+，无 npm 依赖，从仓库根目录运行：

~~~sh
node scripts/mipmap_compare/verify_gfx12_revision.cjs --directed-only
node scripts/mipmap_compare/verify_gfx12_revision.cjs --count 1000000 --seed 0x20260922 --out build/gfx12_million_results.json
node scripts/mipmap_compare/verify_gfx12_revision.cjs --seed 0x20260922 --replay 999999 --mip 0
~~~

--count 只控制随机配置数量；常规运行另外检查 610 组定向输入和 160 组契约探测。--directed-only 不生成随机配置；--replay 使用零起始随机编号，可省略 --mip 输出整条链。拒绝输入单独计数，保存有限原始/换算输出、覆盖与 SHA256，不保存百万条日志。

当前入口复用归档文档模型中的未修改阶段，并实现主文档 GFX12-01/02/03 的等价公式；参考端为独立的归档 GFX12 模型，不导入文档公式。运行前核对文档、模型与固定 C++ 文件的哈希。该运行版本约束不改写 TRUSTED_BASELINE.json。

本目录原 document.cjs、gfx10.cjs、gfx12.cjs、compare.cjs 为原任务草稿；旧 smoke.cjs 针对修订前文档和原可信清单，不能用于验证当前算法。因为主文档已授权修改，旧 smoke 会先报告原基准差异。

upstream/ 是 AMD PAL 固定提交的原始文件，出处和字节基准见 provenance.json，源码位置见 [SOURCES.md](SOURCES.md)。保留上游版权和许可。旧云端结果见 [归档](../../regression_0924/README.md)；当前上下文见 [PROJECT_CONTEXT.md](../../docs/PROJECT_CONTEXT.md)。
