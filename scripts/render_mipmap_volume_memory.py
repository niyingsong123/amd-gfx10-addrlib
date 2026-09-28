"""Extend the original mip-cube illustration into a spatial/address diagram.

Uses the checked original-document example from render_mipmap_memory.py.
SVG and PNG are generated from the same vector primitives. Original images
are retained. This does not implement or verify a graphics allocation API.
"""
from pathlib import Path
import html
import json
import hashlib
import re
import sys
from PIL import Image, ImageDraw
from render_mipmap_memory import Canvas, make_data, ROOT, OUT, INK, MUTED, LINE, PALE, COLORS, FILLS

FIGURES = [
    ('image-20260913172212926.png','19_mipmap_volume_memory','三维 mip 链、Z 平面、宏块对齐与 tail 内存排布'),
    ('image-20260913172222181.png','20_mipmap_2d_chain','二维 mip 逐级缩小示意'),
]


class Spatial(Canvas):
    shift_y = 0

    def rect(self,x,y,*args,**kwargs):
        return super().rect(x,y+self.shift_y,*args,**kwargs)

    def text(self,x,y,*args,**kwargs):
        return super().text(x,y+self.shift_y,*args,**kwargs)

    def line(self,x1,y1,x2,y2,*args,**kwargs):
        return super().line(x1,y1+self.shift_y,x2,y2+self.shift_y,*args,**kwargs)

    def dot(self,x,y,*args,**kwargs):
        return super().dot(x,y+self.shift_y,*args,**kwargs)

    def polygon(self, points, fill, stroke=LINE, width=1, hatch=False):
        points=[(x,y+self.shift_y) for x,y in points]
        pts=[(round(x*2),round(y*2)) for x,y in points]
        if hatch:
            xs=[x for x,y in pts];ys=[y for x,y in pts]
            x0,y0=min(xs),min(ys);w=max(xs)-x0+1;h=max(ys)-y0+1
            tile=Image.new('RGB',(w,h),PALE);td=ImageDraw.Draw(tile)
            for k in range(-h,w+1,20): td.line((k,h,k+h,0),fill=LINE,width=2)
            mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon([(x-x0,y-y0) for x,y in pts],fill=255)
            self.im.paste(tile,(x0,y0),mask)
        else: self.draw.polygon(pts,fill=fill)
        if stroke: self.draw.line(pts+[pts[0]],fill=stroke,width=round(width*2))
        ps=' '.join(f'{x},{y}' for x,y in points)
        self.svg.append(f'<polygon points="{ps}" fill="{"url(#hatch)" if hatch else fill}" stroke="{stroke or "none"}" stroke-width="{width}"/>')


def project(x,y,z,origin,s=1.0,d=.4):
    return origin[0]+x*s+z*d,origin[1]+y*s-z*d


def cuboid(c,origin,dims,m=0,s=1,d=.4,hatch=False,stroke=None):
    w,h,z=dims
    p=lambda a,b,k:project(a,b,k,origin,s,d)
    color=stroke or COLORS[m]
    c.polygon([p(0,0,0),p(w,0,0),p(w,0,z),p(0,0,z)],FILLS[m],color,1.3,hatch)
    c.polygon([p(w,0,0),p(w,h,0),p(w,h,z),p(w,0,z)],FILLS[m],color,1.3,hatch)
    c.polygon([p(0,0,0),p(w,0,0),p(w,h,0),p(0,h,0)],FILLS[m],color,1.5,hatch)
    return p


def heading(c,x,y,number,title):
    c.text(x,y,number,22,COLORS[2],True)
    c.text(x+50,y-4,title,27,bold=True)


