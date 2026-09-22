# 项目协作约定

## 默认上下文

先读 docs/PROJECT_CONTEXT.md，再读 ADDRLIB.md 和 case/README.md 中与任务相关的用例。需要历史操作记录时读 docs/WORK_LOG.md。

不要默认递归读取 backup/，也不要把备份加入常规搜索、检索或算法依据。搜索时优先指定 ADDRLIB.md、case/、docs/、scripts/；全仓库搜索使用排除 backup/** 的规则。

## 可信边界

- 当前确认状态以 case/README.md、docs/PROJECT_CONTEXT.md 和 docs/TRUSTED_BASELINE.json 为准。
- 文件放入 case/ 只是分类，不应单凭位置或文件名推断确认状态。
- 用户解释用例源哈希不同可能因为产生于不同对话。保留此解释，不因哈希不同降低用户确认的可信状态，也不把版本追溯设置为默认前置任务。
- 不把用户确认的用例误表述为本轮已重新执行的算法回归。
- backup/ 仅为历史留存，用户认为后续很可能不用。旧文件中的“已修正”“已核对”不构成当前依据；不主动安排逐项审计或恢复归档内容。
- 不擅自修改研究正文、历史哈希或换行符。目录重组保留原文字节；必要的技术修改说明依据与范围，保留 Git 历史，并记录基准变化。不得仅更新哈希来消除失败。
- 新分析记录源文件、配置、输入、单位、位宽假设和实际验证范围；上游规则不自动覆盖本项目基准。

## 完成工作

- 运行 powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_trusted_baseline.ps1。该检查仅验证文件字节。
- 按实际修改验证相关算法；不要将归档脚本当作当前验证入口。
- 检查 git diff 和 git status，不覆盖用户修改。
- 当前状态或决定变化时维护 docs/PROJECT_CONTEXT.md，用例状态变化时维护 case/README.md；实质工作记入 docs/WORK_LOG.md。
- 不再维护默认的历史资料复核队列；原队列已归档，只作历史记录。
