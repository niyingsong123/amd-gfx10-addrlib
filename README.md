# AddrLib 地址计算项目

以 [ADDRLIB.md](ADDRLIB.md) 为主文档，[case/](case/README.md) 集中保存逐步计算用例。历史分析仅作备份，默认不参与后续工作。

## 项目结构

```text
ADDRLIB.md                  主文档
case/                       三个逐步计算用例及状态索引
docs/
  PROJECT_CONTEXT.md        当前上下文与决定
  TRUSTED_BASELINE.json      已确认文件的字节基准
  WORK_LOG.md               工作记录
scripts/
  verify_trusted_baseline.ps1
backup/                     历史资料，仅备份，默认不读
AGENTS.md                   后续会话协作规则
```

## 阅读顺序

1. [项目上下文](docs/PROJECT_CONTEXT.md)。
2. [主文档](ADDRLIB.md)及 [用例索引](case/README.md) 中与当前任务相关的用例。
3. 需要了解过往操作时，再读 [工作记录](docs/WORK_LOG.md)。

用例源哈希可能因不同对话、不同源文件快照而不同；哈希不一致本身不能证明用例错误。用例原文和原始哈希均保留。

## Git 与校验

本地 main 分支已建立，尚未配置远程。首次提交 `405c58b` 保存原始目录，`165afe0` 建立初版上下文。后续目录调整单独提交。

```powershell
git status
git log --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_trusted_baseline.ps1
```

校验只检查已确认文件的字节是否变化，不替代算法验证。执行策略参数仅对该次进程有效。研究正文禁用 Git 换行转换。

备份仍纳入 Git 以保留历史，但不作为当前依据，也不设默认复核计划。仅在用户明确要求或当前任务确需追溯时按需访问。
