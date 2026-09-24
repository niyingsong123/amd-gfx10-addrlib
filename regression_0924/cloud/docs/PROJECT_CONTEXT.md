# 项目上下文

## 当前状态

项目用于研究 AddrLib 地址计算。ADDRLIB.md 为主文档，case/ 保存用例；具体可信文件及字节基准见 TRUSTED_BASELINE.json。

已完成 mipmap_param_calc_core_gc 与公开 GFX10/GFX12 独立模型的小规模比较。统一入口为 `node scripts/mipmap_compare/run.cjs`，结果和限制见 `docs/MIPMAP_COMPARE_SMALL_REPORT.md`；结果否定模块与公开 GFX10 完全匹配，若干宏块阶段则在可比样本中一致。先与用户讨论，再决定是否做百万组，本阶段不得自行扩展。

文件哈希一致仅证明字节未变，不证明算法正确；不同用例的源哈希差异不能单凭此判断用例错误。未做 RTL 仿真。

## 目录与使用范围

- ADDRLIB.md、case/：日常研究依据，用例导航见 case/README.md。
- docs/：当前上下文、可信清单和工作记录。
- scripts/：维护校验脚本、开发中的算法对比工具及固定版本参考源码。
- backup/：历史备份，默认不读取、不作为依据、不主动复核。

新增 case 按已有最大编号加 1，命名和协作要求见根目录 AGENTS.md。

Git 目标仓库为 https://github.com/niyingsong123/amd-gfx10-addrlib，主分支 main。云端可用 node scripts/verify_trusted_baseline.cjs 校验字节，node scripts/mipmap_compare/smoke.cjs 做迁移基本检查。详细历史由 Git 保存。
