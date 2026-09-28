# ADDRLIB_MAS 重写记录

讲解稿改为直接阅读的 Markdown：先解释布局和一次地址访问，再对应 S0～S8。主例固定为 256×256、1 BPE、单采样、SW_4KB_2D、mip0～8；三维图和详细公式后置，正文不放提纲、来源引用或修订记录。

## 文件与备份

- 当前正文：[ADDRLIB_MAS.md](../ADDRLIB_MAS.md)。
- 重写前原始字节备份：[backup/ADDRLIB_MAS_before_markdown_rewrite_20260928_71c10f7c5164.md](../backup/ADDRLIB_MAS_before_markdown_rewrite_20260928_71c10f7c5164.md)。
- 备份 SHA-256：`71c10f7c5164b093a77f25676ca05f3c9fad95bcba2450863fc0d4e4170d0e18`。
- 新版 SHA-256：`a154d3adbaa5cdf9c7645e9efa53f878db7d4521fb00b7b1df0c3be78769f650`。
- 本次读取的 ADDRLIB.md SHA-256：`bf72a3e1d5088e1e2c9cdf8f0ad5f207179dc752730ecd4f1371566138d5687a`；写入前后保持不变。
- 原可信清单未改。ADDRLIB.md 因用户新增 stage 注释，与旧字节基准不同；去除 stage 标记及空白后仍与基准快照一致。

## 内容口径

- 用 4 KiB、1 BPE 统一主例的图文参数，区分逻辑尺寸、pitch、块数、256 B 编码和字节地址。
- 将原来容易混淆的 bpp/BPE、sw_mode/sw_type、宏块间与宏块内排列分别解释；不修改 ADDRLIB.md 的算法内容。
- 保留 8 种模式映射、15 行三维尺寸表和 100 行 swizzle 位表，位表逐项与 ADDRLIB.md 核对一致。
- 拍次以独立段标记和单变量覆盖解释；S2→S3 作为分界。S4 的块索引中间量与 S7 的 blk_index 输出分开列出；不推定未标出的延迟寄存器或握手。
- 沿用 ADDRLIB.md 的计算规则，未将 ADDRLIB_GFX12.md 的另一套修订公式混入讲解稿。

## 数值与图形验证

复算入口：`node scripts/verify_mas_examples.cjs`；[机器可读结果](ADDRLIB_MAS_REWRITE_CHECK.json)。

| 检查 | 结果 |
| --- | --- |
| 普通 mip1，(69,70,0) | `0x30005039` |
| tail mip4，(5,6,0) | `0x30000639` |
| 整条二维链 | 22 块，90112 B；87381 个有效元素地址互不重叠，均在分配范围内 |
| 三维 mip0，(69,134,195) | `0x31440175` |
| 三维 mip4，(5,6,3) | `0x30008175` |
| 原点重复叠加检查 | tail 的 0x639 已含 orig 作用，不能再加原点编码 0x600 |

大整数地址与乘法使用 BigInt；reverse 以 7 位补码解释，原点编码 20 位、X/Y 原点 10 位；字节地址 48 位、256B 基址 40 位、低基址字段 12 位，所选基址低字段为 0。未声明的中间宽度不额外截断。

新增 27～30 四张 SVG/PNG 配图，生成入口为 `python scripts/render_mas_teaching.py`；已检查标签、网格、箭头和版面。复用配图均保留，备份文档中的原图片引用可由项目 assets 目录对应查阅。

本次是限定算例的功能复算和文档检查，没有运行大规模随机比较、编译上游 C++、RTL 仿真或综合时序分析。来源、验证范围和备份记录只保存在此文件及配套数据，不插入讲解正文。

最终基准检查：三个可信 case 均通过；ADDRLIB.md 仅报告此前用户 stage 注释引起的字节变化。Git 差异检查仅提示用户已有 `//s7 stage ` 行末空格，保留该源文件原样；讲解稿及本轮管理文件没有新增空白错误。
