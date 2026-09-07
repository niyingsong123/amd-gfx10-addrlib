
ADDRLIB

//////////////////////////module definition/////////////////////////

module mipmap_param_calc_core_gc

input map0_w_minus_1;
input map0_h_minus_1;
input map0_d_minus_1;
input sw_mode;
input log2_num_samples;
input log2_element_bytes;
input mip_level;
input maxmip;
output pitch;
output slice;
output mip_in_tail;
output mip_offset_b;
output l2_ms;
output l2_data_blk_width;
output l2_data_blk_height;
output l2_data_blk_depth;

//变量含义
map0_w //mipmap0 width -1 for non_TC/padded sclaed width for TC
map0_h //mipmap0 height -1 for non_TC/padded sclaed height for TC
map0_d //mipmap0 depth -1 for non_TC/padded sclaed depth for TC
l2_eb //log2_element_bytes //0:1byte 1:2byte 2:4byte 3:8 bytes 4:16byte
log2_num_samples // specifies the log2 of 'the number of samples', for non-MSAA hardware, tie 0 0: 1sample 1: 2samples 2: 4samples 3: 8samples
pitch //padded_width - 1 no of elements
slice //(padded_width * padded_ht) - 1, no of elements

\`define PAD_W_MSB(mip) ((mip < W0_B_WIDTH) ? (mip-1) : (W0_B_WIDTH-1))
\`define PAD_H_MSB(mip) ((mip < H0_B_WIDTH) ? (mip-1) : (H0_B_WIDTH-1))

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
dim3D = (sw_type == \`SW_S_3D)
msaa = （dim3D | linear）？ 2‘d0 ：l2_ns
block_size_elements = l2_ms - (l2_eb + msaa_cnt)

if {linear, sw_type} == {1'b0, \`SW_D_2D}
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
else if {linear, sw_type} == {1'b0, \`SW_S_3D}
{
​	l2_blk_w = sheet(l2_ms[4:1] l2_eb[2:0]) //看下面表格
​	l2_blk_h = sheet(l2_ms[4:1] l2_eb[2:0]) //看下面表格
​	l2_blk_d = sheet(l2_ms[4:1] l2_eb[2:0]) //看下面表格

| macro size, element size | l2_ms[4:1] l2_eb[2:0] | l2_blk_w_3d | l2_blk_h_3d | l2_blk_d_3d |
| ------------------------ | --------------------- | ----------- | ----------- | ----------- |
| 4KB, 8bpp                | 4'b0110, 3'd0         | 4 (16)      | 4 (16)      | 4 (16)      |
| 4KB, 16bpp               | 4'b0110, 3'd1         | 3 (8)       | 4 (16)      | 4 (16)      |
| 4KB, 32bpp               | 4'b0110, 3'd2         | 3 (8)       | 4 (16)      | 3 (8)       |
| 4KB, 64bpp               | 4'b0110, 3'd3         | 3 (8)       | 3 (8)       | 3 (8)       |
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
//fix for 128B pitch alignment
//slice must still be calculated at 256B alignment, so use this forslice calculations
l2_blk_w_slice = (linear && (l2_blk_w < 'd8)) ? ('d8 - l2_eb) : ll2_blk_w; //256B align
l2_ms_256B = (l2_ms_128B=='d0) ? 'd0 : (l2_ms_128B - 1) // log 256B align
l2_mip_offset = (l2_ms < 5'd8) ? 5'd0 : l2_ms - 5'd8
//prevent underflow in sw_linear case

/////////function al_num_mips_inside_tail////////////
function (input l2_ms_256B, input sw_type, output num_mips_in_tail)
{
​	is_3d_blk_size = (sw_type == `SW_S_3D) //no always the same as dim_type == `dim_3D
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
​	4'd4, 4'd6, 4'd7, 4'd8, 4'd9, 4'd10, 4'd11, 4'd12: num_mips_in_tail = (l2_ms_256B_eff + 4'd4) // (((effecttive_block_size_log2_256B + 8) - 11) + 7) => (l2_ms_256B_eff + 4'd4)
}
num_mips_in_tail = al_num_mips_inside_tail(l2_ms_256B, sw_type)

