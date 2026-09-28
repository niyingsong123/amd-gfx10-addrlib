# ADDRLIB_MAS 配图

配套文档：[ADDRLIB硬件算法.md](../../ADDRLIB硬件算法.md)。

- original/：原稿引用的 18 张配图，按原始字节复制，保留文件名。没有修改图片内容。
- diagrams/：01～06 工程框图保存 Mermaid 源码（.mmd）与 SVG；07～35 内存空间图、纹理示意图和参数流程图保存 SVG、PNG 和配套记录，由 Python 脚本生成。

| 框图 | Mermaid 源码 | SVG |
| ---- | ------------ | --- |
| 顶层地址数据通路 | [01](diagrams/01_address_pipeline.mmd) | [查看](diagrams/01_address_pipeline.svg) |
| mipmap 参数 S0/S1/S2 | [02](diagrams/02_mipmap_stages.mmd) | [查看](diagrams/02_mipmap_stages.svg) |
| tail 原点与块内寻址 | [03](diagrams/03_tail_origin.mmd) | [查看](diagrams/03_tail_origin.svg) |
| y_bias 与坐标轴交换 | [04](diagrams/04_axis_rules.mmd) | [查看](diagrams/04_axis_rules.svg) |
| XOR 和地址合成 | [05](diagrams/05_xor_compose.mmd) | [查看](diagrams/05_xor_compose.svg) |
| 算例的 mip 内存排列 | [06](diagrams/06_example_memory.mmd) | [查看](diagrams/06_example_memory.svg) |

01～06 的 SVG 由 Mermaid 11.12.0 渲染。修改时先编辑 .mmd，再用支持 Mermaid 的工具导出同名 SVG。文档使用相对图片链接，查看 SVG 不需要安装 Mermaid；浏览器、本地 Markdown 编辑器和 GitHub 均可直接打开图片。

框图表达文档的数据依赖，不额外推断流水线周期或 RTL 接口。06 内存排列图对应附录中的 256³、1 BPE、SW_256KB_3D、maxmip=12 算例；块宽仅用于示意，不按容量比例绘制。

## 多 mipmap 内存空间图

[配图、计算口径与复现说明](MIPMAP_MEMORY_LAYOUT.md)：采用 250×180×130、mip0～7 的原版算法推导例，分开表达真实字节地址、Z 分组、坐标边缘补齐与 tail 内的原点。非新增可信用例。

| 图 | SVG | PNG |
| --- | --- | --- |
| mip 次序、Z 平面与宏块对齐 | [07](diagrams/07_mipmap_memory_layout.svg) | [查看](diagrams/07_mipmap_memory_layout.png) |
| tail 的 orig 与各级有效位置 | [08](diagrams/08_mipmap_tail_layout.svg) | [查看](diagrams/08_mipmap_tail_layout.png) |

生成入口：[scripts/render_mipmap_memory.py](../../scripts/render_mipmap_memory.py)。

## 标记图片重绘

ADDRLIB硬件算法.md 中标注的 10 张图片已替换为统一样式的矢量图。原 PNG 保留在 original/；正文公式不变。Standard / Z-order 两图按原文概念定义绘制，不替代具体 sw_mode 位表。

| 图 | SVG | PNG |
| --- | --- | --- |
| 低分辨率纹理放大 | [09](diagrams/09_texture_magnification.svg) | [查看](diagrams/09_texture_magnification.png) |
| 高分辨率纹理缩小 | [10](diagrams/10_texture_minification.svg) | [查看](diagrams/10_texture_minification.png) |
| Standard：宏块、微块与元素排布 | [11](diagrams/11_standard_block_layout.svg) | [查看](diagrams/11_standard_block_layout.png) |
| Z-order：宏块内元素级 Morton 排布 | [12](diagrams/12_zorder_block_layout.svg) | [查看](diagrams/12_zorder_block_layout.png) |
| 256B 对齐与偏移单位 | [13](diagrams/13_macro_256b_alignment.svg) | [查看](diagrams/13_macro_256b_alignment.png) |
| tail 容量计算 | [14](diagrams/14_tail_capacity.svg) | [查看](diagrams/14_tail_capacity.png) |
| tail 层级数量检查 | [15](diagrams/15_tail_count_check.svg) | [查看](diagrams/15_tail_count_check.png) |
| 各 mip 的对齐块数 | [16](diagrams/16_per_mip_blocks.svg) | [查看](diagrams/16_per_mip_blocks.png) |
| tail 尺寸检查 | [17](diagrams/17_tail_size_check.svg) | [查看](diagrams/17_tail_size_check.png) |
| 首个 tail mip 与块贡献 | [18](diagrams/18_tail_id_and_size.svg) | [查看](diagrams/18_tail_id_and_size.png) |

