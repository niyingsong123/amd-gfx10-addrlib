'use strict';
// Literal ADDRLIB.md:43-569 functional model, not compiled RTL.
// Dimensions/exponents are exact small Numbers; products, masks and offsets use BigInt.
const MODE={SW_LINEAR:[7,false],SW_256B_2D:[8,false],SW_4KB_2D:[12,false],
 SW_64KB_2D:[16,false],SW_256KB_2D:[18,false],SW_4KB_3D:[12,true],
 SW_64KB_3D:[16,true],SW_256KB_3D:[18,true]};
const TABLE={12:[[4,4,4],[3,4,4],[3,4,3],[3,3,3],[2,3,3]],
 16:[[6,5,5],[5,5,5],[5,5,4],[5,4,4],[4,4,4]],
 18:[[6,6,6],[5,6,6],[5,6,5],[5,5,5],[4,5,5]]};
function ceilShift(v,k) {
 const base=2**k; return Math.floor(v/base)+Number(v%base!==0);
}
function block(i) {
 const [L,thick]=MODE[i.mode],linear=i.mode==='SW_LINEAR',ns=linear||thick?0:i.s,n=L-i.e-ns;
 let logs;
 if(linear) logs=[n,0,0];
 else if(thick) logs=TABLE[L][i.e].slice();
 else logs=[((n>>1)&15)+((n&1)&Number(Boolean((i.e&1)||(i.s&1)))),(n>>1)&15,0];
 return {L,thick,linear,ns,logs,bws:linear&&logs[0]<8?8-i.e:logs[0]};
}
function capacity(b) {
 const q=Math.max(0,b.L-8),eff=b.thick?({4:3,8:6,10:7}[q]):q;
 return eff===0?1:eff===3?5:eff+4;
}
function firstTail(i,b,cap) {
 const [bw,bh]=b.logs,y=b.thick&&(b.L===12||b.L===18);
 const tw=2**bw/(y?1:2),th=2**bh/(y?2:1),outside=i.maxmip-cap;
 const wb0=ceilShift(i.W,bw),hb0=ceilShift(i.H,bh),bits=[];
 for(let m=0;m<17;m++) bits.push(((m>outside)||(outside<0))&&(m===0?
  i.W<=tw&&i.H<=th:ceilShift(wb0,m-1)<=(y?2:1)&&ceilShift(hb0,m-1)<=(y?1:2)));
 let raw=17;
 for(let m=0;m<17;m++) if(m===0?bits[0]:bits[m]!==bits[m-1]) raw=m;
 return {first:i.maxmip===0||((b.L-7)>>1)===0?17:raw,raw,bits,threshold:[tw,th]};
}
function surface(i,overrides={}) {
 const b=overrides.block||block(i),cap=overrides.capacity??capacity(b),t=firstTail(i,b,cap);
 const first=overrides.first??t.first,[bw,bh]=b.logs;
 const wb0=ceilShift(i.W,bw),hb0=ceilShift(i.H,bh),ws0=ceilShift(i.W,b.bws);
 const pitch=[],height=[],slicePitch=[],sizes=[],bytesPerMip=[],offset=[],mipSizes=[];
 let sum=0n;
 for(let m=0;m<17;m++) {
  const wb=ceilShift(wb0,m),hb=ceilShift(hb0,m),ws=ceilShift(ws0,m);
  pitch.push(wb*2**bw);height.push(hb*2**bh);slicePitch.push(ws*2**b.bws);
  mipSizes.push([ceilShift(i.W,m),ceilShift(i.H,m)]);
  const size=m>first?0n:(m===first||m===16)?1n:BigInt(ws)*BigInt(hb);
  sizes.push(size);bytesPerMip.push((size<<BigInt(b.bws+bh))*BigInt(2**(i.e+b.ns)));
  if(m<=i.maxmip) sum+=size;
 }
 // Literal maxmip mask and equivalent suffix sum of selected mips.
 const mask=(1n<<BigInt(i.maxmip+1))-1n;
 let rest=0n;
 for(let m=16;m>=0;m--) {
  offset[m]=rest<<BigInt(Math.max(0,b.L-8));
  if((mask&(1n<<BigInt(m)))!==0n) rest+=sizes[m];
 }
 return {b,cap,first,rawFirst:t.raw,threshold:t.threshold,tailBits:t.bits,
  pitch,height,slicePitch,sizes,bytesPerMip,mipSizes,offset,
  slice:sum<<BigInt(b.bws+bh),sliceBytes:(sum<<BigInt(b.bws+bh))*BigInt(2**(i.e+b.ns))};
}
function outputs(s,m) {return [s.pitch[m],s.slice,m<s.first?17:m-s.first,s.offset[m],s.b.L,...s.b.logs,s.b.bws];}
module.exports={MODE,block,capacity,firstTail,surface,outputs,ceilShift};
