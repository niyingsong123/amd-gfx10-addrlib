"""Supplement the six-chapter teaching document with five figure groups.

The three new figures use the checked 3D walkthrough and the current source bit
table. The two reused figures retain their interface and sampling scope. This
script verifies only the values used in the figures, not a new RTL/regression run.
"""
from pathlib import Path
import hashlib
import json
import re
from render_mipmap_memory import Canvas, ROOT, INK, MUTED, LINE, PALE, COLORS, FILLS
from redraw_mas_remaining_diagrams import interface, sampling


def heading(c, tag, title, subtitle):
    c.text(64, 26, tag, 16, MUTED, True)
    c.text(64, 65, title, 39, INK, True)
    c.text(64, 124, subtitle, 21, MUTED)


def figure_data(data):
    source = ROOT / 'ADDRLIB.md'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == data['sources']['ADDRLIB.md']
    line = next(line for line in source.read_text(encoding='utf-8').splitlines()
                if '{`SW_256KB_3D, AA_1X, BPE_1}' in line)
    names = re.findall(r'([xyz])\[(\d+)\]', line.split('|')[2])
    assert [a+b for a, b in names] == data['bit_mapping_msb_first']
    assert len(names) == len(set(names)) == 18

    def offset(x, y, z):
        coords = dict(x=x, y=y, z=z)
        value = 0
        for axis, bit in names:
            value = (value << 1) | ((coords[axis] >> int(bit)) & 1)
        return value

    # Each micro block is an aligned 8x4x8 coordinate region. Its high field
    # enumerates 1024 distinct 256-byte blocks; the low field enumerates 256 bytes.
    micro_ids = {offset(x*8, y*4, z*8) >> 8
                 for z in range(8) for y in range(16) for x in range(8)}
    element_offsets = {offset(x, y, z)
                       for z in range(8) for y in range(4) for x in range(8)}
    assert micro_ids == set(range(1024))
    assert element_offsets == set(range(256))
    micro_xy = [[offset(x*8, y*4, 0) >> 8 for x in range(8)] for y in range(4)]
    element_xy = [[offset(x, y, 0) for x in range(8)] for y in range(4)]
    x, y, z = [v % 64 for v in data['visit']['sheet']]
    high = offset((x//8)*8, (y//4)*4, (z//8)*8) >> 8
    low = offset(x % 8, y % 4, z % 8)
    assert (high << 8) | low == int(data['visit']['blk_offset'])

    rows = []
    for row in data['mips'][data['first_tail_mip']:]:
        w, h, d = row['logical_dimensions']
        ox, oy, oz = row['origin']
        assert ox+w <= 64 and oy+h <= 64 and oz == 0
        rows.append(dict(mip=row['mip'], origin=row['origin'],
                         group_dimensions=[w, h, min(d, 64)]))
    total = sum(w*h*d for w, h, d in [r['group_dimensions'] for r in rows])
    assert total == data['checks']['tail_texels_per_z_group']['0'] == 56054
    return dict(source_sha256=digest, source_line=source.read_text(encoding='utf-8').splitlines().index(line)+1,
                bit_mapping_msb_first=[a+b for a, b in names],
                micro_ids_xy_at_z0=micro_xy, byte_offsets_xy_at_z0=element_xy,
                unique_micro_ids=len(micro_ids), unique_micro_byte_offsets=len(element_offsets),
                selected_access_decomposition=dict(micro_id=high, byte_within_micro=low,
                                                    byte_within_macro=(high << 8) | low),
                tail_group=0, tail_rows=rows, tail_valid_bytes=total,
                separately_aligned_tail_bytes=len(rows)*data['macro_bytes'],
                shared_tail_macro_bytes=data['macro_bytes'])


def numbered_grid(c, x, y, values, size, color, fill, font=20):
    for j, row in enumerate(values):
        for i, value in enumerate(row):
            c.rect(x+i*size, y+j*size, size, size, fill, LINE)
            c.text(x+(i+.5)*size, y+j*size+(size-font)/2-2,
                   str(value), font, color, True, 'middle')


def hierarchy(data, facts):
    c = Canvas(1680, 1290, '宏块、微块与元素的地址位层次',
               '三维256KB模式中，宏块为64x64x64，微块为8x4x8。坐标切片中的编号按实际位映射生成。')
    heading(c, 'BLOCKS AND ADDRESS BITS', '由宏块到微块，再到一个元素',
            'SW_256KB_3D · 1 BPE / 1X · 宏块 64×64×64 · 微块 8×4×8')
    for x, tag, title in [(64, '01', '一个 mip 的宏块网格'),
                          (610, '02', '一个宏块中的微块'),
                          (1156, '03', '一个微块中的元素')]:
        c.text(x, 197, tag, 20, COLORS[0], True)
        c.text(x, 234, title, 26, INK, True)
    c.text(64, 284, 'mip0 · 固定一个 Z 分组', 21, MUTED)
    c.text(610, 284, '固定 Zμ=0，显示前 4 行 Yμ', 21, MUTED)
    c.text(1156, 284, '固定微块内 z=0，显示 XY 平面', 21, MUTED)

    numbered_grid(c, 90, 371, [[x+4*y for x in range(4)] for y in range(3)],
                  87, COLORS[0], FILLS[0], 28)
    c.text(90, 334, '宏块在本 mip 区域内的编号', 20, COLORS[0], True)
    c.text(90, 662, 'X：4 块  ·  Y：3 块', 23, COLORS[0], True)
    c.text(90, 710, '沿 X 递增，再进入下一行 Y。', 21, MUTED)
    c.text(90, 750, '每块容纳 256 KB 的地址空间。', 21, MUTED)
    c.arrow(471, 481, 574, 481, MUTED, 2)
    c.text(525, 439, '展开', 20, MUTED, False, 'middle')

    numbered_grid(c, 634, 371, facts['micro_ids_xy_at_z0'], 50, COLORS[3], FILLS[3], 18)
    c.text(634, 334, '微块编号：块内偏移的高 10 位', 20, COLORS[3], True)
    c.text(834, 585, '…  其余 Y 行与 Z 平面省略  …', 21, MUTED, False, 'middle')
    c.text(634, 620, '横向 Xμ=0…7；纵向 Yμ=0…3', 19, MUTED)
    c.text(634, 662, '8×16×8 = 1024 个微块', 23, COLORS[3], True)
    c.text(634, 710, '每个微块占 256 B。', 21, MUTED)
    c.text(634, 750, '编号由坐标位交织生成。', 21, MUTED)
    c.arrow(1058, 481, 1125, 481, MUTED, 2)
    c.text(1092, 439, '展开', 20, MUTED, False, 'middle')

    numbered_grid(c, 1180, 371, facts['byte_offsets_xy_at_z0'], 50, COLORS[1], FILLS[1], 18)
    c.text(1180, 334, '字节偏移：块内偏移的低 8 位', 20, COLORS[1], True)
    c.text(1380, 585, '…  其余 7 个 Z 平面省略  …', 21, MUTED, False, 'middle')
    c.text(1180, 620, '横向 x=0…7；纵向 y=0…3', 19, MUTED)
    c.text(1180, 662, '8×4×8 = 256 个元素', 23, COLORS[1], True)
    c.text(1180, 710, '每元素 1 B，偏移范围 0…255。', 21, MUTED)
    c.text(1180, 750, '同一行不一定是连续字节。', 21, MUTED)

    c.line(64, 819, 1616, 819)
    c.text(64, 857, '18 位块内字节偏移：高位选择微块，低位选择微块内字节', 27, INK, True)
    x0, cell = 100, 80
    c.rect(x0, 919, 10*cell, 43, FILLS[3])
    c.rect(x0+10*cell, 919, 8*cell, 43, FILLS[1])
    c.text(x0+5*cell, 928, '高 10 位 · 0…1023', 22, COLORS[3], True, 'middle')
    c.text(x0+14*cell, 928, '低 8 位 · 0…255', 22, COLORS[1], True, 'middle')
    for i, name in enumerate(facts['bit_mapping_msb_first']):
        color, fill = (COLORS[3], FILLS[3]) if i < 10 else (COLORS[1], FILLS[1])
        c.text(x0+(i+.5)*cell, 986, str(17-i), 18, MUTED, False, 'middle')
        c.rect(x0+i*cell, 1022, cell, 68, fill, LINE)
        c.text(x0+(i+.5)*cell, 1040, name, 26, color, True, 'middle')
    c.text(64, 1134, 'X / Y / Z 先按块尺寸拆分；各层内部再按对应位序排列。', 25, INK, True)
    c.text(64, 1184, '编号和偏移都从 0 开始；方格表达 XY 坐标，沿格子逐行阅读不等于沿字节地址递增。', 22, MUTED)
    c.text(64, 1230, '这里的高 / 低位分界适用于所列模式与格式；其他组合使用各自的位映射。', 21, MUTED)
    c.save('32_macro_micro_swizzle')


def tail_packing(data, facts):
    c = Canvas(1680, 1200, '同一个Z分组内的tail打包前后',
               '固定zb=0，mip3至10的有效数据为56054字节。假设逐级占一宏块需2MiB，共享尾区使用一个256KB宏块。')
    heading(c, 'MIPMAP TAIL PACKING', '同一个 Z 分组内，小 mip 共享尾区',
            '250×180×1537 · mip0…10 · SW_256KB_3D · 1 BPE / 1X')
    c.rect(64, 170, 1552, 62, PALE)
    c.text(84, 187, '仅比较 zb=0：各 mip 的本级 z=0…63；不足 64 层时只计有效深度。', 24, INK, True)
    c.text(64, 258, '假设每一级分别占一个宏块', 27, INK, True)
    c.text(64, 302, '8 块 × 256 KB = 2 MiB', 26, COLORS[2], True)
    for i, row in enumerate(facts['tail_rows']):
        x = 64 + (i % 4)*180
        y = 372 + (i // 4)*215

        m = row['mip']; w, h, d = row['group_dimensions']; s = 2
        c.rect(x, y, 128, 128, stroke=LINE, hatch=True)
        c.rect(x, y, w*s, h*s, FILLS[m % 8], COLORS[m % 8], 1.4)
        c.text(x, y+141, f'mip{m}', 22, COLORS[m % 8], True)
        c.text(x, y+175, f'{w}×{h}×{d}', 19, MUTED)
    c.arrow(789, 547, 881, 547, COLORS[3], 2)
    c.text(835, 504, '共享', 21, COLORS[3], True, 'middle')

    c.text(926, 258, '按 orig 放进共享 tail 宏块', 27, INK, True)
    c.text(926, 302, '1 块 × 256 KB = 256 KB', 26, COLORS[3], True)
    x0, y0, scale = 926, 372, 5.25
    c.rect(x0, y0, 64*scale, 64*scale, stroke=LINE, hatch=True)
    for row in facts['tail_rows']:
        m = row['mip']; ox, oy, _ = row['origin']; w, h, _ = row['group_dimensions']
        c.rect(x0+ox*scale, y0+oy*scale, w*scale, h*scale, FILLS[m % 8], COLORS[m % 8], 1.4)
        c.dot(x0+ox*scale, y0+oy*scale, 3, COLORS[m % 8])
    c.text(x0+29, y0+195, 'mip3', 25, COLORS[3], True)
    c.text(x0+32*scale+5, y0+13, 'mip4', 21, COLORS[4], True)
    c.text(1296, 370, 'mip / orig(X,Y,Z) / D组', 19, INK, True)
    for j, row in enumerate(facts['tail_rows']):
        m = row['mip']; orig = ','.join(map(str, row['origin'])); d = row['group_dimensions'][2]
        c.text(1296, 415+j*42, f'm{m}   ({orig})   {d}', 21, COLORS[m % 8], True)
    c.text(926, 748, 'XY 投影；圆点标出各 mip 的 orig。', 20, MUTED)
    c.text(926, 786, 'D组为该 mip 在当前 Z 分组内的有效深度。', 19, MUTED)

    c.line(64, 851, 1616, 851)
    c.text(64, 883, '只看这 8 级在 zb=0 中的宏块占用', 26, INK, True)
    for i, row in enumerate(facts['tail_rows']):
        m = row['mip']
        c.rect(64+i*87, 941, 87, 65, FILLS[m % 8], LINE)
        c.text(64+(i+.5)*87, 959, f'm{m}', 22, COLORS[m % 8], True, 'middle')
    c.arrow(790, 973, 881, 973, COLORS[3], 2)
    c.rect(926, 941, 690, 65, FILLS[3], LINE)
    c.text(1271, 959, 'Tail · 一个 256 KB 宏块', 25, COLORS[3], True, 'middle')
    c.text(64, 1032, '有效数据同为 56,054 B；变化的是块占用，图中左右地址条不按相同容量比例绘制。', 23, INK, True)
    c.text(64, 1081, '共享条件包含尺寸和层级容量限制，不能只用有效数据量之和判断是否可进入 tail。', 22, MUTED)
    c.text(64, 1128, 'mip3、mip4 还在其他 Z 分组中有数据；上图不代表整条三维 tail 的总容量。', 22, MUTED)
    c.text(64, 1171, '两侧方框均为 64×64 的 XY 坐标范围；地址条为宏块槽位，彩色投影不表示连续字节段。', 18, MUTED)
    c.save('33_tail_packing_3d')


def box(c, x, y, w, h, color, fill, lines):
    c.rect(x, y, w, h, fill, LINE)
    c.rect(x, y, 5, h, color)
    for i, (text, size) in enumerate(lines):
        c.text(x+22, y+17+i*39, text, size, color if i == 0 else INK, i == 0)


def address_composition():
    c = Canvas(1600, 1420, 'Tiled地址的高低位、XOR和最终合成',
               '块内高位先掩码后XOR再左移八位，块内低八位单独保留，与宏块字节偏移按位或，最后加处理后的基址与mip偏移。')
    heading(c, 'TILED ADDRESS COMPOSITION', '块内高低位、XOR 与最终地址',
            '宏块偏移和块内字段先做 OR；基址与 mip 偏移经过单位转换后，再做加法。')
    box(c, 64, 211, 919, 110, COLORS[0], FILLS[0],
        [('位映射输出：blk_offset', 27), ('单位：字节；拆分高于 bit7 的字段与低 8 位', 23)])
    box(c, 1050, 211, 486, 110, COLORS[3], FILLS[3],
        [('基址中提取的 swizzle 字段', 24), ('swizzle_bits_256B', 24)])
    c.arrow(274, 321, 274, 416, COLORS[1], 2)
    c.arrow(773, 321, 773, 416, COLORS[2], 2)
    box(c, 64, 416, 420, 110, COLORS[1], FILLS[1],
        [('仅保留低 8 位', 26), ('blk_offset[7:0]', 25)])
    box(c, 563, 416, 420, 110, COLORS[2], FILLS[2],
        [('高位截取并 AND 掩码', 24), ('blk_offset[…:8] & ms_mask_256B', 20)])
    c.arrow(773, 526, 773, 612, COLORS[2], 2)
    box(c, 563, 612, 420, 94, COLORS[2], FILLS[2],
        [('XOR', 27), ('得到 swizzle_bits', 22)])
    c.line(1293, 321, 1293, 659, COLORS[3], 2)
    c.arrow(1293, 659, 983, 659, COLORS[3], 2)
    c.arrow(773, 706, 773, 772, COLORS[2], 2)
    box(c, 563, 772, 420, 96, COLORS[2], FILLS[2],
        [('左移 8 位，放回高位位置', 23), ('(swizzle_bits << 8)[19:0]', 23)])
    box(c, 1050, 772, 486, 96, COLORS[0], FILLS[0],
        [('宏块字节偏移', 25), ('blk_index[47:0]', 24)])
    c.line(274, 526, 274, 989, COLORS[1], 2)
    c.arrow(274, 989, 563, 989, COLORS[1], 2)
    c.text(74, 789, 'blk_offset_final', 24, COLORS[1], True)
    c.text(74, 832, '低位直接保留', 23, MUTED)
    c.arrow(773, 868, 773, 942, COLORS[2], 2)
    c.line(1293, 868, 1293, 989, COLORS[0], 2)
    c.arrow(1293, 989, 983, 989, COLORS[0], 2)
    box(c, 563, 942, 420, 94, INK, PALE,
        [('OR：按字段合成', 26), ('addr_offset，单位：字节', 23)])
    box(c, 64, 1135, 650, 118, COLORS[3], FILLS[3],
        [('基址与 mip 偏移：256 B → 字节', 26),
         ('(baseAddr256B_out + mip_offset_b) << 8', 22)])
    c.line(773, 1036, 773, 1085, INK, 2)
    c.line(773, 1085, 880, 1085, INK, 2)
    c.arrow(880, 1085, 880, 1160, INK, 2)
    c.arrow(714, 1191, 845, 1191, COLORS[3], 2)
    c.dot(880, 1191, 29, PALE)
    c.text(880, 1175, '+', 37, INK, True, 'middle')
    c.arrow(916, 1191, 1010, 1191, INK, 2)
    box(c, 1010, 1135, 526, 118, COLORS[1], FILLS[1],
        [('S8：address_final', 29), ('最终字节地址', 24)])
    c.text(64, 1301, '不能再把完整 blk_offset OR 进结果，否则会覆盖高位 XOR 的效果。', 23, INK, True)
    c.text(64, 1349, '本图展开 Tiled 通路；Linear 使用 micro_offset_linear 作为低位候选。', 21, MUTED)
    c.text(64, 1388, '字段截取、基址清理及非零 XOR 的模式条件，按相应公式和位宽约定处理。', 19, MUTED)
    c.save('34_address_compose')


def render(data):
    facts = figure_data(data)
    interface()
    counts = sampling()
    hierarchy(data, facts)
    tail_packing(data, facts)
    address_composition()
    result = dict(
        status='checked teaching figures; not a trusted baseline',
        sources={'ADDRLIB.md': facts.pop('source_sha256'),
                 'docs/ADDRLIB_MAS_3D_WALKTHROUGH_CHECK.json': hashlib.sha256(
                     (ROOT/'docs/ADDRLIB_MAS_3D_WALKTHROUGH_CHECK.json').read_bytes()).hexdigest(),
                 'scripts/render_mas_supplement.py': hashlib.sha256(
                     Path(__file__).read_bytes()).hexdigest()},
        input=data['input'], figures=facts, sampling=counts,
        units={'coordinates': 'elements local to the selected mip',
               'micro_id': '256-byte block number within a macro',
               'element_offset': 'bytes within a micro',
               'tail_capacity_comparison': 'bytes within Z group 0 only'},
        assumptions=['ordinary uncompressed 1-byte elements, one sample',
                     'figure coordinates and bit indices fit in exact Python integers',
                     'bit-table hierarchy is specific to SW_256KB_3D / AA_1X / BPE_1',
                     'tail depths are clipped to the selected 64-layer group',
                     'address diagram retains masks and widths symbolically; it defines no new widths'],
        validation_scope='1024 micro IDs and 256 low-byte offsets are permutations; selected address decomposition and Z-group tail volumes match the existing walkthrough; sampling neighbor counts checked. No new random/RTL/upstream run.')
    (ROOT/'docs/ADDRLIB_MAS_SUPPLEMENT_CHECK.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Rendered 5 figure groups; checked micro/element numbering, tail volumes and sampling reuse.')


if __name__ == '__main__':
    render(json.loads((ROOT/'docs/ADDRLIB_MAS_3D_WALKTHROUGH_CHECK.json').read_text(encoding='utf-8')))
