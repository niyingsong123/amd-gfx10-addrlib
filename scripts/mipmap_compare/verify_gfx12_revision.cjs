'use strict';
// Functional comparison, not RTL simulation and not compiled C++ execution.
// The unchanged document stages and independent GFX12 reference stay immutable.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const doc = require('../../regression_0924/cloud/scripts/mipmap_compare/document.cjs');
const gfx12 = require('../../regression_0924/cloud/scripts/mipmap_compare/gfx12.cjs');
const gen = require('./generate.cjs');
const json = (v, pretty = false) => JSON.stringify(v, (_, x) => typeof x === 'bigint' ? x.toString() : x, pretty ? 2 : undefined);
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex');
const EXPECTED = {
  'ADDRLIB.md': 'a6864bd26943078add333142bb40b87a9600b106572928f8b94621522ccacd8c',
  'regression_0924/cloud/scripts/mipmap_compare/document.cjs': 'f15ffba64a73558c4bc37002be4bcabb34c5d4bd9bd26440c7fc1d7181007e78',
  'regression_0924/cloud/scripts/mipmap_compare/gfx12.cjs': 'fcbb4895e0f957f2468614a3d76e1fda35fd540698e701dcd969a170a898ff23',
  'scripts/mipmap_compare/upstream/src/gfx12/gfx12addrlib.cpp': '9210bb10078c48a3757e1f1a2f9483d5a355b04d83fbca19a65485938b1da8db',
  'scripts/mipmap_compare/upstream/src/core/addrlib3.cpp': '068c124ef619aad4d83f636bee425146b9bf590e47d899f7c751a1736676a8fd'
};
for (const [file, expected] of Object.entries(EXPECTED)) assert.equal(sha(file), expected, file + ' changed; review formulas before updating this run guard');
const opts = {count: 1000000, seed: 0x20260922, replay: null, mip: null, out: null, directedOnly: false};
for (let k = 2; k < process.argv.length; k++) {
  const arg = process.argv[k];
  if (arg === '--directed-only') { opts.directedOnly = true; continue; }
  if (!['--count', '--seed', '--replay', '--mip', '--out'].includes(arg)) throw Error('Unknown argument: ' + arg);
  const v = process.argv[++k];
  if (v === undefined) throw Error('Missing value: ' + arg);
  const key = arg.slice(2);
  opts[key] = key === 'out' ? v : Number(v);
}
for (const key of ['count', 'seed', 'replay', 'mip']) {
  const value = opts[key];
  if (value !== null && (!Number.isSafeInteger(value) || value < 0)) throw Error('Invalid ' + key);
}
if (opts.seed > 0xffffffff) throw Error('Seed must fit uint32');
if (opts.directedOnly) opts.count = 0;
if (opts.mip !== null && opts.replay === null) throw Error('--mip requires --replay');
const fields = ['pitch', 'slice_bytes', 'mip_in_tail', 'macro_offset_bytes', 'l2_ms', 'l2_blk_w', 'l2_blk_h', 'l2_blk_d', 'l2_blk_w_slice'];
const rawFields = ['pitch', 'slice', 'mip_in_tail', 'mip_offset_b', 'l2_ms', 'l2_blk_w', 'l2_blk_h', 'l2_blk_d', 'l2_blk_w_slice'];

