"""Draw the final six marked figures with standalone technical labels.

Sources and verification records live in JSON/README, never in image captions.
Original source images are preserved. --apply changes only matched images and
the corresponding marker text in ADDRLIB硬件算法.md.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import re
import subprocess
import sys
from render_mipmap_memory import Canvas, ROOT, OUT, INK, MUTED, LINE, PALE, COLORS, FILLS, runtime_node
from redraw_mas_marked_diagrams import header, footer, flow

ENTRIES=[
 ('image-20260913170701792.png','21_addrlib_interface','AddrLib：输入参数与地址输出'),
 ('image-20260913171528469.png','22_texture_sample_reuse','采样密度与纹理邻点复用'),
 ('image-20260913172742516.png','23_mipmap_tail_packing','mipmap tail：共享空间与内存顺序'),
 ('image-20260914203649543.png','24_swizzle_mode_decode','swizzle 模式解码'),
 ('image-20260914203740508.png','25_macro_block_size','宏块大小、对数与掩码'),
 ('image-20260914202847708.png','26_macro_block_dimensions','宏块宽高深计算'),
]


def interface():
 c=Canvas(1440,840,ENTRIES[0][2],'逻辑坐标、元素格式、采样数、表面参数和mip层级经过地址计算，输出字节地址和tail标志。')
 header(c,'ADDRESS INTERFACE','AddrLib：从逻辑坐标到纹理存储地址','坐标和布局参数共同决定访问位置；当前 mip 的局部坐标直接参与寻址。')
 groups=[(190,96,'访问点',['x / y / z / s']),
         (302,110,'格式与采样',['log2_element_bytes','log2_num_samples']),
         (428,134,'表面描述',['sw_mode / baseAddr256B','mip0 宽、高、深（减一编码）']),
         (578,98,'层级选择',['mip_level / maxmip'])]
 for y,h,label,values in groups:
  c.rect(56,y,446,h,FILLS[0],LINE);c.rect(56,y,5,h,COLORS[0])
  c.text(77,y+13,label,21,COLORS[0],True)
  for j,value in enumerate(values):c.text(77,y+48+j*29,value,20)
  c.line(502,y+h/2,555,y+h/2,MUTED,1.5)
 c.line(555,238,555,627,MUTED,1.5);c.arrow(555,432,630,432,MUTED,2)
 c.rect(649,290,357,275,FILLS[2],LINE);c.rect(649,290,357,5,COLORS[2])
 c.text(679,321,'AddrLib',37,COLORS[2],True)
 for j,t in enumerate(['mipmap 参数 / tail 原点','块内 swizzle / 宏块索引','基址与各级偏移合成']):c.text(679,397+j*46,t,21)
 c.arrow(1024,432,1100,432,MUTED,2)
 c.rect(1115,333,269,213,FILLS[1],LINE);c.rect(1115,333,269,5,COLORS[1])
 c.text(1137,361,'address_final',22,COLORS[1],True)
 c.text(1137,399,'当前元素的字节地址',18,MUTED)
 c.text(1137,450,'mipid_in_tail',22,COLORS[1],True)
 c.text(1137,490,'当前 mip 是否位于 tail',18,MUTED)
 footer(c,740,'输入描述“访问哪个元素、采用什么布局”，输出给出存储地址。','baseAddr256B 的单位为 256 B；address_final 的单位为字节。')
 c.save(ENTRIES[0][1])


def sampling():
 c=Canvas(1440,940,ENTRIES[1][2],'四次双线性采样都访问16个邻点。分散布局涉及16个不同texel；相邻布局复用中心和边缘texel，仅涉及9个不同texel。')
 header(c,'TEXTURE SAMPLING','采样密度匹配时，相邻像素可复用更多纹理数据','四次双线性采样的邻点示意：每次访问 4 个邻近 texel。')
 sets=[(6,[(.5,.5),(4.5,.5),(.5,4.5),(4.5,4.5)],(115,298),67,'过细纹理：邻点分散',16),
       (3,[(.5,.5),(1.5,.5),(.5,1.5),(1.5,1.5)],(940,332),136,'匹配 mip：邻点可复用',9)]
 counts=[]
 for index,(n,queries,(x0,y0),step,title,expected) in enumerate(sets):
  left=56 if index==0 else 790;c.text(left,199,title,28,bold=True)
  count=Counter();edges=[]
  for qx,qy in queries:
   x=int(qx);y=int(qy)
   for p in [(x,y),(x+1,y),(x,y+1),(x+1,y+1)]:count[p]+=1;edges.append(((qx,qy),p))
  assert sum(count.values())==16 and len(count)==expected
  counts.append(dict(sample_positions=queries,neighbor_accesses=16,distinct_texels=len(count),reuse_counts=[dict(x=x,y=y,count=v) for (x,y),v in count.items()]))
  for (qx,qy),(px,py) in edges:c.line(x0+qx*step,y0+qy*step,x0+px*step,y0+py*step,LINE,1.5)
  for y in range(n):
   for x in range(n):
    v=count[(x,y)];px=x0+x*step;py=y0+y*step
    c.dot(px,py,17,COLORS[1] if v else '#DDE4E8')
    if v:c.text(px,py-12,str(v),18,'#FFFFFF',True,'middle')
  for qx,qy in queries:c.dot(x0+qx*step,y0+qy*step,10,COLORS[0])
  c.text(left,696,f'16 次邻点访问 → {expected} 个不同 texel',25,COLORS[index],True)
 c.line(725,195,725,750)
 c.dot(77,801,13,COLORS[1]);c.text(102,787,'被访问的 texel：数字为次数',20)
 c.dot(570,801,10,COLORS[0]);c.text(593,787,'目标采样位置',20)
 c.dot(956,801,13,'#DDE4E8');c.text(981,787,'本组采样未使用的 texel',20)
 c.text(56,858,'邻点复用有助于减少重复数据读取；实际 cache miss 还受地址布局、过滤方式和缓存配置影响。',21,MUTED)
 c.text(56,901,'连线只表示采样与邻点的关系，不表示物理内存中的排列。',18,MUTED)
 c.save(ENTRIES[1][1]);return counts


def tail_data():
 inp=dict(mode='SW_4KB_2D',W=256,H=256,D=1,e=0,s=0,maxmip=8)
 js="const s=require('./scripts/mipmap_compare/document.cjs').surface(JSON.parse(process.argv[1]));console.log(JSON.stringify(s,(_,v)=>typeof v==='bigint'?v.toString():v));"
 model=json.loads(subprocess.check_output([runtime_node(),'-e',js,json.dumps(inp)],cwd=ROOT,text=True,encoding='utf-8'))
 assert model['first']==3 and model['cap']==8 and model['b']['logs']==[6,6,0]
 assert [int(v) for v in model['sizes'][:9]]==[16,4,1,1,0,0,0,0,0]
 assert int(model['sliceBytes'])==22*4096
 def sw(x,y):
  value=0
  for bit in 'x5 y5 x4 y4 y3 x3 y2 y1 x2 y0 x1 x0'.split():value=(value<<1)|((dict(x=x,y=y)[bit[0]]>>int(bit[1]))&1)
  return value
 rows=[];addresses=set()
 for m in range(3,9):
  reverse=8-(m-3+1);code=(16<<reverse) if reverse>6 else reverse<<8
  x=sum(((code>>(9+2*k))&1)<<k for k in range(6))*16
  y=sum(((code>>(8+2*k))&1)<<k for k in range(6))*16
  side=256>>m
  for yy in range(side):
   for xx in range(side):
    a=sw(x+xx,y+yy);assert a<4096 and a not in addresses;addresses.add(a)
  rows.append(dict(mip=m,side=side,origin=[x,y],origin_code=code,origin_bytes=sw(x,y)))
 assert len(addresses)==1365
 return dict(input=inp,macro_dimensions=[64,64,1],macro_bytes=4096,first_tail_mip=3,tail_capacity=8,
             tail_mips=rows,tail_texel_bytes=1365,tail_address_collisions=0,chain_blocks=22,chain_bytes=90112,
             separately_aligned_tail_bytes=24576,shared_tail_bytes=4096,
             source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['ADDRLIB.md','scripts/mipmap_compare/document.cjs']},
             assumptions=['MAXMIP=17; integer arithmetic has sufficient width','zero base and swizzle seed','micro block 16x16x1; origin generation uses 20-bit offset field'],
             verification='single illustrative configuration; tail addresses enumerated; not RTL or a random regression')


def packing(data):
 c=Canvas(1440,980,ENTRIES[2][2],'二维256乘256纹理的mip3至8进入同一个4KiB tail，六个小mip共1365字节；整链低地址依次tail、mip2、mip1、mip0，共22块。')
 header(c,'MIPMAP TAIL','小 mip 共享一个 tail，避免逐级占满整个宏块','示例：256×256、mip0…8、SW_4KB_2D、1 BPE / 1X；macro = 64×64 = 4 KiB。')
 c.text(56,196,'如果每级分别按块分配',28,bold=True)
 c.text(56,240,'6 个宏块 = 24 KiB',25,COLORS[2],True)
 for j,row in enumerate(data['tail_mips']):
  x=56+(j%3)*176;y=295+(j//3)*171;m=row['mip'];side=row['side']
  c.rect(x,y,112,112,stroke=LINE,hatch=True)
  c.rect(x,y,side*112/64,side*112/64,FILLS[m%8],COLORS[m%8])
  c.text(x,y+126,f'mip{m} · {side}×{side}',19,COLORS[m%8],True)
 c.text(56,651,'有效数据合计仅 1365 B',24,bold=True)
 c.arrow(601,447,742,447,COLORS[3],2)
 c.text(672,402,'共享 tail',23,COLORS[3],True,'middle')
 c.text(791,196,'满足条件后打包进一个宏块',28,bold=True)
 c.text(791,240,'1 个宏块 = 4 KiB',25,COLORS[3],True)
 x0,y0,scale=791,295,5.5
 c.rect(x0,y0,64*scale,64*scale,stroke=LINE,hatch=True)
 for row in data['tail_mips']:
  m=row['mip'];x,y=row['origin'];side=row['side']
  c.rect(x0+x*scale,y0+y*scale,side*scale,side*scale,FILLS[m%8],COLORS[m%8],1.5)
  c.dot(x0+x*scale,y0+y*scale,3,COLORS[m%8])
 c.text(x0+32*scale+20,y0+45,'mip3',28,COLORS[3],True)
 c.text(x0+16*scale+8,y0+32*scale+24,'mip4',20,COLORS[4],True)
 for j,row in enumerate(data['tail_mips']):
  c.text(1170,311+49*j,f"m{row['mip']}  {tuple(row['origin'])}",20,COLORS[row['mip']%8],True)
 c.text(1166,275,'orig (X,Y)',20,bold=True)
 c.text(791,665,'填色为有效 texel；斜线为未使用坐标区。',18,MUTED)
 c.line(56,708,1384,708)
 c.text(56,732,'整条 mip 链的低→高地址顺序：22 个宏块 = 88 KiB',26,bold=True)
 bounds=[56,194,332,628,1384]
 for j,(m,label) in enumerate([(3,'Tail · 1块'),(2,'mip2 · 1块'),(1,'mip1 · 4块'),(0,'mip0 · 16块')]):
  c.rect(bounds[j],787,bounds[j+1]-bounds[j],60,FILLS[m],LINE)
  c.text((bounds[j]+bounds[j+1])/2,805,label,21,COLORS[m],True,'middle')
  c.text(bounds[j],861,['偏移 0','0x1000','0x2000','0x6000'][j],17,MUTED)
 c.text(1384,861,'末端 0x16000 B',17,MUTED,False,'end')
 c.text(56,914,'是否进入 tail 必须同时满足尺寸和层级容量限制，不能只凭有效数据量之和判断。',22,bold=True)
 c.text(56,952,'XY 坐标布局与字节地址条分别显示；地址条各段宽度不按容量比例绘制。',17,MUTED)
 c.save(ENTRIES[2][1])


def parameter_flows():
 flow(0,'swizzle 解码：把一个模式拆成独立的布局属性','块类别决定容量；布局类型区分 Linear、2D 与 3D。',
      ['sw_mode'],['① 解码块类别 blk_type','② 解码布局类型 sw_type','③ 派生 linear = (sw_type == SW_L)','例：SW_4KB_3D','→ SZ_4KB + SW_S_3D；linear=0'],
      ['blk_type','sw_type','派生 linear'],'同一个块大小，可以对应不同的二维或三维布局。','SW_LINEAR 对应 SZ_LIN / SW_L；普通 tiled 模式的 linear 为 0。',filename=ENTRIES[3][1])
 flow(0,'宏块大小：生成对数指数与地址掩码','l2_ms 描述字节大小的 log2；ms_mask_128B 描述相应低位范围。',
      ['blk_type'],['输出次序：l2_ms / l2_ms_128B / mask','SZ_LIN → 7 / 0 / 0x0','SZ_256B → 8 / 1 / 0x1','SZ_4KB → 12 / 5 / 0x1F','SZ_64KB → 16 / 9 / 0x1FF','SZ_256KB → 18 / 11 / 0x7FF'],
      ['l2_ms','l2_ms_128B','ms_mask_128B'],'字节大小、相对 128B 的指数和位掩码是三个不同的量。','例如 4 KiB = 2^12 B，包含 2^5 个 128B 单位，对应 5 位掩码 0x1F。',filename=ENTRIES[4][1])
 flow(0,'宏块维度：按布局把元素容量分配到 X / Y / Z','先扣除元素字节数和有效采样数，再计算宽、高、深的对数。',
      ['sw_type / linear','l2_ms','l2_eb / l2_ns'],['① 3D 或 Linear：有效 msaa=0','否则：有效 msaa=l2_ns','② E = l2_ms − (l2_eb + msaa)','③ 2D：分配宽高，并考虑奇偶修正','3D：按块大小、元素大小查表','Linear：宽指数=E，高、深指数=0'],
      ['l2_blk_w','l2_blk_h','l2_blk_d'],'输出采用 log2 表示；实际宽、高、深分别为 2 的对应指数。','二维块深度为 1，所以 l2_blk_d=0；三维块需要同时确定三个方向。',filename=ENTRIES[5][1])


def apply():
 p=ROOT/'ADDRLIB硬件算法.md';before=p.read_bytes();s=before.decode('utf-8');markers=list(re.finditer(r'//优化下面图[ \t]*',s))
 assert len(markers)==6, f'Inspect changed marker list: {len(markers)}'
 lookup={old:(name,title) for old,name,title in ENTRIES};changes=[];seen=set()
 for mark in markers:
  match=re.search(r'!\[[^\]]*\]\(([^)]+)\)',s[mark.end():]);assert match
  old=Path(match.group(1)).name;assert old in lookup and old not in seen;seen.add(old)
  name,title=lookup[old];assert (OUT/(name+'.svg')).exists()
  changes.extend([(mark.start(),mark.end(),''),(mark.end()+match.start(),mark.end()+match.end(),f'![{title}](assets/addrlib_mas/diagrams/{name}.svg)')])
 snapshot=ROOT/'build'/('ADDRLIB_MAS_before_remaining_'+hashlib.sha256(before).hexdigest()[:12]+'.md');snapshot.parent.mkdir(exist_ok=True)
 if not snapshot.exists():snapshot.write_bytes(before)
 for a,b,value in sorted(changes,reverse=True):s=s[:a]+value+s[b:]
 assert '//优化下面图' not in s
 p.write_bytes(s.encode('utf-8'))
 manifest=dict(before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
  replaced_images=6,removed_markers=6,figures=[dict(original=old,svg=name+'.svg',title=title,
  original_sha256=hashlib.sha256((ROOT/'assets/addrlib_mas/original'/old).read_bytes()).hexdigest()) for old,name,title in ENTRIES])
 (OUT/'mas_remaining_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Replaced 6 selected images and removed all 6 remaining markers.')


if __name__=='__main__':
 interface();counts=sampling();data=tail_data();packing(data);parameter_flows()
 (OUT/'mas_remaining_data.json').write_text(json.dumps(dict(sampling=counts,tail=data),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Rendered 6 SVG/PNG figures; verified tail occupancy and sampling counts.')
 if '--apply' in sys.argv:apply()
