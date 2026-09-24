# 代表项与缩减输入

以下 12 项直接来自云端结果，每项对应一个被保留的差异类别，不表示 12 个互不重复的输入。未重新缩减或执行模型。

| 序号 | 类别键 | 原编号/mip | 展示输入 | 模式 | W×H×D | BPE | samples | mip/maxmip | 文档→参考（换算口径） |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | gfx10:numerical_difference:l2_ms | r0/0 | 缩减 | SW_LINEAR | 1×1×1 | 1 | 1 | 0/0 | pitch: 128 → 256；l2_ms: 7 → 8；l2_blk_w: 7 → 8 |
| 2 | gfx10:numerical_difference:l2_blk_w | r0/0 | 缩减 | SW_LINEAR | 1×1×1 | 1 | 1 | 0/0 | pitch: 128 → 256；l2_ms: 7 → 8；l2_blk_w: 7 → 8 |
| 3 | gfx10:numerical_difference:pitch | r1/2 | 缩减 | SW_LINEAR | 1×1×1 | 1 | 1 | 0/0 | pitch: 128 → 256；l2_ms: 7 → 8；l2_blk_w: 7 → 8 |
| 4 | gfx12:numerical_difference:slice | r2/0 | 缩减 | SW_LINEAR | 1×2×1 | 1 | 1 | 0/0 | slice: 512 → 256 |
| 5 | gfx10:reference_rejected:reference_rejected | r6/0 | 原始 | SW_256B_2D | 256×1131×1 | 1 | 2 | 0/0 | 256B/4KB display swizzle does not support MSAA |
| 6 | gfx10:representation_difference:pitch | r29/6 | 原始 | SW_4KB_2D | 1286×256×225 | 2 | 1 | 6/10 | pitch: 64 → 32 |
| 7 | gfx12:representation_difference:pitch | r29/6 | 原始 | SW_4KB_2D | 1286×256×225 | 2 | 1 | 6/10 | pitch: 64 → 32 |
| 8 | gfx10:numerical_difference:l2_blk_h | r46/0 | 缩减 | SW_64KB_2D | 1×1×1 | 1 | 2 | 0/0 | pitch: 256 → 128；l2_blk_w: 8 → 7；l2_blk_h: 7 → 8；l2_blk_w_slice: 8 → 7 |
| 9 | gfx10:numerical_difference:l2_blk_w_slice | r46/0 | 缩减 | SW_64KB_2D | 1×1×1 | 1 | 2 | 0/0 | pitch: 256 → 128；l2_blk_w: 8 → 7；l2_blk_h: 7 → 8；l2_blk_w_slice: 8 → 7 |
| 10 | gfx10:numerical_difference:slice | r48/0 | 缩减 | SW_64KB_2D | 1×126×1 | 1 | 8 | 0/0 | pitch: 128 → 64；slice: 131072 → 65536；l2_blk_w: 7 → 6；l2_blk_h: 6 → 7；l2_blk_w_slice: 7 → 6 |
| 11 | gfx10:no_equivalent:no_equivalent | r65/0 | 原始 | SW_256KB_2D | 8191×10678×220 | 1 | 1 | 0/10 | Fixed 256KB is not GFX10 VAR |
| 12 | gfx12:reference_rejected:reference_rejected | d3/0 | 原始 | SW_LINEAR | 65536×65536×1 | 1 | 1 | 0/16 | V3 MaxMipLevels=16; mip index 16 outside contract |


slice 换算后为字节；mip_offset_b 比较列也为乘 256 后的字节数；pitch 为元素。完整原始值、换算值和输入已保存在 [representatives.json](representatives.json) 与[原 JSON](../cloud/docs/mipmap_compare_small_results.json)。

## 重放编号的含义

原始 rN 表示种子 0x20260922 下随机配置编号 N。缩减项沿用了原 id，但已经改变尺寸、元素/采样参数或 mip；不能仅凭 rN 重建缩减后的输入，必须使用 selected_input 或原 JSON 的 reduced.result.input。

缩减方法为有界贪心，不能称为全局最小反例。x/y/z/s 在本模块不参与布局计算；原始项保留的坐标不保证对当前 mip 是合法 texel 访问。

## GFX12 的两类关键差异

### gfx12:numerical_difference:slice

~~~json
{
  "x": 0,
  "y": 0,
  "z": 0,
  "s": 0,
  "map0_w_minus_1": 0,
  "map0_h_minus_1": 1,
  "map0_d_minus_1": 0,
  "sw_mode": "SW_LINEAR",
  "log2_num_samples": 0,
  "log2_element_bytes": 0,
  "mip_level": 0,
  "maxmip": 0
}
~~~

| 字段 | 文档原始值 | 文档换算 | 参考推导/换算 | 分类 |
| --- | --- | --- | --- | --- |
| pitch | 128 | 128 | 128 | match |
| slice | 512 | 512 | 256 | numerical_difference |
| mip_in_tail | 17 | 17 | 17 | match |
| mip_offset_b | 0 | 0 | 0 | match |
| l2_ms | 7 | 7 | 7 | match |
| l2_blk_w | 7 | 7 | 7 | match |
| l2_blk_h | 0 | 0 | 0 | match |
| l2_blk_d | 0 | 0 | 0 | match |
| l2_blk_w_slice | 8 | 8 | 8 | match |

### gfx12:representation_difference:pitch

~~~json
{
  "x": 117,
  "y": 55,
  "z": 30,
  "s": 0,
  "map0_w_minus_1": 1285,
  "map0_h_minus_1": 255,
  "map0_d_minus_1": 224,
  "sw_mode": "SW_4KB_2D",
  "log2_num_samples": 0,
  "log2_element_bytes": 1,
  "mip_level": 6,
  "maxmip": 10
}
~~~

| 字段 | 文档原始值 | 文档换算 | 参考推导/换算 | 分类 |
| --- | --- | --- | --- | --- |
| pitch | 64 | 64 | 32 | representation_difference |
| slice | 473088 | 946176 | 946176 | match |
| mip_in_tail | 0 | 0 | 0 | match |
| mip_offset_b | 0 | 0 | 0 | match |
| l2_ms | 12 | 12 | 12 | match |
| l2_blk_w | 6 | 6 | 6 | match |
| l2_blk_h | 5 | 5 | 5 | match |
| l2_blk_d | 0 | 0 | 0 | match |
| l2_blk_w_slice | 6 | 6 | 6 | match |


## 另有 GFX10 中间乘法回绕证据

原报告记录一个隔离 slice 阶段差异；云端 run.cjs 的 selfCheck 另有明确断言输入：SW_256B_2D、65536×65536、16 BPE、单采样、maxmip=1，检查 GFX10 mip0 的 UINT32 乘积回绕为 0。它是云端自检证据，不是上表额外生成的随机反例；本次没有重新执行。