// Only these marked changes differ from the immutable document transcription.
// GFX12-01: ADDRLIB.md, slice_b_drop; PAL GetMipOffset + CanTrimLinearPadding.
// GFX12-02: ADDRLIB.md, micro exponent table; PAL GetMipOrigin + HwlGetMicroBlockSize.
function revised(i, base = doc.surface(i)) {
  const out = {...base, pitch: base.pitch.slice()};
  const quantum = BigInt(base.b.bws + base.b.logs[1]);
  const wb0 = base.pitch[0] / 2 ** base.b.logs[0];
  const drop = base.b.linear && i.D === 1 && (wb0 & 1) ? BigInt(Math.floor(i.H / 2)) : 0n;
  out.slice = ((base.slice >> quantum) - drop) << quantum;
  out.sliceBytes = out.slice * BigInt(2 ** (i.e + base.b.ns));
  out.sliceBlockDrop = drop;
  // Match the revised slice accumulation stage, in bytes per XY slice.
  out.bytesPerMip = base.bytesPerMip.slice();
  out.bytesPerMip[0] -= (drop << quantum) * BigInt(2 ** (i.e + base.b.ns));
  const U = (base.b.thick ? [3, 2, 2, 2, 1] : [4, 4, 3, 3, 2])[i.e];
  const yBias = base.b.thick && (base.b.L === 12 || base.b.L === 18);
  const T = base.b.logs[0] - (yBias ? 0 : 1);
  for (let m = base.first; m <= i.maxmip; m++) {
    assert(T >= U, 'Tail exponent must not underflow');
    const k = m - base.first;
    out.pitch[m] = 2 ** (k < T - U ? T - k : U);
  }
  return out;
}
// GFX12-03 is a local interface adapter, not an upstream API output.
const pitchBlocks = (s, m) => Math.max(Math.floor(s.pitch[m] / 2 ** s.b.logs[0]), 1);
function documentVector(s, m) {
  return [s.pitch[m], s.sliceBytes, m < s.first ? 17 : m - s.first, s.offset[m] * 256n, s.b.L, ...s.b.logs, s.b.bws];
}
function referenceVector(s, i, m) {
  // Linear's 128B rendering dimensions are derived; physical blockExtent remains 256B.
  return [s.pitch[m], s.sliceSize, m < s.first ? 17 : m - s.first, s.macroBlockOffset[m],
    s.b.linear ? 7 : s.b.L, s.b.linear ? 7 - i.e : s.b.logs[0], s.b.logs[1], s.b.logs[2], s.b.bws];
}
function referenceRaw(s, m) {
  return {pitch: s.pitch[m], sliceSize: s.sliceSize, macroBlockOffset: s.macroBlockOffset[m],
    firstMipIdInTail: s.firstMipIdInTail, blockDimensions: s.blockDimensions, physicalBlockSizeLog2: s.b.L};
}
function record(i, m, s, r, status) {
  return {status, configurationId: i.id, mip: m, input: gen.rawInput(i, m),
    documentRaw: Object.fromEntries(rawFields.map((f, k) => [f, doc.outputs(s, m)[k]])),
    referenceRaw: referenceRaw(r, m),
    documentNormalized: Object.fromEntries(fields.map((f, k) => [f, documentVector(s, m)[k]])),
    referenceNormalized: Object.fromEntries(fields.map((f, k) => [f, referenceVector(r, i, m)[k]]))};
}
function legal(i) {
  if (!doc.MODE[i.mode] || !Number.isInteger(i.e) || i.e < 0 || i.e > 4 || !Number.isInteger(i.s) || i.s < 0 || i.s > 3)
    return {status: 'model_assumption_unresolved', reason: 'mode/format outside the declared domain'};
  if (![i.W, i.H, i.D].every(v => Number.isInteger(v) && v >= 1 && v <= 65536))
    return {status: 'model_assumption_unresolved', reason: 'dimensions outside 1..65536'};
  if (!Number.isInteger(i.maxmip) || i.maxmip < 0)
    return {status: 'model_assumption_unresolved', reason: 'invalid mip count'};
  return gfx12.eligibility(i);
}
if (opts.replay !== null) {
  const i = gen.random(opts.seed, opts.replay);
  const eligibility = legal(i);
  if (opts.mip !== null && opts.mip > i.maxmip) throw Error('Requested mip exceeds maxmip');
  const output = {seed: opts.seed, sourceDocumentSha256: EXPECTED['ADDRLIB.md'], eligibility, configuration: i};
  if (eligibility.status === 'comparable') {
    const s = revised(i), r = gfx12.surface(i);
    const levels = opts.mip === null ? Array.from({length: i.maxmip + 1}, (_, m) => m) : [opts.mip];
    output.mips = levels.map(m => record(i, m, s, r,
      documentVector(s, m).every((v, k) => v === referenceVector(r, i, m)[k]) ? 'match' : 'numeric_difference'));
  }
  console.log(json(output, true));
  process.exit(output.mips?.some(v => v.status !== 'match') ? 1 : 0);
}

