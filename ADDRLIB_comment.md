# ADDRLIB_comment.md

> 本文件用于记录对 `ADDRLIB.md` 中关键 RTL 算法的逐句注释与推导。
> 本次新增内容重点整理 **Mip Tail 内部 reverse / byte_offset / micro-block 地址计算**，并特别区分 `mip_size` 与 `byte_offset`。

---

## 1. Mip Tail 内部的 reverse 定义

原始 RTL：

```text
mip_in_tail_reverse = (MAXMIP_WIDTH+2)'(num_mips_in_tail - (mip_in_tail + 1));
```

### 注释

```text
mip_in_tail_reverse = num_mips_in_tail - (mip_in_tail + 1)
```

这里的 `mip_in_tail` 是当前 mip 在 tail 中的相对编号：

- `mip_in_tail = 0`：第一个进入 tail 的 mip
- `mip_in_tail = 1`：tail 中第二个 mip
- ...
- `mip_in_tail = num_mips_in_tail-1`：tail 中最后一个、最小的 mip

而 `mip_in_tail_reverse` 是把这个顺序反过来编号：

```text
mip_in_tail = 0                    -> reverse = num_mips_in_tail-1
mip_in_tail = 1                    -> reverse = num_mips_in_tail-2
...
mip_in_tail = num_mips_in_tail-1  -> reverse = 0
```

因此，`reverse=0` 对应 tail 中最后、最小的 mip；越靠近 tail 起始处的 mip，reverse 越大。

这里的 `reverse` 首先是一个 **tail 内部位置索引**，不能直接解释成 mip 的 size。

---

## 2. byte_offset 的 piecewise 计算

原始 RTL：

```text
if(mip_in_tail_reverse[MAXMIP_WIDTH+1])
    byte_offset = 0;
else if(mip_in_tail_reverse > 'd6)
    byte_offset = (MSB_BYTE_OFFSET+1)'(5'd16 << mip_in_tail_reverse[MAXMIP_WIDTH+1:0]);
else
    byte_offset = (MSB_BYTE_OFFSET+1)'(mip_in_tail_reverse[MAXMIP_WIDTH+1:0] << 4'd8);
```

### 注释

首先检查 `mip_in_tail_reverse` 的符号位：

```text
if(mip_in_tail_reverse[MAXMIP_WIDTH+1])
    byte_offset = 0;
```

如果 reverse 是负数，说明当前索引已经超出了有效的 tail-relative 范围。这里直接把 offset 置 0，避免无符号下溢/错误地址传播。

然后是核心分界：

```text
else if(mip_in_tail_reverse > 6)
    byte_offset = 16 << reverse;
```

即：

```text
byte_offset = 16 * 2^reverse
```

而当：

```text
reverse <= 6
```

则使用：

```text
byte_offset = reverse << 8
```

即：

```text
byte_offset = reverse * 256B
```

因此，这段 RTL 实际定义的是一个 **piecewise byte-offset mapping**：

```text
reverse <= 6 : offset = reverse * 256B
reverse >  6 : offset = 16 * 2^reverse
```

特别注意：这里的变量名是 `byte_offset`，不是 `mip_size`。

---

## 3. Tail 内部为什么可以理解成 256B slot

对于 tail 内部通常使用的 `reverse=0..6` 区间：

```text
byte_offset = reverse << 8
           = reverse * 256B
```

因此相邻 reverse 的 offset 间隔为：

```text
256B
```

例如：

| reverse | byte_offset |
|---:|---:|
| 0 | 0 B |
| 1 | 256 B |
| 2 | 512 B |
| 3 | 768 B |
| 4 | 1024 B |
| 5 | 1280 B |
| 6 | 1536 B |

所以如果 tail 中有 6 个 mip，并且它们分别对应 `reverse=5..0`，则位置为：

| mip_in_tail | reverse | byte_offset |
|---:|---:|---:|
| 0 | 5 | 1280 B |
| 1 | 4 | 1024 B |
| 2 | 3 | 768 B |
| 3 | 2 | 512 B |
| 4 | 1 | 256 B |
| 5 | 0 | 0 B |

这说明 tail 内部可以从 **地址 slot / allocation granularity** 的角度理解为：

```text
6 个 mip
    ↓
6 个 256B slot
    ↓
总 tail footprint = 6 * 256B = 1536B
```

这里的“每个 mip 256B”应理解为 **tail packed layout 中分配的 256B slot / granularity**，而不是说 mip 的真实 texel footprint 在所有情况下都严格等于 256B。

---

