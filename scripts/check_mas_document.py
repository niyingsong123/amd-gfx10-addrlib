"""Check the six-chapter document's tables, links and display constraints."""
from pathlib import Path
import re, json, hashlib, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
md=(ROOT/'ADDRLIB硬件算法.md').read_text(encoding='utf-8')
source=(ROOT/'ADDRLIB.md').read_text(encoding='utf-8')
data=json.loads((ROOT/'docs/ADDRLIB_MAS_3D_WALKTHROUGH_CHECK.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/'ADDRLIB.md')==data['sources']['ADDRLIB.md']
chapters=re.findall(r'^## 第[^\n]+',md,re.M)
assert len(chapters)==6
counts=[len(re.findall(r'^### ',p,re.M)) for p in re.split(r'^## 第',md,flags=re.M)[1:]]
assert counts==[3,3,4,3,4,4],counts
assert len(re.findall(r'^## 附录 ',md,re.M))==4
section22=md.split('### 2.2 ',1)[1].split('### 2.3 ',1)[0]
subsections22=re.findall(r'^#### (2\.2\.[1-4]) ',section22,re.M)
assert subsections22==['2.2.1','2.2.2','2.2.3','2.2.4'],subsections22
assert 'KiB' not in md
assert len(re.findall(r'^```',md,re.M))%2==0
assert not re.search(r'[\u200b\u200c\u200d\ufeff]',md)
visible=re.sub(r'!\[[^\]]*\]\([^)]+\)','',md)
assert not re.search(r'ADDRLIB\.md|GFX12|来源|引用|原稿|原图|原版|依据|优化|(?:docs|scripts|backup|addrlib)/',visible,re.I)
for block in re.findall(r'```[^\n]*\n(.*?)```',md,re.S):
    code='\n'.join(line.split('//')[0] for line in block.splitlines())
    assert not re.search(r'[\u4e00-\u9fff]',code),code

sourceRows=[]
for line in source.splitlines():
    if line.startswith('| {`SW_'):
        c=[p.strip() for p in line.split('|')[1:-1]]
        sourceRows.append((c[0].replace('`',''),c[1]))
actual=[]
appendix=md.split('## 附录 C：')[1].split('## 附录 D：')[0]
for line in appendix.splitlines():
    if line.startswith('| `{SW_'):
        c=[p.strip().strip('`') for p in line.split('|')[1:-1]]
        actual.append(tuple(c))
assert len(sourceRows)==100 and actual==sourceRows
sourceBlocks=[]
for line in source.splitlines():
    if re.match(r'^\| (4KB|64KB|256KB), (8|16|32|64|128)bpp\s*\|',line):
        c=[p.strip() for p in line.split('|')[1:-1]]
        if len(c)==5: sourceBlocks.append([c[0],c[2],c[3],c[4]])
actualBlocks=[]
for line in md.splitlines():
    if re.match(r'^\| (4KB|64KB|256KB), (8|16|32|64|128)bpp\s*\|',line):
        actualBlocks.append([p.strip() for p in line.split('|')[1:-1]])
assert len(actualBlocks)==15 and actualBlocks==sourceBlocks
for r in data['mips']:
    row=f"| {r['mip']} | {'×'.join(map(str,r['logical_dimensions']))} | {r['block_xy'][0]} / {r['block_xy'][1]} | {r['z_groups']} | {r['contribution']} |"
    assert row in md,row
bits=[str((int(data['visit']['blk_offset'])>>b)&1) for b in range(17,-1,-1)]
assert '| 本例值 | '+' | '.join(bits)+' |' in md
assert '0x304881D5' in md and '0x480000' in md and '0x81D5' in md

images=[]
for rel in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',md):
    p=ROOT/rel; assert p.is_file()
    tree=ET.parse(p)
    labels=' '.join(t.text or '' for t in tree.iter() if t.tag.endswith(('text','title','desc')))
    assert not re.search(r'ADDRLIB\s*/|addrlib/|来源|原图|依据|优化|\.md|scripts/',labels,re.I),(rel,labels)
    assert 'KiB' not in labels,rel
    images.append({'path':rel,'sha256':sha(p)})
assert len(images)==13
assert {Path(row['path']).stem for row in images} == {
    '09_texture_magnification', '10_texture_minification', '19_mipmap_volume_memory',
    '21_addrlib_interface', '22_texture_sample_reuse', '30_teaching_stages',
    '31_teaching_3d_tail_access', '32_macro_micro_swizzle', '33_tail_packing_3d',
    '34_address_compose', '11_standard_block_layout', '12_zorder_block_layout',
    '35_block_hierarchy'}
for block in re.findall(r'(?:^\|.*\n)+',md,re.M):
    lines=block.splitlines()
    widths=[len(re.split(r'(?<!\\)\|',s))-2 for s in lines]
    assert len(set(widths))==1,(lines[:2],widths)
result={'document_sha256':sha(ROOT/'ADDRLIB硬件算法.md'),'source_sha256':sha(ROOT/'ADDRLIB.md'),
        'chapters':6,'subsection_counts':counts,'section22_subsections':subsections22,'appendices':4,'swizzle_rows':100,'block_dimension_rows':15,
        'mip_layout_rows':len(data['mips']),'images':images,'source_annotations_in_body_or_images':0,
        'scope':'Document structure, exact source table comparison, checked mip data, links and visible image labels; numerical scope is in the walkthrough check JSON'}
(ROOT/'docs/ADDRLIB_MAS_DOCUMENT_CHECK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('images','scope')},ensure_ascii=False,indent=2))