绘图入口：[scripts/redraw_mas_marked_diagrams.py](../../scripts/redraw_mas_marked_diagrams.py)，复用 render_mipmap_memory.py 的字体与绘图组件。

仅生成图片时运行 `python scripts/redraw_mas_marked_diagrams.py`；`--apply` 仅用于替换已检查的对应标记引用。[替换记录](diagrams/mas_redraw_manifest.json) 保存旧图哈希与新图映射。

## 原图三维 mip 链的扩展

在原三维体块递减图的基础上增加 Z 平面、宏块对齐、tail 原点和真实地址次序；相邻标记的二维 mip 图同时统一样式。

| 图 | SVG | PNG |
| --- | --- | --- |
| 三维 mip 与内存顺序综合图 | [19](diagrams/19_mipmap_volume_memory.svg) | [查看](diagrams/19_mipmap_volume_memory.png) |
| 二维 mip 递减图 | [20](diagrams/20_mipmap_2d_chain.svg) | [查看](diagrams/20_mipmap_2d_chain.png) |

[计算口径](MIPMAP_MEMORY_LAYOUT.md) · [绘图脚本](../../scripts/render_mipmap_volume_memory.py) · [替换记录](diagrams/mipmap_volume_replacement.json)。二维图单独采用 256×256 示例，仅表达逻辑 mip 尺寸。

## 接口、采样与参数图

| 图 | SVG | PNG |
| --- | --- | --- |
| AddrLib 输入与输出 | [21](diagrams/21_addrlib_interface.svg) | [查看](diagrams/21_addrlib_interface.png) |
| 纹理采样密度与邻点复用 | [22](diagrams/22_texture_sample_reuse.svg) | [查看](diagrams/22_texture_sample_reuse.png) |
| mipmap tail 打包与地址次序 | [23](diagrams/23_mipmap_tail_packing.svg) | [查看](diagrams/23_mipmap_tail_packing.png) |
| swizzle 模式解码 | [24](diagrams/24_swizzle_mode_decode.svg) | [查看](diagrams/24_swizzle_mode_decode.png) |
| 宏块大小与掩码 | [25](diagrams/25_macro_block_size.svg) | [查看](diagrams/25_macro_block_size.png) |
| 宏块宽、高、深 | [26](diagrams/26_macro_block_dimensions.svg) | [查看](diagrams/26_macro_block_dimensions.png) |

绘图入口：[scripts/redraw_mas_remaining_diagrams.py](../../scripts/redraw_mas_remaining_diagrams.py)。运行不带参数时仅生成图片；`--apply` 仅适用于六个对应标记尚未替换的文档。[替换记录](diagrams/mas_remaining_manifest.json) 保存文档前后哈希及原图片哈希；[计算记录](diagrams/mas_remaining_data.json) 保存源哈希、输入和验证范围。

21、24～26 依据 ADDRLIB.md 的接口与参数公式绘制；22 是四次双线性采样的邻点计数示例，不直接推断缓存命中率。23 独立使用 256×256、SW_4KB_2D、1 BPE / 1X、mip0～8：mip3 开始进入 tail，整链 22 个 4 KiB 块，已检查 1,365 个 tail 有效 texel 的地址互不重叠。这些是说明性配图，不新增可信 case，也不扩展算法验证范围。

图内仅呈现可独立理解的技术内容；来源、假设、验证范围及修订记录放在本说明或配套数据中。

## 统一二维主例与拍次图

