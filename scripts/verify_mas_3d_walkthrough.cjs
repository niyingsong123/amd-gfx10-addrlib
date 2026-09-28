'use strict';
// Finite checks and shared data for the single 3D Markdown walkthrough.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('assert/strict');
const model = require('./mipmap_compare/document.cjs');
const {bitTable, mapBits, origin, access} = require('./verify_mas_examples.cjs');
const root = path.resolve(__dirname, '..');
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(path.join(root, p))).digest('hex');
const input = {mode: 'SW_256KB_3D', W: 250, H: 180, D: 1537, e: 0, s: 0, maxmip: 10};
const surface = model.surface(input), table = bitTable(input.mode);
const visit = access(input, surface, table, 4, [5, 6, 69]);
const ceil = (n, d) => Math.floor(n/d) + Number(n%d !== 0);
assert.deepEqual(surface.b.logs, [6,6,6]);
assert.equal(surface.cap, 11); assert.equal(surface.first, 3);
assert.equal(surface.slice, 73728n);
assert.equal(visit.blk_index, 0x480000n);
assert.equal(visit.blk_offset, 0x81d5n);
assert.equal(visit.address_final, 0x304881d5n);
assert.deepEqual(visit.origin.xyz, [32,0,0]);
assert.equal(table.length, 18);
assert.equal(new Set(table.map(([a,b]) => a+b)).size, 18);
for (const a of ['x','y','z']) for (let b=0;b<6;b++) assert(table.some(t=>t[0]===a&&t[1]===b));

const rows = [];
for (let m=0;m<=input.maxmip;m++) {
  const dimensions = [input.W,input.H,input.D].map(d=>Math.max(1, Math.floor(d/2**m)));
  const blockXY = [ceil(ceil(input.W,64),2**m),ceil(ceil(input.H,64),2**m)];
  const expectedSize = m>3?0:m===3?1:blockXY[0]*blockXY[1];
  assert.equal(surface.sizes[m], BigInt(expectedSize));
  assert.equal(surface.pitch[m],blockXY[0]*64);
  const o=origin(input,surface,m);
  const zGroups=ceil(dimensions[2],64);
  const offsetBytes=Number(surface.offset[m]<<8n);
  const suffix=surface.sizes.slice(m+1,input.maxmip+1).reduce((a,b)=>a+b,0n);
  assert.equal(BigInt(offsetBytes),suffix*0x40000n);
  rows.push({mip:m, logical_dimensions:dimensions, block_xy:blockXY, z_groups:zGroups,
    aligned_dimensions:[blockXY[0]*64,blockXY[1]*64,zGroups*64],
    pitch:surface.pitch[m], contribution:expectedSize,
    macro_offset_256B:Number(surface.offset[m]), macro_offset_bytes:offsetBytes,
    in_tail:m>=3, relative_tail:m>=3?m-3:17,
    origin:o.xyz, reverse:o.reverse, code:Number(o.code), micro_coordinates:o.microCoordinates});
}
const chainBlocks=rows.reduce((n,r)=>n+r.contribution,0);
const stride=chainBlocks*0x40000;
assert.equal(chainBlocks,18);assert.equal(stride,0x480000);
assert.equal(Math.floor(Math.log2(Math.max(input.W,input.H,input.D))),input.maxmip);
assert(visit.xyz.every((v,a)=>v>=0&&v<rows[4].logical_dimensions[a]));

// Check every valid tail texel, including tail levels spanning several Z groups.
const lut={};
for(const a of ['x','y','z']) lut[a]=Array.from({length:64},(_,n)=>Number(mapBits(table,{x:0,y:0,z:0,s:0,[a]:n})));
const occupied=new Set(); let tailTexels=0;
const groupCounts={};
for(const r of rows.filter(r=>r.in_tail)) {
  const [w,h,d]=r.logical_dimensions,[ox,oy,oz]=r.origin;
  assert(ox+w<=64&&oy+h<=64&&oz===0);
  for(let z=0;z<d;z++) for(let y=0;y<h;y++) for(let x=0;x<w;x++) {
    const g=Math.floor(z/64);
    const inBlock=lut.x[x+ox]|lut.y[y+oy]|lut.z[z%64];
    const relative=g*stride+inBlock;
    assert(relative>=g*stride&&relative<(g*stride+0x40000));
    assert(!occupied.has(relative),`tail overlap at mip${r.mip} (${x},${y},${z})`);
    occupied.add(relative);tailTexels++;
    groupCounts[g]=(groupCounts[g]||0)+1;
  }
}
assert.equal(occupied.size,tailTexels);
assert(occupied.has(Number(visit.address_final-0x30000000n)));

