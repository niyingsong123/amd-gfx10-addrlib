"""Render vector figures for the single-example Markdown walkthrough."""
import json
from render_mipmap_memory import Canvas, ROOT, OUT, INK, MUTED, LINE, PALE, COLORS, FILLS
from redraw_mas_marked_diagrams import header


def box(c, x, y, w, h, lines, color=0, size=23):
    c.rect(x, y, w, h, FILLS[color], LINE)
    for n, line in enumerate(lines):
        c.text(x+18, y+20+n*(size+12), line, size, COLORS[color], n == 0)


def overview():
    c = Canvas(1440, 690, '从访问请求到字节地址', '布局参数描述资源，局部坐标描述本次访问；布局、宏块位置和块内位映射在地址合成处汇合。')
    header(c, 'ADDRESS WALKTHROUGH', '给定 mip 和局部坐标，找到一个字节地址', '主例：256×256 · 1 BPE · 1X · SW_4KB_2D · mip0…8')
    box(c, 56, 198, 300, 140, ['资源参数', '尺寸、格式、模式', 'mip 总数与基址'])
    box(c, 448, 198, 350, 140, ['布局', 'pitch、mip 偏移', '块尺寸、tail 位置'], 2)
    box(c, 56, 402, 300, 140, ['一次访问', 'mip1 · (69,70,0)', 'sample s=0'], 1)
    box(c, 448, 402, 350, 140, ['本次元素的位置', '宏块位置 + 块内位映射', 'tail 时先加坐标原点'], 3, 21)
    box(c, 934, 294, 450, 176, ['地址合成', '字节地址 address_final', 'tail 标志 mipid_in_tail'], 4, 23)
    c.arrow(364, 268, 435, 268)
    c.arrow(364, 472, 435, 472)
    c.arrow(622, 346, 622, 390)
    c.arrow(810, 268, 918, 338)
    c.arrow(810, 472, 918, 420)
    c.line(56, 587, 1384, 587)
    c.text(56, 612, 'mip 与坐标在输入时已经确定；这里不计算 LOD，也不生成纹理过滤权重。', 24, bold=True)
    c.save('27_teaching_address_overview')


def macro_grid():
    c = Canvas(1440, 1010, '宏块坐标与边缘对齐', 'mip1尺寸128乘128，由四个64乘64宏块组成；访问69,70位于块1,1，块内坐标5,6。独立小图说明非整齐尺寸的边缘补齐。')
    header(c, 'COORDINATES & ALIGNMENT', '先找宏块，再找块内位置', 'mip1 = 128×128；macro = 64×64；每个元素 1 B。X 向右，Y 向下。')
    x0, y0, side = 88, 245, 330
    for j in range(2):
        for i in range(2):
            n = j*2+i
            c.rect(x0+i*side/2, y0+j*side/2, side/2, side/2, FILLS[1] if n==3 else PALE, LINE, 2)
            c.text(x0+i*side/2+18, y0+j*side/2+22, f'块 {n} · ({i},{j})', 21, COLORS[1] if n==3 else MUTED, True)
    for v in [0,64,128]:
        c.text(x0+v*side/128, y0-36, str(v), 19, MUTED, False, 'middle')
        c.text(x0-17, y0+v*side/128-10, str(v), 19, MUTED, False, 'end')
    px, py = x0+69*side/128, y0+70*side/128
    c.dot(px, py, 6, COLORS[4])
    c.line(px+10, py, 480, py, COLORS[4], 2)
    c.text(500, 265, '访问坐标 (69,70)', 30, COLORS[1], True)
    for n, text in enumerate(['宏块坐标：floor(69/64), floor(70/64) = (1,1)',
                              '块内坐标：69−64, 70−64 = (5,6)',
                              '每行 2 块；块号 = 1×2+1 = 3',
                              '宏块字节偏移 = 3×4096 = 0x3000 B']):
        c.text(500, 329+n*52, text, 24, INK if n<3 else COLORS[1], n==3)
    c.text(88, 611, '块内 (5,6) 的字节位置由 swizzle 位表决定，不直接使用 y×64+x。', 24, bold=True)
    c.line(56, 669, 1384, 669)
    c.text(56, 696, '独立的对齐小例：257×129 → 320×192', 28, bold=True)
    ax, ay, scale = 88, 762, .8
    c.rect(ax, ay, 320*scale, 192*scale, stroke=LINE, hatch=True)
    c.rect(ax, ay, 257*scale, 129*scale, FILLS[0])
    for i in range(6): c.line(ax+i*64*scale, ay, ax+i*64*scale, ay+192*scale, MUTED)
    for i in range(4): c.line(ax, ay+i*64*scale, ax+320*scale, ay+i*64*scale, MUTED)
    c.text(396, 776, '横向需要 5 块，纵向需要 3 块；有效尺寸仍为 257×129。', 24)
    c.text(396, 824, 'pitch = 5×64 = 320 个元素；斜线区没有有效 texel。', 24)
    c.text(396, 874, '这是坐标边缘的补齐；swizzle 后不一定是末尾一段连续字节。', 22, MUTED)
    c.save('28_teaching_macro_coordinates')


