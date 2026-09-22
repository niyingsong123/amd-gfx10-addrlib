# 项目协作约定

## 开始工作

先读 docs/PROJECT_CONTEXT.md，再按任务查阅 docs/REVIEW_QUEUE.md 和 docs/WORK_LOG.md。不必无差别读取所有历史分析。

## 可信边界

- 用户明确确认的文件只有 ADDRLIB.md、analysis/case_mip0_xyz_69_134_195_step_by_step.md、analysis/case_mip6_xyz_1_1_17_step_by_step.md。mip0 重复一次，不能据此把 mip4 加入可信清单。
- 其余既有技术资料，包括 backup、版本审计、GFX12 对照原文和校验脚本，一律待核实。不能因旧文档声称“已修正”“验证通过”就升级信任状态。
- 尊重用户确认的可信状态，同时区分源版本。两个可信用例的源哈希不同，不能默认为对当前主文件完成了回归验证。
- 不擅自重写可信文件、批量格式化或转换换行符。需要修订时说明依据、保留 Git 历史，并记录基准变更；不得只更新哈希来消除校验失败。
- 冲突先记录到问题清单。新分析注明源文件路径与哈希、配置、输入、单位、位宽假设、结果及实际验证范围。
- 不把某一 GFX 代际或上游规则自动覆盖到用户基准；上游比较需注明固定版本及差异证据。

## 完成工作

- 执行 powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_trusted_baseline.ps1，检查可信文件字节是否变化。它不是算法测试。
- 算法变化应按实际需要复算相关用例，不能用历史脚本通过替代端到端验证。
- 检查 git diff 与 git status，避免混入无关文件或覆盖用户改动。备份原稿也受版本管理，不删除原始证据。
- 有实质进展时更新 docs/WORK_LOG.md；当前状态或决定变化时同步更新 docs/PROJECT_CONTEXT.md；问题状态变化时更新 docs/REVIEW_QUEUE.md。
- 上下文记录区分用户确认、当前观察、推测、待核实与已验证，只记录实际执行过的检查。
- 管理类文档的维护不等于其中引用的技术资料已获验证。
