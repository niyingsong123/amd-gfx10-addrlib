'use strict';
// Independent PAL V3, ADDR_GFX12_SHARED_BUILD=0. No document/V2 imports.
// Default flags; no custom pitch/height. See SOURCES.md.
const MAP={SW_LINEAR:['ADDR3_LINEAR',8,false],SW_256B_2D:['ADDR3_256B_2D',8,false],
 SW_4KB_2D:['ADDR3_4KB_2D',12,false],SW_64KB_2D:['ADDR3_64KB_2D',16,false],
 SW_256KB_2D:['ADDR3_256KB_2D',18,false],SW_4KB_3D:['ADDR3_4KB_3D',12,true],
 SW_64KB_3D:['ADDR3_64KB_3D',16,true],SW_256KB_3D:['ADDR3_256KB_3D',18,true]};
function eligibility(i) {
 if(i.maxmip>15) return {status:'reference_rejected',reason:'V3 MaxMipLevels=16; mip index 16 outside contract'};
 if(i.s>0&&(i.maxmip>0||MAP[i.mode][2]||i.mode==='SW_LINEAR'))
  return {status:'reference_rejected',reason:'MSAA requires single-level 2D tiled resource'};
 return {status:'comparable',mapping:MAP[i.mode][0]};
}
function block(i) {
 const [,L,thick]=MAP[i.mode],linear=i.mode==='SW_LINEAR';
 let logs;
 if(linear) logs=[L-i.e,0,0];
 else if(thick) {
  const a=Math.floor(L/3)-Math.floor(i.e/3);
  logs=[a+Number(L%3>0)-Number(i.e%3>0),a,a+Number(L%3>1)-Number(i.e%3>1)];
 } else logs=[Math.floor(L/2)-Math.floor(i.e/2)-Math.floor(i.s/2)-(i.e&i.s&1),
  Math.floor(L/2)-Math.floor(i.e/2)-Math.floor(i.s/2)-((i.e|i.s)&1),0];
 return {L,thick,linear,ns:i.s,logs,bws:logs[0]};
}
function capacity(b) {
 let effective=b.L;
 if(b.thick&&b.L>=8) effective-=Math.floor((b.L-8)/3);
 return effective>8?(effective<=11?1+2**(effective-9):effective-4):1;
}
function mipDims(i,m) {return [Math.ceil(Math.max(i.W,1)/2**m),Math.ceil(Math.max(i.H,1)/2**m)];}
function firstTail(i,b,cap) {
 const dims=b.logs.map(v=>2**v);
 if(b.thick) dims[b.L%3===0?1:b.L%3===1?0:2]/=2;
 else dims[b.L%2===0?0:1]/=2;
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
  const p=align(wh[0],b.linear?128/2**i.e:dims[0]),h=align(wh[1],dims[1]);
  let ps=b.linear?align(p,256/2**i.e):p,bytes=0n;
  if(m<first) {
   bytes=BigInt(ps)*BigInt(h)*unit*samples;
   if(b.linear&&i.D===1&&m===0) {
    const data=BigInt(p)*BigInt(h)*unit*samples;
    bytes=((data+255n)/256n)*256n;ps=p;
   }
  } else if(m===first) bytes=BigInt(2**b.L)/BigInt(dims[2]);
  pitch.push(p);height.push(h);slicePitch.push(ps);bytesPerMip.push(bytes);sliceSize+=bytes;
 }
 let off=first<=i.maxmip?BigInt(2**b.L):0n;
 for(let m=Math.min(first-1,i.maxmip);m>=0;m--) {
  macroBlockOffset[m]=off;off+=bytesPerMip[m]*BigInt(dims[2]);
 }
 if(first<=i.maxmip) {
  const bits=8-i.e;
  const micro=b.thick?[2**(Math.floor(bits/3)+Number(bits%3>1)),2**Math.floor(bits/3)]:
   [2**(Math.floor(bits/2)+(bits%2)),2**Math.floor(bits/2)];
  let p=tail.threshold[0],h=tail.threshold[1];
  for(let m=first;m<=i.maxmip;m++) {
   p=align(p,micro[0]);h=align(h,micro[1]);
   pitch[m]=p;height[m]=h;slicePitch[m]=null;macroBlockOffset[m]=0n;
   p=Math.max(Math.floor(p/2),1);h=Math.max(Math.floor(h/2),1);
  }
 }
 return {b,cap,first,firstMipIdInTail:first===17?i.maxmip+1:first,threshold:tail.threshold,
  pitch,height,slicePitch,bytesPerMip,mipSizes,macroBlockOffset,sliceSize,blockDimensions:dims};
}
module.exports={MAP,eligibility,block,capacity,firstTail,mipDims,surface};