//you can fit only some number of mips inside a tail, everything else will be outside
//this condition needs to be in conjunction with the mipsizes check
mips_outside_tail = (maxmip_in - mips_in_tail) //extra bit to allow for negative result
generate
​	for (m=0; m<MAXMIP:m=m+1) begin
​		assign in_tail_chk[m] = ((m > mips_outside_tail) | mips_outside_tail[msb]) // if mips_outside_tail is -ve, then in_tail_chk is true, mips_outside_tail[msb] only use mips_outside_tail's msb bit, only 1 bit
​	end
endgenerate

//Since no VAR mode, swtich back to the 10.1 design with addition of 256KB.
//i.e. only need to look at SW_TYPE[0], which is set for 4KB and 256KB
y_bias_intail = (sw_type ==`SW_S_3D) & (blk_type[0] == 1'b1)
//special case, where in_tail condition is handled differently
//convert mip0 width/height to padded width/height. Padding based on blk_type

function pad_to_log2sz_gc (input dim_in, input l2_pad_sz_in, output pad_out)
{
//total "after padding" bits required depends on what is the minimum size of the padding supported
//pads to atleast on block
//in some cases, user can pass 'PAD_WIDTH' to override this
pad_sz_mask = (1'b1 << l2_pad_sz_in) - 1'b1
pad_out = ((dim_in >> L2_pad_sz_in + |(dim_in & pad_sz_mask))
}
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
​		assign Wb[m] = (Wb0 >> m) + |Wb0[\`PAD_W_MSB(m):0];
​		assign Hb[m] = (Hb0 >> m) + |Hb0[\`PAD_H_MSB(m):0];
​		assign Wb_slice[m] = (Wb_slice0 >> m) + |Wb_slice0[\`PAD_W_MSB(m):0]

///////////in_mip_tail///////////
w_tail_sz = y_bias ? pad_sz_w : (pad_sz_w >> 1)
h_tail_sz = y_bias ? (pad_sz_h>>1) : pad_sz_h
in_miptail = (H<= h_tail_sz) & (W<= w_tail_sz) & in_tail_chk

generate
​	for(m=0;m<MAXMIP-1;m=m+1) begin: CHK_NEXT_IN_MIPTAIL
​		//y_bias_intail is special condition for checking in_tail
​		//in_tail_chk[m+1] is check if the mip is outside the number of levels that can fit inside a tail
​		//next_in_tail[m+1]  //=1, if the next mip is inside the miptail
​		height_in_tail = y_bias_intail ? (Hb[m] <=1) : (Hb[m]<=2);
​		width_in_tail = y_bias_intail ? (Wb[m] <=2) : (Wb[m]<=1);
​		in_miptail[m+1] = next_in_tail[m+1] = height_in_tail && width_in_tail && in_tail_chk[m+1]
​	end
endgenerate

//////////////tail_mipid_calc///////////////
//set the tail mipid to max to indicate no tails are supported
assign tail_mipid = ((maxmip == 0) | ((l2_ms_128B>>1) == 0) ? MAXMIP : tail_mipid_raw) // linear and SW_*_256B are treated same - no miptails
tail_mipid_raw = {MAXMIP} // no tail
for(i=0; i<MAXMIP; i++) begin
​	if(i==0) begin if(in_miptail[i]) tail_mipid_raw = i; end
​	else begin if(in_miptail[i]^in_miptail[i-1]) tail_mipid_raw = i; end
end

for (int mip_idx=MAXMIP-1;mip_idx >=6; --mip_idx) begin
​	if(mip_idx > tail_mipid) begin
​		mipsize[mip_idx] = 'd0;
​	end else if ((mip_idx==tail_mipid) || (mip_idx == (MAXMIP-1))) begin
​		mipsize[mip_idx] = 'd1;
​	end else begin
​		mipsize[mip_idx] = Wb_slice[mip_idx] * Hb[mip_idx];
​	end
end

//TIMING_FIX: break into smaller terms and pre-compute mip_offset_b and slice_b additions
assign mip_mask = ((1'b1<<(mip_level + 4'd1)) - 1'b1); //for SLICE_CALC, ignore mip
assign maxmip_mask = ((1'b1)<<(maxmip + 4'd1) - 1b1);
slice_input_en = maxmip_mask; // no miptails for linear case
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
​		 (slice_input_en[6] ? mipsize[6] : 'd0);

mip_offset_in_blks = mip_offset_in_blks +
​					(mip_off_en[1] ? mipsize[1] : 'd0) +
​					 (mip_off_en[2] ? mipsize[2] : 'd0) +
​					 (mip_off_en[3] ? mipsize[3] : 'd0) +
​					 (mip_off_en[4] ? mipsize[4] : 'd0) +
​					 (mip_off_en[5] ? mipsize[5] : 'd0);

slice_b = slice_b +
​		(slice_input_en[0] ? mipsize[0] : 'd0) +
​		 (slice_input_en[1] ? mipsize[1] : 'd0) +
​		 (slice_input_en[2] ? mipsize[2] : 'd0) +
​		 (slice_input_en[3] ? mipsize[3] : 'd0) +
​		 (slice_input_en[4] ? mipsize[4] : 'd0) +
​		 (slice_input_en[5] ? mipsize[5] : 'd0);

slice_out = slice_b << ({1'b0, l2_blk_w_slice} + {1'b0, l2_blk_h});
pitch_out = pitch;
mip_offset_b_out = mip_offset_in_blks << l2_mip_offset;
mip_in_tail_out = (mip_level < tail_mipid) ? {MAXMIP} : (mip_level - tail_mipid);
l2_blk_width_out = l2_blk_w;
l2_blk_height_out = l2_blk_h;
l2_blk_depth_out = l2_blk_d;
l2_ms_out = l2_ms

////////////////////////module definition///////////////////////////
module calc_mip_inside_tail_xyz_orig
input l2_ms_odd;
input mip_in_tail;
input log2_element_bytes;
input log2_num_samples;
input sw_type;
input l2_data_block_size_128B;
output x_mip_in_tail_orig;
output y_mip_in_tail_orig;
output z_mip_in_tail_orig;

l2_data_block_size_256B = (l2_data_block_size_128B == 'd0) ? 'd0 : (l2_data_block_size_128B - 1);
num_mips_in_tail = num_mips_inside_tail(l2_data_block_size_256B, sw_type);
{l2_ublk_w, l2_ublk_h, l2_ublk_d} = micro_block_dim_calc(log2_element_bytes, sw_type, log2_num_samples);
function micro_block_dim_calc(input l2_eb, input sw_type, input l2_ns, output l2_blk_w, output l2_blk_h, output l2_blk_d)
{
​	block_bits = 4'(4'd8 - (l2_eb + l2_ns));
​	l2_2d_blk_w = block_bits[3:1] + block_bits[0];
​	l2_2d_blk_h = block_bits[3:1];
​	case(block_bits)
​	{
​		4'd4: q_3 = 1; r_3 = 1;
​		4'd5: q_3 = 1; r_3 = 2;
​		4'd6: q_3 = 2; r_3 = 0;
​		4'd7: q_3 = 2; r_3 = 1;
​		4'd8: q_3 = 2; r_3 = 2;
​	}
​	l2_3d_blk_d = q_3 + (r_3 > 0);
​	l2_3d_blk_w = q_3 + (r_3 > 1);
​	l2_3d_blk_h = {1'b0, q_3};
​	dim3D = (sw_type == \`SW_S_3D);
​	l2_blk_w = (dim3D) ? l2_3d_blk_w : l2_2d_blk_w;
​	l2_blk_h = (dim3D) ? l2_3d_blk_h : l2_2d_blk_h;
​	l2_blk_d = (dim3D) ? l2_3d_blk_d : 0;
}
mip_in_tail_reverse = (MAXMIP_WIDTH+2)'(num_mips_in_tail - (mip_in_tail + 1));
if(mip_in_tail_reverse[MAXMIP_WIDTH+1])
​	{byte_offset = 0;}
else if(mip_in_tail_reverse > 'd6)
​	{byte_offset = (MSB_BYTE_OFFSET+1)'(5'd16 << mip_in_tail_reverse[MAXMIP_WIDTH+1:0]);}
else
​	{byte_offset = (MSB_BYTE_OFFSET+1)'(mip_in_tail_reverse[MAXMIP_WIDTH+1:0] << 4'd8);}
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
x_mip_micro_block_final = (l2_ms_odd) ? y_mip_micro_blocks; x_mip_micro_blocks;
y_mip_micro_block_final = (l2_ms_odd) ? x_mip_micro_blocks; y_mip_micro_blocks;
x_mip_in_tail_orig = 10'(x_mip_micro_block_final << l2_ublk_w);
y_mip_in_tail_orig = 10'(y_mip_micro_block_final << l2_ublk_h);
z_mip_in_tail_orig = 'd0;
return;
