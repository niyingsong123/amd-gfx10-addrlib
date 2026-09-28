"""Rebuild the two explanatory memory diagrams (Python + Pillow, Node.js).

This is a derived illustration of the original ADDRLIB.md, not an allocator
implementation, RTL simulation, or a new trusted regression case.
"""
from pathlib import Path
import hashlib
import html
import json
import math
import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/addrlib_mas/diagrams"
DATA = OUT / "mipmap_memory_data.json"
INPUT = dict(mode="SW_256KB_3D", W=250, H=180, D=130, e=0, s=0, maxmip=7)
INK = "#183248"
MUTED = "#516577"
LINE = "#D5DFE6"
PAPER = "#FFFFFF"
PALE = "#F3F6F9"
COLORS = {0: "#246BB0", 1: "#15867D", 2: "#A56A13", 3: "#7552B2",
          4: "#BB477D", 5: "#398443", 6: "#9B7415", 7: "#407CA5"}
FILLS = {0: "#E0EDF9", 1: "#DEF2EF", 2: "#FFF0CF", 3: "#EEE5FC",
         4: "#FBE4EF", 5: "#E5F2DE", 6: "#FFF2BB", 7: "#E2F2FB"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_node():
    choices = [os.environ.get("NODE_BINARY"), shutil.which("node"),
               str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")]
    return next(p for p in choices if p and Path(p).is_file())


def swizzle(x, y, z):
    # ADDRLIB.md SW_256KB_3D, AA_1X, BPE_1, MSB to LSB.
    names = "y5 z5 x5 y4 z4 x4 y3 z3 x3 y2 z2 x2 z1 y1 y0 z0 x1 x0".split()
    xyz = dict(x=x, y=y, z=z)
    value = 0
    for name in names:
        value = (value << 1) | ((xyz[name[0]] >> int(name[1])) & 1)
    return value


def origin(relative_mip):
    reverse = 11 - (relative_mip + 1)
    code = 0 if reverse < 0 else (16 << reverse if reverse > 6 else reverse << 8)
    xmicro = sum(((code >> (9 + 2 * k)) & 1) << k for k in range(6))
    ymicro = sum(((code >> (8 + 2 * k)) & 1) << k for k in range(6))
    return [xmicro << 3, ymicro << 2, 0], reverse, code


def make_data():
    js = """const m=require('./scripts/mipmap_compare/document.cjs');
const s=m.surface(JSON.parse(process.argv[1]));
console.log(JSON.stringify(s,(_,v)=>typeof v==='bigint'?v.toString():v));"""
    model = json.loads(subprocess.check_output(
        [runtime_node(), "-e", js, json.dumps(INPUT)], cwd=ROOT, text=True, encoding="utf-8"))
    assert model["b"]["logs"] == [6, 6, 6]
    assert model["first"] == 3 and model["cap"] == 11
    assert list(map(int, model["sizes"][:8])) == [12, 4, 1, 1, 0, 0, 0, 0]
    assert int(model["slice"]) == 18 * 64 * 64
    rows = []
    for m in range(8):
        row = dict(mip=m, logical_dimensions=[max(1, INPUT[k] >> m) for k in ("W", "H", "D")],
                   document_pitch=model["pitch"][m],
                   xy_macro_blocks=[model["pitch"][m] // 64, model["height"][m] // 64],
                   mipsize_contribution=int(model["sizes"][m]),
                   macro_offset_256B=int(model["offset"][m]),
                   macro_offset_bytes=int(model["offset"][m]) * 256)
        if m >= 3:
            orig, reverse, code = origin(m - 3)
            row.update(tail_relative_mip=m-3, origin=orig, reverse=reverse,
                       origin_generation_code=code, swizzled_origin_bytes=swizzle(*orig))
        rows.append(row)
    occupied = {}
    for r in rows[3:]:
        ox, oy, oz = r["origin"]
        w, h, d = r["logical_dimensions"]
        assert ox+w <= 64 and oy+h <= 64 and oz+d <= 64
        for z in range(d):
            for y in range(h):
                for x in range(w):
                    a = swizzle(ox+x, oy+y, oz+z)
                    assert a not in occupied, (r["mip"], occupied.get(a), a)
                    occupied[a] = r["mip"]
    # Check the coordinate lookup against existing trusted examples.
    assert origin(1)[0] == [32, 0, 0]
    assert swizzle(37, 6, 3) == 0x8175
    assert 0x30000000 + (6+3*22+2*4+1)*0x40000 + swizzle(69,134,195) == 0x31440175
    assert swizzle(0,0,1) == 4 and swizzle(0,0,2) == 32
    last_begin = (2*18 + 6 + 2*4 + 3) * 0x40000
    assert last_begin == 0xD40000 and last_begin + 0x40000 == 0xD80000
    return dict(
        status="derived illustration; not a trusted case", algorithm="original ADDRLIB.md",
        sources={f: sha(ROOT/f) for f in ["ADDRLIB.md", "scripts/mipmap_compare/document.cjs",
                 "case/case0_mip4_xyz_5_6_3.md", "case/case1_mip0_xyz_69_134_195.md"]},
        input=INPUT, byte_base=0, swizzle_seed=0, macro_dimensions=[64,64,64], macro_bytes=262144,
        micro_dimensions=[8,4,8], first_tail_mip=3, tail_capacity=11,
        chain_blocks_per_z_group=18, chain_stride_bytes=0x480000,
        slice_raw=int(model["slice"]), mips=rows,
        boundary_macro=dict(index=[3,2,2], origin=[192,128,128], effective_dimensions=[58,52,2],
                            valid_texel_bytes=58*52*2, interval_bytes=[last_begin,last_begin+0x40000]),
        assumptions=["MAXMIP=17; integer arithmetic has sufficient width",
                     "Logical texel dimensions use max(1, floor(base dimension / 2**mip)); this does not replace the document block recurrence",
                     "The document does not consume map0_d in mipmap layout; depth here only identifies valid local mip coordinates",
                     "Uniform z-group address coverage is not an upstream exact resource allocation size",
                     "Zero swizzle seed, byte base B=0, coordinates local to the selected mip",
                     "Origin generation uses BYTE_OFFSET_IN_MIPTAIL_WIDTH=20 and the original 256KB 3D BPE1 bit table"],
        checks=dict(tail_address_injectivity_texels=len(occupied), tail_address_collisions=0,
                    trusted_mip4_address="0x30008175", trusted_mip0_address="0x31440175",
                    scope="one illustrative configuration and two selected known coordinate checks; no RTL or random regression"))


def font_paths():
    candidates = [
        ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ]
    if os.environ.get("DIAGRAM_FONT"):
        p = os.environ["DIAGRAM_FONT"]
        return p, os.environ.get("DIAGRAM_BOLD_FONT", p)
    return next((a,b) for a,b in candidates if Path(a).is_file() and Path(b).is_file())


class Canvas:
    def __init__(self, w, h, title, desc):
        self.w, self.h, self.scale = w, h, 2
        self.im = Image.new("RGB", (w*2, h*2), PAPER)
        self.draw = ImageDraw.Draw(self.im)
        self.regular, self.bold = font_paths()
        self.fonts = {}
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
                    f'<title>{html.escape(title)}</title><desc>{html.escape(desc)}</desc>',
                    '<defs><pattern id="hatch" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="12" fill="#F3F6F9"/><path d="M-3,3 L3,-3 M0,12 L12,0 M9,15 L15,9" stroke="#D5DFE6" stroke-width="1"/></pattern></defs>',
                    f'<rect width="{w}" height="{h}" fill="white"/>']

    def rect(self, x,y,w,h, fill=PAPER, stroke=None, sw=1, hatch=False):
        box=(round(x*2),round(y*2),round((x+w)*2),round((y+h)*2))
        if hatch:
            tile=Image.new('RGB',(max(1,round(w*2)),max(1,round(h*2))),PALE)
            d=ImageDraw.Draw(tile)
            for k in range(-round(h*2),round(w*2)+1,24):
                d.line((k,round(h*2),k+round(h*2),0),fill=LINE,width=2)
            self.im.paste(tile,(box[0],box[1]))
        else:
            self.draw.rectangle(box, fill=fill)
        if stroke: self.draw.rectangle(box, outline=stroke, width=max(1,round(sw*2)))
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{"url(#hatch)" if hatch else fill}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')

    def line(self, x1,y1,x2,y2, color=LINE, width=1):
        self.draw.line(tuple(round(n*2) for n in (x1,y1,x2,y2)), fill=color, width=max(1,round(width*2)))
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')

    def text(self,x,y,value,size=20,color=INK,bold=False,anchor="start"):
        key=(size,bold)
        if key not in self.fonts:
            self.fonts[key]=ImageFont.truetype(self.bold if bold else self.regular,round(size*2))
        font=self.fonts[key]
        length=self.draw.textlength(value,font=font)/2
        left=x-(length if anchor=="end" else length/2 if anchor=="middle" else 0)
        assert left >= 0 and left+length <= self.w, (value,left,length)
        self.draw.text((round(left*2),round(y*2)),value,font=font,fill=color,anchor="lt")
        self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" dominant-baseline="text-before-edge">{html.escape(value)}</text>')

    def dot(self,x,y,r=4,color=INK):
        self.draw.ellipse(((x-r)*2,(y-r)*2,(x+r)*2,(y+r)*2),fill=color)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

    def arrow(self,x1,y1,x2,y2,color=MUTED,width=1.5):
        self.line(x1,y1,x2,y2,color,width)
        a=math.atan2(y2-y1,x2-x1)
        for off in [-0.45,0.45]:
            self.line(x2,y2,x2-10*math.cos(a+off),y2-10*math.sin(a+off),color,width)

    def save(self,name):
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/(name+".svg")).write_text('\n'.join(self.svg+['</svg>'])+'\n',encoding='utf-8')
        self.im.save(OUT/(name+".png"),optimize=True)


def header(c,part,title,subtitle):
    c.text(56,34,"ADDRLIB  /  MEMORY ATLAS",16,MUTED,bold=True)
    c.text(1384,34,part,16,MUTED,anchor="end")
    c.text(56,72,title,42,bold=True)
    c.text(56,134,subtitle,22,MUTED)
    c.rect(56,181,1328,72,PALE)
    c.text(76,194,"250 × 180 × 130    ·    mip0…7    ·    SW_256KB_3D    ·    1 B/元素    ·    单采样",20,bold=True)
    c.text(76,225,"macro = 64 × 64 × 64 = 256 KiB    |    B 为字节基址，swizzle seed = 0",17,MUTED)


def memory_figure(data):
    c=Canvas(1440,1320,"多 mipmap 的内存排布：mip、z 与对齐",
             "每个z宏块分组链步长18个宏块。组内顺序tail、mip2、mip1、mip0。三维宏块含64层，最后宏块有效58乘52乘2。")
    header(c,"01 / 02","多 mipmap 的内存排布","先看线性地址，再展开 Z 深度分组与宏块边界。所有地址偏移单位为字节。")
    c.text(56,280,"01  线性地址：同一 Z 分组内，tail → mip2 → mip1 → mip0",26,bold=True)
    c.text(56,319,"zb = z >> 6（mip 内坐标）",17,MUTED)
    xs=[284,414,544,804,1384]
    for x,t in zip(xs,["+0","+0x040000","+0x080000","+0x180000","+0x480000"]):
        c.text(x,331,t,16,MUTED,anchor="end" if x==1384 else "start")
    for g,y in enumerate([370,463,556]):
        c.text(56,y+2,f"zb={g} · z={g*64}…{g*64+63}",20,bold=True)
        c.text(56,y+32,f"组基址 B+0x{g*0x480000:06X}",17,MUTED)
        labels=["tail · m3…7","mip2 · 1块","mip1 · 4块","mip0 · 12块"]
        if g==1: labels=["无有效 mip","无有效 mip","mip1 · 仅 z=64 有效","mip0 · z=64…127"]
        if g==2: labels=["无有效 mip","无有效 mip","无有效 mip","mip0 · 仅 z=128、129 有效"]
        for k,m in enumerate([3,2,1,0]):
            unused=(g==1 and k<2) or (g==2 and k<3)
            c.rect(xs[k],y,xs[k+1]-xs[k],57,FILLS[m],LINE,hatch=unused)
            c.text((xs[k]+xs[k+1])/2,y+18,labels[k],17 if k<2 else 19,
                   MUTED if unused else COLORS[m],bold=not unused,anchor="middle")
        c.text(xs[0]+65,y+62,"共享1块" if g==0 else "",14,MUTED,anchor="middle")
    c.text(56,657,"链步长 = (1 + 1 + 4 + 12) × 256 KiB = 0x480000 B = 4.5 MiB",23,bold=True)
    c.text(56,698,"斜线槽位没有本 mip 的有效数据；这里画统一步长覆盖的地址区间，不宣称精确资源分配总量。段宽已压缩。",19,MUTED)
    c.line(56,745,1384,745)
    c.text(56,777,"02  一个宏块内的不同 z 平面",26,bold=True)
    for x,y,label in [(150,843,"z_local=63"),(126,886,"z_local=1"),(102,929,"z_local=0")]:
        c.rect(x,y,370,92,FILLS[0],COLORS[0],1.5)
        c.text(x+18,y+14,label,21,COLORS[0],bold=True)
    c.text(548,839,"… z=2…62 …",17,MUTED)
    c.text(548,880,"每面 64×64",18,MUTED)
    c.text(548,914,"共 64 层",18,MUTED)
    c.text(56,1048,"同一宏块内，z 位参与 swizzle，平面字节并非连续。",20,bold=True)
    c.text(56,1087,"(0,0,0) → 0x0   ·   (0,0,1) → 0x4   ·   (0,0,2) → 0x20",18,MUTED)
    c.text(56,1122,"到 z=64 才换到下一个 Z 分组；中间各层用 … 省略。",19,MUTED)
    c.line(738,785,738,1158)
    c.text(782,777,"03  最后一个宏块：边缘补齐",26,bold=True)
    x,y,s=792,850,240
    c.rect(x,y,s,s,stroke=LINE,hatch=True)
    c.rect(x,y,s*58/64,s*52/64,FILLS[0],COLORS[0])
    c.text(x+12,y+58,"有效 XY：58×52",20,COLORS[0],bold=True)
    c.text(x+12,y+95,"x=192…249",18,COLORS[0])
    c.text(x+12,y+126,"y=128…179",18,COLORS[0])
    c.text(x+s/2,y+s*52/64+13,"12 行补齐",16,MUTED,anchor="middle")
    c.text(x+116,y-30,"对齐宽 64",18,MUTED,anchor="middle")
    c.text(1062,841,"块坐标 (3,2,2)",20,bold=True)
    c.text(1062,880,"原点 (192,128,128)",18,MUTED)
    c.text(1062,918,"有效 58×52×2",21,COLORS[0],bold=True)
    c.text(1062,955,"→ 对齐到 64×64×64",19,MUTED)
    c.rect(1062,1001,270,35,hatch=True,stroke=LINE)
    c.rect(1062,1001,270*2/64,35,FILLS[0],COLORS[0])
    c.text(1062,1050,"Z：2 层有效 + 62 层补齐",19,MUTED)
    c.text(792,1123,"X 尾部补齐 6 列；Y 尾部补齐 12 行。",19,MUTED)
    c.line(56,1175,1384,1175)
    c.text(56,1202,"最后宏块 [B+0xD40000, B+0xD80000)：边界按 256 KiB 对齐。",22,bold=True)
    c.text(56,1244,"补齐区是 X/Y/Z 坐标空间的边缘，经 swizzle 后可能分散；不能一律画成末尾一段连续字节。",20,MUTED)
    c.text(56,1283,"共享 tail 占 1 个宏块；尾内各级通过不同 orig 定位。",16,MUTED)
    c.save("07_mipmap_memory_layout")


def tail_figure(data):
    c=Canvas(1440,1260,"共享 mipmap tail：orig 原点、深度截面与块内地址",
             "mip3至mip7共享一个64立方宏块，分别平移到不同XY原点。图以texel坐标显示占用区域，右侧列出深度有效范围和swizzle后的原点字节偏移。")
    header(c,"02 / 02","放大 mipmap tail：orig 决定落点","所有 tail mip 共用同一宏块基址；先加局部坐标原点，再按位表得到块内字节地址。")
    c.text(56,279,"04  zb=0 的 tail：一个 64×64×64 宏块",26,bold=True)
    c.text(56,322,"共享范围 [B, B+0x40000)  ·  XY 投影（元素单位）",19,MUTED)
    x,y,s=96,405,512
    c.rect(x,y,s,s,hatch=True,stroke=LINE)
    for v in range(8,64,8):
        c.line(x+v*8,y,x+v*8,y+s,"#DFE6ED")
        c.line(x,y+v*8,x+s,y+v*8,"#DFE6ED")
    for v in [0,16,32,48,64]:
        c.text(x+v*8,y-32,str(v),17,MUTED,anchor="middle")
        c.text(x-17,y+v*8-9,str(v),17,MUTED,anchor="end")
    c.arrow(x,y-52,x+s,y-52)
    c.text(x+s+12,y-65,"X",20,MUTED)
    c.arrow(x-55,y,x-55,y+s)
    c.text(x-63,y+s+13,"Y",20,MUTED)
    for r in data["mips"][3:]:
        m=r["mip"]; ox,oy,_=r["origin"]; w,h,_=r["logical_dimensions"]
        c.rect(x+ox*8,y+oy*8,w*8,h*8,FILLS[m],COLORS[m],2)
        c.dot(x+ox*8,y+oy*8,4,COLORS[m])
    c.text(x+18,y+32*8+24,"mip3",29,COLORS[3],bold=True)
    c.text(x+18,y+32*8+65,"orig (0,32,0)",21,COLORS[3])
    c.text(x+18,y+32*8+99,"31×22×16",21,COLORS[3])
    c.text(x+32*8+12,y+16,"mip4",24,COLORS[4],bold=True)
    c.text(x+32*8+12,y+52,"15×11×8",17,COLORS[4])
    c.text(x+65,y+16*8+3,"mip5",20,COLORS[5],bold=True)
    c.text(x+16*8+34,y+2,"mip6",18,COLORS[6],bold=True)
    c.line(x+8*8+9,y+8*8+4,x+8*8+45,y+8*8+4,COLORS[7])
    c.text(x+8*8+50,y+8*8-9,"mip7",18,COLORS[7],bold=True)
    c.dot(100,956,4,INK)
    c.text(115,943,"圆点为各级 orig；填色为有效 texel 的 XY 投影。",19,MUTED)
    c.text(96,977,"斜线为未使用/补齐坐标区；不同 z 的有效区域见右表。",18,MUTED)
    c.text(681,335,"tail_mipid=3  ·  容量上限11级  ·  本例使用5级",20,bold=True)
    c.text(681,378,"mip",17,MUTED)
    c.text(754,378,"有效 W×H×D",17,MUTED)
    c.text(940,378,"orig (X,Y,Z)",17,MUTED)
    c.text(1137,367,"原点经 swizzle 后",16,MUTED)
    c.text(1137,389,"块内字节偏移",16,MUTED)
    c.line(681,422,1384,422)
    for j,r in enumerate(data["mips"][3:]):
        yy=444+j*54; m=r['mip']
        c.text(681,yy,f"m{m}",21,COLORS[m],bold=True)
        c.text(754,yy,"×".join(map(str,r['logical_dimensions'])),20)
        c.text(940,yy,"("+",".join(map(str,r['origin']))+")",20)
        c.text(1137,yy,f"0x{r['swizzled_origin_bytes']:05X}",20,COLORS[m],bold=True)
        c.line(681,yy+37,1384,yy+37)
    c.text(681,743,"同一 tail 内：随 z 增大，有效 mip 逐渐减少",22,bold=True)
    for j,(label,mips) in enumerate([("z=0",[3,4,5,6,7]),("z=1",[3,4,5,6]),
            ("z=2…3",[3,4,5]),("z=4…7",[3,4]),("z=8…15",[3]),("z=16…63",[])]):
        yy=790+34*j
        c.text(681,yy,label,19,MUTED)
        for k,m in enumerate(mips):
            c.rect(859+75*k,yy-1,65,27,FILLS[m])
            c.text(891+75*k,yy+1,f"mip{m}",17,COLORS[m],bold=True,anchor="middle")
        if not mips: c.text(859,yy,"无有效 texel（全部为未使用空间）",18,MUTED)
    c.line(56,1035,1384,1035)
    c.text(56,1062,"例：mip4 的局部点 (5,6,3)",23,bold=True)
    c.text(56,1109,"orig (32,0,0) + (5,6,3) = (37,6,3)",24,COLORS[4],bold=True)
    c.arrow(650,1125,717,1125,COLORS[4],2)
    c.text(740,1109,"swizzle → 0x8175 → B+0x8175",24,COLORS[4],bold=True)
    c.text(56,1164,"生成 orig 的 byte_offset=0x2000 是拆位用的中间量，不能直接当成该点或该 mip 的字节偏移。",20,MUTED)
    c.text(56,1204,"坐标先加 orig，再生成块内偏移；mip_offset_b × 256 确定相对基址的宏块起点。",17,MUTED)
    c.save("08_mipmap_tail_layout")


if __name__ == "__main__":
    data=make_data()
    memory_figure(data)
    tail_figure(data)
    DATA.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(generated=["07_mipmap_memory_layout.svg/.png","08_mipmap_tail_layout.svg/.png"],
                         checks=data['checks']),ensure_ascii=False))
