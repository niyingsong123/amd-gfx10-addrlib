#!/usr/bin/env node
'use strict';
// Print the checked-in machine result in a terminal-friendly form so the
// outcome is not dependent on Markdown/JSON artifact viewing support.
const fs=require('node:fs'),path=require('node:path');
const file=process.argv[2]||path.join(__dirname,'../../docs/mipmap_compare_small_results.json');
const r=JSON.parse(fs.readFileSync(file,'utf8'));
const fmt=n=>Number(n).toLocaleString('en-US');
function row(name,x) {
 return `${name}: 一致 ${fmt(x.match)}；数值差异 ${fmt(x.numerical_difference)}；`+
  `表达口径不同 ${fmt(x.representation_difference)}；无等价模式 ${fmt(x.no_equivalent)}；`+
  `参考拒绝 ${fmt(x.reference_rejected)}；模型假设未明确 ${fmt(x.model_assumption)}`;
}
console.log('mipmap_param_calc_core_gc 小规模对比摘要');
console.log(`种子 ${r.parameters.seed}；随机配置 ${fmt(r.parameters.randomConfigurationCount)}；`+
 `总配置 ${fmt(r.counts.configurations)}；mip ${fmt(r.counts.requestedMips)}；字段比较 ${fmt(r.counts.fieldComparisons)}`);
console.log(row('公开 GFX10（按配置）',r.references.gfx10.configurations));
console.log(row('GFX12 辅助（按配置）',r.references.gfx12.configurations));
console.log(row('公开 GFX10（按 mip）',r.references.gfx10.mips));
console.log(row('GFX12 辅助（按 mip）',r.references.gfx12.mips));
console.log(`扰动 ${fmt(r.invariance.probes)} 次；异常 ${fmt(r.invariance.failures.length)} 次`);
console.log(`输入摘要 ${r.hashes.inputSummarySha256}`);
console.log(`输出摘要 ${r.hashes.outputSummarySha256}`);
console.log('结论：存在否定“与公开 GFX10 完全匹配”的明确反例；未执行百万组。');
