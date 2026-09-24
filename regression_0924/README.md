# 2026-09-24 mipmap 比较资料

本目录整理云端任务 [Conduct mipmap_param_calc_core_gc comparison](https://chatgpt.com/codex/tasks/task_e_6ab3d09d7da8832889f0370c4333c5e4) 的交付文件，并补充面向 GFX12 的差异分析。原结果生成于 2026-09-23，2026-09-24 从云端最新补丁归档；**本次没有复跑模型或随机测试**。

## 阅读顺序

1. [目前的差异与 GFX12 修改建议](GFX12_MATCHING_ANALYSIS.md)。
2. [配置、字段、阶段与模式统计](summary/RESULT_SUMMARY.md)。
3. [代表性差异与缩减输入](summary/REPRESENTATIVE_CASES.md)。
4. [云端原始报告](cloud/docs/MIPMAP_COMPARE_SMALL_REPORT.md)及[完整结果 JSON](cloud/docs/mipmap_compare_small_results.json)。

| 位置 | 内容 |
| --- | --- |
| cloud/docs/ | 云端原始报告、结果 JSON，以及该任务当时的上下文和工作记录 |
| cloud/scripts/mipmap_compare/ | 云端变更的脚本及分析所需的未变更模型、来源索引；原始文件内容保持不变 |
| summary/ | 由已保存 JSON 整理的表格、反例导航和 CSV，不是新增测试结果 |
| provenance/cloud.diff | 从云端下载的完整补丁，包含 9 个变更文件 |
| provenance/manifest.json | 任务信息、归档文件哈希、Git blob、上游固定版本和本次校验范围 |
| provenance/task.json | 指定任务的名称、地址和查询时状态 |

本次共归档一份云端中文报告、一份结果 JSON 和其配套变更。JSON 保存汇总、三个可信用例回归和 12 类限量代表项，并不含 10,670 组配置逐条完整日志。输入摘要不能代替这些未保存的日志。

## 重要边界

- 数据来自独立 JavaScript 算法转写，固定 AMD PAL 提交 `c5e800072a32f68b6ccc4422936d96167c6e0728`，GFX12 为 `ADDR_GFX12_SHARED_BUILD=0` 分支。
- 原文称“公开 GFX10”，没有把它精确归属为 GFX10.2 的证据。
- `cloud/` 是研究归档，里面的上下文不是本项目当前上下文；其脚本不是已经合入主线的版本。
- 归档保留补丁及必要模型，没有复制完整上游目录和运行环境。若以后获准重测，应先恢复相容基提交与补丁、校验源文件，而不是直接运行主线旧草稿。
- 本次只整理和分析，没有修改可信原文、主线算法或用例预期，也没有把表达差异改记为通过。

字节校验、结果计数核对和汇总摘要复核见 [manifest](provenance/manifest.json)。当前工作约定仍以根目录 [AGENTS.md](../AGENTS.md) 为准。
