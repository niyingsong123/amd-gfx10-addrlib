'use strict';
// Migration smoke check only. This is NOT the requested randomized validation.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
require('../verify_trusted_baseline.cjs');
const provenance=require('./provenance.json');
for(const f of provenance.files) {
 const bytes=fs.readFileSync(path.join(__dirname,f.local_path));
 assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),f.sha256,f.local_path);
 assert.equal(crypto.createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex'),f.git_blob,f.local_path);
}
const doc=require('./document.cjs'),G=require('./generate.cjs');
for(const c of G.trusted) assert.deepEqual(doc.outputs(doc.surface(c),c.mip),c.expected,c.id);
assert.equal(G.combos.length,100);
for(const file of ['gfx10.cjs','gfx12.cjs','compare.cjs']) require('./'+file);
console.log('PASS: 9 upstream files verified; 3 document regressions; 100 generator combinations.');
console.log('Reference ports remain unreviewed. Randomized comparison has not run.');
