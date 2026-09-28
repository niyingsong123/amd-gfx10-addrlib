"""Render the six-chapter walkthrough figures from its checked numeric data."""
import json
from render_mipmap_memory import Canvas, ROOT, OUT, INK, MUTED, LINE, PALE, COLORS, FILLS
from render_mipmap_volume_memory import Spatial, cuboid
from redraw_mas_marked_diagrams import magnification, minification
from render_mas_teaching import stages


def title(c, tag, heading, subtitle):
    c.text(64, 26, tag, 16, MUTED, True)
    c.text(64, 65, heading, 40, INK, True)
    c.text(64, 125, subtitle, 22, MUTED)


def section(c, x, y, number, label):
    c.text(x, y, number, 22, COLORS[2], True)
    c.text(x+48, y-2, label, 27, INK, True)


def volume(data):
    c=Spatial(1760,2110,'三维 mip、宏块对齐、Z 分组与内存顺序',
        '一条三维 mip 链，普通 mip 的宏块网格、最后一块的补齐、tail 的坐标原点，以及多个 Z 分组的地址顺序。')
    title(c,'MIPMAP MEMORY LAYOUT','三维 mip 怎样排进 memory','体块表达元素坐标；底部地址条表达字节顺序。Z 方向压缩显示，重复结构用省略号表示。')
    c.rect(64,175,1632,60,PALE)
    c.text(84,192,'250×180×1537 · mip0…10 · SW_256KB_3D · 1 BPE / 1X · macro 64×64×64',23,INK,True)
    section(c,64,273,'01','各级 mip 的体积与宏块边界')
    positions=[78,650,980,1230,1430]
    for m,x in enumerate(positions):
        r=data['mips'][m];w,h,d=r['logical_dimensions']
        scale=1.18; depth=.060
        y=636-h*scale
        p=cuboid(c,(x,y),(w,h,d),m,scale,depth)
        if m<3:
            for vx in range(64,w,64):
                c.line(*p(vx,0,0),*p(vx,h,0),COLORS[m],1)
                c.line(*p(vx,0,0),*p(vx,0,d),COLORS[m],1)
            for vy in range(64,h,64):
                c.line(*p(0,vy,0),*p(w,vy,0),COLORS[m],1)
                c.line(*p(w,vy,0),*p(w,vy,d),COLORS[m],1)
        # Show representative Z boundaries on all mips, including tail mips.
        boundaries=[v for v in (64,128,d//64*64) if 0<v<d]
        for z in sorted(set(boundaries)):
            c.line(*p(0,0,z),*p(w,0,z),COLORS[m],1.5)
            c.line(*p(w,0,z),*p(w,h,z),COLORS[m],1.5)
        c.text(x,658,f'mip{m}',27,COLORS[m],True)
        c.text(x,700,'×'.join(map(str,(w,h,d))),22,INK,True)
        if m<3:
            bx,by=r['block_xy']
            c.text(x,740,f'{bx}×{by} 块 / Z 分组',19,MUTED)
            c.text(x,774,f'{r["z_groups"]} 个 Z 分组',19,MUTED)
    c.text(1580,603,'…',38,MUTED)
    c.text(1570,658,'mip5…10',23,COLORS[5],True)
    c.text(1590,700,'→ 1×1×1',21,MUTED)
    c.text(108,480,'mip0',35,COLORS[0],True)
    c.text(108,531,'X / Y 按 64 切分',23,COLORS[0])
    c.text(693,562,'mip1',26,COLORS[1],True)
    c.text(364,336,'z=64、128 … 1536',19,MUTED)
    c.text(1230,751,'mip3 起进入 tail',24,COLORS[3],True)
    c.text(1230,791,'tail 区域可分布于多个 Z 分组',20,MUTED)
    c.line(64,842,1696,842)

    section(c,64,878,'02','边缘宏块的补齐')
    section(c,923,878,'03','tail 内部的 orig 与有效区域')
    p=cuboid(c,(88,1040),(64,64,64),0,3.45,1.0,True,LINE)
    c.rect(88,1040,58*3.45,52*3.45,FILLS[0],COLORS[0],1.5)
    c.polygon([p(0,0,0),p(58,0,0),p(58,0,1),p(0,0,1)],FILLS[0],COLORS[0],1)
    c.text(103,1090,'有效 XY',24,COLORS[0],True)
    c.text(103,1131,'58×52',29,COLORS[0],True)
    for j,t in enumerate(['mip0 最后一个宏块','块坐标 (3,2,24)','原点 (192,128,1536)',
                          '有效尺寸 58×52×1','对齐尺寸 64×64×64','补齐 X:6 · Y:12 · Z:63']):
        c.text(399,965+j*52,t,24 if j in (0,3) else 21,INK if j==0 else MUTED,j in (0,3))
    c.text(88,1290,'只有一个有效 Z 平面，其余 63 层补齐',21,MUTED)

    # XY projection of the first Z group's tail. Z extents are stated separately.
    x0,y0,s=950,975,4.15
    c.rect(x0,y0,64*s,64*s,stroke=LINE,hatch=True)
    for r in data['mips'][3:]:
        m=r['mip'];ox,oy,_=r['origin'];w,h,_=r['logical_dimensions']
        c.rect(x0+ox*s,y0+oy*s,w*s,h*s,FILLS[m%8],COLORS[m%8],1.4)
        c.dot(x0+ox*s,y0+oy*s,3,COLORS[m%8])
    c.text(x0+9*s,y0+39*s,'mip3',24,COLORS[3],True)
    c.text(x0+32*s,y0+3*s,'m4',18,COLORS[4],True)
    c.text(1301,941,'orig（元素） / 有效深度',21,INK,True)
    for j,r in enumerate(data['mips'][3:7]):
        x,y,z=r['origin'];m=r['mip']
        c.text(1301,987+j*47,f'm{m}  ({x},{y},{z}) / {r["logical_dimensions"][2]}',22,COLORS[m],True)
    c.text(1301,1191,'mip7…10 省略文字标签',19,MUTED)
    c.text(950,1279,'彩色点为 orig；投影中的区域不表示连续字节',19,MUTED)
    c.text(950,1318,'mip3 深 192、mip4 深 96，均跨越 Z 分组',20,INK,True)
    c.line(64,1374,1696,1374)

    section(c,64,1411,'04','实际内存顺序：每个 Z 分组内先 tail，再 mip2、mip1、mip0')
    x0,u=253,79
    edges=[x0,x0+u,x0+2*u,x0+6*u,x0+18*u]
    c.arrow(x0,1473,edges[-1],1473,MUTED,1.5)
    c.text(64,1456,'低地址 → 高地址',19,MUTED)
    groups=[(0,1513),(1,1593),(2,1673),(12,1796),(24,1917)]
    for g,y in groups:
        c.text(64,y+3,f'zb={g}',23,INK,True)
        c.text(64,y+34,f'B+0x{g*data["chain_stride_bytes"]:07X}',17,MUTED)
        present=[g<3,g<6,g<12,g<25]
        labels=['T','m2','mip1 · 4 块','mip0 · 12 块']
        if g==24:labels[3]='mip0 · 仅本级 z=1536 有效'
        for k,m in enumerate([3,2,1,0]):
            xx=edges[k];ww=edges[k+1]-xx
            c.rect(xx,y,ww,55,FILLS[m],LINE,hatch=not present[k])
            c.text(xx+ww/2,y+13,labels[k] if present[k] else '—',21,
                   COLORS[m] if present[k] else MUTED,present[k],'middle')
            if g==0 and k>=2:
                for n in range(1,ww//u): c.line(xx+n*u,y+41,xx+n*u,y+55,COLORS[m])
    for y in [1753,1875]: c.text(900,y,'…',30,MUTED,False,'middle')
    c.text(253,1997,'T：zb=0 含 mip3…10；zb=1 含 mip3、mip4；zb=2 仅含 mip3。',21,COLORS[3],True)
    c.text(64,2042,'组步长 0x480000 B；组内偏移 T:0 · m2:0x040000 · m1:0x080000 · m0:0x180000。',21,INK,True)
    c.text(64,2080,'B 为字节基址。斜线表示没有有效 texel 的槽位；每个 mip 的 z 都是本级局部坐标。',17,MUTED)
    c.save('19_mipmap_volume_memory')


def selected_tail(data):
    c=Canvas(1600,1170,'mip4 的坐标、tail 原点与最终地址',
        'mip4 的5,6,69位于第二个Z分组。XY平移到37,6，Z组内坐标5。宏块偏移0x480000，块内偏移0x81D5。')
    title(c,'ONE 3D ACCESS','mip4 的 (5,6,69) 在哪里','macro 64×64×64 · orig (32,0,0) · 当前 Z 分组 zb=1')
    x0,y0,s=88,261,6
    c.rect(x0,y0,64*s,64*s,stroke=LINE,hatch=True)
    for m in [3,4]:
        r=data['mips'][m];ox,oy,_=r['origin'];w,h,_=r['logical_dimensions']
        c.rect(x0+ox*s,y0+oy*s,w*s,h*s,FILLS[m],COLORS[m],2)
    for v in [0,16,32,48,64]:
        c.text(x0+v*s,y0-34,str(v),18,MUTED,False,'middle')
        c.text(x0-18,y0+v*s-9,str(v),18,MUTED,False,'end')
    c.text(x0+7*s,y0+40*s,'mip3',25,COLORS[3],True)
    c.text(x0+33*s,y0+2*s,'mip4',20,COLORS[4],True)
    c.dot(x0+32*s,y0,5,COLORS[4])
    px,py=x0+37*s,y0+6*s
    c.dot(px,py,6,INK)
    c.line(px,py,553,py,INK,1.5)
    c.text(579,242,'局部坐标        (5,6,69)',27,INK,True)
    c.text(579,298,'tail orig          (32,0,0)',27,COLORS[4],True)
    c.text(579,354,'查表坐标        (37,6,69)',27,INK,True)
    c.text(579,414,'宏块坐标        (0,0,1)',26,COLORS[2],True)
    c.text(579,470,'块内有效坐标 (37,6,5)',26,INK,True)
    c.text(579,536,'Z 高位选择分组，低 6 位参与块内 swizzle。',23,MUTED)
    c.text(579,581,'orig 改变 X/Y 块内位置；Z 原点为 0。',23,MUTED)
    c.text(88,674,'Z 组内 z=5 的 XY 截面；斜线区没有有效 texel。',22,MUTED)
    c.line(64,733,1536,733)
    c.text(64,769,'Z 分组',25,INK,True)
    for g,x in enumerate([262,608,954]):
        c.rect(x,765,302,80,FILLS[4] if g==1 else PALE,COLORS[4] if g==1 else LINE,2)
        c.text(x+151,780,f'zb={g} · z={g*64}…{g*64+63}',22,COLORS[4] if g==1 else MUTED,g==1,'middle')
    c.text(88,875,'mip4 有效 z=0…95，因此 zb=1 中只有前 32 个 Z 平面有效。',23,INK,True)
    c.rect(64,935,1472,170,PALE)
    c.text(89,958,'基址 0x30000000 + mip 偏移 0 + 宏块偏移 0x480000 + 块内偏移 0x81D5',25,INK,True)
    c.text(89,1012,'最终地址 0x304881D5',37,COLORS[4],True)
    c.text(89,1071,'本例 seed=0；orig 的作用已经包含在块内偏移中。',22,MUTED)
    c.save('31_teaching_3d_tail_access')


if __name__=='__main__':
    data=json.loads((ROOT/'docs/ADDRLIB_MAS_3D_WALKTHROUGH_CHECK.json').read_text(encoding='utf-8'))
    magnification();minification();volume(data);stages();selected_tail(data)
    from render_mas_supplement import render
    render(data)
    from render_mas_block_concepts import render as render_blocks
    render_blocks()
    print('Rendered all 13 document figures (SVG/PNG).')
