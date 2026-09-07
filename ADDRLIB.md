
ADDRLIB

//变量含义

map0_w //mipmap0 width -1 for non_TC/padded sclaed width for TC

map0_h //mipmap0 height -1 for non_TC/padded sclaed height for TC

map0_d //mipmap0 depth -1 for non_TC/padded sclaed depth for TC

l2_eb //log2_element_bytes //0:1byte 1:2byte 2:4byte 3:8 bytes 4:16byte

log2_num_samples // specifies the log2 of 'the number of samples', for non-MSAA hardware, tie 0 0: 1sample 1: 2samples 2: 4smaples 3: 8samples

pitch //padded_width - 1 no of elements

slice //(padded_width * padded_ht) - 1, no of elements

`define PAD_W_MSB(mip) ((mip < W0_B_WIDTH) ? (mip-1) : (W0_B_WIDTH-1))

`define PAD_H_MSB(mip) ((mip < H0_B_WIDTH) ? (mip-1) : (H0_B_WIDTH-1))



// ============================================================================
// Analysis: GFX10 Mipmap Tail overall model
//
// 对这份 RTL 而言，mip-tail 处理不是简单的“尺寸变小后把 mip 放在最后”。
// 算法实际上分成几层：
//   1) 先根据 block / swizzle 得到 mip 的 block geometry；
//   2) 根据 block size 计算一个 tail capacity upper bound；
//   3) 同时检查 mip 的尺寸条件和“距离 mip chain 尾部的级数”条件；
//   4) 找到第一个 0->1 transition，得到 tail_mipid；
//   5) 在 surface-level footprint 统计中，把整个 packed tail 折叠成一个
//      tail region，而 tail 内各 mip 的进一步布局属于更细一层的 address rule。
//
// 因而这里要特别区分：
//   tail_mipid              = 第一个进入 tail 的 mip level
//   mipsize[m]              = surface layout 层面的 mip footprint
//   mip_offset_in_blks      = mip offset 的中间尺度（当前片段中其方向需结合
//                             完整 address-generation 逻辑进一步确认）
//   mip_offset_b_out        = 再转换到当前 block-size 地址尺度后的输出
// ============================================================================

//S0 stage

//calculate W0/H0: padded width/height of mip0

//Decode sw_mode: get dim_type, sw_type, blk_type, is_linear

//calculate macro_block_size: l2_ms = log2 of block size (base on blk_type)

//calculate block dimensions: l2_blk_w/h/d

/////////sw_mode_dec////////////

linear = sw_type == `SW_LINEAR

{blk_type, sw_type} = sw_mode_dec(sw_mode) 

//SW_L == Linear/1D

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

///////macro_blk_size_calc//////////

{l2_ms, l2_ms_128B, ms_mask_128B} = macro_blk_size_calc(blk_type)

| blk_type | l2_ms | l2_ms_128B | ms_mask_128B(mask of ms bits used) |
| -------- | ----- | ---------- | ---------------------------------- |
| SZ_LIN   | 7     | 0          | 0                                  |
| SZ_256B  | 8     | 1          | 1                                  |
| SZ_4KB   | 12    | 5          | 1f                                 |
| SZ_64KB  | 16    | 9          | 1ff                                |
| SZ_256KB | 18    | 11         | 7ff                                |

/////////macro_block_dim_calc///////////

dim3D = (sw_type == `SW_S_3D)

msaa = （dim3D | linear）？ 2‘d0 ：l2_ns

block_size_elements = l2_ms - (l2_eb + msaa_cnt)

