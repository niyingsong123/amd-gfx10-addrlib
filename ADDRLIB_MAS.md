# ADDRLIB

**第一章：为什么需要 Mipmap（3 页）**

- **纹理缩小时遇到的问题**
  用近处和远处的同一张纹理说明：大量纹理细节落入少量屏幕像素，容易出现锯齿、摩尔纹和闪烁。解释直接从高分辨率纹理采样的局限。
- **Mipmap 如何解决这些问题**
  展示逐级缩小、经过预过滤的纹理金字塔。解释 mip level，以及如何根据屏幕上的覆盖尺度选择合适层级。LOD 和三线性过滤只介绍作用。
- **Mipmap 的收益与代价**
  讲清画质、采样效率与额外存储之间的关系。用普通二维纹理说明各级数据量的变化，区分理想数据量和考虑对齐后的实际占用。

**第二章：为什么还需要 Mip Tail（3 页）**

- **GPU 纹理的分块存储**
  简单介绍线性布局与 tiled 布局，以及 tile/block、对齐的含义。让听众理解：实际分配空间受到块大小和布局规则约束。
- **小 Mip 带来的空间浪费**
  用示意图说明：纹理层级越来越小，如果每级仍独占完整的大块，大量空间会空着。比较有效数据量与分配空间。
- **Mip Tail 的基本思路**
  将多个小 mip 按规则放入共享区域，提高空间利用率。介绍普通 mip、tail mip 和“第一个进入 tail 的层级”。说明各级仍然独立，tail 中仍需要地址映射。

**第三章：AddrLib 在工程中负责什么（2 页）**

- **输入与输出**
  输入包括纹理尺寸、格式、mip 数量、资源类型和布局模式。输出包括对齐尺寸、各级位置、tail 信息及资源占用。
- **布局计算与地址计算的关系**
  先确定各级 mip 在资源中的布局，再确定指定 texel 的位置。通过一张流程图串起 mip、block、块内坐标和 swizzle；swizzle 只讲作用与输入输出。

**第四章：完整计算过程与贯穿算例（6 页，重点章节）**

使用同一张纹理贯穿整章，建议选择 **二维 RGBA8、单采样、完整 mip 链、GFX10 的一种明确支持的 64KB 布局模式**。普通 mip 和 tail mip 各选一个坐标进行计算。

| 页次 | 讲解内容                                                     | 本页要得到的结果                              |
| ---- | ------------------------------------------------------------ | --------------------------------------------- |
| 1    | 明确输入参数、资源基址、布局模式和计算目标，解释每个参数的单位 | 一张可复算的输入表                            |
| 2    | 逐级计算 mip 尺寸，结合块尺寸说明对齐、pitch 和普通 mip 的块数 | 各级尺寸与空间需求表                          |
| 3    | 逐级检查进入 tail 的条件，同时考虑尺寸限制和剩余层级数量     | 第一个 tail mip，以及普通 mip/tail mip 的分界 |
| 4    | 按所选模式的实际规则计算普通 mip 偏移、共享 tail 分配和资源总占用 | 带数值与偏移标注的内存布局图                  |
| 5    | 选取一个普通 mip 内的 texel，计算所属块、块内坐标、swizzle 结果并组合地址 | 一个完整的普通 mip 地址                       |
| 6    | 选取一个 tail mip 内的 texel，计算 tail 原点、平移后的坐标，再进行 swizzle 和地址组合 | 一个完整的 tail mip 地址，并与普通路径对照    |

这一章的讲解要求：

- 每一步都展示“输入、计算方法、中间结果、结果用途”，避免只列公式。
- 全章使用同一套参数，明确区分元素数、块数和字节数。
- swizzle 展示所需映射及代入结果，最多挑一两个地址位解释，不展开整张位映射表。
- tail 原点与最终 texel 地址分别说明，避免重复叠加 tail 偏移。
- 用一个简短的非整齐尺寸例子补充说明对齐，不再引入第二套完整算例。

