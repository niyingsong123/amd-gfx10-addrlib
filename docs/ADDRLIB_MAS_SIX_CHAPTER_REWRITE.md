# 六章讲解稿重写记录

## 交付与备份

- 当前正文：ADDRLIB_MAS.md；六章、每章 3～4 小节、四个附录。
- 旧稿与其使用的八组 SVG/PNG：[backup/ADDRLIB_MAS_before_six_chapters_20260928_a154d3adbaa5/ADDRLIB_MAS.md](../backup/ADDRLIB_MAS_before_six_chapters_20260928_a154d3adbaa5/ADDRLIB_MAS.md)。保留相对 assets 路径，备份稿可独立显示原有配图。
- 备份正文 SHA-256：`a154d3adbaa5cdf9c7645e9efa53f878db7d4521fb00b7b1df0c3be78769f650`；17 个文档/图片文件的哈希见备份目录 manifest.json。
- 当前正文 SHA-256：`c8775654257fc81e69e50c1004c3fe4019238b31c52dc6b307825925d39a4251`。
- 算法源 ADDRLIB.md SHA-256：`bf72a3e1d5088e1e2c9cdf8f0ad5f207179dc752730ecd4f1371566138d5687a`，本轮未改动。

## 内容与技术口径

放大与缩小采样均有说明。第一至四章建立概念、布局和拍次分工，第五章集中完成一个三维 tail 访问，第六章提供通用公式；完整模式/维度/位映射和字段约定置于附录。正文、图片可见文字及图片描述不包含来源、引用关系或文件路径。

主例为 W250/H180/D1537、SW_256KB_3D、1 BPE、单采样、mip0～10；访问 mip4 的 (5,6,69)，基址 0x30000000，seed=0。tail 从 mip3 开始，orig=(32,0,0)，宏块坐标 (0,0,1)，blk_index=0x480000 B，blk_offset=0x81D5 B，最终地址 0x304881D5。

保持原版布局公式、tail pitch、slice 口径和最新 stage 标记，不混入 ADDRLIB_GFX12.md 的修订。tail 跨多个 Z 分组的画法与当前算法使用宽高/层级数量判定 tail、Z 单独参与索引的行为一致；统一步长图不声明上游精确分配大小。

## 检查与再生成

```text
node scripts/verify_mas_3d_walkthrough.cjs
python scripts/render_mas_3d_walkthrough.py
python scripts/check_mas_document.py
```

- 148,630 个有效 tail 元素地址全部枚举，无重叠；包含多个 Z 分组。
- 354 个普通宏块槽位无交叠，2,784 个有效边界角点通过完整地址链计算；所选 18 位块内映射是各坐标低六位的排列。
- 检查 mip4 的 z=63/64 分组边界；完整链和坐标范围均满足本例约定。
- 100 条 swizzle 位映射和 15 行三维宏块维度与 ADDRLIB.md 逐项相同；整链表与机器结果一致。
- 十三张 SVG 可解析、图片路径有效、没有来源或路径式标注。实际 Markdown 本地渲染无页面水平溢出、无图片加载失败；已显示检查算例页、综合图和 tail 放大图。
- 机器结果：ADDRLIB_MAS_3D_WALKTHROUGH_CHECK.json、ADDRLIB_MAS_DOCUMENT_CHECK.json 和 ADDRLIB_MAS_SUPPLEMENT_CHECK.json。

数值计算使用 BigInt 地址/乘积；reverse 按七位有符号值、原点编码二十位、X/Y 原点十位解释；本例采用四十八位字节地址、四十位基址、十二位低基址字段，低字段为零。未声明中间位宽不额外截断。以上是单一配置的功能和文档检查，没有运行百万随机、上游 C++、RTL、综合或 STA。

可信校验结果：三个原可信 case 通过；ADDRLIB.md 仍因先前用户增加的 stage 标记而与旧字节基准不同，本轮源哈希保持不变，原可信清单未更新。

## 配图与概念补充

