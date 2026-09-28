'use strict';
// Bounded arithmetic checks for the Markdown teaching examples; not RTL.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const assert = require('assert/strict');
const doc = require('./mipmap_compare/document.cjs');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'ADDRLIB.md'), 'utf8');
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(path.join(root, p))).digest('hex');
const stageNeutral = s => s.replace(/\/\/[sS]\d+\s*(?:stage|->\s*[sS]\d+)/g, '').replace(/\s+/gu, '');
assert.equal(stageNeutral(source), stageNeutral(fs.readFileSync(path.join(root, 'docs/baselines/ADDRLIB_pre_gfx12_20260924.md'), 'utf8')));

function bitTable(mode) {
  const row = source.split(/\r?\n/).find(s => s.startsWith('| {`' + mode + ', AA_1X, BPE_1}'));
  assert(row, mode);
  return row.split('|')[2].trim().replace(/[{}]/g, '').split(',').map(s => {
    const m = s.trim().match(/^([xyzs])\[(\d+)\]$/);
    assert(m, s); return [m[1], Number(m[2])];
  });
}
function mapBits(table, xyzs) {
  return table.reduce((v, [axis, bit]) => (v << 1n) | ((BigInt(xyzs[axis]) >> BigInt(bit)) & 1n), 0n);
}
function origin(i, surface, m) {
  assert.equal(i.e, 0); assert.equal(i.s, 0);
  const relative = m < surface.first ? 17 : m - surface.first;
  const reverse = surface.cap - relative - 1;
  const code = reverse < 0 ? 0n : reverse > 6 ? 16n << BigInt(reverse) : BigInt(reverse) << 8n;
  let xm = 0, ym = 0;
  for (let k = 0; k < 6; k++) {
    xm += Number((code >> BigInt(9 + 2 * k)) & 1n) * 2 ** k;
    ym += Number((code >> BigInt(8 + 2 * k)) & 1n) * 2 ** k;
  }
  if (surface.b.L & 1) [xm, ym] = [ym, xm];
  const microLogs = surface.b.thick ? [3, 2, 3] : [4, 4, 0];
  return {relative, reverse, reverse7: reverse & 127, code,
    microLogs, microCoordinates: [xm, ym], xyz: [(xm * 2 ** microLogs[0]) & 1023, (ym * 2 ** microLogs[1]) & 1023, 0]};
}
function access(i, surface, table, m, xyz, base = 0x30000000n) {
  const o = origin(i, surface, m);
  const sheet = xyz.map((v, a) => v + o.xyz[a]);
  const [lw, lh, ld] = surface.b.logs;
  const pitch = BigInt(surface.pitch[m]);
  const pitch_b = pitch >> BigInt(lw);
  const slice_b = surface.slice >> BigInt(surface.b.bws + lh);
  const [xb, yb, zb] = xyz.map((v, a) => BigInt(Math.floor(v / 2 ** [lw, lh, ld][a])));
  const slice_times_z_l = (slice_b & 65535n) * zb;
  const slice_times_z_h = (slice_b >> 16n) * zb;
  const pitch_times_y = pitch_b * yb;
  const blk_index_pitch = pitch_times_y + xb;
  const blk_index_slice = slice_times_z_l + (slice_times_z_h << 16n);
  const l2_ms_slice = Math.max(surface.b.L, 8);
  const blk_index = (blk_index_pitch << BigInt(surface.b.L)) + (blk_index_slice << BigInt(l2_ms_slice));
  const blk_offset = mapBits(table, {x: sheet[0], y: sheet[1], z: sheet[2], s: 0});
  const baseAddr256B = base >> 8n;
  const ms_mask_128B = (1n << BigInt(surface.b.L - 7)) - 1n;
  const ms_mask_256B = ms_mask_128B >> 1n;
  const swizzle_bits_256B = (baseAddr256B & 4095n) & ms_mask_256B;
  // Explicit 12-bit unsigned low field. All selected bases have this field zero.
  const baseAddr256B_out = (baseAddr256B & ~4095n) | ((baseAddr256B & 4095n) & ((~ms_mask_128B & 4095n) >> 1n));
  const mip_offset_b = surface.offset[m];
  const mipoffset_BaseAddr256B_out = baseAddr256B_out + mip_offset_b;
  const blk_offset_final = blk_offset & 255n;
  const swizzle_bits = ((blk_offset >> 8n) & ms_mask_256B) ^ swizzle_bits_256B;
  const addr_offset = blk_index | (swizzle_bits << 8n) | blk_offset_final;
  const address_final = (mipoffset_BaseAddr256B_out << 8n) + addr_offset;
  assert.equal(swizzle_bits_256B, 0n);
  assert.equal(addr_offset, blk_index + blk_offset);
  const semanticBlockNumber = zb * slice_b + yb * pitch_b + xb;
  assert.equal(address_final, base + (mip_offset_b << 8n) + (semanticBlockNumber << BigInt(surface.b.L)) + blk_offset);
  return {mip: m, xyz, origin: o, sheet, pitch, slice: surface.slice, mip_offset_b,
    pitch_b, slice_b, xb, yb, zb, slice_times_z_l, slice_times_z_h, pitch_times_y,
    blk_index_pitch, blk_index_slice, blk_index, baseAddr256B, ms_mask_128B, ms_mask_256B,
    swizzle_bits_256B, baseAddr256B_out, mipoffset_BaseAddr256B_out, blk_offset,
    blk_offset_final, swizzle_bits, addr_offset, address_final, mipid_in_tail: Number(o.relative !== 17)};
}