def main_figure(data):
    c=Spatial(1760,1826,'三维 mip 链与内存排布',
        '从大到小排列的三维mip体块。上方为逻辑尺寸，下方分别放大z平面及宏块补齐、tail的orig，再列出低到高地址次序。')
    c.text(64,31,'ADDRLIB  /  FROM MIP VOLUMES TO MEMORY',16,MUTED,True)
    c.text(64,70,'从三维 mip 链，看到 memory 中的位置',42,bold=True)
    c.text(64,132,'三维体块逐级缩小；逻辑尺寸、块内坐标和线性地址分开标注。',23,MUTED)
    c.rect(64,181,1632,67,PALE)
    c.text(85,192,'250×180×130  ·  mip0…7  ·  SW_256KB_3D  ·  1 BPE / 1X  ·  macro = 64×64×64 = 256 KiB',23,bold=True)
    c.text(85,227,'B 为字节基址，swizzle seed=0。体块是坐标空间示意，不代表连续字节段。',17,MUTED)
    heading(c,64,279,'01','三维 mip 排列：每级沿 X / Y / Z 缩小')
    c.shift_y=56
    baseline=618
    positions=[78,614,930,1124,1306,1470,1548,1640]
    for r,x in zip(data['mips'],positions):
        m=r['mip'];w,h,d=r['logical_dimensions'];s=1.55;depth=.56
        yy=baseline-h*s
        p=cuboid(c,(x,yy),(w,h,d),m,s,depth)
        if m < data['first_tail_mip']:
            # Show every pre-tail mip's macro boundaries on all visible faces.
            # Tail mips occupy regions of one shared block and are not split here.
            bw,bh,bd=data['macro_dimensions']
            grid_color = '#A3BDCF' if m == 0 else COLORS[m]
            for vx in range(bw,w,bw):
                c.line(*p(vx,0,0),*p(vx,h,0),grid_color,1.2)
                c.line(*p(vx,0,0),*p(vx,0,d),grid_color,1.2)
            for vy in range(bh,h,bh):
                c.line(*p(0,vy,0),*p(w,vy,0),grid_color,1.2)
                c.line(*p(w,vy,0),*p(w,vy,d),grid_color,1.2)
            for zz in range(bd,d,bd):
                c.line(*p(0,0,zz),*p(w,0,zz),grid_color,1.2)
                c.line(*p(w,0,zz),*p(w,h,zz),grid_color,1.2)
        if m==0:
            c.text(125,389,'mip0',37,COLORS[0],True)
            c.text(125,447,'每 64 个元素',22,COLORS[0])
            c.text(125,484,'切一个宏块边界',22,COLORS[0])
            c.text(78,678,'z=0 前平面；z=64、128 的分界见顶面',18,MUTED)
            c.text(78,644,'250×180×130',25,COLORS[0],True)
        elif m<3:
            c.text(x+12,yy+24,f'mip{m}',29 if m==1 else 23,COLORS[m],True)
            c.text(x,644,'×'.join(map(str,(w,h,d))),23,COLORS[m],True)
            if m==1:
                c.text(x,678,'2×2×2 macro = 8 块',20,COLORS[m],True)
                c.text(x,714,'每 Z 分组 4 块；第二组仅 z=64 有效',16,MUTED)
                c.text(x+20,yy-106,'z=64 分界',18,COLORS[m])
                c.arrow(x+96,yy-72,*p(40,0,64),COLORS[m],1.5)
        elif m<5:
            c.text(x,535,f'mip{m}',23,COLORS[m],True)
            c.text(x,644,'×'.join(map(str,(w,h,d))),20,COLORS[m],True)
        elif m==5:
            c.text(x,571,'mip5',20,COLORS[m],True)
        elif m==6:
            c.text(x-5,571,'…',25,MUTED)
        else:
            c.text(x-25,571,'mip7',20,COLORS[m],True)
    c.text(1470,646,'… → 1×1×1',20,MUTED)
    c.line(1110,697,1696,697,COLORS[3],2)
    c.line(1110,681,1110,697,COLORS[3],2);c.line(1696,681,1696,697,COLORS[3],2)
    c.text(1403,710,'mip3…7 共用一个 tail 宏块 ↓',23,COLORS[3],True,'middle')
    c.text(64,714,'此行按 mip 编号排列；实际低→高地址次序见最下方。',18,MUTED)
    c.line(64,758,1696,758)

    heading(c,64,792,'02','不同 z 平面与宏块尾部对齐')
    heading(c,925,792,'03','共享 tail：orig 后的实际位置')
    # Boundary macro: front XY and depth shell make each padding direction visible.
    p=cuboid(c,(86,912),(64,64,64),0,3.7,1.15,True,LINE)
    c.rect(86,912,58*3.7,52*3.7,FILLS[0],COLORS[0],1.5)
    # Only the first two z planes contain data in this last macro.
    c.polygon([p(0,0,0),p(58,0,0),p(58,0,2),p(0,0,2)],FILLS[0],COLORS[0],1)
    c.text(99,955,'有效 XY',25,COLORS[0],True)
    c.text(99,998,'58 × 52',29,COLORS[0],True)
    c.text(104,1114,'Y 补齐 12 行',18,MUTED)
    c.text(83,1168,'z=0、1 有效；z=2…63 补齐',20,MUTED)
    c.arrow(339,966,415,966,MUTED,1.5)
    c.text(439,860,'mip0 最后一个宏块',24,bold=True)
    c.text(439,906,'块坐标 (3,2,2)',22,MUTED)
    c.text(439,947,'全局原点 (192,128,128)',21,MUTED)
    c.text(439,992,'有效 58×52×2',25,COLORS[0],True)
    c.text(439,1037,'→ 对齐到 64×64×64',22,MUTED)
    c.text(439,1087,'X 补齐 6 列；Z 补齐 62 层',20,MUTED)
    c.text(64,1220,'斜线是补齐空间；块内 z 平面经 swizzle 交织，不是独立的连续字节数组。',18,MUTED)

    # Wire/container plus occupied mip cuboids. The projection is qualitative,
    # while all extents, origins and logical depths use the checked integer data.
    o=(990,908);s=4.1;d=.67
    tp=cuboid(c,o,(64,64,64),3,s,d,True,LINE)
    for r in data['mips'][3:]:
        m=r['mip'];ox,oy,oz=r['origin'];origin2=tp(ox,oy,oz)
        cuboid(c,origin2,r['logical_dimensions'],m,s,d)
        c.dot(*origin2,4,COLORS[m])
    c.text(1004,1064,'mip3',26,COLORS[3],True)
    c.text(1131,918,'m4',19,COLORS[4],True)
    c.text(1335,854,'orig（元素坐标）',23,bold=True)
    for j,r in enumerate(data['mips'][3:]):
        m=r['mip'];c.text(1335,901+49*j,f"m{m}  ({','.join(map(str,r['origin']))})",23,COLORS[m],True)
    c.text(988,1190,'圆点 = 各 mip 的 orig',20,MUTED)
    c.text(925,1220,'先加 orig，再走 swizzle；Z 原点均为 0，各 mip 的有效深度不同。',18,MUTED)
    c.line(64,1267,1696,1267)

    heading(c,64,1300,'04','真实内存顺序：每个 Z 分组中，低地址先 tail，随后 mip2、mip1、mip0')
    x0=235;u=80; boundaries=[x0,x0+u,x0+2*u,x0+6*u,x0+18*u]
    c.arrow(x0,1357,x0+18*u,1357,MUTED,1.8)
    c.text(64,1347,'低地址 → 高地址',19,MUTED)
    labels=[['T','m2','mip1 · 4 块','mip0 · 12 块'],
            ['—','—','mip1：仅 z=64 有效','mip0：z=64…127'],
            ['—','—','无有效 mip','mip0：仅 z=128、129 有效']]
    for g,y in enumerate([1401,1475,1549]):
        c.text(64,y+4,f'zb={g}',23,bold=True)
        c.text(64,y+36,f'B+0x{g*0x480000:06X}',17,MUTED)
        for k,m in enumerate([3,2,1,0]):
            xx=boundaries[k];ww=boundaries[k+1]-xx
            unused=(g==1 and k<2) or (g==2 and k<3)
            c.rect(xx,y,ww,55,FILLS[m],LINE,hatch=unused)
            c.text(xx+ww/2,y+15,labels[g][k],20,MUTED if unused else COLORS[m],not unused,'middle')
            if g==0 and k in [2,3]:
                for n in range(1,ww//u):c.line(xx+n*u,y+41,xx+n*u,y+55,COLORS[m],1)
    c.text(235,1640,'T = mip3…7 共享1块  |  组内偏移：T 0；m2 0x040000；m1 0x080000；m0 0x180000',19,MUTED)
    c.text(64,1692,'Z 分组步长 = 18 × 256 KiB = 0x480000 B；各 mip 的 z 为本级局部坐标。',22,bold=True)
    c.text(64,1734,'斜线表示无有效 texel 的地址槽位；地址条采用统一 Z 分组步长，步长覆盖量与有效数据量分别计量。',17,MUTED)
    c.save(FIGURES[0][1])


def plane_figure():
    c=Spatial(1440,660,'二维 mip 链','二维纹理逐级缩小，宽和高各减半，面积为前一级四分之一；逻辑编号不代表地址次序。')
    c.text(56,28,'ADDRLIB  /  2D MIP CHAIN',16,MUTED,True)
    c.text(56,67,'二维 mip：宽、高各减半，面积约为前一级的 1/4',34,bold=True)
    c.text(56,126,'256×256 纹理的各级尺寸；按逻辑 mip 编号从大到小展示。',21,MUTED)
    bottom=492
    for m,x in [(0,60),(1,498),(2,788),(3,1000),(4,1150),(8,1320)]:
        side=256>>m;shown=side*1.13
        c.rect(x,bottom-shown,shown,shown,FILLS[m%8],COLORS[m%8],1.5)
        c.text(x,bottom+23,f'mip{m}',23,COLORS[m%8],True)
        c.text(x,bottom+64,f'{side}×{side}',21,MUTED)
        if m==0:c.text(x+72,bottom-shown+105,'原始纹理',30,COLORS[0],True)
    c.text(1241,467,'…',29,MUTED)
    c.text(56,613,'二维面积约按 1/4 递减；三维纹理的体积约按 1/8 递减。内存顺序由布局算法另行决定。',20,MUTED)
    c.save(FIGURES[1][1])


def apply_figures():
    p=ROOT/'ADDRLIB硬件算法.md'; before=p.read_bytes();s=before.decode('utf-8')
    changes=[]
    for old,name,title in FIGURES:
        pattern=r'!\[[^\]]*\]\(assets/addrlib_mas/original/'+re.escape(old)+r'\)'
        matches=list(re.finditer(pattern,s)); assert len(matches)==1,(old,len(matches))
        im=matches[0]
        changes.append((im.start(),im.end(),f'![{title}](assets/addrlib_mas/diagrams/{name}.svg)'))
        markers=list(re.finditer(r'//优化下面图[ \t]*',s[:im.start()]))
        if markers:
            mark=markers[-1]
            if not re.search(r'!\[',s[mark.end():im.start()]): changes.append((mark.start(),mark.end(),''))
    assert len({(a,b) for a,b,_ in changes})==len(changes)
    snapshot=ROOT/'build'/('ADDRLIB_MAS_before_volume_'+hashlib.sha256(before).hexdigest()[:12]+'.md')
    snapshot.parent.mkdir(exist_ok=True)
    if not snapshot.exists():snapshot.write_bytes(before)
    for a,b,new in sorted(changes,reverse=True):s=s[:a]+new+s[b:]
    p.write_bytes(s.encode('utf-8'))
    manifest=dict(source_before_sha256=hashlib.sha256(before).hexdigest(),
                  source_after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                  replaced_figures=2, removed_markers=len(changes)-2,
                  sources=[dict(original=old,original_sha256=hashlib.sha256((ROOT/'assets/addrlib_mas/original'/old).read_bytes()).hexdigest(),
                                svg=name+'.svg') for old,name,title in FIGURES])
    (OUT/'mipmap_volume_replacement.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Updated the 3D and marked adjacent 2D figure references; original text/code preserved.')


if __name__=='__main__':
    data=make_data();main_figure(data);plane_figure()
    (OUT/'mipmap_volume_data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Rendered 19_mipmap_volume_memory and 20_mipmap_2d_chain (SVG and PNG).')
    if '--apply' in sys.argv:apply_figures()
