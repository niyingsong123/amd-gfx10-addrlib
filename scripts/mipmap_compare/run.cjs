#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const gen=require('./generate.cjs'),doc=require('./document.cjs'),cmp=require('./compare.cjs');

function args(argv) {
 const o={seed:0x20260922,count:10000,directed:true,out:null,configNumbers:null,mip:null};
 for(let n=0;n<argv.length;n++) {
  const a=argv[n],v=argv[n+1];
  if(a==='--seed') {o.seed=Number(BigInt(v));n++;}
  else if(a==='--config-count') {o.count=Number(v);n++;}
  else if(a==='--config-number') {o.configNumbers=v.split(',').map(Number);n++;}
  else if(a==='--mip') {o.mip=Number(v);n++;}
  else if(a==='--no-directed') o.directed=false;
  else if(a==='--directed-only') {o.count=0;o.directed=true;}
  else if(a==='--out') {o.out=v;n++;}
  else if(a==='--help') {console.log('node run.cjs [--seed 0x...] [--config-count N] [--config-number N[,N]] [--mip N] [--no-directed|--directed-only] [--out FILE]');process.exit(0);}
  else throw Error('Unknown argument: '+a);
 }
 if(!Number.isSafeInteger(o.seed)||o.seed<0||o.seed>0xffffffff) throw Error('seed must be uint32');
 if(!Number.isSafeInteger(o.count)||o.count<0) throw Error('config-count must be nonnegative');
 if(o.configNumbers&&o.configNumbers.some(v=>!Number.isSafeInteger(v)||v<0)) throw Error('invalid config-number');
 if(o.mip!==null&&(!Number.isSafeInteger(o.mip)||o.mip<0||o.mip>16)) throw Error('mip must be 0..16');
 return o;
}
const json=(v,space=0)=>JSON.stringify(v,(_,x)=>typeof x==='bigint'?x.toString():x,space);
const hash=v=>crypto.createHash('sha256').update(json(v)).digest('hex');
const blank=()=>({match:0,numerical_difference:0,representation_difference:0,no_equivalent:0,reference_rejected:0,model_assumption:0});
const add=(x,k,n=1)=>{if(x[k]===undefined)x[k]=0;x[k]+=n;};
function selfCheck() {
 for(const c of gen.trusted) assert.deepEqual(doc.outputs(doc.surface(c),c.mip),c.expected,c.id);
 assert.deepEqual(cmp.refs.gfx10.block({mode:'SW_64KB_2D',e:0,s:0}).logs,[8,8,0]);
 assert.deepEqual(cmp.refs.gfx10.block({mode:'SW_64KB_3D',e:2,s:0}).logs,[5,5,4]);
 assert.equal(cmp.refs.gfx10.capacity({L:16,thick:true}),10);
 assert.deepEqual(cmp.refs.gfx12.block({mode:'SW_256KB_3D',e:0,s:0}).logs,[6,6,6]);
 const huge={mode:'SW_256B_2D',e:4,s:0,W:65536,H:65536,D:1,maxmip:1,x:0,y:0,z:0,coordS:0};
 assert.equal(cmp.refs.gfx10.surface(huge).bytesPerMip[0],0n,'GFX10 UINT32 micro-tile product wraps');
 return {trustedCases:gen.trusted.length,formulaAssertions:5,uint32WrapAssertion:true};
}
function stageBucket() {return {shared:{},isolated:{}};}
function summarizeConfig(classes) {
 if(classes.includes('numerical_difference')) return 'numerical_difference';
 if(classes.includes('representation_difference')) return 'representation_difference';
 return classes[0]||'model_assumption';
}
function main() {
 const opt=args(process.argv.slice(2)),self=selfCheck();
 const randomIds=opt.configNumbers||Array.from({length:opt.count},(_,i)=>i);
 const configs=randomIds.map(i=>gen.random(opt.seed,i));
 if(opt.directed&&!opt.configNumbers) configs.push(...gen.directed());
 const result={schemaVersion:1,scope:'mipmap_param_calc_core_gc small-scale comparison',generatedAt:new Date().toISOString(),
  parameters:{seed:'0x'+opt.seed.toString(16).padStart(8,'0'),randomConfigurationCount:randomIds.length,
   combinationCount:100,randomPerCombination:opt.configNumbers?null:opt.count/100,directed:opt.directed&&!opt.configNumbers,
   replay:{configNumbers:opt.configNumbers,mip:opt.mip}},assumptions:{documentArithmetic:'BigInt for products/masks/offsets; dimensions are exact Number; unknown RTL widths are not simulated',
   gfx10Identity:'public GFX10 PAL implementation; not claimed to be exactly GFX10.2',maxMip:'PAL MaxMipLevels=16 (indices 0..15); document MAXMIP=17 (indices 0..16)'},
  selfCheck:self,counts:{configurations:configs.length,requestedMips:0,fieldComparisons:0},modes:{},references:{},trustedRegression:[],invariance:{probes:0,failures:[]},representatives:[]};
 for(const c of gen.trusted) result.trustedRegression.push({id:c.id,file:c.file,mip:c.mip,output:doc.outputs(doc.surface(c),c.mip)});
 for(const version of ['gfx10','gfx12']) result.references[version]={configurations:blank(),mips:blank(),fields:Object.fromEntries(cmp.FIELDS.map(f=>[f,blank()])),stages:stageBucket(),eligibleConfigurations:0};
 const repKeys=new Set(),inputSummary=[];
 for(const i of configs) {
  const mips=opt.mip===null?Array.from({length:i.maxmip+1},(_,m)=>m):(opt.mip<=i.maxmip?[opt.mip]:[]);
  result.counts.requestedMips+=mips.length;inputSummary.push(gen.rawInput(i,mips[0]??0));
  const mode=result.modes[i.mode]||(result.modes[i.mode]={configurations:0,mips:0});mode.configurations++;mode.mips+=mips.length;
  for(const version of ['gfx10','gfx12']) {
   const ref=result.references[version],R=cmp.refs[version],eligible=R.eligibility(i),configClasses=[];
   if(eligible.status==='comparable') {ref.eligibleConfigurations++;cmp.stages({stages:ref.stages.shared,isolatedStages:ref.stages.isolated},i,doc.surface(i),R.surface(i));}
   for(const m of mips) {
    const snap=cmp.snapshot(i,m,version),cl=snap.classification;configClasses.push(cl);add(ref.mips,cl);
    for(const f of cmp.FIELDS) {const fc=snap.fields?snap.fields[f]:cl;add(ref.fields[f],fc);result.counts.fieldComparisons++;}
    if(cl!=='match') {
     const differing=snap.fields?cmp.FIELDS.filter(f=>snap.fields[f]!=='match'):[cl];
     for(const f of differing) {const key=version+':'+cl+':'+f;if(repKeys.size<36&&!repKeys.has(key)) {repKeys.add(key);let reduced=null;
       if(snap.fields&&snap.fields[f]==='numerical_difference') reduced=cmp.shrink(i,m,version,cmp.FIELDS.indexOf(f),'numerical_difference');
       result.representatives.push({key,original:snap,reduced});}}
    }
   }
   add(ref.configurations,eligible.status==='comparable'?summarizeConfig(configClasses):eligible.status);
  }
 }
 // Coordinates and the depth input are absent from the document arithmetic. Probe all three models on a bounded sample.
 for(const i of configs.slice(0,100)) {
  const variants=[['x',{...i,x:i.W+7}],['y',{...i,y:i.H+11}],['z',{...i,z:i.D+13}],['s',{...i,coordS:2**i.s+1}],['depth',{...i,D:i.D===65536?65535:i.D+1}]];
  for(const [field,j] of variants) {result.invariance.probes++;const base=hash(doc.surface(i)),changed=hash(doc.surface(j));if(base!==changed) result.invariance.failures.push({id:i.id,field,model:'document'});
   for(const version of ['gfx10','gfx12']) if(cmp.refs[version].eligibility(i).status==='comparable'&&hash(cmp.refs[version].surface(i))!==hash(cmp.refs[version].surface(j))) result.invariance.failures.push({id:i.id,field,model:version});
  }
 }
 result.hashes={inputSummarySha256:hash(inputSummary)};
 result.hashes.outputSummarySha256=hash({counts:result.counts,modes:result.modes,references:result.references,invariance:result.invariance});
 const body=json(result,2)+'\n';if(opt.out) {fs.mkdirSync(path.dirname(opt.out),{recursive:true});fs.writeFileSync(opt.out,body);} else process.stdout.write(body);
 console.error(`DONE: ${configs.length} configs, ${result.counts.requestedMips} mips, ${result.counts.fieldComparisons} field comparisons; output ${result.hashes.outputSummarySha256}`);
}
main();
