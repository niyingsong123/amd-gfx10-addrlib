'use strict';
// Cross-platform equivalent of verify_trusted_baseline.ps1; checks bytes, not algorithms.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'docs/TRUSTED_BASELINE.json'),'utf8'));
if(manifest.schema_version!==1||!manifest.files?.length) throw Error('Invalid baseline manifest');
for(const entry of manifest.files) {
 const bytes=fs.readFileSync(path.join(root,entry.path));
 const hash=crypto.createHash('sha256').update(bytes).digest('hex');
 if(bytes.length!==entry.bytes||hash.toUpperCase()!==entry.sha256.toUpperCase())
  throw Error('Trusted file changed: '+entry.path);
 console.log('OK: '+entry.path);
}
console.log('PASS: '+manifest.files.length+' trusted files unchanged; algorithm correctness is not implied.');
