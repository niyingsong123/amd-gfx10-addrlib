# mipmap 比较工具

当前包含文档/GFX10/GFX12 的独立模型、输入生成器、比较辅助函数和统一批量入口。小规模结果及模型边界见
[MIPMAP_COMPARE_SMALL_REPORT.md](../../docs/MIPMAP_COMPARE_SMALL_REPORT.md)，机器可读结果见
[mipmap_compare_small_results.json](../../docs/mipmap_compare_small_results.json)。有限随机测试不能作为数学证明。

云端续做范围和用户最新要求见 [CLOUD_HANDOFF.md](../../docs/CLOUD_HANDOFF.md)。**先讨论小规模结果，再决定百万组。**

运行基本检查和小规模对比：

```sh
node scripts/mipmap_compare/smoke.cjs
node scripts/mipmap_compare/run.cjs --seed 0x20260922 --config-count 10000 \
  --out docs/mipmap_compare_small_results.json
node scripts/mipmap_compare/summary.cjs
```

`smoke.cjs` 只检查可信文件及参考源哈希、三个文档回归值、生成器组合数和模块可加载性；随机比较由
`run.cjs` 执行。后者支持 `--seed`、`--config-count`、`--config-number` 和 `--mip`，可按配置编号与 mip
重放。Node.js 20+，仅用内置模块。

若当前界面不能直接打开云端生成的 Markdown 或 JSON，可执行 `summary.cjs` 在终端直接查看已提交结果的
核心规模、分类、扰动检查和摘要哈希；也可把其他结果 JSON 路径作为第一个参数传入。小规模已提交结果为：

- 10,000 个随机配置加 670 个定向配置，共 36,607 个 mip、658,926 次字段比较；
- 公开 GFX10 按配置分类：2,688 一致、1,169 数值差异、938 表达口径不同、2,665 无等价、3,210 参考拒绝；
- GFX12 按配置分类：8,919 一致、127 数值差异、1,464 表达口径不同、160 参考拒绝；
- 已发现否定“模块与公开 GFX10 完全匹配”的明确反例，未执行百万组。

upstream/ 是 AMD PAL 固定提交的原始文件，出处和字节基准见 provenance.json。保留其版权和许可声明。位置索引见 [SOURCES.md](SOURCES.md)。