## 4. 一个非常重要的概念：byte_offset != mip_size

不能因为：

```text
reverse = 4 -> byte_offset = 1024B
```

就说：

```text
mip_size = 1024B
```

因为 `byte_offset` 表示的是 **位置**，而 `mip_size` 表示的是 **这个 mip 自己需要多少存储空间**。

二者属于不同层次：

```text
mip_size
   │
   │ 描述 mip 自身 footprint
   ↓
allocation / layout information

byte_offset
   │
   │ 描述当前 mip 在特定 packed layout 中的位置
   ↓
micro-block / micro-tile coordinate
   ↓
最终地址
```

尤其在 `reverse > 6` 的区域，offset 直接进入指数增长：

```text
reverse = 7  -> 2048 B
reverse = 8  -> 4096 B
reverse = 9  -> 8192 B
```

不能把这些数直接当成对应 mip 的 size。

---

## 5. byte_offset 如何进一步变成 micro-block 坐标

原始 RTL：

```text
{x_mip_micro_block[5],
 y_mip_micro_block[5],
 x_mip_micro_block[4],
 y_mip_micro_block[4],
 x_mip_micro_block[3],
 y_mip_micro_block[3],
 x_mip_micro_block[2],
 y_mip_micro_block[2],
 x_mip_micro_block[1],
 y_mip_micro_block[1],
 x_mip_micro_block[0],
 y_mip_micro_block[0]} = byte_offset[BYTE_OFFSET_IN_MIPTAIL_WIDTH-1:8];
```

### 注释

这里是理解 `byte_offset` 最关键的一步。

RTL 并没有继续把 `byte_offset` 当成“size”使用，而是把它的高位重新解释为：

```text
x_mip_micro_block[*]
y_mip_micro_block[*]
```

也就是说：

```text
byte_offset
    │
    │ 去掉低 8 bit
    │ （256B granularity）
    ↓
剩余 bit
    │
    │ 按 X/Y 交错方式重新解释
    ↓
x_mip_micro_block / y_mip_micro_block
```

所以这里可以把 `byte_offset` 理解成：

> **把 mip 在 tail 中的 reverse 位置转换成 micro-block 坐标的一种中间地址表示。**

这也是为什么 `byte_offset` 与 `mip_size` 不能画等号。

---

## 6. l2_ms_odd 对 X/Y 方向的交换

原始 RTL：

```text
x_mip_micro_block_final = (l2_ms_odd) ? y_mip_micro_blocks; x_mip_micro_blocks;
y_mip_micro_block_final = (l2_ms_odd) ? x_mip_micro_blocks; y_mip_micro_blocks;
```

### 注释

当 `l2_ms_odd` 为真时，X/Y 两个 micro-block 坐标交换；否则保持原顺序。

因此：

```text
l2_ms_odd = 0
    x_final = x
    y_final = y

l2_ms_odd = 1
    x_final = y
    y_final = x
```

这说明 tail 内部的 packed address 并不是简单的一维线性排列，还需要考虑 block/swizzle 对 X/Y 方向的组织方式。

---

## 7. micro-block index 再转换成 element coordinate

原始 RTL：

```text
x_mip_in_tail_orig = 10'(x_mip_micro_block_final << l2_ublk_w);
y_mip_in_tail_orig = 10'(y_mip_micro_block_final << l2_ublk_h);
z_mip_in_tail_orig = 'd0;
```

### 注释

`x_mip_micro_block_final` / `y_mip_micro_block_final` 还是 micro-block 坐标。

一个 micro-block 在 X/Y 方向分别包含：

```text
2^l2_ublk_w elements
2^l2_ublk_h elements
```

因此左移：

```text
x << l2_ublk_w
```

相当于：

```text
x * 2^l2_ublk_w
```

从 micro-block index 转换为 element-space 的 X 坐标。

Y 方向同理。

所以完整链条可以写成：

```text
mip_in_tail
      ↓
reverse
      ↓
byte_offset
      ↓
去掉低 8 bit
      ↓
X/Y micro-block index
      ↓
考虑 l2_ms_odd 做 X/Y 交换
      ↓
乘以 micro-block 的 element 尺寸
      ↓
x_mip_in_tail_orig / y_mip_in_tail_orig
```

---

## 8. reverse / offset 数值表：注意它是 offset 表，不是 size 表

根据 RTL：

```text
reverse <= 6:
    offset = reverse * 256B

reverse > 6:
    offset = 16 * 2^reverse
```

得到：

