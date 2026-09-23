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
```

`smoke.cjs` 只检查可信文件及参考源哈希、三个文档回归值、生成器组合数和模块可加载性；随机比较由
`run.cjs` 执行。后者支持 `--seed`、`--config-count`、`--config-number` 和 `--mip`，可按配置编号与 mip
重放。Node.js 20+，仅用内置模块。

upstream/ 是 AMD PAL 固定提交的原始文件，出处和字节基准见 provenance.json。保留其版权和许可声明。位置索引见 [SOURCES.md](SOURCES.md)。