**第五章：工程对照与关键认识（2 页）**

- **讲解内容与工程资料的对应关系**
  指出概念说明、tail 分析、计算示例和版本核对资料各自的位置，并标明相关上游源码入口，便于听众后续阅读。
- **容易混淆的概念**
  回顾 mip 层级与内存排列顺序、逻辑尺寸与对齐尺寸、tail 原点与最终地址。说明 tail 的具体规则需要结合架构代际和布局模式理解。



### addrlib解决的问题

​	addrlib是把输入坐标、元素的bpp、swizzle mode、mip0尺寸、base addr、mipmap_level、max mipmap id、sample num和msaa等信息作为输入，通过一系列计算，得到当前元素对应的tiled surface地址的模块。

![image-20260913170701792](C:\Users\niyingsong\AppData\Roaming\Typora\typora-user-images\image-20260913170701792.png)

#### 为什么需要mipmap

​	GPU 纹理模块经常会遇到以下两种情况。低分辨率纹理插值出高分辨率的目标图，以及高分辨率的纹理插值出低分辨率的目标图。这是因为在GPU的渲染中，视角会一直变，同一个物体，可能突然会用很近的视角去观察，之后又会用很远的视角去观察。

​	低分辨率纹理插值出高分辨率的目标图，会遇到目标图清晰度很低的问题。

![image-20260913171630996](D:\文件\codec\SDMA\assets\image-20260913171630996.png)

​	而高分辨率的纹理插值出低分辨率的目标图，会遇到cache miss率很高，性能很差的问题。

![image-20260913171654415](D:\文件\codec\SDMA\assets\image-20260913171654415.png)

​	左边的图是高分辨率纹理插值低分辨率目标图的场景，一些纹理样点没被使用或者使用频率低。反而造成了大量cache miss。右边是比较理想的插值情况，这种情况下，即不会造成清晰度变差，也不会导致cache miss变高。

![image-20260913171528469](D:\文件\codec\SDMA\assets\image-20260913171528469.png)

#### 	mipmap方案

​	下图分辨是在GPU中对纹理的真实的存储方式，不仅需要把原始mip_id = 0的图片存储，还需要把它多次2倍抽样出的纹理图存下来。当进行纹理渲染时，可以直接使用分辨率接近的mipmap图用来插值。

![image-20260913172212926](D:\文件\codec\SDMA\assets\image-20260913172212926.png)

![image-20260913172222181](D:\文件\codec\SDMA\assets\image-20260913172222181.png)

#### 	mipmap tail

​	对于某一个mipmap，会按macro block来对齐。macro block是tiled surface的最大的tile单位。使用macro block可以方便计算，并且使得拥有更好的空间关联性。对于mip_id比较小的mipmap来说，通常由很多macro block组成。对于mip_id比较大的mimap来说，通常由1个或者几个macro block组成。而对于mip_id更大的mimap来说，存储它所有样点所需要的存储空间都远不到一个macro block的尺寸。如果按macro block来对齐，每一个mip_id更大的mimap都会占用一个macro block的存储空间，会非常浪费。因此会把这些mipmap全部打包到一个macro block当中一起存储，这个macro block叫做mipmap_tail。

![image-20260913172742516](D:\文件\codec\SDMA\assets\image-20260913172742516.png)

#### 	tiled surface排布

##### 	standard

​	下图表示了某一个不属于mipmap tail的mipmap的常见排布方式，swizzle mode是standard。

​	一张以tiled方式排布的图像，首先会以macro block的方式把图像切成很多块，macro block常见的大小有256B、4KB、64KB、256KB，以raster的顺序排列。如果swizzle mode是standard，macro block接下来会以256B的大小切割成很多micro block。micro block的排列顺序按照morton排序。在一个micro block内部，多个样点之间依然采取raster order。

​	下图中一个macro block的size是4KB，bpp=1，64x64x1=4KB。macro block的元素有64x64个。micro block的size是256B，16x16x1 = 256B，micro block的元素有16x16个。

