# 项目上下文

## 当前状态

项目用于研究 AddrLib 地址计算。ADDRLIB.md 为主文档，case/ 保存用例；具体可信文件及字节基准见 TRUSTED_BASELINE.json。

mipmap_param_calc_core_gc 与公开 GFX10/GFX12 的云端小规模比较已完成，用户接受云端结果并要求不复跑；百万组尚未启动。本地主分支的 scripts/mipmap_compare/ 仍是迁移时的模型草稿，未合入云端改动，不能代表已接受的云端测试版本。任务入口：[云端比较任务](https://chatgpt.com/codex/tasks/task_e_6ab3d09d7da8832889f0370c4333c5e4)；原测试范围见 CLOUD_HANDOFF.md。

文件哈希一致仅证明字节未变，不证明算法正确；不同用例的源哈希差异不能单凭此判断用例错误。未做 RTL 仿真。

## 目录与使用范围

- ADDRLIB.md、case/：日常研究依据，用例导航见 case/README.md。
- ADDRLIB_MAS.md：按原稿格式补全的讲解稿，不属于可信基准；配图及 Mermaid 源码在 assets/addrlib_mas/。原稿保存于提交 669bb67，可用于逐项比较。
- docs/：当前上下文、可信清单和工作记录。
- scripts/：维护校验脚本、开发中的算法对比工具及固定版本参考源码。
- backup/：历史备份，默认不读取、不作为依据、不主动复核。

新增 case 按已有最大编号加 1，命名和协作要求见根目录 AGENTS.md。

Git 目标仓库为 https://github.com/niyingsong123/amd-gfx10-addrlib，主分支 main。云端可用 node scripts/verify_trusted_baseline.cjs 校验字节，node scripts/mipmap_compare/smoke.cjs 做迁移基本检查。详细历史由 Git 保存。
