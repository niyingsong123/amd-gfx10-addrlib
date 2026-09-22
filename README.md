# AddrLib 地址计算项目

以 [ADDRLIB.md](ADDRLIB.md) 为主文档，[case/](case/README.md) 保存计算用例。历史分析归入 backup/，仅作备份，默认不参与后续工作。

## 项目结构

```text
ADDRLIB.md                  主文档
case/                       计算用例及索引
docs/
  PROJECT_CONTEXT.md        当前上下文
  TRUSTED_BASELINE.json     可信文件字节基准
  WORK_LOG.md               重要成果与验证范围
scripts/
  verify_trusted_baseline.ps1
backup/                     历史备份，默认不读
AGENTS.md                   协作规则
```

从 [项目上下文](docs/PROJECT_CONTEXT.md) 开始，再读取主文档与当前任务相关的用例。

## Git 与校验

本地 main 分支，尚未配置远程；详细变更历史由 Git 保存。

```powershell
git status
git log --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_trusted_baseline.ps1
```

校验检查可信文件的字节是否变化，不替代算法验证。研究正文禁用 Git 换行转换。