const started = process.hrtime.bigint();
const hashStream = crypto.createHash('sha256');
const stages = ['block_dimensions', 'tail_capacity', 'first_tail_effective', 'mip_dimensions', 'pitch', 'slice_contribution_bytes', 'macro_offset_bytes', 'address_pitch_blocks'];
const histogram = () => ({match: 0, difference: 0});
function stats() {
  return {configurations: 0, comparableConfigurations: 0, mips: 0, fieldComparisons: 0,
    classes: {match: 0, numeric_difference: 0, representation_difference: 0, no_equivalent_mode: 0, reference_rejected: 0, model_assumption_unresolved: 0},
    matchingMips: 0, differentMips: 0,
    fields: Object.fromEntries(fields.map(f => [f, histogram()])),
    stages: Object.fromEntries(stages.map(f => [f, histogram()])),
    modes: {}, combinations: {}, coverage: {linearSingleLayer: 0, linearArray: 0, linearTrimChanged: 0, tail: 0, noTail: 0, firstTailZero: 0, msaa: 0, singleLevel: 0, fullChain: 0, truncatedChain: 0, mip15: 0}};
}
const output = {
  schema_version: 1, kind: 'gfx12-revised-functional-comparison', seed: opts.seed, seedHex: '0x' + opts.seed.toString(16),
  requestedRandomConfigurations: opts.count, palCommit: 'c5e800072a32f68b6ccc4422936d96167c6e0728',
  branch: 'ADDR_GFX12_SHARED_BUILD=0', sourceDocumentSha256: EXPECTED['ADDRLIB.md'],
  sourceHashes: {...EXPECTED, 'scripts/mipmap_compare/generate.cjs': sha('scripts/mipmap_compare/generate.cjs'),
    'scripts/mipmap_compare/verify_gfx12_revision.cjs': sha('scripts/mipmap_compare/verify_gfx12_revision.cjs')},
  method: 'One Node.js process, exact integer functional evaluation. Revised document formulas vs independent archived PAL GFX12 C++ transcription. No C++ compilation, RTL simulation or synthesis.',
  normalization: 'slice*2^(e+s) to bytes (s=0 for Linear/3D); mip_offset_b*256 to macroBlockOffset; no-tail=17; Linear l2_ms and l2_blk_w are derived 128B rendering values, not raw physical blockExtent.',
  contract: {maxmip: [0, 15], randomWidthHeight: [1, 16384], random3DDepth: [1, 2048], elementBytes: [1, 2, 4, 8, 16], samples: [1, 2, 4, 8],
    resources: 'Linear non-3D; 2D swizzles use 2D; 3D swizzles use 3D. MSAA only single-level tiled 2D. Default flags, uncompressed elements, no custom pitch/height or denseSliceExact.'},
  random: stats(), directed: stats(), probes: stats(), examples: [], counterexamples: [], rejectedExamples: [],
  invariance: {coordinateConfigurations: 0, coordinateFieldChecks: 0, nonLinearDepthConfigurations: 0, nonLinearDepthFieldChecks: 0},
  outputDigestFormat: 'For every comparable mip, JSON array [group, raw12Input, normalizedDocument9, normalizedReference9] + LF; rejected inputs use [group, config, eligibility] + LF; BigInt decimal strings.',
  limitations: ['Finite sampled domain, not a proof for all inputs.', 'Both sides are functional transcriptions, not direct execution of compiled upstream C++.',
    'Only mipmap module outputs and macro-pitch adapter checked; no full texel-address pipeline, RTL timing or synthesis.', 'Undefined RTL truncation is not invented. Products, offsets and masks use BigInt.']
};
function stage(st, name, same) {st.stages[name][same ? 'match' : 'difference']++;}
function check(i, group, sample = false) {
  const st = output[group], eligibility = legal(i);
  st.configurations++;
  if (eligibility.status !== 'comparable') {
    st.classes[eligibility.status]++;
    if (output.rejectedExamples.length < 12) output.rejectedExamples.push({group, input: gen.rawInput(i), eligibility});
    hashStream.update(json([group, i, eligibility]) + '\n');
    return;
  }
  st.comparableConfigurations++;
  const base = doc.surface(i), s = revised(i, base), r = gfx12.surface(i);
  const combo = [i.mode, i.e, i.s].join('/');
  st.combinations[combo] = (st.combinations[combo] || 0) + 1;
  const mode = st.modes[i.mode] ||= {configurations: 0, mips: 0, differentMips: 0};
  mode.configurations++;
  const cov = st.coverage, full = Math.floor(Math.log2(Math.max(i.W, i.H, s.b.thick ? i.D : 1)));
  if (s.b.linear) cov[i.D === 1 ? 'linearSingleLayer' : 'linearArray']++;
  if (s.sliceBlockDrop) cov.linearTrimChanged++;
  cov[s.first <= i.maxmip ? 'tail' : 'noTail']++;
  if (s.first === 0) cov.firstTailZero++;
  if (i.s) cov.msaa++;
  cov[i.maxmip === 0 ? 'singleLevel' : i.maxmip === full ? 'fullChain' : 'truncatedChain']++;
  if (i.maxmip === 15) cov.mip15++;
  stage(st, 'block_dimensions', (s.b.linear ? [8 - i.e, 0, 0] : s.b.logs).every((v, k) => v === r.b.logs[k]));
  stage(st, 'tail_capacity', s.cap === r.cap);
  stage(st, 'first_tail_effective', (s.first <= i.maxmip ? s.first : 17) === (r.first <= i.maxmip ? r.first : 17));
  let differs = false;
  for (let m = 0; m <= i.maxmip; m++) {
    const a = documentVector(s, m), b = referenceVector(r, i, m);
    st.mips++; mode.mips++;
    let mipDiffers = false;
    for (let k = 0; k < fields.length; k++) {
      const same = a[k] === b[k];
      st.fieldComparisons++;
      st.fields[fields[k]][same ? 'match' : 'difference']++;
      if (!same) mipDiffers = true;
    }
    st[mipDiffers ? 'differentMips' : 'matchingMips']++;
    if (mipDiffers) {
      differs = true; mode.differentMips++;
      if (output.counterexamples.length < 20) output.counterexamples.push({group, ...record(i, m, s, r, 'numeric_difference')});
    }
    stage(st, 'mip_dimensions', s.mipSizes[m].every((v, k) => v === r.mipSizes[m][k]));
    stage(st, 'pitch', a[0] === b[0]);
    stage(st, 'slice_contribution_bytes', s.bytesPerMip[m] === r.bytesPerMip[m]);
    stage(st, 'macro_offset_bytes', a[3] === b[3]);
    stage(st, 'address_pitch_blocks', pitchBlocks(s, m) === base.pitch[m] / 2 ** base.b.logs[0]);
    hashStream.update(json([group, gen.rawInput(i, m), a, b]) + '\n');
  }
  st.classes[differs ? 'numeric_difference' : 'match']++;
  if (sample && output.examples.length < 12) output.examples.push(record(i, i.mip ?? 0, s, r, differs ? 'numeric_difference' : 'match'));
  // First 100 random IDs cover each mode/element/sample combination exactly once.
  if (group === 'random' && Number(i.id.slice(1)) < 100) {
    for (const coord of ['x', 'y', 'z', 'coordS']) {
      const changed = revised({...i, [coord]: i[coord] === 0 ? 1 : 0});
      for (let m = 0; m <= i.maxmip; m++) {
        assert.deepEqual(doc.outputs(changed, m), doc.outputs(s, m), coord + ' affected layout');
        output.invariance.coordinateFieldChecks += 9;
      }
    }
    output.invariance.coordinateConfigurations++;
    if (!s.b.linear) {
      const changed = revised({...i, D: i.D === 1 ? 2 : 1});
      for (let m = 0; m <= i.maxmip; m++) {
        assert.deepEqual(doc.outputs(changed, m), doc.outputs(s, m), 'Non-linear depth affected layout');
        output.invariance.nonLinearDepthFieldChecks += 9;
      }
      output.invariance.nonLinearDepthConfigurations++;
    }
  }
}