module.exports = {bitTable, mapBits, origin, access};

if (require.main === module) {
const input = {mode: 'SW_4KB_2D', W: 256, H: 256, D: 1, e: 0, s: 0, maxmip: 8};
const surface = doc.surface(input), table = bitTable(input.mode);
assert.equal(surface.first, 3); assert.equal(surface.cap, 8); assert.equal(surface.sliceBytes, 90112n);
const ordinary = access(input, surface, table, 1, [69, 70, 0]);
const tail = access(input, surface, table, 4, [5, 6, 0]);
assert.equal(ordinary.address_final, 0x30005039n);
assert.equal(tail.address_final, 0x30000639n);
assert.deepEqual(tail.origin.xyz, [16, 32, 0]);
// Enumerate the finite primary example to check occupancy, macro boundaries and tail aliases.
const occupied = new Set();
const mips = [];
for (let m = 0; m <= input.maxmip; m++) {
  const side = Math.max(1, input.W >> m), o = origin(input, surface, m);
  const pitchBlocks = BigInt(surface.pitch[m] / 64);
  for (let y = 0; y < side; y++) for (let x = 0; x < side; x++) {
    const blk = BigInt(Math.floor(y / 64)) * pitchBlocks + BigInt(Math.floor(x / 64));
    const offset = (surface.offset[m] << 8n) + blk * 4096n + mapBits(table, {x: x + o.xyz[0], y: y + o.xyz[1], z: 0, s: 0});
    assert(offset >= 0n && offset < surface.sliceBytes);
    const key = Number(offset); assert(!occupied.has(key), `address alias at mip${m}: ${offset}`); occupied.add(key);
  }
  mips.push({mip: m, side, pitch: surface.pitch[m], blocks: surface.sizes[m],
    offsetBytes: surface.offset[m] << 8n, origin: o});
}
assert.equal(occupied.size, 87381);

const classicInput = {mode: 'SW_256KB_3D', W: 256, H: 256, D: 256, e: 0, s: 0, maxmip: 12};
const classicSurface = doc.surface(classicInput), classicTable = bitTable(classicInput.mode);
const classic0 = access(classicInput, classicSurface, classicTable, 0, [69, 134, 195]);
const classic4 = access(classicInput, classicSurface, classicTable, 4, [5, 6, 3]);
assert.equal(classic0.address_final, 0x31440175n); assert.equal(classic4.address_final, 0x30008175n);

const result = {source_sha256: hash('ADDRLIB.md'), model_sha256: hash('scripts/mipmap_compare/document.cjs'),
  stage_only_change_verified: true, input, primary: {ordinary, tail, mips,
    firstTail: surface.first, capacity: surface.cap, slice: surface.slice, chainBytes: surface.sliceBytes,
    outputs_mip1: doc.outputs(surface, 1), outputs_mip4: doc.outputs(surface, 4),
    enumeratedTexels: occupied.size, addressCollisions: 0, unusedBytes: Number(surface.sliceBytes) - occupied.size},
  classic3d: {input: classicInput, ordinary: classic0, tail: classic4},
  assumptions: ['BPE1, one sample, zero swizzle seed, selected modes only',
    'MAXMIP=17; reverse is signed 7 bits; origin code is 20 bits; origins are masked to 10 bits',
    'Byte address 48 bits, base field 40 bits, low base field 12 bits; selected values do not overflow',
    'BigInt products and addresses; no truncation of unspecified intermediate widths',
    'Stage tags document ownership only; no sequential execution or register model'],
  scope: 'Finite primary texture address enumeration and two 3D accesses; not upstream C++ comparison, RTL simulation, or timing verification'};
const output = path.join(root, 'docs/ADDRLIB_MAS_REWRITE_CHECK.json');
fs.writeFileSync(output, JSON.stringify(result, (_, v) => typeof v === 'bigint' ? v.toString() : v, 2) + '\n');
console.log(JSON.stringify({primary: ['0x' + ordinary.address_final.toString(16), '0x' + tail.address_final.toString(16)],
  enumeratedTexels: occupied.size, addressCollisions: 0, classic3d: ['0x' + classic0.address_final.toString(16), '0x' + classic4.address_final.toString(16)], output}, null, 2));

}
