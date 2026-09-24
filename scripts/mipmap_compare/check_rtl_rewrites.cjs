'use strict';
// Algebraic checks for timing candidates; no RTL simulation, synthesis or STA.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const doc = require('../../regression_0924/cloud/scripts/mipmap_compare/document.cjs');
const source = fs.readFileSync(path.join(root, 'ADDRLIB_GFX12.md'));
const sourceSha256 = crypto.createHash('sha256').update(source).digest('hex');
assert.equal(sourceSha256, 'a6864bd26943078add333142bb40b87a9600b106572928f8b94621522ccacd8c');
const counts = {linearWidthParity: 0, halfHeightFromMinusOne: 0, tailExponentPrecompute: 0, thermometerEncoder: 0};
for (let e = 0; e <= 4; e++) {
  const b = 7 - e;
  for (let width = 1; width <= 65536; width++) {
    const oldParity = Math.ceil(width / 2 ** b) % 2;
    const inputBit = (Math.floor((width - 1) / 2 ** b)) % 2;
    assert.equal(1 - inputBit, oldParity);
    counts.linearWidthParity++;
  }
}
for (let height = 1; height <= 65536; height++) {
  const hMinusOne = height - 1;
  assert.equal(Math.floor(hMinusOne / 2) + (hMinusOne % 2), Math.floor(height / 2));
  counts.halfHeightFromMinusOne++;
}
for (const mode of Object.keys(doc.MODE)) for (let e = 0; e <= 4; e++) {
  const b = doc.block({mode, e, s: 0});
  if (b.L <= 8) continue; // Linear and 256B modes have no tail.
  const U = (b.thick ? [3, 2, 2, 2, 1] : [4, 4, 3, 3, 2])[e];
  const yBias = b.thick && [12, 18].includes(b.L);
  const T = b.logs[0] - (yBias ? 0 : 1);
  assert(T >= U);
  for (let first = 0; first <= 15; first++) for (let m = first; m <= 15; m++) {
    const oldExp = (m - first < T - U) ? T - (m - first) : U;
    const base = first + T, stop = base - U;
    const newExp = m < stop ? base - m : U;
    assert.equal(newExp, oldExp);
    assert(newExp >= 0 && newExp <= 8);
    counts.tailExponentPrecompute++;
  }
}
for (let first = 0; first <= 17; first++) {
  const tail = Array.from({length: 17}, (_, m) => m >= first);
  let oldIndex = 17, encoded = 0, any = false;
  for (let m = 0; m < 17; m++) {
    if (m === 0 ? tail[0] : tail[m] !== tail[m - 1]) oldIndex = m;
    const firstHot = tail[m] && (m === 0 || !tail[m - 1]);
    if (firstHot) { encoded |= m; any = true; }
  }
  assert.equal(any ? encoded : 17, oldIndex);
  counts.thermometerEncoder++;
}
const result = {status: 'PASS', sourceDocument: 'ADDRLIB_GFX12.md', sourceSha256, counts,
  total: Object.values(counts).reduce((a, b) => a + b, 0),
  method: 'Exhaustive integer identity checks on declared dimensions/exponents and all 17-bit monotonic tail vectors. Does not evaluate physical delay, RTL timing, synthesis or pipeline behavior.',
  assumptions: ['W,H are actual dimensions 1..65536; minus-one inputs are exact, without truncation.',
    'Linear rendering exponent is 7-e, e=0..4. H/2 result must retain 16 bits at H=65536.',
    'Tail mode is legal and single-sampled; precomputed base/stop retain at least five unsigned bits.',
    'Parallel tail encoder applies only to a monotonic tail vector; forced no-tail modes still override to 17.']};
if (process.argv[2] === '--out') {
  const target = path.resolve(root, process.argv[3]);
  fs.mkdirSync(path.dirname(target), {recursive: true});
  fs.writeFileSync(target, JSON.stringify(result, null, 2) + '\n');
}
console.log(JSON.stringify(result, null, 2));
