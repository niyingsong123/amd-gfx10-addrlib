# AddrLib 研究项目

本项目保存地址计算说明、逐步计算用例及历史研究资料。**以用户明确确认的 3 个文件为可信基准，其他既有技术资料均待核实。** 入库不代表技术结论已验证。

## 阅读入口

1. [项目上下文](docs/PROJECT_CONTEXT.md)：当前状态、信任边界、版本关系。
2. [协作约定](AGENTS.md)：供后续会话读取和遵循。
3. [待核实清单](docs/REVIEW_QUEUE.md)：历史资料的复核队列。
4. [工作记录](docs/WORK_LOG.md)：实际完成的工作与验证。

## 用户确认的可信文件

| 文件 | 用途 |
| --- | --- |
| [ADDRLIB.md](ADDRLIB.md) | 当前地址计算基准 |
| [mip0 / (69,134,195)](analysis/case_mip0_xyz_69_134_195_step_by_step.md) | 用户确认的逐步计算用例 |
| [mip6 / (1,1,17)](analysis/case_mip6_xyz_1_1_17_step_by_step.md) | 用户确认的逐步计算用例 |

用户消息中 mip0 重复一次，按同一文件处理；mip4 未获同样确认。三个文件保留原始字节，SHA-256 见 [基准清单](docs/TRUSTED_BASELINE.json)。两个用例引用不同历史源版本，不能直接声称都已通过当前主文档的回归验证。

## 目录

| 路径 | 内容与状态 |
| --- | --- |
| analysis/ | 两个可信用例及其他待核实资料，见 [分析索引](analysis/README.md) |
| backup/ | 历史备份，纳入 Git，但不自动获得可信地位 |
| upstream/ | 历史来源说明；没有完整上游源码快照，来源声明待核实 |
| verilog/ | 规划说明；没有完整 RTL 实现 |
| docs/ | 项目上下文、可信清单、问题队列和工作记录 |
| scripts/ | 项目维护脚本 |

## 本地版本管理

已建立本地 main 分支，尚未配置远程仓库。原始目录完整保存在首次提交 `405c58b441e970b1043ba2c118bf7230b130e79f`，后续上下文建设单独提交。

```powershell
git status
git log --oneline
git diff
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_trusted_baseline.ps1
```

基准校验只检查文件字节是否变化，不证明算法正确。历史脚本 analysis/verify_version_audit.ps1 自身也待核实，不能以它通过作为全部文件正确的证据。

新增结论需注明源文件版本、输入、假设和验证范围；完成工作后同步维护项目上下文与工作记录。
