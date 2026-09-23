'use strict';
const doc=require('./document.cjs'),gen=require('./generate.cjs');
const refs={gfx10:require('./gfx10.cjs'),gfx12:require('./gfx12.cjs')};
const FIELDS=['pitch','slice','mip_in_tail','mip_offset_b','l2_ms','l2_blk_w','l2_blk_h','l2_blk_d','l2_blk_w_slice'];
const normalizedFirst=(s,i)=>s.first<=i.maxmip?s.first:17;
function referenceVector(r,i,m,version) {
 // Alignment exponents are derived quantities, NOT extra official API outputs.
 const lin12=version==='gfx12'&&r.b.linear;
 return [r.pitch[m],r.sliceSize,m<r.first?17:m-r.first,r.macroBlockOffset[m],
  lin12?7:r.b.L,lin12?7-i.e:r.b.logs[0],r.b.logs[1],r.b.logs[2],r.b.bws];
}
function documentVector(d,m) {const a=doc.outputs(d,m);a[1]=d.sliceBytes;a[3]*=256n;return a;}
function fieldClasses(d,r,i,m,version) {
 const a=documentVector(d,m),b=referenceVector(r,i,m,version);
 return a.map((v,k)=>v===b[k]?'match':k===0&&m>=d.first&&m>=r.first?
  'representation_difference':'numerical_difference');
}
function overall(c) {return c.includes('numerical_difference')?'numerical_difference':
 c.includes('representation_difference')?'representation_difference':'match';}
function snapshot(i,m,version) {
 const d=doc.surface(i),R=refs[version],eligibility=R.eligibility(i);
 const result={id:i.id,mip:m,input:gen.rawInput(i,m),adapter:{resourceType:d.b.thick?'3D':'2D',
  bpp:8*2**i.e,numSamples:2**i.s,numFragments:2**i.s,numMipLevels:i.maxmip+1,numSlices:i.D},eligibility,
  document:{raw:Object.fromEntries(FIELDS.map((f,n)=>[f,doc.outputs(d,m)[n]])),
   converted:Object.fromEntries(FIELDS.map((f,n)=>[f,documentVector(d,m)[n]])),
   firstTailRaw:d.first,firstTailInRequestedChain:normalizedFirst(d,i),tailCapacity:d.cap,
   bytesPerMip:d.bytesPerMip.slice(0,i.maxmip+1)}};
 if(eligibility.status==='comparable') {
  const r=R.surface(i),classes=fieldClasses(d,r,i,m,version);
  result.reference={version,raw:{pitch:r.pitch[m],sliceSize:r.sliceSize,macroBlockOffset:r.macroBlockOffset[m],
   firstMipIdInTail:r.firstMipIdInTail,blockDimensions:r.blockDimensions,pitchForSlice:r.slicePitch[m]},
   derived:Object.fromEntries(FIELDS.map((f,n)=>[f,referenceVector(r,i,m,version)[n]])),
   tailCapacity:r.cap,bytesPerMip:r.bytesPerMip};
  result.fields=Object.fromEntries(FIELDS.map((f,n)=>[f,classes[n]]));result.classification=overall(classes);
 } else result.classification=eligibility.status;
 return result;
}
function counter() {return {match:0,numerical_difference:0,representation_difference:0,no_equivalent:0,reference_rejected:0,model_assumption:0};}
function stats() {return {configurations:0,mips:0,comparableConfigurations:0,comparableMips:0,
 whole:counter(),fields:Object.fromEntries(FIELDS.map(f=>[f,counter()])),stages:{},isolatedStages:{},modes:{}};}
function stage(t,name,same) {
 const c=t[name]||(t[name]={match:0,difference:0,notApplicable:0});
 c[same===null?'notApplicable':same?'match':'difference']++;
}
function stages(s,i,d,r) {
 stage(s.stages,'block_dimensions',d.b.logs.every((v,k)=>v===r.b.logs[k]));
 stage(s.stages,'tail_capacity',r.cap===null?null:d.cap===r.cap);
 stage(s.stages,'first_tail',normalizedFirst(d,i)===r.first);
 stage(s.stages,'slice_sum',d.sliceBytes===r.sliceSize);
 for(let m=0;m<=i.maxmip;m++) {
  stage(s.stages,'mip_dimensions',d.mipSizes[m].every((v,k)=>v===r.mipSizes[m][k]));
  stage(s.stages,'slice_contribution',d.bytesPerMip[m]===r.bytesPerMip[m]);
  stage(s.stages,'pitch',d.pitch[m]===r.pitch[m]);
  stage(s.stages,'macro_offset',d.offset[m]*256n===r.macroBlockOffset[m]);
 }
 // Same reference block/capacity, then same first tail, fed to both sides.
 // Linear physical slice block is not the V3 rendering block: isolation is N/A.
 if(r.b.linear) {
  for(const n of ['first_tail','slice_sum','slice_contribution','macro_offset','pitch_outside_tail']) stage(s.isolatedStages,n,null);
  return;
 }
 const dd=doc.surface(i,{block:r.b,capacity:r.cap??1});
 stage(s.isolatedStages,'first_tail',normalizedFirst(dd,i)===r.first);
 const forced=doc.surface(i,{block:r.b,capacity:r.cap??1,first:r.first});
 stage(s.isolatedStages,'slice_sum',forced.sliceBytes===r.sliceSize);
 for(let m=0;m<=i.maxmip;m++) {
  stage(s.isolatedStages,'slice_contribution',forced.bytesPerMip[m]===r.bytesPerMip[m]);
  stage(s.isolatedStages,'macro_offset',forced.offset[m]*256n===r.macroBlockOffset[m]);
  stage(s.isolatedStages,'pitch_outside_tail',m<r.first?forced.pitch[m]===r.pitch[m]:null);
 }
}
function shrink(i,m,version,field,kind) {
 const R=refs[version];let cur={...i},level=m,trials=0;
 function holds(j,n) {
  trials++;if(n>j.maxmip||R.eligibility(j).status!=='comparable') return false;
  return fieldClasses(doc.surface(j),R.surface(j),j,n,version)[field]===kind;
 }
 for(let pass=0;pass<3;pass++) {
  for(const k of ['e','s','maxmip','W','H','D']) {
   const min=['W','H','D'].includes(k)?1:k==='maxmip'?level:0;
   const vals=[min,2,3,4,8,16,32,64,128,256,Math.floor(cur[k]/2),cur[k]-1].filter(v=>v>=min&&v<cur[k]).sort((a,b)=>a-b);
   for(const v of vals) if(holds({...cur,[k]:v},level)) {cur[k]=v;break;}
  }
  for(let n=0;n<level;n++) if(holds(cur,n)) {level=n;break;}
 }
 cur.x=cur.y=cur.z=cur.coordS=0;
 return {method:'bounded greedy; not global minimum',trials,original:{id:i.id,mip:m},
  field:FIELDS[field],classification:kind,result:snapshot(cur,level,version)};
}
module.exports={FIELDS,refs,normalizedFirst,referenceVector,documentVector,fieldClasses,overall,snapshot,counter,stats,stages,shrink};