| 图 | SVG | PNG |
| --- | --- | --- |
| 从请求到字节地址 | [27](diagrams/27_teaching_address_overview.svg) | [查看](diagrams/27_teaching_address_overview.png) |
| mip1 宏块坐标与边缘对齐 | [28](diagrams/28_teaching_macro_coordinates.svg) | [查看](diagrams/28_teaching_macro_coordinates.png) |
| mip4 的 tail 原点与地址 | [29](diagrams/29_teaching_tail_access.svg) | [查看](diagrams/29_teaching_tail_access.png) |
| S0～S8 的计算分工 | [30](diagrams/30_teaching_stages.svg) | [查看](diagrams/30_teaching_stages.png) |

生成入口：[render_mas_teaching.py](../../scripts/render_mas_teaching.py)。先运行 `node scripts/verify_mas_examples.cjs` 生成数值记录，再运行 `python scripts/render_mas_teaching.py`。图内仅保留技术说明，源哈希、单位/位宽约定与验证范围见 [重写记录](../../docs/ADDRLIB_MAS_REWRITE.md)。02 仅描述原先 S0/S1/S2 的局部概览；当前正文使用 30 对应完整拍次。

## 当前六章讲解稿配图

当前正文使用 09、10、11、12、19、21、22、30、31、32、33、34、35，共十三张。2.2 先用35解释包含关系，再用11/12对比排序粒度，最后用32说明实际三维位表。09/10 表达放大与缩小采样，21/22 说明接口和邻点复用；19/31/32/33 使用同一三维参数 250×180×1537、SW_256KB_3D、1 BPE、单采样、mip0～10。30 展示 S0～S8 分工，34 展开 Tiled 高低位、XOR 和地址合成。图中不显示来源、文件路径或修订说明。

| 图 | SVG | PNG |
| --- | --- | --- |
| 三维 tail 访问与地址 | [31](diagrams/31_teaching_3d_tail_access.svg) | [查看](diagrams/31_teaching_3d_tail_access.png) |
| 宏块、微块与元素的地址位层次 | [32](diagrams/32_macro_micro_swizzle.svg) | [查看](diagrams/32_macro_micro_swizzle.png) |
| 同一 Z 分组内的 tail 打包 | [33](diagrams/33_tail_packing_3d.svg) | [查看](diagrams/33_tail_packing_3d.png) |
| 块内高低位、XOR 与地址合成 | [34](diagrams/34_address_compose.svg) | [查看](diagrams/34_address_compose.png) |
| 纹理、宏块、微块与元素的包含关系 | [35](diagrams/35_block_hierarchy.svg) | [查看](diagrams/35_block_hierarchy.png) |

统一入口为 [render_mas_3d_walkthrough.py](../../scripts/render_mas_3d_walkthrough.py)，数值记录由 `node scripts/verify_mas_3d_walkthrough.cjs` 生成；仅补图使用 [render_mas_supplement.py](../../scripts/render_mas_supplement.py)。主数据和补图检查分别见 [三维复算](../../docs/ADDRLIB_MAS_3D_WALKTHROUGH_CHECK.json)、[补图核对](../../docs/ADDRLIB_MAS_SUPPLEMENT_CHECK.json)，源版本、单位和位宽假设保存在其中。

32 的微块编号及微块内字节编号直接按当前位表生成，不复用旧 Standard / Z-order 图的抽象编号。33 的容量比较只针对 zb=0，不代表整条三维 tail 仅占一个宏块。34 保留掩码、位宽和 OR / 加法的区别，Linear 的低位候选另作说明。21/22 保留接口与采样构图，邻点数不直接当作缓存命中率。

旧版 19 参数为 250×180×130，图片随旧稿备份；上方旧生成记录仅作历史导航。当前 19 不使用旧的 mipmap_volume_data.json，23/27～29 均不嵌入当前正文。备份及本轮检查范围见 [六章稿记录](../../docs/ADDRLIB_MAS_SIX_CHAPTER_REWRITE.md)。

11/12/35 的独立生成入口为 [render_mas_block_concepts.py](../../scripts/render_mas_block_concepts.py)，已纳入统一生成入口。11/12 表达两种明确的二维概念排布，35 仅表达包含关系；[编号检查](../../docs/ADDRLIB_MAS_BLOCK_CONCEPTS_CHECK.json) 记录示意参数、局部编号及适用范围。