if {linear, sw_type} == {1'b0, `SW_D_2D}

{

​	l2_blk_w = block_size_elements[4:1] + (block_size_elements[0] & (l2_eb[0] || l2_ns[0])

​	l2_blk_h = block_size_elements[4:1]

​	l2_blk_d = 4'h0

//下面表格只是举例，最终看上面公式

| macro size, element size | l2_ms, l2_ns, l2_eb | block_size_elements | l2_blk_w_2d | l2_blk_h_2d | l2_blk_d_2d |
| ------------------------ | ------------------- | ------------------- | ----------- | ----------- | ----------- |
| 256B, 8bpp               | 4'b1000, 2'b0, 3'b0 | 8                   | 4 (16)      | 4 (16)      | 0           |
| 256B, 8bpp               | 4'b1000, 2'b1, 3'b0 | 7                   | 4 (16)      | 3 (8)       | 0           |
| 256B, 8bpp               | 4'b1000, 2'b2, 3'b0 | 6                   | 3 (8)       | 3 (8)       | 0           |
| 256B, 8bpp               | 4'b1000, 2'b3, 3'b0 | 5                   | 3 (8)       | 2 (4)       | 0           |
| 256B, 8bpp               | 4'b1000, 2'b0, 3'b0 | 8                   | 4 (16)      | 4 (16)      | 0           |
| 256B, 16bpp              | 4'b1000, 2'b0, 3'b1 | 7                   | 4 (16)      | 3 (8)       | 0           |
| 256B, 16bpp              | 4'b1000, 2'b1, 3'b1 | 6                   | 3 (8)       | 3 (8)       | 0           |
| 256B, 32bpp              | 4'b1000, 2'b2, 3'b2 | 4                   | 2 (4)       | 2 (4)       | 0           |
| 256B, 32bpp              | 4'b1000, 2'b3, 3'b2 | 3                   | 2 (4)       | 1 (2)       | 0           |

}

else if {linear, sw_type} == {1'b0, `SW_S_3D}

{

​	l2_blk_w = sheet(l2_ms[4:1] l2_eb[2:0]) //看下面表格

​	l2_blk_h =  sheet(l2_ms[4:1] l2_eb[2:0]) //看下面表格

​	l2_blk_d =  sheet(l2_ms[4:1] l2_eb[2:0]) //看下面表格

| macro size, element size | l2_ms[4:1] l2_eb[2:0] | l2_blk_w_3d | l2_blk_h_3d | l2_blk_d_3d |
| ------------------------ | --------------------- | ----------- | ----------- | ----------- |
| 4KB, 8bpp                | 4'b0110, 3'd0         | 4 (16)      | 4 (16)      | 4 (16)      |
| 4KB, 16bpp               | 4'b0110, 3'd1         | 3 (8)       | 4 (16)      | 4 (16)      |
| 4KB, 32bpp               | 4'b0110, 3'd2         | 3 (8)       | 4 (16)      | 3 (8)       |
| 4KB, 64bpp                | 4'b0110, 3'd3         | 3 (8)       | 3 (8)       | 3 (8)       |
| 4KB, 128bpp              | 4'b0110, 3'd4         | 2 (4)       | 3 (8)       | 3 (8)       |
| 64KB, 8bpp               | 4'b1000, 3'd0         | 6 (64)      | 5 (32)      | 5 (32)      |
| 64KB, 16bpp              | 4'b1000, 3'd1         | 5 (32)      | 5 (32)      | 5 (32)      |
| 64KB, 32bpp              | 4'b1000, 3'd2         | 5 (32)      | 5 (32)      | 4 (16)      |
| 64KB, 64bpp              | 4'b1000, 3'd3         | 5 (32)      | 4 (16)      | 4 (16)      |
| 64KB, 128bpp             | 4'b1000, 3'd4         | 4 (16)      | 4 (16)      | 4 (16)      |
| 256KB, 8bpp              | 4'b1001, 3'd0         | 6 (64)      | 6 (64)      | 6 (64)      |
| 256KB, 16bpp             | 4'b1001, 3'd1         | 5 (32)      | 6 (64)      | 6 (64)      |
| 256KB, 32bpp             | 4'b1001, 3'd2         | 5 (32)      | 6 (64)      | 5 (32)      |
| 256KB, 64bpp             | 4'b1001, 3'd3         | 5 (32)      | 5 (32)      | 5 (32)      |
| 256KB, 128bpp            | 4'b1001, 3'd4         | 4 (16)      | 5 (32)      | 5 (32)      |

}

else //1D or linear

{

​	l2_blk_w = block_size_elements

​	l2_blk_h = 4'h0

​	l2_blk_d = 4'h0

}

//////////////256B align////////////////

// -----------------------------------------------------------------------------
// Analysis: `l2_blk_w_slice` / 256B slice granularity
//
// slice-size 的统计粒度与普通 pitch/layout 的 block width 并不完全相同。
// 特别是在 128B linear 情况下，这里强制使用至少 256B 的 slice 统计粒度，
// 后面的 Wb_slice[m] / slice_b 都建立在这个粒度上。
// -----------------------------------------------------------------------------
//fix for 128B pitch alignment

//slice must still be calculated at 256B alignment, so use this forslice calculations

l2_blk_w_slice = (linear && (l2_blk_w < 'd8)) ? ('d8 - l2_eb) : ll2_blk_w; //256B align

// -----------------------------------------------------------------------------
// Analysis: `l2_ms_256B`
//
// 把 block size 转换成“以 256B 为基准”的指数尺度：
//     l2_ms_256B ~= log2(block_size / 256B)
// 例如：64KB -> 8，256KB -> 10。
// 这个归一化值随后作为 `num_mips_in_tail` 的输入。
// -----------------------------------------------------------------------------
l2_ms_256B = (l2_ms_128B=='d0) ? 'd0 : (l2_ms_128B - 1) // log 256B align

// -----------------------------------------------------------------------------
// Analysis: `l2_mip_offset`
//
// 这不是“mip level 的 offset”。它描述的是：当前 block size 相对于 256B
// 基础粒度需要放大多少位。因为 256B = 2^8，所以：
//     l2_mip_offset = max(l2_ms - 8, 0)
// 最后的 `mip_offset_b_out` 会使用这个值把统一 block 单位转换到当前
// block-size 地址尺度。
// -----------------------------------------------------------------------------
l2_mip_offset = (l2_ms < 5'd8) ? 5'd0 : l2_ms - 5'd8

//prevent underflow in sw_linear case



/////////function al_num_mips_inside_tail////////////

// -----------------------------------------------------------------------------
// Analysis: 3D tail-capacity correction
//
// 2D mip 每级缩小主要体现在 W/H 两个维度；3D mip 还会继续缩小 depth，
// 所以 tail capacity 不能直接复用 2D 的 block-size 参数。这里把原始
// l2_ms_256B 映射为一个 3D effective value，再统一进入后面的
// `num_mips_in_tail` 计算。
// -----------------------------------------------------------------------------
is_3d_blk_size = (sw_type == `SW_S_3D) //no always the same as dim_type == `dim_3D

case(l2_ms_256B)

{

4'd4: l2_ms_256B_3d = 4'd3 //12-4/3 - 8 = 3 (4kB)

4'd8: l2_ms_256B_3d = 4'd6 //16-8/3 - 8 = 6 (64KB)

4'd10: l2_ms_256B_3d = 4'd7 //18 - 10/3 - 8 = 7 (256KB)

}

l2_ms_256B_eff = (is_3d_blk_size) ? l2_ms_256B_3d : l2_ms_256B



//this assumes that l2_ms_256B can only be 256B, 4K, 64K, VAR

//VAR sizes are : l2_ms = 14 ... 20

//GFX12: Block sizes are: 256B(8), 4KB(12), 64KB(16), 256KB(18)

// -----------------------------------------------------------------------------
// Analysis: `num_mips_in_tail`
//
// 这里计算的是 tail 的“最大可容纳 mip level 数”上限，而不是直接判断
// 某一级 mip 是否已经进入 tail。它对应公开 AddrLib 中类似
// `GetMaxNumMipsInTail()` 的概念。
// -----------------------------------------------------------------------------
case (l2_ms_256B_eff)

4'd0: num_mips_in_tail = 'd1 //this will handle the linear cases as well (l2_ms = 7)

4'd3: num_mips_in_tail = 'd5 //(1+(1<<(l2_ms_256B_eff + 8 - 9)))

4'd4, 4'd6, 4'd7, 4'd8, 4'd9, 4'd10, 4'd11, 4'd12: num_mips_in_tail = (l2_ms_256B_eff + 4'd4) // (((effecttive_block_size_log2_256B + 8) - 11) + 7) => (l2_ms_256B_eff + 4'd4)



//you can fit only some number of mips inside a tail, everything else will be outside

// -----------------------------------------------------------------------------
// Analysis: `mips_outside_tail`
//
// 这个值把“tail 最多能容纳多少级”转换成 mip level 边界：
//     mips_outside_tail = maxmip_in - mips_in_tail
// 例如 maxmip_in=11、capacity=6 时，前面的 Mip0~Mip5 在 tail 外，
// Mip6~Mip11 才有资格进入 tail。
// 额外保留符号位是为了处理 maxmip_in < mips_in_tail 的负值情况；
// 此时整个 mip chain 的长度不足以填满 tail capacity。
// -----------------------------------------------------------------------------
mips_outside_tail = (maxmip_in - mips_in_tail) //extra bit to allow for negative result

generate 

​	for (m=0; m<MAXMIP:m=m+1) begin

​		assign in_tail_chk[m] = ((m > mips_outside_tail) | mips_outside_tail[msb]) // if mips_outside_tail is -ve, then in_tail_chk is true, mips_outside_tail[msb] only use mips_outside_tail's msb bit, only 1 bit

​	end

endgenerate


// -----------------------------------------------------------------------------
// Analysis: `in_tail_chk`
//
// 这一项只负责“tail 数量容量”这个条件，对应：
//     numMipsToTheEnd <= maxNumMipsInTail
// 它还不能独立决定 in_miptail；真正的 tail 判定还必须结合 W/H 尺寸条件。
// 对负的 mips_outside_tail，MSB 让所有 mip 通过这一层数量检查。
// -----------------------------------------------------------------------------

//Since no VAR mode, swtich back to the 10.1 design with addition of 256KB.

//i.e. only need to look at SW_TYPE[0], which is set for 4KB and 256KB

// -----------------------------------------------------------------------------
// Analysis: `y_bias_intail`
//
// tail 的二维 orientation 并非永远相同。这里对特定 3D block 类型切换
// width/height 的 bias，后面的 tail 尺寸判定因此有两种方向：
//   normal: Wb <= 1, Hb <= 2
//   y-bias: Wb <= 2, Hb <= 1
// -----------------------------------------------------------------------------
y_bias_intail = (sw_type == `SW_S_3D) & (blk_type[0] == 1'b1)

//special case, where in_tail condition is handled differently

//convert mip0 width/height to padded width/height. Padding based on blk_type


function pad_to_log2sz_gc (input dim_in, input l2_pad_sz_in, output pad_out)
{

//total "after padding" bits required depends on what is the minimum size of the padding supported

//pads to atleast on block

//in some cases, user can pass 'PAD_WIDTH' to override this

// -----------------------------------------------------------------------------
// Analysis: `pad_to_log2sz_gc`
//
// 该函数本质上执行：
//     ceil(dim_in / 2^l2_pad_sz_in)
// 即把实际尺寸换算成“需要多少个 block”，不足一个 block 时向上取整。
// -----------------------------------------------------------------------------
pad_sz_mask = (1'b1 << l2_pad_sz_in) - 1'b1

pad_out = ((dim_in >> L2_pad_sz_in + |(dim_in & pad_sz_mask))

}

// -----------------------------------------------------------------------------
// Analysis: mip0 的 block geometry
//
// Wb0 / Hb0 是 mip0 在正常 block granularity 下的 block 数；
// Wb_slice0 则是 slice-size 统计所使用的 width granularity。
// 后续所有 mip 的 Wb/Hb 都以这些“已经按 block 对齐的 mip0 尺寸”为基础。
// -----------------------------------------------------------------------------
Wb0 = pad_to_log2sz_gc(map0_w, l2_blk_w)

Hb0 = pad_to_log2sz_gc(map0_h, l2_blk_h)

Wb_slice0 = pad_to_log2sz_gc(map0_w, l2_blk_w_slice)



pad_data_sz_w = 1'b1 << l2_blk_w

pad_data_sz_h = 1'b1 << l2_blk_h



//S1 stage

//calculate padded width/height for remaining mip levels

//determine which mip levels are in the tail

//get mip index of lowest mip level in miptail

//calculate mipsize at each mip level

//begin pre-computing mip_offset and slice_b(for timing)



generate

​	for(m=1;MAXMIP;m=m+1) begin: W_H_block_calc

// -----------------------------------------------------------------------------
// Analysis: 每一级 mip 的 block 尺寸
//
// 这一写法等价于向上取整：
//     Wb[m]       = ceil(Wb0 / 2^m)
//     Hb[m]       = ceil(Hb0 / 2^m)
//     Wb_slice[m] = ceil(Wb_slice0 / 2^m)
// 低位 OR 用来检测右移后被丢掉的非零部分，从而实现 ceil 而非 floor。
// -----------------------------------------------------------------------------
​		assign Wb[m] = (Wb0 >> m) + |Wb0[\`PAD_W_MSB(m):0];

​		assign Hb[m] = (Hb0 >> m) + |Hb0[\`PAD_H_MSB(m):0];

​		assign Wb_slice[m] = (Wb_slice0 >> m) + |Wb_slice0[\`PAD_W_MSB(m):0]


///////////in_mip_tail///////////

// -----------------------------------------------------------------------------
// Analysis: 真正的 `in_miptail` 判定
//
// 这里同时检查三件事：
//   1) mip width 是否足够小；
//   2) mip height 是否足够小；
//   3) 从当前 mip 到 mip chain 尾部的级数是否不超过 tail capacity。
//
// 因此“尺寸小”并不是进入 tail 的唯一条件。
// -----------------------------------------------------------------------------
w_tail_sz = y_bias ? pad_sz_w : (pad_sz_w >> 1)

h_tail_sz = y_bias ? (pad_sz_h>>1) : pad_sz_h

in_miptail = (H<= h_tail_sz) & (W<= w_tail_sz) & in_tail_chk


generate

​	for(m=0;m<MAXMIP-1;m=m+1) begin: CHK_NEXT_IN_MIPTAIL

​		//y_bias_intail is special condition for checking in_tail

​		//in_tail_chk[m+1] is check if the mip is outside the number of levels that can fit inside a tail 

​		//next_in_tail[m+1]  //=1, if the next mip is inside the miptail

// -----------------------------------------------------------------------------
// Analysis: `CHK_NEXT_IN_MIPTAIL`
//
// 对下一级 mip 做增量判断。normal orientation 下要求 Hb<=2、Wb<=1；
// y-bias orientation 下交换为 Hb<=1、Wb<=2。这体现了 tail packing 的方向性。
// -----------------------------------------------------------------------------
​		height_in_tail = y_bias_intail ? (Hb[m] <=1) : (Hb[m]<=2);

​		width_in_tail = y_bias_intail ? (Wb[m] <=2) : (Wb[m]<=1);

​		in_miptail[m+1] = next_in_tail[m+1] = height_in_tail && width_in_tail && in_tail_chk[m+1]

​	end

endgenerate



//////////////tail_mipid_calc///////////////

//set the tail mipid to max to indicate no tails are supported

// -----------------------------------------------------------------------------
// Analysis: `tail_mipid`
//
// tail_mipid_raw 是由 in_miptail 的 0->1 transition 检出的候选起点；
// 最终 `tail_mipid` 还要受 surface/swizzle mode 限制。对于 linear 和
// SW_*_256B，这份 RTL 明确把它们作为“不支持 mip tail”的情况处理，
// 用 MAXMIP 表示无 tail。
// -----------------------------------------------------------------------------
assign tail_mipid = ((maxmip == 0) | ((l2_ms_128B>>1) == 0) ? MAXMIP : tail_mipid_raw) // linear and SW_\\*_256B are treated  same - no miptails

tail_mipid_raw = {MAXMIP} // no tail

// -----------------------------------------------------------------------------
// Analysis: 查找 first mip in tail
//
// 后面的 XOR：
//     in_miptail[i] ^ in_miptail[i-1]
// 用来寻找 0->1 transition，从而得到第一个进入 tail 的 mip level，
// 对应公开 AddrLib 的 `firstMipIdInTail` 概念。
// -----------------------------------------------------------------------------
for(i=0; i<MAXMIP; i++) begin

​	if(i==0) begin if(in_miptail[i]) tail_mipid_raw = i; end

​	else begin if(in_miptail[i]^in_miptail[i-1]) tail_mipid_raw = i; end

end


for (int mip_idx=MAXMIP-1;mip_idx >=6; --mip_idx) begin

// -----------------------------------------------------------------------------
// Analysis: `mipsize[m]` 的特殊 tail 语义
//
// `mipsize` 是 surface-layout 层面的 block footprint，并不是简单的 pixel 数。
// tail 起点被折叠为一个 packed tail region，因此：
//   mip < tail_mipid : 计算各自独立 footprint
//   mip == tail_mipid: 记作 1 个 tail region
//   mip > tail_mipid : 记作 0（已经包含在该 tail region 内）
// 注意：这里不是说 tail 中每个 mip 都只占 1 block，而是说在更高一级的
// surface footprint 统计中，整个 packed tail 以一个 region 表示。
// -----------------------------------------------------------------------------
​	if(mip_idx > tail_mipid) begin

​		mipsize[mip_idx] = 'd0;

​	end else if ((mip_idx==tail_mipid) || (mip_idx == (MAXMIP-1))) begin

​		mipsize[mip_idx] = 'd1;

​	end else begin

​		mipsize[mip_idx] = Wb_slice[mip_idx] * Hb[mip_idx];

​	end

end


//TIMING_FIX: break into smaller terms and pre-compute mip_offset_b and slice_b additions

// -----------------------------------------------------------------------------
// Analysis: mip masks
//
// mip_mask 生成 bit0..bit(mip_level)=1 的范围；maxmip_mask 生成有效 mip
// chain 的范围。它们随后用于选择参与 slice 与 mip offset 累加的 mip footprint。
// -----------------------------------------------------------------------------
assign mip_mask = ((1'b1<<(mip_level + 4'd1)) - 1'b1); //for SLICE_CALC, ignore mip

maxmip_mask = ((1'b1)<<(maxmip + 4'd1) - 1b1); 

slice_input_en = maxmip_mask; // no miptails for linear case 

// -----------------------------------------------------------------------------
// Analysis: `mip_off_input_en` 的注意事项
//
// 从纯 bit-mask 数学看，这里选择的是 current mip 之后的 mip。
// 但如果把 `mip_offset_in_blks` 直接解释成传统意义上的“当前 mip 起始地址”，
// 通常又会期待累加 current mip 之前的 mip。因此，仅凭当前抽取片段不能武断
// 确定其最终方向；需要结合后续完整 address-generation 使用方式继续验证。
// 原因可能是：RTL 抽取时方向被简化、`mip_offset` 的定义不同，或还有未保留
// 的控制逻辑。
// -----------------------------------------------------------------------------
mip_off_input_en = slice_input_en & ~mip_mask; //no miptails for linear case



//S2 stage: compute outputs

pitch = Wb[mip_level] << l2_blk_w;


for (int mip_idx=5; mip_idx>=0; --mip_idx) begin

​	if (mip_idx > tail_mipid) begin

​		mipsize[mip_idx] = 'd0

​	end else if ((mip_idx == tail_mipid)) begin

​		mipsize[mip_idx] = 'd1

​	end else begin

​		mipsize[mip_idx] = Wb_slice[mip_idx] * Hb[mip_idx]

​	end

end

// -----------------------------------------------------------------------------
// Analysis: `mip_offset_in_blks`
//
// 这里在统一的 block footprint 单位中累加 mip_size，随后再通过
// `l2_mip_offset` 把这个中间值转换到当前 block-size 地址尺度。
// 由于上面的 `mip_off_input_en` 方向存在待确认点，这里的“它具体表示
// 当前 mip 之前还是之后的 region”也应该保持为开放问题，直到完整地址生成
// 逻辑闭环以后再下最终结论。
// -----------------------------------------------------------------------------
mip_offset_in_blks = (mip_off_input_en[16] ? mip_size[16] : 'd0) + 

​				     (mip_off_input_en[15] ? mip_size[15] : 'd0) + 

​				     (mip_off_input_en[14] ? mip_size[14] : 'd0) + 

​				     (mip_off_input_en[13] ? mip_size[13] : 'd0) + 

​				     (mip_off_input_en[12] ? mip_size[12] : 'd0) + 

​				     (mip_off_input_en[11] ? mip_size[11] : 'd0) + 

​				     (mip_off_input_en[10] ? mip_size[10] : 'd0) + 

​				     (mip_off_input_en[9] ? mip_size[9] : 'd0) + 

​				     (mip_off_input_en[8] ? mip_size[8] : 'd0) + 

​				     (mip_off_input_en[7] ? mip_size[7] : 'd0) + 

​				     (mip_off_input_en[6] ? mip_size[6] : 'd0);

// -----------------------------------------------------------------------------
// Analysis: `slice_b`
//
// 这是整个有效 mip chain 的 aggregate block footprint：
//     slice_b = Σ(enabled mip mipsize[m])
// 对存在 tail 的情况，tail 在这一层已经通过 `mipsize[tail_mipid]=1` 被
// 折叠成一个共享 region，tail 后面的 mip 不再重复计入。
// -----------------------------------------------------------------------------
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

​		 (slice_input_en[6] ? mipsize[6] : 'd0) ;

mip_offset _in_blks = mip_offset_in_blks + 

​					(mip_off_en[1] ? mipsize[1] : 'd0) + 

​					 (mip_off_en[2] ? mipsize[2] : 'd0) + 

​					 (mip_off_en[3] ? mipsize[3] : 'd0) + 

​					 (mip_off_en[4] ? mipsize[4] : 'd0) +

​					 (mip_off_en[5] ? mipsize[5] : 'd0) ;

slice_b = slice_b + 

​		(slice_input_en[0] ? mipsize[0] : 'd0) + 

​		 (slice_input_en[1] ? mipsize[1] : 'd0) + 

​		 (slice_input_en[2] ? mipsize[2] : 'd0) + 

​		 (slice_input_en[3] ? mipsize[3] : 'd0) + 

​		 (slice_input_en[4] ? mipsize[4] : 'd0) + 

​		 (slice_input_en[5] ? mipsize[5] : 'd0) ;

// -----------------------------------------------------------------------------
// Analysis: `slice_out`
//
// 把 slice_b 的 block count 换算回对应的 element/byte footprint；这里的
// shift 使用 slice width granularity 与 block height 的组合指数。
// -----------------------------------------------------------------------------
slice_out = slice_b << ({1'b0, l2_blk_w_slice} + {1'b0, l2_blk_h});

pitch_out = pitch;

// -----------------------------------------------------------------------------
// Analysis: `mip_offset_b_out`
//
// 这是 mip offset 从统一 block 单位转换到当前 block-size 地址尺度的最后一步：
//     mip_offset_b_out = mip_offset_in_blks << l2_mip_offset
// 其中 l2_mip_offset 表示相对于 256B 基准需要额外增加的尺度位数。
// -----------------------------------------------------------------------------
mip_offset_b_out = mip_offset_in_blks << l2_mip_offset;

// -----------------------------------------------------------------------------
// Analysis: `mip_in_tail_out`
//
// 如果当前 mip 在 tail 之前，则输出 MAXMIP 作为“无有效 tail-relative index”
// 的标记；进入 tail 后，输出相对于 `tail_mipid` 的 level index：
//     mip_in_tail = mip_level - tail_mipid
// 这说明 tail_mipid 不仅用于 footprint 折叠，也直接参与 tail 内 mip 的相对编号。
// -----------------------------------------------------------------------------
mip_in_tail_out = (mip_level < tail_mipid) ? {MAXMIP} : (mip_level - tail_mipid);

l2_blk_width_out = l2_blk_w;

l2_blk_height_out = l2_blk_h;

l2_blk_depth_out = l2_blk_d;

l2_ms_out = l2_ms


// ============================================================================
// Analysis: 这段 RTL 与 GFX10 MipTail 的统一理解
//
// 可以把整个流程概括为：
//
//     block/swizzle parameters
//              |
//              v
//        Wb0 / Hb0 / Wb_slice0
//              |
//              v
//      每级 mip 的 ceil(/2^m)
//              |
//              +------------------+
//              |                  |
//              v                  v
//       tail size condition   tail capacity condition
//              |                  |
//              +--------+---------+
//                       v
//                 in_miptail[m]
//                       |
//                       v
//                  tail_mipid
//                       |
//              +--------+---------+
//              |                  |
//              v                  v
//       independent mip      packed tail region
//       footprint            (mipsize = 1)
//              |                  |
//              +--------+---------+
//                       v
//             mip offset / slice footprint
//                       |
//                       v
//              final address-scale outputs
//
// 最重要的一点：tail 是一个“surface layout 层面的 packed region”，而不是
// 简单的 linear append。对 tail 内具体 texel 地址的 swizzle / address equation
// 仍需结合完整 GFX10 address-generation 逻辑单独分析。
// ============================================================================
