'use strict';
// Independent PAL V2 transcription. No document/V3 imports. See SOURCES.md.
// MAP identifies layout branches, not address-swizzle equivalence.
const MAP={SW_LINEAR:['ADDR_SW_LINEAR',8,false],SW_256B_2D:['ADDR_SW_256B_D',8,false],
 SW_4KB_2D:['ADDR_SW_4KB_D',12,false],SW_64KB_2D:['ADDR_SW_64KB_R_X',16,false],
 SW_4KB_3D:['ADDR_SW_4KB_S',12,true],SW_64KB_3D:['ADDR_SW_64KB_S',16,true]};
function eligibility(i) {
 if(!MAP[i.mode]) return {status:'no_equivalent',reason:'Fixed 256KB is not GFX10 VAR'};
 if(i.maxmip>15) return {status:'reference_rejected',reason:'V2 MaxMipLevels=16; mip index 16 outside contract'};
 if(i.s>0&&(i.maxmip>0||MAP[i.mode][2]||i.mode==='SW_LINEAR'))
  return {status:'reference_rejected',reason:'MSAA requires single-level 2D tiled resource'};
 if(i.s>0&&(i.mode==='SW_256B_2D'||i.mode==='SW_4KB_2D'))
  return {status:'reference_rejected',reason:'256B/4KB display swizzle does not support MSAA'};
 return {status:'comparable',mapping:MAP[i.mode][0]};
}
function block(i) {
 const [,L,thick]=MAP[i.mode],linear=i.mode==='SW_LINEAR';
 let logs;
 if(linear) logs=[8-i.e,0,0];
 else if(thick) {
  // addrlib2.cpp:48,1758: expand Block1K_3d, independently of the document table.
  const micro=[[16,8,8],[8,8,8],[8,8,4],[8,4,4],[4,4,4]][i.e];
  const amp=Math.floor((L-10)/3),rem=(L-10)%3;
  logs=[Math.log2(micro[0])+amp,Math.log2(micro[1])+amp+Math.floor(rem/2),
   Math.log2(micro[2])+amp+Number(rem!==0)];
 } else {
  // addrlib2.cpp:1680 ComputeThinBlockDimension.
  const n=L-i.e-i.s,preferWidth=i.s%2===0||L%2!==0,w=Math.floor((n+Number(preferWidth))/2);
  logs=[w,n-w,0];
 }
 return {L,thick,linear,ns:i.s,logs,bws:logs[0]};
}
function capacity(b) {
 if(b.L<=8) return null; // No tail-capacity API calculation for Linear/MicroTiled.
 let effective=b.L;
 if(b.thick) effective-=Math.floor((b.L-8)/3);
 return effective<=11?1+2**(effective-9):effective-4;
}
function mipDims(i,m) {return [Math.ceil(i.W/2**m),Math.ceil(i.H/2**m)];}
function firstTail(i,b,cap) {
 const dims=b.logs.map(v=>2**v);
 if(b.thick) dims[b.L%3===0?1:b.L%3===1?0:2]/=2; else dims[0]/=2;
 let first=17;
 if(b.L>8&&i.maxmip>0) for(let m=0;m<=i.maxmip;m++) {
  const [w,h]=mipDims(i,m);
  if(w<=dims[0]&&h<=dims[1]&&i.maxmip+1-m<=cap) {first=m;break;}
 }
 return {first,threshold:dims.slice(0,2)};
}
const align=(v,a)=>Math.ceil(v/a)*a;
function surface(i,overrides={}) {
 const b=overrides.block||block(i),cap=overrides.capacity??capacity(b),tail=firstTail(i,b,cap);
 const first=overrides.first??tail.first,dims=b.logs.map(v=>2**v),unit=BigInt(2**i.e),samples=BigInt(2**i.s);
 const pitch=[],height=[],slicePitch=[],bytesPerMip=[],macroBlockOffset=[],mipSizes=[];
 let sliceSize=0n;
 for(let m=0;m<=i.maxmip;m++) {
  const wh=mipDims(i,m);mipSizes.push(wh);
  const p=align(wh[0],dims[0]),h=align(wh[1],dims[1]);
  pitch.push(p);height.push(h);slicePitch.push(p);
  let bytes=0n;
  if(m<first) {
   if((b.L===8)&&!b.linear&&(i.maxmip>0)) {
    // ComputeSurfaceInfoMicroTiled adds a UINT_32 product to UINT_64.
    // Preserve the C++ intermediate wrap instead of widening every operand.
    const product=(Math.imul(Math.imul(p,h),2**i.e))>>>0;
    bytes=BigInt(product);
   } else bytes=BigInt(p)*BigInt(h)*unit*(i.maxmip===0?samples:1n);
  }
  else if(m===first) bytes=BigInt(2**b.L)/BigInt(dims[2]);
  bytesPerMip.push(bytes);sliceSize+=bytes;
 }
 // Macro offsets advance by a block-depth slab, not the entire volume.
 let off=first<=i.maxmip?BigInt(2**b.L):0n;
 for(let m=Math.min(first-1,i.maxmip);m>=0;m--) {
  macroBlockOffset[m]=off;off+=bytesPerMip[m]*BigInt(dims[2]);
 }
 if(first<=i.maxmip) {
  let p=tail.threshold[0],h=tail.threshold[1];
  const micro=b.thick?[[8,4,8],[4,4,8],[4,4,4],[4,2,4],[2,2,4]][i.e]:
   [[16,16],[16,8],[8,8],[8,4],[4,4]][i.e];
  for(let m=first;m<=i.maxmip;m++) {
   pitch[m]=p;height[m]=h;slicePitch[m]=p;macroBlockOffset[m]=0n;
   p=Math.max(Math.floor(p/2),micro[0]);h=Math.max(Math.floor(h/2),micro[1]);
  }
 }
 return {b,cap,first,firstMipIdInTail:first===17?i.maxmip+1:first,threshold:tail.threshold,
  pitch,height,slicePitch,bytesPerMip,mipSizes,macroBlockOffset,sliceSize,blockDimensions:dims};
}
module.exports={MAP,eligibility,block,capacity,firstTail,mipDims,surface};