| reverse | byte_offset | 不能直接解释成 mip_size |
|---:|---:|:---|
| 0 | 0 B | 是位置 0 |
| 1 | 256 B | 是位置 256B |
| 2 | 512 B | 是位置 512B |
| 3 | 768 B | 是位置 768B |
| 4 | 1024 B | 是位置 1024B |
| 5 | 1280 B | 是位置 1280B |
| 6 | 1536 B | 是位置 1536B |
| 7 | 2048 B | 是位置 2048B |
| 8 | 4096 B | 是位置 4096B |
| 9 | 8192 B | 是位置 8192B |

特别注意 `reverse=6`：

```text
reverse > 6   = false
```

因此 RTL 选择：

```text
6 << 8 = 1536B
```

而不是：

```text
16 << 6 = 1024B
```

所以不能用 `reverse=6 -> 1024B` 来解释这段 RTL 的 `byte_offset`。

如果某个独立算法得到 `1024B` 的 mip size，则需要去找真正计算 `mip_size` 的代码，不能由这里的 `byte_offset` 直接推导。

---

## 9. 与 surface-level mipsize 的区别

前面的 RTL 还有一套完全不同的 `mipsize` 计算：

```text
if(mip_idx > tail_mipid)
    mipsize[mip_idx] = 'd0;
else if(mip_idx == tail_mipid)
    mipsize[mip_idx] = 'd1;
else
    mipsize[mip_idx] = Wb_slice[mip_idx] * Hb[mip_idx];
```

这里的 `mipsize` 用于 **surface footprint / mip offset / slice footprint 的统计**。

特别是：

```text
mip == tail_mipid
    mipsize = 1

mip > tail_mipid
    mipsize = 0
```

它表达的是：

> 在 surface-level footprint 统计中，把整个 packed mip tail 当作一个 region 计算，而不是逐个把 tail 内 mip 重复累加。

因此这里又出现了三个不能混淆的概念：

```text
1. mip_size / mipsize
   → mip 或 surface layout footprint

2. mip_offset
   → mip 在更高层 surface layout 中的偏移

3. byte_offset
   → mip-tail 内部地址生成过程中，用来得到 micro-block 坐标的中间地址量
```

这三个量虽然最后都会参与地址计算，但含义不同。

---

## 10. 当前阶段的统一理解

现在可以把 Mip Tail 相关逻辑分成两层：

```text
                    Mipmap chain
                         │
                         ↓
                 判断是否进入 tail
                         │
                         ↓
                    tail_mipid
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ↓                             ↓
   Surface-level layout          Tail-internal address
          │                             │
          ↓                             ↓
       mipsize                     mip_in_tail
          │                             │
          ↓                             ↓
     mip_offset                  reverse index
          │                             │
          │                             ↓
          │                       byte_offset
          │                             │
          │                             ↓
          │                    micro-block X/Y
          │                             │
          │                             ↓
          │                    element coordinate
          │                             │
          └──────────────┬──────────────┘
                         ↓
                  final address
```

### 核心结论

**Tail 内部：**

```text
reverse = num_mips_in_tail - (mip_in_tail + 1)
```

对于 `reverse <= 6`：

```text
byte_offset = reverse * 256B
```

因此 tail 内部可以自然地理解为 256B-granularity 的 packed slots。

**Tail 外部 / reverse > 6：**

RTL 使用：

```text
byte_offset = 16 * 2^reverse
```

但这个量仍然叫 `byte_offset`，不能直接当作 `mip_size`。

最终最重要的认知是：

> **`byte_offset` 是地址计算工具，不是 mip size。它的主要作用是在 mip-tail packed layout 中，把 reverse position 映射为后续 micro-block / micro-tile 坐标，从而最终参与地址生成。**

---

## 11. 当前仍需进一步验证的问题

下面这个问题不要仅凭当前 RTL 的 `byte_offset` 代码下结论：

> **tail 外第一个 mip 的真实 `mip_size` 到底是多少？**

尤其是 `reverse=6` 对应的那个边界 mip，不能简单地用：

```text
16 * 2^6 = 1024B
```

作为结论，因为当前 piecewise RTL 在 `reverse=6` 时明确走的是：

```text
6 * 256B = 1536B
```

这两个数属于不同语义时才可能同时成立：

```text
1024B → 某个 mip 的真实 footprint / size（如果其他代码证明）
1536B → 当前 RTL 算出的 byte_offset
```

后续应继续追踪真正的 `mipsize` / `GetMipSize()` / mip allocation 计算，而不要从 `byte_offset` 反推 `mip_size`。