补充前的当前稿及五组 SVG/PNG 共 11 个文件已按原字节备份于 [backup/ADDRLIB_MAS_before_visual_supplement_20260928_c3a2602e8bae/ADDRLIB_MAS.md](../backup/ADDRLIB_MAS_before_visual_supplement_20260928_c3a2602e8bae/ADDRLIB_MAS.md)，正文 SHA-256 为 `c3a2602e8baecc9e6ecdf153bffde7502d22e70539f18f5acffb56474e4e9a95`，清单为同目录 manifest.json。备份包括用户最后补充的缓存说明；本次将其绝对判断改为有条件的局部复用说明。

| 位置 | 补充内容 |
| --- | --- |
| 1.1 | 采样邻点复用图；明确 texel 计数不能直接推导 cache miss；限定约三分之一存储量的适用条件 |
| 1.3 | 输入参数与地址输出总览；四环节地址计算表 |
| 2.1 | 当前 mip 的局部坐标不能再次按 mip_level 缩小 |
| 2.2 | 四个子小节依次说明块层次、Standard/Z-order、Morton 递归与位交织、实际三维编号；使用 35、11、12、32 四张图 |
| 3.3 | 同一个 Z 分组内的 tail 打包前后；普通 mip 与 tail 的对照表 |
| 6.4 | 块内高低位、XOR、OR 和最后基址加法的关系 |

保留六章结构、单一完整算例、全部代码块及四个附录；正文和图中继续不写外部来源或文件路径。32/33/34 为新图，21/22 沿用原构图并清理路径式标题；11/12 作为概念排布图用于 2.2；23/05 保留归档。统一绘图入口仍为 `python scripts/render_mas_3d_walkthrough.py`，仅生成补图可运行 `python scripts/render_mas_supplement.py`。

实际核对：1024 个微块编号及 256 个微块内字节偏移分别完整覆盖对应范围；主访问点拆分为微块 129、块内字节 213，合并仍为 0x81D5。zb=0 的 tail 有效数据合计 56,054 B，与既有三维复算一致；图示的 2 MiB 与 256 KB 只比较该分组内八级 tail 分别占块和共享占块。四次双线性采样的邻点访问均为 16 次，两组分别涉及 16 和 9 个不同 texel。

检查 13 张图片均能在本地 Markdown 页面加载，无页面水平溢出；逐图检查了新增五组的布局。原五组配图字节保持不变，全部公式代码块、第五章算例、附录及算法源均保持原样。可信校验仍为三个 case 通过、源文档因既有 stage 标记与历史基准不同；没有更新可信清单。本轮没有重新执行大规模算法回归。

Git 检查：本轮修改的正文及管理文档无新增空白问题；全仓库 diff --check 仍报告 ADDRLIB.md:913 既有 stage 注释的行尾空格，本轮保留其字节。已检查工作区状态及补充前后的正文差异。

## 2.2 的分层讲解

重排前的正文、当时全部配图及待加入的 11/12 共 25 个文件已备份于 [backup/ADDRLIB_MAS_before_section22_structure_29c3e8c1d77e/ADDRLIB_MAS.md](../backup/ADDRLIB_MAS_before_section22_structure_29c3e8c1d77e/ADDRLIB_MAS.md)，原始哈希见同目录 manifest.json。

2.2.1 新增包含关系图35；2.2.2 加入图11/12并解释排序粒度；2.2.3 从 2×2 到 4×4 递归次序，再说明二维位交织和三维扩展；2.2.4 保留图32，说明宏块、微块和元素编号，以及 x=4 映射到微块内字节偏移64的原因。其他节、原有公式代码块和完整算例保持不变。

11/12 延续二维 256×256、1 BPE、4 KB 宏块/256 B 微块的概念参数，统一使用 KB 并清除路径式页眉；不等同于项目的任意具体 sw_mode。实际三维布局继续使用主例及原位表。新增检查数据为 ADDRLIB_MAS_BLOCK_CONCEPTS_CHECK.json；绘图入口 render_mas_block_concepts.py 已接入统一绘图入口。原算法及可信清单未修改。

本次概念图检查：16 个微块编号覆盖 0～15；两种概念排布各覆盖宏块内 4096 个字节位置，无重复；4×4 Morton 表中 (2,1) 的编号为 6。实际三维位表的首行 x=4 对应字节偏移 64，与正文解读相符。13 张配图正常加载，2.2 的图序为35、11、12、32，无页面水平溢出；原有十张图字节不变。
