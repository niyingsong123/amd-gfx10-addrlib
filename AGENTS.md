# 项目协作约定

## 阅读范围

先读 docs/PROJECT_CONTEXT.md，再按任务读取 ADDRLIB.md 和 case/ 中的相关用例。backup/ 仅作备份，默认不读取、不搜索、不作为依据；仅在用户要求或确需溯源时按需访问。

## 工作规则

- 可信文件以 docs/TRUSTED_BASELINE.json 为准。新增用例的可信状态需独立确认，不能因放入 case/ 而自动获得。
- 用例文件名采用 case{num}_mip{level}_xyz_{x}_{y}_{z}.md，新增编号按已有最大编号加 1，同步 case/README.md。
- 保留研究正文、源哈希与换行符。技术修改需说明依据和验证范围，不得仅更新基准哈希来掩盖变化。
- 新分析记录源文件、输入、单位、位宽假设和实际验证结果；上游规则不能直接覆盖本项目基准。
- 完成修改后运行 powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_trusted_baseline.ps1，并检查 git diff、git status。哈希校验不能替代算法验证。

## 上下文维护

当前事实与有效决定放入 docs/PROJECT_CONTEXT.md；用例导航放入 case/README.md；重要成果和未解决事项简记于 docs/WORK_LOG.md。

保持简洁，及时删除过时状态。不记录笔误、确认往返、改名过程、重复对应关系或逐次工具操作；详细变更由 Git 保存。不要在多个文件重复展开同一规则。
