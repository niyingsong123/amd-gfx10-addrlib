"""Render section 2.2 concept diagrams, independently of the 3D address model."""
from pathlib import Path
import hashlib
import json
from render_mipmap_memory import Canvas, ROOT, INK, MUTED, LINE, PALE, COLORS, FILLS
from redraw_mas_marked_diagrams import standard, zorder, morton


def hierarchy():
    c=Canvas(1600,535,'纹理、宏块、微块与元素的包含关系',
             '从一张mip纹理逐层展开到宏块、微块与元素；只表达包含关系，不规定访问顺序。')
    c.text(64,26,'BLOCK HIERARCHY',16,MUTED,True)
    c.text(64,65,'先认识四层对象，再看各层怎样排列',38,INK,True)
    c.text(64,125,'每次展开一个对象，查看它包含的下一层；块的容量与几何尺寸是两个不同的量。',22,MUTED)
    entries=[('一张 mip 纹理','由多个宏块组成','具有有效宽、高、深'),
             ('宏块 · macro','具有固定字节容量','包含若干微块'),
             ('微块 · micro','较小的布局单位','本文采用 256 B 微块'),
             ('元素 · element','实际存储的数据单位','每个元素占 BPE 字节')]
    for i,(name,detail,note) in enumerate(entries):
        x=64+i*390;color=COLORS[i];fill=FILLS[i]
        c.rect(x,235,300,170,fill,LINE)
        c.rect(x,235,300,5,color)
        c.text(x+20,258,name,26,color,True)
        c.text(x+20,314,detail,23,INK)
        c.text(x+20,359,note,21,MUTED)
        if i<3:
            c.arrow(x+312,326,x+376,326,MUTED,2)
            c.text(x+344,283,'展开',18,MUTED,False,'middle')
    c.rect(64,447,1472,61,PALE)
    c.text(84,465,'包含关系确定对象的层次；排序规则确定同一层对象在内存中的先后位置。',23,INK,True)
    c.save('35_block_hierarchy')


def render():
    # These are the two explicit teaching layouts drawn by standard()/zorder(),
    # not a claim that a named production sw_mode uses either complete formula.
    micro_ids={morton(x,y,2) for y in range(4) for x in range(4)}
    standard_offsets={morton(x//16,y//16,2)*256+(y%16)*16+(x%16)
                      for y in range(64) for x in range(64)}
    zorder_offsets={morton(x,y,6) for y in range(64) for x in range(64)}
    assert micro_ids==set(range(16))
    assert standard_offsets==zorder_offsets==set(range(4096))
    assert morton(2,1,2)==6
    hierarchy();standard();zorder()
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    result={
        'scope':'Conceptual 2D layouts in figures 11/12 and the containment diagram 35; no RTL or upstream validation.',
        'sources':{p:sha(ROOT/p) for p in ['ADDRLIB.md','scripts/redraw_mas_marked_diagrams.py',
                                          'scripts/render_mas_block_concepts.py']},
        'input':{'texture_xy':[256,256],'bytes_per_element':1,'samples':1,
                 'macro_xy':[64,64],'macro_bytes':4096,'micro_xy':[16,16],'micro_bytes':256},
        'morton_4x4':[[morton(x,y,2) for x in range(4)] for y in range(4)],
        'zorder_visible_8x8':[[morton(x,y,6) for x in range(8)] for y in range(8)],
        'checks':{'micro_ids':len(micro_ids),'standard_macro_offsets':len(standard_offsets),
                  'zorder_macro_offsets':len(zorder_offsets),'morton_2_1':6},
        'units':{'coordinates':'elements or explicitly labelled block coordinates',
                 'diagram_numbers':'local order at the displayed level; not complete addresses',
                 'KB':'1024 bytes'},
        'assumptions':['Unsigned coordinates within the drawn grids; enough-width Python integers.',
                       'Morton interleaves x into even bits and y into odd bits.',
                       'Standard is the depicted micro-Morton / intra-micro-raster teaching layout.',
                       'Specific SW_256KB_3D ordering remains defined by the separate source bit table.']}
    (ROOT/'docs/ADDRLIB_MAS_BLOCK_CONCEPTS_CHECK.json').write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Rendered block hierarchy and Standard/Z-order figures; checked 16 micro IDs and 4096 offsets in each conceptual layout.')


if __name__=='__main__':
    render()
