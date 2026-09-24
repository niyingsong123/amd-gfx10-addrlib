# AddrLib 地址计算项目

[ADDRLIB.md](ADDRLIB.md) 保存原始算法，[ADDRLIB_GFX12.md](ADDRLIB_GFX12.md) 保存适配 GFX12 的算法，[case/](case/README.md) 保存计算用例。历史分析归入 backup/，仅作备份，默认不参与后续工作。

## 项目结构

```text
ADDRLIB.md                  原始算法（可信基准）
ADDRLIB_GFX12.md            GFX12 修订算法
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

目标仓库：[niyingsong123/amd-gfx10-addrlib](https://github.com/niyingsong123/amd-gfx10-addrlib)。主分支 main；云端算法比较范围见 [续做说明](docs/CLOUD_HANDOFF.md)。

```powershell
git status
git log --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_trusted_baseline.ps1
```

校验检查可信文件的字节是否变化，不替代算法验证。研究正文禁用 Git 换行转换。


云端/Linux 使用 Node.js 20+（无 npm 依赖）：

```sh
node scripts/verify_trusted_baseline.cjs
node scripts/mipmap_compare/verify_gfx12_revision.cjs --directed-only
```

当前 GFX12 修订版已完成百万组功能比较，结果和复现入口见 [修订报告](docs/GFX12_ALGORITHM_REVISION.md)。原可信清单保持不变，ADDRLIB.md 和原可信 case 均匹配基准；旧 smoke 检查原版，新比较入口核对 ADDRLIB_GFX12.md。
