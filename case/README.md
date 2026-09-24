# 计算用例

主文档：[ADDRLIB.md](../ADDRLIB.md)。

## 已确认的可信用例

case0～case2 已获用户确认，字节基准见 [可信清单](../docs/TRUSTED_BASELINE.json)。

- [case0](case0_mip4_xyz_5_6_3.md)
- [case1](case1_mip0_xyz_69_134_195.md)
- [case2](case2_mip6_xyz_1_1_17.md)

## 待独立确认的推导用例

以下文件为手工公式推导，尚未运行模型、C++ 或 RTL 验证，未加入可信基准：

- [case3](case3_mip0_xyz_0_0_0.md)：Linear 1×2，mip0 的 slice 为文档 512B、GFX12 256B。
- [case4](case4_mip1_xyz_0_0_0.md)：4KB 二维 64×64、三个 mip，mip1 的 pitch 为文档 64、GFX12 32；明确上一 mip 块数与下一 mip tail 判定的下标关系。

新增用例按已有最大编号加 1，命名格式见 [协作约定](../AGENTS.md)。新增后更新此索引，确认可信后再加入基准清单。
