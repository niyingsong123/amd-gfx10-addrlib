"""Render the ten diagrams selected by //优化下面图 in ADDRLIB_MAS.md.

Vector-native redrawing; original PNGs and algorithm documents are untouched.
Run rendering first, inspect the results, then use --apply to replace references.
Requires the same Pillow/font setup as render_mipmap_memory.py.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import sys
from render_mipmap_memory import Canvas, COLORS, FILLS, INK, MUTED, LINE, PALE, OUT, ROOT

ENTRIES = [
    ('image-20260913171630996.png','09_texture_magnification','低分辨率纹理放大'),
    ('image-20260913171654415.png','10_texture_minification','高分辨率纹理缩小'),
    ('image-20260914200151169.png','11_standard_block_layout','Standard：宏块、微块与元素排布'),
    ('image-20260914201059328.png','12_zorder_block_layout','Z-order：宏块内元素级 Morton 排布'),
    ('image-20260914205805703.png','13_macro_256b_alignment','256B 对齐与偏移单位'),
    ('image-20260915082435084.png','14_tail_capacity','tail 容量计算'),
    ('image-20260915083349580.png','15_tail_count_check','tail 层级数量检查'),
    ('image-20260915092249060.png','16_per_mip_blocks','各 mip 的对齐块数'),
    ('image-20260915090911322.png','17_tail_size_check','tail 尺寸检查'),
    ('image-20260915092306709.png','18_tail_id_and_size','首个 tail mip 与块贡献'),
]


def header(c, tag, title, subtitle):
    c.text(56,28,tag,15,MUTED,bold=True)
    c.text(56,65,title,36,bold=True)
    c.text(56,122,subtitle,21,MUTED)


def footer(c, y, title, detail):
    c.line(56,y-24,1384,y-24)
    c.text(56,y,title,24,bold=True)
    c.text(56,y+42,detail,19,MUTED)


def sample(i,j):
    # A small, original procedural texture; no source bitmap is edited.
    if (i-3.5)**2+(j-3.5)**2 < 7: return (35,113,133)
    if j > 5 or i < 1: return (71,153,129)
    return (196,224,237)


def texture(c,x,y,size,n,smooth=False):
    for j in range(n):
        for i in range(n):
            if smooth:
                u=i*7/(n-1); v=j*7/(n-1); a=int(u); b=int(v)
                dx=u-a;dy=v-b
                rgb=tuple(round(sample(a,b)[k]*(1-dx)*(1-dy)+sample(min(7,a+1),b)[k]*dx*(1-dy)
                     +sample(a,min(7,b+1))[k]*(1-dx)*dy+sample(min(7,a+1),min(7,b+1))[k]*dx*dy) for k in range(3))
            else: rgb=sample(i*8//n,j*8//n)
            fill='#' + ''.join(f'{v:02x}' for v in rgb)
            c.rect(x+i*size/n,y+j*size/n,size/n,size/n,fill)
    c.line(x,y,x+size,y,LINE); c.line(x,y+size,x+size,y+size,LINE)


def magnification():
    c=Canvas(1440,790,ENTRIES[0][2],'64乘64原始纹理经过插值放大为256乘256；增加像素数量不能补回原始细节。')
    header(c,'TEXTURE SCALE','放大纹理：更多像素，并不意味着更多细节','低分辨率纹理 → 高分辨率目标图；网格和纹理图案仅作示意。')
    texture(c,130,342,112,8)
    c.text(186,278,'原始纹理',27,COLORS[0],True,'middle')
    c.text(186,482,'64 × 64',26,COLORS[0],True,'middle')
    c.arrow(334,401,766,401,COLORS[0],3)
    c.text(550,337,'插值放大',28,COLORS[0],True,'middle')
    c.text(550,435,'宽、高各扩大 4 倍',21,MUTED,False,'middle')
    texture(c,844,184,448,32,True)
    c.text(1068,649,'目标图 256 × 256',25,COLORS[1],True,'middle')
    footer(c,711,'插值可以平滑过渡，但无法恢复原纹理里没有的细节。','屏幕上物体变大时，需要足够清晰的源纹理；mipmap 主要解决缩小时的采样问题。')
    c.save(ENTRIES[0][1])


def minification():
    c=Canvas(1440,790,ENTRIES[1][2],'256乘256纹理缩小到64乘64；单个目标像素覆盖更多源texel，选用匹配的mip可降低不必要采样。')
    header(c,'TEXTURE SCALE','缩小纹理：一个目标像素覆盖更多源 texel','高分辨率纹理 → 低分辨率目标图；采样覆盖范围随缩小比例增大。')
    texture(c,102,184,448,32)
    # 448 drawn pixels / 256 texels * 4 texels = 7 drawn pixels.
    c.rect(102+168,184+168,7,7,FILLS[2],COLORS[2],2)
    c.text(326,649,'原始纹理 256 × 256',25,COLORS[0],True,'middle')
    c.arrow(598,401,1016,401,COLORS[1],3)
    c.text(807,318,'宽、高各缩小为 1/4',25,COLORS[1],True,'middle')
    c.text(807,442,'约 4×4 源 texel / 目标像素',21,MUTED,False,'middle')
    c.text(807,484,'示例采用均匀、正视缩小',17,MUTED,False,'middle')
    texture(c,1110,342,112,8,True)
    c.text(1166,278,'目标图',27,COLORS[1],True,'middle')
    c.text(1166,482,'64 × 64',26,COLORS[1],True,'middle')
    footer(c,711,'选择与像素覆盖范围匹配的 mip，减少不必要的高频细节与采样负担。','直接访问过细纹理可能增加缓存压力；实际 cache miss 还取决于访问模式与缓存配置。')
    c.save(ENTRIES[1][1])


def morton(x,y,bits):
    return sum(((x>>k)&1)<<(2*k) | ((y>>k)&1)<<(2*k+1) for k in range(bits))


def grid(c,x,y,size,n,kind='raster',highlight=None,number=True,raster_stride=None):
    cell=size/n
    points={}
    for row in range(n):
        for col in range(n):
            order=row*(raster_stride or n)+col if kind=='raster' else morton(col,row,round(math.log2(n)))
            points[order]=(x+(col+.5)*cell,y+(row+.58)*cell)
            fill=FILLS[(row//2+col//2)%3] if kind=='morton' else FILLS[0]
            if highlight==(col,row): fill=FILLS[2]
            c.rect(x+col*cell,y+row*cell,cell,cell,fill,LINE)
            if number:
                c.text(x+col*cell+6,y+row*cell+5,str(order),18 if n==4 else 15,MUTED)
    if highlight:
        col,row=highlight
        # Border without erasing the original cell label or arrow.
        a=x+col*cell;b=y+row*cell
        for coords in [(a,b,a+cell,b),(a,b,a,b+cell),(a+cell,b,a+cell,b+cell),(a,b+cell,a+cell,b+cell)]:
            c.line(*coords,COLORS[2],3)


def standard():
    c=Canvas(1440,760,ENTRIES[2][2],'Standard 概念布局：宏块间raster顺序，宏块内微块Morton顺序，微块内元素raster顺序。')
    header(c,'BLOCK LAYOUT','Standard：逐层展开，三种粒度各司其职','256×256 纹理、1 B/元素；每个 macro 为 4 KB，每个 micro 为 256 B。')
    for x,tag,title in [(56,'01','整张纹理'),(560,'02','一个 macro'),(1064,'03','一个 micro')]:
        c.text(x,189,tag,20,COLORS[2],True); c.text(x+48,183,title,27,bold=True)
    grid(c,56,249,320,4,highlight=(0,3))
    grid(c,560,249,320,4,'morton',highlight=(0,3))
    grid(c,1064,249,320,4,raster_stride=16)
    c.arrow(408,409,528,409,MUTED,2); c.text(468,359,'放大宏块',18,MUTED,False,'middle')
    c.arrow(912,409,1032,409,MUTED,2); c.text(972,359,'放大微块',18,MUTED,False,'middle')
    for x,title,detail in [(56,'macro 间：raster','4×4 个宏块；按行排列'),(560,'micro 间：Morton','4×4 个微块；按 Z 形递归'),(1064,'元素间：raster','局部 4×4 元素；行内 X 递增')]:
        c.text(x,590,title,23,bold=True);c.text(x,628,detail,19,MUTED)
    c.text(56,700,'宏块 64×64×1 B = 4 KB     →     微块 16×16×1 B = 256 B',21,bold=True)
    c.text(56,737,'数字表示当前层级的顺序编号；宏块按行排列，微块按 Morton 排列，微块内元素按行排列。',15,MUTED)
    c.save(ENTRIES[2][1])


def zorder():
    c=Canvas(1440,760,ENTRIES[3][2],'宏块之间按raster顺序，宏块内元素按Morton顺序；放大显示局部8乘8元素，其余用省略号表示。')
    header(c,'BLOCK LAYOUT','Z-order：Morton 排序直接落到元素粒度','256×256 纹理、1 B/元素；宏块之间按 raster 排列，宏块内部按元素坐标交织。')
    c.text(56,187,'整张纹理',28,bold=True)
    c.text(574,187,'一个 64×64 的 macro',28,bold=True)
    grid(c,56,251,320,4,highlight=(0,3))
    c.arrow(410,411,542,411,MUTED,2);c.text(476,362,'放大宏块',19,MUTED,False,'middle')
    grid(c,574,251,320,8,'morton')
    c.text(916,384,'…',32,MUTED)
    c.text(720,582,'…',32,MUTED)
    c.text(574,625,'每格一个元素；局部 8×8，其余省略',20,MUTED)
    c.text(1020,259,'位交织',26,COLORS[2],True)
    for j,line in enumerate(['X = x[5:0]','Y = y[5:0]','order =','{y5,x5, … , y0,x0}']):
        c.text(1020,306+j*43,line,22)
    c.text(1020,511,'12 位 → 4096 个元素',21,COLORS[2],True)
    c.text(1020,549,'4096 × 1 B = 4 KB',20,MUTED)
    footer(c,692,'宏块之间按行排列；宏块内的元素按 Morton 顺序排列。','格内数字是元素的 Morton 编号：局部为 0…63，完整宏块为 0…4095。')
    c.save(ENTRIES[3][1])


def flow(index,title,subtitle,inputs,steps,outputs,conclusion,note,*,filename=None):
    c=Canvas(1440,670,title,subtitle+'；输入、处理和输出分开显示。')
    header(c,'MIPMAP PARAMETERS',title,subtitle)
    for x,w,name,tint,color in [(56,308,'输入',FILLS[0],COLORS[0]),(460,566,'处理',FILLS[2],COLORS[2]),(1122,262,'输出',FILLS[1],COLORS[1])]:
        c.rect(x,200,w,308,tint,LINE)
        c.rect(x,200,w,5,color)
        c.text(x+22,225,name,24,color,True)
    c.arrow(382,354,441,354,MUTED,2)
    c.arrow(1042,354,1103,354,MUTED,2)
    for j,line in enumerate(inputs): c.text(78,282+j*34,line,21)
    for j,line in enumerate(steps): c.text(482,280+j*29,line,19)
    for j,line in enumerate(outputs): c.text(1144,282+j*38,line,20,COLORS[1],True)
    footer(c,556,conclusion,note)
    c.save(filename or ENTRIES[index][1])


def flows():
    flow(4,'256B 对齐：统一 slice 与 mip 偏移的计算口径','区分 Linear 与 tiled 的对齐要求，并避免减法下溢。',
         ['linear','l2_blk_w / l2_eb','l2_ms / l2_ms_128B'],
         ['① slice 宽度','linear 且 l2_blk_w < 8：用 8 − l2_eb','否则：沿用 l2_blk_w','② l2_ms_128B = 0：输出 0；否则减 1','③ l2_ms < 8：偏移指数取 0；否则减 8'],
         ['l2_blk_w_slice','l2_ms_256B','l2_mip_offset'],
         'slice 的对齐粒度与 mip 偏移的单位，要分别处理。','l2_ms_256B 与 l2_mip_offset 均为对数指数；实际字节偏移由 mip_offset_b × 256 得到。')
    flow(5,'tail 容量：先求有效块尺寸，再查可容纳层级','num_mips_in_tail 是容量上限，不等于本资源实际进入 tail 的 mip 数。',
         ['sw_type','l2_ms_256B'],
         ['① 按 sw_type 判断是否为 3D 块','3D：4→3，8→6，10→7','非 3D：保留 l2_ms_256B','② 得到 l2_ms_256B_eff','③ eff=0 → 1；eff=3 → 5','其余已列举的合法 eff：容量为 eff+4'],
         ['num_mips_in_tail'],
         '厚块先折算有效尺寸，再由该尺寸得到 tail 容量。','eff 为有效块大小的对数参数；容量是上限，实际 tail 层数还取决于尺寸与 mip 链长度。')
    flow(6,'数量条件：当前 mip 是否落在 tail 容量允许的范围','剩余层级数与尺寸限制必须同时满足，才能进入 tail。',
         ['maxmip_in','mips_in_tail'],
         ['① mips_outside_tail =','    maxmip_in − mips_in_tail','② 遍历 m = 0…MAXMIP−1','若 m > mips_outside_tail，条件成立','或差值为负数，条件也成立'],
         ['in_tail_chk[m]'],
         '使用差值符号位识别负数，避免无符号减法造成错误判断。','maxmip_in 是最大 mip 编号；mips_in_tail 是 tail 可容纳的层级数。')
    flow(7,'每级块数：先对齐 mip0，再逐级向上取整','Wb / Hb 的单位是宏块个数，不是对齐后的元素个数。',
         ['map0_w / map0_h','l2_blk_w / l2_blk_h','l2_blk_w_slice'],
         ['① 用 pad_to_log2sz_gc 求初始块数','Wb0 / Hb0 / Wb_slice0','② 从初始块数递推各级','Wb[m] = ceil(Wb0 / 2^m)','Hb 与 Wb_slice 同理','通过移位 + 低位 OR 归约实现'],
         ['Wb[m]','Hb[m]','Wb_slice[m]'],
         '同一套块数分别服务于 pitch、尺寸判定与 slice 累加。','右移得到商，低位 OR 归约判断余数；不能整除时加 1。')
    flow(8,'尺寸条件：mip0 直接比较，后续 mip 看前一级块数','y_bias 决定哪一条轴采用半块阈值；数量条件与尺寸条件共同生效。',
         ['y_bias','pad_sz_w / pad_sz_h','W / H；Wb[m] / Hb[m]','in_tail_chk'],
         ['① y_bias=1：块宽 × (块高/2)','    y_bias=0：(块宽/2) × 块高','② mip0：直接检查实际宽、高与数量条件','③ 检查 mip(m+1) 时使用 Wb[m]/Hb[m]','y_bias=1：Wb≤2 且 Hb≤1','y_bias=0：Wb≤1 且 Hb≤2','并且 in_tail_chk[m+1] 为真'],
         ['in_miptail[0]','in_miptail[m+1]'],
         '检查下一级 mip 时，读取的是前一级的块数。','阈值由 pad_sz_w / pad_sz_h 得到；mip0 直接检查宽高，后续级使用前一级块数。')
    flow(9,'首个 tail 与块贡献：共享空间只累计一次','先确定 tail_mipid，再给每个 mip 计算参与布局累加的 mipsize。',
         ['maxmip / l2_ms_128B','in_miptail[]','Wb_slice[m] / Hb[m]'],
         ['① 找到首个入 tail 的 mip；无 tail 为 17','maxmip=0 或 (l2_ms_128B>>1)=0：无 tail','② 按以下 if / else if 优先级计算贡献','m > tail_mipid：0','否则 m = tail_mipid 或 m = 16：1','否则：Wb_slice[m] × Hb[m]'],
         ['tail_mipid','mipsize[m]'],
         'tail 后续 mip 贡献为 0，表示共享已经分配的空间。','计 0 不代表没有 texel；mip16 使用特殊分支，是否参与总和由 maxmip_mask 决定。')


def apply_references():
    p=ROOT/'ADDRLIB_MAS.md'; before=p.read_bytes(); s=before.decode('utf-8')
    markers=list(re.finditer(r'//优化下面图[ \t]*',s))
    if not markers:
        print('No pending markers; rendered assets only.');return
    assert len(markers)==10, f'Expected 10 reviewed markers, found {len(markers)}; inspect before applying'
    expected={old:(name,title) for old,name,title in ENTRIES}
    replacements=[]; selected=[]
    for mark in markers:
        m=re.search(r'!\[([^\]]*)\]\(([^)]+)\)',s[mark.end():])
        assert m is not None
        old=m.group(2); key=Path(old).name; assert key in expected,key
        name,title=expected[key]; selected.append(key)
        assert (OUT/(name+'.svg')).exists() and (OUT/(name+'.png')).exists()
        replacements += [(mark.start(),mark.end(),''),
                         (mark.end()+m.start(),mark.end()+m.end(),f'![{title}](assets/addrlib_mas/diagrams/{name}.svg)')]
    assert len(set(selected))==10
    build=ROOT/'build'; build.mkdir(exist_ok=True)
    snapshot=build/('ADDRLIB_MAS_before_redraw_'+hashlib.sha256(before).hexdigest()[:12]+'.md')
    if not snapshot.exists(): snapshot.write_bytes(before)
    out=s
    for a,b,new in sorted(replacements,reverse=True): out=out[:a]+new+out[b:]
    # Preserve all other content byte for byte, including code, indentation and line endings.
    cursor=0; pieces=[]
    for a,b,new in sorted(replacements): pieces.extend([s[cursor:a],new]);cursor=b
    pieces.append(s[cursor:]);assert ''.join(pieces)==out
    assert '//优化下面图' not in out
    p.write_bytes(out.encode('utf-8'))
    manifest=dict(source_before_sha256=hashlib.sha256(before).hexdigest(),
                  source_after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                  marker_count=10, scope='Only selected image markdown references and marker text changed',
                  figures=[dict(original='assets/addrlib_mas/original/'+old,
                                original_sha256=hashlib.sha256((ROOT/'assets/addrlib_mas/original'/old).read_bytes()).hexdigest(),
                                svg='assets/addrlib_mas/diagrams/'+name+'.svg',title=title) for old,name,title in ENTRIES])
    (OUT/'mas_redraw_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Updated 10 selected image references and removed 10 markers. All other content preserved.')


if __name__=='__main__':
    magnification();minification();standard();zorder();flows()
    print('Rendered 10 SVG and 10 PNG diagrams.')
    if '--apply' in sys.argv: apply_references()