![image-20260914200151169](D:\文件\codec\SDMA\assets\image-20260914200151169.png)

​	morton排序是一种特殊的排序方式，多运用在对空间关联性要求比较高的场景。以上图为例，假设X坐标用2bit表示X[1:0], Y坐标用2bit表示Y[1:0]，morton排序的方式是，先把每个坐标的每个bit抽出来得到：X[1], X[0], Y[1], Y[0]。接下来对bit进行高低位排列，比如{Y[1], X[1], Y[0], X[0]} = order[3:0]。那么以morton排序的micro block的顺序就是[order=0, order=1 .... order=15]. 再把每个order值换算成对应的[X, Y]坐标，如下表。这是一种最简单的morton排序方式。

​	morton排序的坐标的维度可以是任意，每个轴的bit数也可以任意，每个bit的排序也是任意的，因此morton排序能够构建出无数种排序方式。把每个轴的低bit放在低位，高bit放在高位，即可得到空间关联性很强的排序方式。

| order      | [X, Y] 坐标 |
| ---------- | ----------- |
| order = 0  | [0, 0]      |
| order = 1  | [1, 0]      |
| order = 2  | [0, 1]      |
| order = 3  | [1, 1]      |
| order = 4  | [2, 0]      |
| order = 5  | [3, 0]      |
| order = 6  | [2, 1]      |
| order = 7  | [3, 1]      |
| order = 8  | [0, 2]      |
| order = 9  | [1, 2]      |
| order = 10 | [0, 3]      |
| order = 11 | [1, 3]      |
| order = 12 | [2, 2]      |
| order = 13 | [3, 2]      |
| order = 14 | [2, 3]      |
| order = 15 | [3, 3]      |

##### 	zorder

​	下图表示了某一个不属于mipmap tail的mipmap的常见排布方式，swizzle mode是zorder。

​	一张以tiled方式排布的图像，首先会以macro block的方式把图像切成很多块，macro block常见的大小有256B、4KB、64KB、256KB，以raster的顺序排列。如果swizzle mode是zorder，macro block的排列顺序按照morton排序。也就是说，standard是以micro block做morton排序，micro block内部做raster排序。而zorder是在macro block内部直接以元素为单位做morton排序。

​	下图中一个macro block的size是4KB，bpp=1，64x64x1=4KB。macro block的元素有64x64个。morton排序会在64x64大小的macro block来做。X轴一共有6个bit，Y轴有6个bit，也就说一共是12个bit的morton排序。图中省略了morton排序的

![image-20260914201059328](D:\文件\codec\SDMA\assets\image-20260914201059328.png)

### 计算方式

#### 	swizzle mode decoder

![image-20260914203649543](D:\文件\codec\SDMA\assets\image-20260914203649543.png)

