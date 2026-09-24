'use strict';
const doc=require('./document.cjs');
const combos=[];
for(const mode of Object.keys(doc.MODE)) for(let e=0;e<5;e++)
 for(let s=0;s<(mode.endsWith('_2D')?4:1);s++) combos.push({mode,e,s});
if(combos.length!==100) throw Error('Expected exactly 100 combinations');
function rng(seed,id) {
 let a=(seed^Math.imul(id+1,0x9e3779b9))>>>0;
 return n=>{a=(a+0x6d2b79f5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);
  t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)%n;};
}
function random(seed,id) {
 const c=combos[id%100],r=rng(seed,id),b=doc.block(c),dims=b.logs.map(v=>2**v);
 function dim(limit,block) {
  const kind=r(5);let v;
  if(kind<2) v=1+r(limit);
  else if(kind===2) v=2**r(Math.floor(Math.log2(limit))+1)+r(3)-1;
  else if(kind===3) v=block*(1+r(Math.max(1,Math.floor(limit/block))))+r(3)-1;
  else v=Math.max(1,block/2)*2**r(6)+r(3)-1;
  return Math.max(1,Math.min(limit,v));
 }
 const W=dim(16384,dims[0]),H=dim(16384,dims[1]);
 const D=b.thick?dim(2048,dims[2]):(r(2)?1:2+r(255));
 const full=Math.floor(Math.log2(Math.max(W,H,b.thick?D:1))),kind=r(3);
 const maxmip=c.s?0:kind===0?0:kind===1?full:r(full+1);
 return {...c,W,H,D,maxmip,x:r(W),y:r(H),z:r(D),coordS:r(2**c.s),id:'r'+id,group:'random'};
}
function directed() {
 const out=[];
 for(const c of combos) {
  const b=doc.block(c),[bw,bh]=b.logs.map(v=>2**v),yb=b.thick&&(b.L===12||b.L===18);
  const tw=bw/(yb?1:2),th=bh/(yb?2:1);
  const vals=[[1,1,0,'single_min'],[16384,16384,0,'single_max'],
   [65536,65536,0,'size_65536'],[65536,65536,16,'mip_16']];
  if(c.s===0) {
   vals.push([16384,8193,14,'full_chain'],[16384,16383,2,'truncated_no_tail']);
   for(const delta of [-1,0,1]) vals.push([Math.max(1,tw+delta),Math.max(1,th+delta),4,'tail_boundary_'+delta]);
  } else vals.push([257,129,4,'msaa_mipmap_probe']);
  for(const [W,H,maxmip,tag] of vals) out.push({...c,W,H,D:b.thick?2048:1,maxmip,
   x:0,y:0,z:0,coordS:0,id:'d'+out.length,group:'directed',tag});
 }
 for(let e=0;e<5;e++) for(const D of [1,2]) out.push({mode:'SW_LINEAR',e,s:0,
  W:1,H:2,D,maxmip:0,x:0,y:0,z:0,coordS:0,id:'d'+out.length,group:'directed',tag:'linear_trim'});
 return out;
}
const trusted=[
 {id:'case0',file:'case/case0_mip4_xyz_5_6_3.md',mode:'SW_256KB_3D',e:0,s:0,W:256,H:256,D:256,maxmip:12,mip:4,x:5,y:6,z:3,coordS:0,
  expected:[64,90112n,1,0n,18,6,6,6,6]},
 {id:'case1',file:'case/case1_mip0_xyz_69_134_195.md',mode:'SW_256KB_3D',e:0,s:0,W:256,H:256,D:256,maxmip:12,mip:0,x:69,y:134,z:195,coordS:0,
  expected:[256,90112n,17,6144n,18,6,6,6,6]},
 {id:'case2',file:'case/case2_mip6_xyz_1_1_17.md',mode:'SW_64KB_3D',e:2,s:0,W:128,H:128,D:2048,maxmip:11,mip:6,x:1,y:1,z:17,coordS:0,
  expected:[32,22528n,3,0n,16,5,5,4,5]}
].map(v=>({...v,group:'trusted'}));
function rawInput(i,m=0) {return {x:i.x,y:i.y,z:i.z,s:i.coordS,map0_w_minus_1:i.W-1,
 map0_h_minus_1:i.H-1,map0_d_minus_1:i.D-1,sw_mode:i.mode,log2_num_samples:i.s,
 log2_element_bytes:i.e,mip_level:m,maxmip:i.maxmip};}
function fromRaw(v) {
 for(const k of ['x','y','z','s','map0_w_minus_1','map0_h_minus_1','map0_d_minus_1',
  'log2_num_samples','log2_element_bytes','mip_level','maxmip'])
  if(!Number.isSafeInteger(v[k])||v[k]<0) throw Error('Invalid integer: '+k);
 if(!doc.MODE[v.sw_mode]||v.log2_element_bytes>4||v.log2_num_samples>3||v.maxmip>16||v.mip_level>v.maxmip)
  throw Error('Input outside documented mode/format/mip domain');
 if(Math.max(v.map0_w_minus_1,v.map0_h_minus_1,v.map0_d_minus_1)>65535) throw Error('Declared dimension bound is 65536');
 return {mode:v.sw_mode,e:v.log2_element_bytes,s:v.log2_num_samples,W:v.map0_w_minus_1+1,
  H:v.map0_h_minus_1+1,D:v.map0_d_minus_1+1,maxmip:v.maxmip,mip:v.mip_level,
  x:v.x,y:v.y,z:v.z,coordS:v.s,id:'input',group:'replay'};
}
module.exports={combos,random,directed,trusted,rawInput,fromRaw};