def tail_visit():
    data = json.loads((ROOT/'docs/ADDRLIB_MAS_REWRITE_CHECK.json').read_text(encoding='utf-8'))['primary']
    c = Canvas(1440, 1030, 'tail原点和两条访问路径', 'mip4局部坐标5,6加原点16,32得到21,38，位映射结果为0x639；普通mip1访问结果为0x30005039。')
    header(c, 'TAIL ORIGIN & ADDRESS', 'mip4 的 (5,6)，在共享 tail 中位于哪里', '共享宏块 = 64×64；不同 mip 有不同 orig。坐标单位为元素，地址单位为字节。')
    x0, y0, scale = 90, 238, 6.0
    c.rect(x0, y0, 64*scale, 64*scale, stroke=LINE, hatch=True)
    for row in data['mips'][3:]:
        m = row['mip']; x,y,_ = row['origin']['xyz']; side = row['side']
        c.rect(x0+x*scale, y0+y*scale, side*scale, side*scale, FILLS[m%8], COLORS[m%8], 2)
        c.dot(x0+x*scale, y0+y*scale, 3, COLORS[m%8])
    c.text(x0+39*scale, y0+12*scale, 'mip3', 24, COLORS[3], True)
    c.text(x0+17*scale, y0+42*scale, 'mip4', 20, COLORS[4], True)
    px, py = x0+21*scale, y0+38*scale
    c.dot(px, py, 6, INK)
    c.line(px, py, 500, py, INK, 1.5)
    c.text(90, 649, '黑点：查表坐标 (21,38)', 24, bold=True)
    c.text(90, 688, '彩色点：各级 orig；斜线：未使用坐标区', 20, MUTED)
    rows = [
        ('相对 tail 编号', 'mip4 − mip3 = 1'),
        ('原点编码', 'reverse = 8−(1+1) = 6；code = 0x600'),
        ('拆成微块坐标', '(1,2)；micro = 16×16'),
        ('得到 orig', '(1×16, 2×16) = (16,32)'),
        ('平移局部坐标', '(5,6) + (16,32) = (21,38)'),
        ('查 swizzle 位表', 'blk_offset = 0x639'),
    ]
    for n, (title, detail) in enumerate(rows):
        y = 236+n*78
        c.text(566, y, title, 23, COLORS[4] if n in [3,4,5] else INK, True)
        c.text(566, y+33, detail, 21, MUTED)
    c.line(56, 754, 1384, 754)
    box(c, 56, 784, 632, 140, ['普通 mip1', '0x30000000 + 0x2000 + 0x3000 + 0x39', '= 0x30005039'], 1, 23)
    box(c, 720, 784, 664, 140, ['tail mip4', '0x30000000 + 0 + 0 + 0x639', '= 0x30000639'], 4, 23)
    c.text(56, 959, '0x639 已包含 orig 的影响；不能再把原点编码 0x600 加入最终地址。', 25, bold=True)
    c.save('29_teaching_tail_access')


def stages():
    c = Canvas(1800, 1020, 'S0到S8的计算分工', '上方为布局参数和块内映射通路；下方为S4基址与宏块中间量，块索引在S7输出。S7合成相对偏移，S8形成最终地址。')
    c.text(64, 30, 'PIPELINE STAGES', 17, MUTED, True)
    c.text(64, 73, 'S0～S8 的计算分工', 40, bold=True)
    c.text(64, 136, 'S0 输入 → S3 mipmap 参数 → S8 最终地址；从输入到输出共 8 拍（3 + 5）。', 25, MUTED)
    left, cw = 64, 185
    for n in range(9):
        x=left+n*cw
        c.rect(x, 210, cw-8, 58, FILLS[n%8])
        c.text(x+(cw-8)/2, 223, (f'S{n} · 输入' if n==0 else f'S{n} · 输出' if n==8 else f'S{n}'), 27, COLORS[n%8], True, 'middle')
        c.line(x, 280, x, 866)
    rows = [
        (0, ['模式与宏块', 'tail 容量', 'mip0 块数']),
        (1, ['各级块数', 'tail 与使能', '高编号块贡献']),
        (2, ['pitch', '低编号块贡献', '高编号部分和']),
        (3, ['补齐低编号和', 'slice / mip 偏移', 'tail 相对编号']),
        (4, ['micro 尺寸', 'reverse / 编码', '原点中间量']),
        (5, ['orig', '+ 局部坐标', 'x/y/z_in_sheet']),
        (6, ['坐标位映射', 'blk_offset']),
    ]
    for n, lines in rows:
        x=left+n*cw
        box(c,x,319,cw-12,155,lines,n%8,18)
        if n<6:c.arrow(x+cw-8,397,x+cw-1,397,MUTED,1)
    box(c,left+7*cw,445,cw-12,175,['blk_index', '高低位 / XOR', 'addr_offset'],7,18)
    box(c,left+8*cw,445,cw-12,175,['address_final', 'mipid_in_tail'],0,18)
    c.arrow(left+7*cw-10,395,left+7*cw+35,433,MUTED,1.5)
    c.arrow(left+8*cw-10,525,left+8*cw-1,525,MUTED,1.5)
    box(c,left+4*cw,684,cw-12,153,['基址处理', '宏块坐标', '乘加中间量'],2,18)
    c.line(left+3*cw+80,483,left+3*cw+80,737,MUTED,1.5)
    c.arrow(left+3*cw+80,737,left+4*cw-6,737,MUTED,1.5)
    c.line(left+5*cw-8,730,left+7*cw+80,730,COLORS[2],2)
    c.arrow(left+7*cw+80,730,left+7*cw+80,632,COLORS[2],2)
    c.text(left+5*cw+8,689,'块索引中间量 → S7 输出',20,COLORS[2],True)
    c.line(left+5*cw-8,820,left+8*cw+80,820,MUTED,1.5)
    c.arrow(left+8*cw+80,820,left+8*cw+80,632,MUTED,1.5)
    c.text(left+5*cw+8,849,'基址 + mip 偏移 → 最终地址',20,MUTED)
    c.line(64,913,1724,913)
    c.text(64,944,'每条通路都使用同一次访问的数据；连线不指定寄存器数量、握手或停顿机制。',26,bold=True)
    c.save('30_teaching_stages')


if __name__ == '__main__':
    overview(); macro_grid(); tail_visit(); stages()
    print('Rendered four teaching figures as SVG and PNG.')