linear = sw_type == `SW_LINEAR

| swizzle mode | blk_type         | sw_type |
| ------------ | ---------------- | ------- |
| SW_LINEAR    | SZ_LIN (SZ_128B) | SW_L    |
| SW\_256B_2D  | SZ_256B          | SW_D_2D |
| SW\_4KB_2D   | SZ_4KB           | SW_D_2D |
| SW\_64KB_2D  | SZ_64KB          | SW_D_2D |
| SW\_256KB_2D | SZ_256KB         | SW_D_2D |
| SW\_4KB_3D   | SZ_4K            | SW_S_3D |
| SW\_64KB_3D  | SZ_64KB          | SW_S_3D |
| SW\_256KB_3D | SZ_256KB         | SW_S_3D |

#### 	macro block size

![image-20260914203740508](D:\文件\codec\SDMA\assets\image-20260914203740508.png)

| blk_type | l2_ms | l2_ms_128B | ms_mask_128B(mask of ms bits used) |
| -------- | ----- | ---------- | ---------------------------------- |
| SZ_LIN   | 7     | 0          | 0                                  |
| SZ_256B  | 8     | 1          | 1                                  |
| SZ_4KB   | 12    | 5          | 1f                                 |
| SZ_64KB  | 16    | 9          | 1ff                                |
| SZ_256KB | 18    | 11         | 7ff                                |

#### 	macro block dimention calculation

![image-20260914202847708](D:\文件\codec\SDMA\assets\image-20260914202847708.png)

dim3D = (sw_type == \`SW_S_3D)

msaa = (dim3D | linear) ? 2'd0 : l2_ns **//l2_ns is log2 of num samples**

block_size_elements = l2_ms - (l2_eb + msaa) **//l2_ms is log2 of macro size //l2_eb is log2 of element size** 

if {linear, sw_type} == {1'b0, \`SW_D_2D} //2D

{

​	l2_blk_w = block_size_elements[4:1] + (block_size_elements[0] & (l2_eb[0] || l2_ns[0]))

​	l2_blk_h = block_size_elements[4:1]

​	l2_blk_d = 4'h0

}

else if {linear, sw_type} == {1'b0, \`SW_S_3D} //3D

{

​	l2_blk_w = sheet(l2_ms[4:1] l2_eb[2:0])  **//log2 of block width**

​	l2_blk_h =  sheet(l2_ms[4:1] l2_eb[2:0]) **//log2 of block height**

​	l2_blk_d =  sheet(l2_ms[4:1] l2_eb[2:0]) **//log2 of block depth**

}

else //1D or linear

{

​	l2_blk_w = block_size_elements

​	l2_blk_h = 4'h0

​	l2_blk_d = 4'h0

}

| IN<br />macro size, element size | IN<br />l2_ms[4:1], l2_eb[2:0] | OUT<br />l2_blk_w_3d<br />log2 of 3d blk width | OUT<br />l2_blk_h_3d<br />log2 of 3d blk height | OUT<br />l2_blk_d_3d<br />log2 of 3d blk depth |
| -------------------------------- | ------------------------------ | ---------------------------------------------- | ----------------------------------------------- | ---------------------------------------------- |
| 4KB, 8bpp                        | 4'b0110, 3'd0                  | 4 (16)                                         | 4 (16)                                          | 4 (16)                                         |
| 4KB, 16bpp                       | 4'b0110, 3'd1                  | 3 (8)                                          | 4 (16)                                          | 4 (16)                                         |
| 4KB, 32bpp                       | 4'b0110, 3'd2                  | 3 (8)                                          | 4 (16)                                          | 3 (8)                                          |
| 4KB, 64bpp                       | 4'b0110, 3'd3                  | 3 (8)                                          | 3 (8)                                           | 3 (8)                                          |
| 4KB, 128bpp                      | 4'b0110, 3'd4                  | 2 (4)                                          | 3 (8)                                           | 3 (8)                                          |
| 64KB, 8bpp                       | 4'b1000, 3'd0                  | 6 (64)                                         | 5 (32)                                          | 5 (32)                                         |
| 64KB, 16bpp                      | 4'b1000, 3'd1                  | 5 (32)                                         | 5 (32)                                          | 5 (32)                                         |
| 64KB, 32bpp                      | 4'b1000, 3'd2                  | 5 (32)                                         | 5 (32)                                          | 4 (16)                                         |
| 64KB, 64bpp                      | 4'b1000, 3'd3                  | 5 (32)                                         | 4 (16)                                          | 4 (16)                                         |
| 64KB, 128bpp                     | 4'b1000, 3'd4                  | 4 (16)                                         | 4 (16)                                          | 4 (16)                                         |
| 256KB, 8bpp                      | 4'b1001, 3'd0                  | 6 (64)                                         | 6 (64)                                          | 6 (64)                                         |
| 256KB, 16bpp                     | 4'b1001, 3'd1                  | 5 (32)                                         | 6 (64)                                          | 6 (64)                                         |
| 256KB, 32bpp                     | 4'b1001, 3'd2                  | 5 (32)                                         | 6 (64)                                          | 5 (32)                                         |
| 256KB, 64bpp                     | 4'b1001, 3'd3                  | 5 (32)                                         | 5 (32)                                          | 5 (32)                                         |
| 256KB, 128bpp                    | 4'b1001, 3'd4                  | 4 (16)                                         | 5 (32)                                          | 5 (32)                                         |

#### 	macro size 256B align

![image-20260914205805703](D:\文件\codec\SDMA\assets\image-20260914205805703.png)

l2_blk_w_slice = (linear && (l2_blk_w < 'd8)) ? ('d8 - l2_eb) : l2_blk_w; //256B align

l2_ms_256B = (l2_ms_128B=='d0) ? 'd0 : (l2_ms_128B - 1) // log 256B align

l2_mip_offset = (l2_ms < 5'd8) ? 5'd0 : l2_ms - 5'd8

#### 	calculate num mips in tail

![image-20260915082435084](D:\文件\codec\SDMA\assets\image-20260915082435084.png)

​	is_3d_blk_size = (sw_type == `SW_S_3D) //not always the same as dim_type == \`dim_3D

