# 计算用例

当前主文档：[ADDRLIB.md](../ADDRLIB.md)；[GFX12 修订与验证说明](../docs/GFX12_ALGORITHM_REVISION.md)。

## 原始用例

原文件保持原样，以各自记录的源版本和哈希为准。case0～case2 已获用户确认，见 [可信清单](../docs/TRUSTED_BASELINE.json)；case3～case4 是修订前差异的手工推导，尚未加入可信基准。它们不是当前修订稿的输出预期。

- [case0](case0_mip4_xyz_5_6_3.md)
- [case1](case1_mip0_xyz_69_134_195.md)
- [case2](case2_mip6_xyz_1_1_17.md)
- [case3](case3_mip0_xyz_0_0_0.md)：修订前 Linear slice 差异。
- [case4](case4_mip1_xyz_0_0_0.md)：修订前 tail pitch 差异及 next-in-tail 下标说明。

本轮修改前 ADDRLIB.md 的原始字节另见 [历史快照](../docs/baselines/ADDRLIB_pre_gfx12_20260924.md)，可结合各用例源哈希追溯。

## GFX12 修订版用例

以下文件按新公式独立保存，包含本模块完整输入、步骤、九个输出及 GFX12 对照。已做定向功能复算，尚未独立确认为可信基准；没有重新计算完整 texel 地址。

- [case0_GFX12](case0_mip4_xyz_5_6_3_GFX12.md)：mip4 的 pitch 64→32。
- [case1_GFX12](case1_mip0_xyz_69_134_195_GFX12.md)：九个输出保持一致，单独记录新公式版本。
- [case2_GFX12](case2_mip6_xyz_1_1_17_GFX12.md)：mip6 的 pitch 32→4。
- [case3_GFX12](case3_mip0_xyz_0_0_0_GFX12.md)：Linear slice 512→256。
- [case4_GFX12](case4_mip1_xyz_0_0_0_GFX12.md)：tail pitch 64→32。

## 命名

全新输入按已有最大 case 编号加 1，基础格式见 [协作约定](../AGENTS.md)。同一 case 的 GFX12 修订对照沿用编号、mip 和坐标，在扩展名前加 _GFX12：case{num}_mip{level}_xyz_{x}_{y}_{z}_GFX12.md，不另占新编号。更新此索引，独立确认可信后再加入基准清单。