// A bijective 18-bit mapping plus disjoint macro slots proves no ordinary
// block crosses its slot; check valid corners against the full address path.
const usedSlots=new Set(); let checkedCorners=0;
for(const r of rows.filter(r=>!r.in_tail)) {
  const [w,h,d]=r.logical_dimensions;
  for(let zb=0;zb<r.z_groups;zb++) for(let yb=0;yb<r.block_xy[1];yb++) for(let xb=0;xb<r.block_xy[0];xb++) {
    const slot=zb*18+r.macro_offset_bytes/0x40000+yb*r.block_xy[0]+xb;
    assert(!usedSlots.has(slot));usedSlots.add(slot);
    const ranges=[[xb*64,Math.min(w-1,xb*64+63)],[yb*64,Math.min(h-1,yb*64+63)],[zb*64,Math.min(d-1,zb*64+63)]];
    for(const x of new Set(ranges[0])) for(const y of new Set(ranges[1])) for(const z of new Set(ranges[2])) {
      const a=access(input,surface,table,r.mip,[x,y,z]);
      const relative=Number(a.address_final-0x30000000n);
      assert(Math.floor(relative/0x40000)===slot);checkedCorners++;
    }
  }
}
for(const g of Object.keys(groupCounts).map(Number)) assert(!usedSlots.has(g*18));
const low=access(input,surface,table,4,[5,6,63]);
const high=access(input,surface,table,4,[5,6,64]);
assert.equal(low.zb,0n);assert.equal(high.zb,1n);
const boundary={macro_index:[3,2,24], origin:[192,128,1536],effective_dimensions:[58,52,1],
  aligned_dimensions:[64,64,64],padding:[6,12,63]};
const result={status:'derived teaching example; not a trusted baseline',
  sources:Object.fromEntries(['ADDRLIB.md','scripts/mipmap_compare/document.cjs','scripts/verify_mas_examples.cjs',
    'scripts/verify_mas_3d_walkthrough.cjs'].map(p=>[p,hash(p)])), input,base_bytes:'0x30000000',seed:0,
  macro_dimensions:[64,64,64],macro_bytes:0x40000,micro_dimensions:[8,4,8],
  first_tail_mip:3,tail_capacity:11,chain_blocks_per_z_group:18,chain_stride_bytes:stride,
  slice_raw:Number(surface.slice),mips:rows,visit,boundary,
  selected_outputs:model.outputs(surface,4),bit_mapping_msb_first:table.map(([a,b])=>a+b),
  checks:{tail_texels:tailTexels,tail_address_collisions:0,tail_texels_per_z_group:groupCounts,
    ordinary_macro_slots:usedSlots.size,ordinary_corners:checkedCorners,bit_mapping_is_permutation:true,
    z_boundary:[low,high].map(a=>({z:a.xyz[2],zb:a.zb,address:a.address_final})),
    scope:'Every valid tail texel and ordinary macro corners of this configuration; no upstream C++, RTL, timing or broad random comparison'},
  units:{coordinates:'elements local to selected mip',slice:'XY element positions of the mip chain',
    mip_offset_b:'256 bytes',blk_index:'bytes',blk_offset:'bytes'},
  assumptions:['MAXMIP=17; finite requested mip0..10; positive ordinary uncompressed dimensions',
    'Logical dimensions max(1,floor(base/2^m)); layout still uses Wb0/Hb0 recurrence',
    'Layout ignores depth; depth bounds accesses, not upstream exact allocation size',
    'BPE1, one sample, zero seed, selected base low field zero',
    'Signed 7-bit reverse, 20-bit origin code, 10-bit X/Y origins; 48-bit byte address, 40-bit base, 12-bit low base field',
    'Unspecified intermediate widths use sufficient integers; products and addresses use BigInt',
    'Stage ownership only; no register scheduling model']};
const out=path.join(root,'docs/ADDRLIB_MAS_3D_WALKTHROUGH_CHECK.json');
fs.writeFileSync(out,JSON.stringify(result,(_,v)=>typeof v==='bigint'?v.toString():v,2)+'\n');
console.log(JSON.stringify({input,tailTexels,ordinaryMacroSlots:usedSlots.size,checkedCorners,
  blk_index:'0x'+visit.blk_index.toString(16),blk_offset:'0x'+visit.blk_offset.toString(16),
  address:'0x'+visit.address_final.toString(16),output:out},null,2));