​	case(l2_ms_256B)

​	{

​		4'd4: l2_ms_256B_3d = 4'd3 //12-4/3 - 8 = 3 (4kB)

​		4'd8: l2_ms_256B_3d = 4'd6 //16-8/3 - 8 = 6 (64KB)

​		4'd10: l2_ms_256B_3d = 4'd7 //18 - 10/3 - 8 = 7 (256KB)

​	}

​	l2_ms_256B_eff = (is_3d_blk_size) ? l2_ms_256B_3d : l2_ms_256B

​	//this assumes that l2_ms_256B can only be 256B, 4K, 64K, VAR

​	//VAR sizes are : l2_ms = 14 ... 20

​	//GFX12: Block sizes are: 256B(8), 4KB(12), 64KB(16), 256KB(18)

​	case (l2_ms_256B_eff)

​	4'd0: num_mips_in_tail = 'd1 //this will handle the linear cases as well (l2_ms = 7)

​	4'd3: num_mips_in_tail = 'd5 //(1+(1<<(l2_ms_256B_eff + 8 - 9)))

​	4'd4, 4'd6, 4'd7, 4'd8, 4'd9, 4'd10, 4'd11, 4'd12: num_mips_in_tail = (l2_ms_256B_eff + 4'd4) // (((effective_block_size_log2_256B + 8) - 11) + 7) => (l2_ms_256B_eff + 4'd4)



#### 	in_tail_chk for num

![image-20260915083349580](D:\文件\codec\SDMA\assets\image-20260915083349580.png)

//you can fit only some number of mips inside a tail, everything else will be outside

//this condition needs to be in conjunction with the mipsizes check

mips_outside_tail = (maxmip_in - mips_in_tail) //extra bit to allow for negative result

for (m=0; m<MAXMIP;m=m+1)

{

​		in_tail_chk[m] = ((m > mips_outside_tail) | mips_outside_tail[msb]) // if mips_outside_tail is -ve, then in_tail_chk is true, mips_outside_tail[msb] only use mips_outside_tail's msb bit, only 1 bit

}

#### 	calculate per mip size(block unit)

![image-20260915092249060](D:\文件\codec\SDMA\assets\image-20260915092249060.png)

