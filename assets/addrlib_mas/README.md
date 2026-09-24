# ADDRLIB_MAS 配图

配套文档：[ADDRLIB_MAS.md](../../ADDRLIB_MAS.md)。

- original/：原稿引用的 18 张配图，按原始字节复制，保留文件名。没有修改图片内容。
- diagrams/：本次新增的 6 张工程框图。每张同时保存可编辑的 Mermaid 源码（.mmd）与渲染结果（.svg）。

| 框图 | Mermaid 源码 | SVG |
| ---- | ------------ | --- |
| 顶层地址数据通路 | [01](diagrams/01_address_pipeline.mmd) | [查看](diagrams/01_address_pipeline.svg) |
| mipmap 参数 S0/S1/S2 | [02](diagrams/02_mipmap_stages.mmd) | [查看](diagrams/02_mipmap_stages.svg) |
| tail 原点与块内寻址 | [03](diagrams/03_tail_origin.mmd) | [查看](diagrams/03_tail_origin.svg) |
| y_bias 与坐标轴交换 | [04](diagrams/04_axis_rules.mmd) | [查看](diagrams/04_axis_rules.svg) |
| XOR 和地址合成 | [05](diagrams/05_xor_compose.mmd) | [查看](diagrams/05_xor_compose.svg) |
| 算例的 mip 内存排列 | [06](diagrams/06_example_memory.mmd) | [查看](diagrams/06_example_memory.svg) |

SVG 由 Mermaid 11.12.0 渲染。修改时先编辑 .mmd，再用支持 Mermaid 的工具导出同名 SVG。文档使用相对图片链接，查看 SVG 不需要安装 Mermaid；浏览器、本地 Markdown 编辑器和 GitHub 均可直接打开图片。

框图表达文档的数据依赖，不额外推断流水线周期或 RTL 接口。内存排列图对应正文的 256³、1 BPE、SW_256KB_3D、maxmip=12 算例；块宽仅用于示意，不按容量比例绘制。
