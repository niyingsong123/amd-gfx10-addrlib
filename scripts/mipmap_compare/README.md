# mipmap 比较工具（开发中）

当前包含文档/GFX10/GFX12 的独立转写草稿、输入生成器和比较辅助函数。统一批量入口、逐式复核和随机测试报告尚未完成；不能引用为“算法已匹配”的证据。

云端续做范围和用户最新要求见 [CLOUD_HANDOFF.md](../../docs/CLOUD_HANDOFF.md)。**先讨论小规模结果，再决定百万组。**

迁移后可运行基本检查：

```sh
node scripts/mipmap_compare/smoke.cjs
```

这只检查可信文件及参考源哈希、三个文档回归值、生成器组合数和模块可加载性，不运行随机对比，不验证参考转写正确性。Node.js 20+，仅用内置库。

upstream/ 是 AMD PAL 固定提交的原始文件，出处和字节基准见 provenance.json。保留其版权和许可声明。位置索引见 [SOURCES.md](SOURCES.md)。