​	function pad_to_log2sz_gc (input dim_in, input l2_pad_sz_in, output pad_out)
​	{

​		//total "after padding" bits required depends on what is the minimum size of the padding supported

​		//pads to at least one block

​		//in some cases, user can pass 'PAD_WIDTH' to override this

​		pad_sz_mask = (1'b1 << l2_pad_sz_in) - 1'b1

​		pad_out = (dim_in >> l2_pad_sz_in) + |(dim_in & pad_sz_mask)

​	}

​	Wb0 = pad_to_log2sz_gc(map0_w, l2_blk_w)

​	Hb0 = pad_to_log2sz_gc(map0_h, l2_blk_h)

​	Wb_slice0 = pad_to_log2sz_gc(map0_w, l2_blk_w_slice)

​	pad_data_sz_w = 1'b1 << l2_blk_w

​	pad_data_sz_h = 1'b1 << l2_blk_h

​	for(m=1;m<MAXMIP;m=m+1) { // W_H_block_calc

​		Wb[m] = (Wb0 >> m) + |Wb0[\`PAD_W_MSB(m):0];

​		Hb[m] = (Hb0 >> m) + |Hb0[\`PAD_H_MSB(m):0];

​		Wb_slice[m] = (Wb_slice0 >> m) + |Wb_slice0[\`PAD_W_MSB(m):0]

​	}

#### 	final in mip tail check

![image-20260915090911322](D:\文件\codec\SDMA\assets\image-20260915090911322.png)

​	w_tail_sz = y_bias ? pad_sz_w : (pad_sz_w >> 1)

​	h_tail_sz = y_bias ? (pad_sz_h>>1) : pad_sz_h

​	in_miptail = (H<= h_tail_sz) & (W<= w_tail_sz) & in_tail_chk

​	for(m=0;m<MAXMIP-1;m=m+1) begin: CHK_NEXT_IN_MIPTAIL

​		//y_bias_intail is special condition for checking in_tail

​		//in_tail_chk[m+1] is check if the mip is outside the number of levels that can fit inside a tail 

​		//next_in_tail[m+1]  //=1, if the next mip is inside the miptail

​		height_in_tail = y_bias ? (Hb[m] <=1) : (Hb[m]<=2);

​		width_in_tail = y_bias ? (Wb[m] <=2) : (Wb[m]<=1);

​		in_miptail[m+1] = next_in_tail[m+1] = height_in_tail && width_in_tail && in_tail_chk[m+1]

​	end

####  calculate mip_id and mip_size

![image-20260915092306709](D:\文件\codec\SDMA\assets\image-20260915092306709.png)

//set the tail mipid to max to indicate no tails are supported

tail_mipid_raw = {MAXMIP} // no tail

for(i=0; i<MAXMIP; i++) begin

​	if(i==0) begin if(in_miptail[i]) tail_mipid_raw = i; end

​	else begin if(in_miptail[i]^in_miptail[i-1]) tail_mipid_raw = i; end

end

tail_mipid = ((maxmip == 0) | ((l2_ms_128B>>1) == 0) ? MAXMIP : tail_mipid_raw) // linear and SW_\*_256B are treated  same - no miptails

for (int mip_idx=MAXMIP-1;mip_idx >=6; --mip_idx) begin

​	if(mip_idx > tail_mipid) begin

​		mipsize[mip_idx] = 'd0;

​	end else if ((mip_idx==tail_mipid) || (mip_idx == (MAXMIP-1))) begin

​		mipsize[mip_idx] = 'd1;

​	end else begin

​		mipsize[mip_idx] = Wb_slice[mip_idx] * Hb[mip_idx];

​	end

end



mip_mask = ((1'b1<<(mip_level + 4'd1)) - 1'b1); //for SLICE_CALC, ignore mip

maxmip_mask = ((1'b1 << (maxmip + 4'd1)) - 1'b1); 

slice_input_en = maxmip_mask; //所有有效mip的en，用于总mipsize的累加计算

mip_off_input_en = slice_input_en & ~mip_mask; //

mip_offset_in_blks = (mip_off_input_en[16] ? mipsize[16] : 'd0) + 

​				     (mip_off_input_en[15] ? mipsize[15] : 'd0) + 

​				     (mip_off_input_en[14] ? mipsize[14] : 'd0) + 

​				     (mip_off_input_en[13] ? mipsize[13] : 'd0) + 

​				     (mip_off_input_en[12] ? mipsize[12] : 'd0) + 

​				     (mip_off_input_en[11] ? mipsize[11] : 'd0) + 

​				     (mip_off_input_en[10] ? mipsize[10] : 'd0) + 

​				     (mip_off_input_en[9] ? mipsize[9] : 'd0) + 

​				     (mip_off_input_en[8] ? mipsize[8] : 'd0) + 

​				     (mip_off_input_en[7] ? mipsize[7] : 'd0) + 

​				     (mip_off_input_en[6] ? mipsize[6] : 'd0) +

​					(mip_off_input_en[1] ? mipsize[1] : 'd0) + 

​					 (mip_off_input_en[2] ? mipsize[2] : 'd0) + 

​					 (mip_off_input_en[3] ? mipsize[3] : 'd0) + 

​					 (mip_off_input_en[4] ? mipsize[4] : 'd0) +

​					 (mip_off_input_en[5] ? mipsize[5] : 'd0) ;

slice_b = (slice_input_en[16] ? mipsize[16] : 'd0) + 

​		 (slice_input_en[15] ? mipsize[15] : 'd0) + 

​		 (slice_input_en[14] ? mipsize[14] : 'd0) + 

​		 (slice_input_en[13] ? mipsize[13] : 'd0) + 

​		 (slice_input_en[12] ? mipsize[12] : 'd0) + 

​		 (slice_input_en[11] ? mipsize[11] : 'd0) + 

​		 (slice_input_en[10] ? mipsize[10] : 'd0) + 

​		 (slice_input_en[9] ? mipsize[9] : 'd0) + 

​		 (slice_input_en[8] ? mipsize[8] : 'd0) + 

​		 (slice_input_en[7] ? mipsize[7] : 'd0) + 

​		 (slice_input_en[6] ? mipsize[6] : 'd0) +

​		(slice_input_en[0] ? mipsize[0] : 'd0) + 

​		 (slice_input_en[1] ? mipsize[1] : 'd0) + 

​		 (slice_input_en[2] ? mipsize[2] : 'd0) + 

​		 (slice_input_en[3] ? mipsize[3] : 'd0) + 

​		 (slice_input_en[4] ? mipsize[4] : 'd0) + 

​		 (slice_input_en[5] ? mipsize[5] : 'd0) ;

slice= slice_b << ({1'b0, l2_blk_w_slice} + {1'b0, l2_blk_h});

pitch = Wb[mip_level] << l2_blk_w;

mip_offset_b= mip_offset_in_blks << l2_mip_offset;

mip_in_tail= (mip_level < tail_mipid) ? {MAXMIP} : (mip_level - tail_mipid);

l2_blk_width = l2_blk_w;

l2_blk_height_= l2_blk_h;

l2_blk_depth= l2_blk_d;

l2_ms = l2_ms

### 计算流程图

#### mipmap tail布局

#### y_bias翻转

#### XOR的意义

### 计算举例

//计算举例需要把每一个中间的重要变量计算出来

#### 简单参数计算

map0_w = 256

map0_h = 256

map0_d = 256

l2_eb = 0 //log2 of 元素size

l2_ns = 0 //log2 of msaa采样

blk_type = SZ_256KB //macro block size 64 x 64 x 64 x 1bpp = 256KB

SW_type = SW_S_3D

linear = 0 

l2_ms = 18 //log2 of macro size 256KB

l2_ms_128B = 11 // log2 of macro size, 128B unit, 256KB

l2_ms_256B = 10 // log2 of macro size, 256B unit, 256KB

ms_mask_128B = 0x7FF

dim3D = 1

msaa = 0

block_size_elements //一个macro block，元素个数的log2

l2_blk_w = 6 //一个macro block width的log2

l2_blk_h = 6 //一个macro block height的log2

l2_blk_d = 6 //一个macro block depth的log2

#### in_miptail compution

#### mip_offset_in_blks and slice computation

#### blk_offset computation

#### address_final and mipid_in_tail compution





​		



