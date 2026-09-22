# 项目上下文

最后更新：2026-09-22。当前阶段：组织主文档与用例，保留历史资料备份；未启动全面算法审计。

## 最新用户决定

- 三个逐步计算用例集中到 case/。
- 原 analysis 中非百分百可信资料移入 backup/，仅作备份。
- backup/ 后续很可能不会用到，因此默认不读取、不作依据、不安排复核。
- 两个此前确认用例的源哈希不同，可能因为在不同对话中产生。这是用户提供的可能解释，不是已证实的完整版本溯源。哈希差异不等于用例错误，不作为阻塞后续工作的条件。

## 主工作区

| 路径 | 用途 |
| --- | --- |
| ADDRLIB.md | 用户确认的当前主文档，原文不变 |
| case/ | mip0、mip4、mip6 三个逐步用例；确认状态见 case/README.md |
| docs/ | 当前上下文、已确认文件哈希清单、工作记录 |
| scripts/ | 当前项目维护与基准校验 |
| backup/ | 历史归档；常规工作不读 |

用户现已明确确认 mip4 也可信。当前可信基准共 4 个文件：ADDRLIB.md，以及 case0（mip4）、case1（mip0）、case2（mip6）。用例均已纳入字节基准清单；确认依据为用户指示，本轮未复算算法。

原用例中的计算结果、来源哈希、旧路径均保持原样；当前路径从 case/README.md 进入。没有重新执行用例计算或验证 RTL。

## 用例编号决定

文件名采用 case{num}_mip{level}_xyz_{x}_{y}_{z}.md，不保留 step_by_step。用户指定 mip4 → case0、mip0 → case1、mip6 → case2；现有编号为 case0、case1、case2，后续从 case3 递增。编号不重排、不复用，具体规则与当前索引集中在 case/README.md，协作执行要求写入 AGENTS.md。

## 历史资料策略

旧 analysis、upstream、verilog 目录已整体归档，不在根目录保留空规划目录。旧源文件备份集中在 backup/source_snapshots/。旧复核队列位于 backup/context/，不再作为活动任务列表。

归档可能含过时结论、失效链接及旧目录描述，均按历史材料解释，不修订为当前规范。仅当用户明确要求或当前任务确需溯源时按需取用，取用前核实适用性。

不再把哈希版本映射、历史代际审计或备份复核作为默认下一步。后续围绕用户指定的主文档与用例任务继续。

## Git 与维护

工作目录 D:/project/no_preject/addrlib，本地 main，无远程。原始快照提交 405c58b441e970b1043ba2c118bf7230b130e79f；初版上下文提交 165afe0。工具生成的提交使用命令级 Codex <codex@localhost> 身份，不修改全局配置。

docs/TRUSTED_BASELINE.json 记录已确认文件的路径、长度和 SHA-256。迁移与重命名只更新路径，既有哈希不变；mip4 在用户明确确认后新增基准记录。scripts/verify_trusted_baseline.ps1 只验证字节完整性。常规协作遵循 AGENTS.md，实际工作记录在 WORK_LOG.md。
