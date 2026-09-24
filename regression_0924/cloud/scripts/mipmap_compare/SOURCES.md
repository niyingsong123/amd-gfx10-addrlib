# 转写依据

AMD PAL 固定提交：[c5e800072a32f68b6ccc4422936d96167c6e0728](https://github.com/GPUOpen-Drivers/pal/tree/c5e800072a32f68b6ccc4422936d96167c6e0728/src/core/imported/addrlib)。下列路径相对于 upstream/，行号依据原始文件。文档模型依据根目录 ADDRLIB.md 第 43～569 行。

| 阶段 | 公开 GFX10 | GFX12 非 shared 分支 |
|---|---|---|
| 模式及合法性 | src/gfx10/gfx10addrlib.cpp:60、2430～2663；对应 .h:137～166 | src/gfx12/gfx12addrlib.cpp:2250～2540 |
| 二维块尺寸 | src/core/addrlib2.cpp:1680 | src/gfx12/gfx12addrlib.cpp:2097～2181 |
| 三维块尺寸 | src/core/addrlib2.cpp:48、1758 | src/gfx12/gfx12addrlib.cpp:2097～2181 |
| tail 容量 | src/gfx10/gfx10addrlib.cpp:2079 | src/gfx12/gfx12addrlib.cpp:694 |
| 各级尺寸 | src/gfx10/gfx10addrlib.h:384 | src/gfx12/gfx12addrlib.h:247 |
| tail 阈值与判定 | src/core/addrlib2.cpp:1794；src/gfx10/gfx10addrlib.h:546 | src/gfx12/gfx12addrlib.cpp:2193；对应 .h:77 |
| pitch、slice、宏块偏移 | src/gfx10/gfx10addrlib.cpp:3714～4015、5020～5109 | src/gfx12/gfx12addrlib.cpp:410～614 |
| tail 内 pitch | src/gfx10/gfx10addrlib.cpp:3932～3995 | src/gfx12/gfx12addrlib.cpp:318～400、1810 |
| Linear 末端裁剪 | 无对应分支 | src/core/addrlib3.cpp:1007；src/gfx12/gfx12addrlib.cpp:489 |
| mip 数量上限 | src/core/addrlib2.h:273 | src/gfx12/gfx12addrlib.h:169 |
| API 单位与原始字段 | inc/addrinterface.h | inc/addrinterface.h |

参考函数不导入文档模型。compare.cjs 才做单位归一及派生字段；接口未提供的量必须称为推导值。代码位置是复核入口，不代表转写已经验证。