const directedDoc = JSON.parse(fs.readFileSync(path.join(root, 'docs/gfx12_revision_inputs.json'), 'utf8'));
const directed = directedDoc.inputs.map(row => {
  if (!Array.isArray(row)) return row;
  const c = Object.fromEntries(directedDoc.columns.map((key, k) => [key, row[k]]));
  return {id: c.id, mode: directedDoc.modes[c.modeIndex], e: c.e, s: c.s,
    W: c.W, H: c.H, D: c.D, maxmip: c.maxmip, mip: c.selectedMip};
});
assert(Array.isArray(directed), 'Missing directed inputs');
for (const c of directed) {
  const named = gen.trusted.find(v => v.id === c.id);
  check({x: 0, y: 0, z: 0, coordS: 0, ...named, ...c}, 'directed', c.id.startsWith('case'));
}
// Explicit contract probes are counted as rejected, never as matched.
for (const c of gen.directed()) if (legal(c).status !== 'comparable') check(c, 'probes');
for (let id = 0; id < opts.count; id++) {
  check(gen.random(opts.seed, id), 'random', id < 5);
  if ((id + 1) % 100000 === 0) process.stderr.write((id + 1) + '/' + opts.count + ' configurations; ' + output.random.differentMips + ' differing mips\n');
}
for (const group of ['random', 'directed', 'probes']) {
  const st = output[group];
  assert.equal(Object.values(st.classes).reduce((a, b) => a + b, 0), st.configurations, 'Unclassified configuration');
  assert.equal(st.matchingMips + st.differentMips, st.mips);
  assert.equal(st.fieldComparisons, st.mips * 9);
}
output.outputSha256 = hashStream.digest('hex');
output.elapsedSeconds = Number(process.hrtime.bigint() - started) / 1e9;
output.runtime = {node: process.version, platform: process.platform, arch: process.arch};
const groups = [output.random, output.directed, output.probes];
output.status = groups.some(st => st.differentMips || Object.values(st.stages).some(v => v.difference)) ? 'FAIL' : 'PASS';
output.totals = {generatedConfigurations: groups.reduce((a, s) => a + s.configurations, 0), comparableConfigurations: groups.reduce((a, s) => a + s.comparableConfigurations, 0),
  mips: groups.reduce((a, s) => a + s.mips, 0), fieldComparisons: groups.reduce((a, s) => a + s.fieldComparisons, 0), differingMips: groups.reduce((a, s) => a + s.differentMips, 0)};
if (opts.out) {
  const target = path.resolve(root, opts.out);
  fs.mkdirSync(path.dirname(target), {recursive: true});
  fs.writeFileSync(target, json(output, true) + '\n', 'utf8');
}
console.log(json({status: output.status, seed: output.seedHex, randomConfigurations: output.random.configurations, ...output.totals,
  elapsedSeconds: output.elapsedSeconds, outputSha256: output.outputSha256, resultFile: opts.out}, true));
if (output.status !== 'PASS') process.exitCode = 1;

