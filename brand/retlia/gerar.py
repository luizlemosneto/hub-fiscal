import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

BOLD="/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
REG="/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
OUT="/home/user/hub-fiscal/brand/retlia/"

def text_path(fontfile, text, size, x0, y0, track_em=0.0, kern_pairs=None):
    f=TTFont(fontfile); gs=f.getGlyphSet(); cmap=f.getBestCmap(); upm=f['head'].unitsPerEm
    s=size/upm; pen=SVGPathPen(gs); x=x0
    for i,ch in enumerate(text):
        g=cmap[ord(ch)]
        tp=TransformPen(pen,(s,0,0,-s,x,y0)); gs[g].draw(tp)
        adv=gs[g].width*s + track_em*size
        if kern_pairs and i+1<len(text): adv+=kern_pairs.get(text[i:i+2],0)*size
        x+=adv
    return pen.getCommands(), x - track_em*size

INK="#141414"
# Wordmark: cap height of Inter Display ~0.727em
SIZE=200; CAP=0.727*SIZE
TRACK=-0.085
KERN={"Re":-0.01,"et":-0.025,"tL":-0.02,"Li":-0.012,"ia":-0.01}

def symbol(x, base, H):
    """Upper half of the Brazilian-flag lozenge + a small sliver of the globe.
    Flag proportions: lozenge 16.6 x 10.6 -> half: width W = H*2*1.566/... """
    # lozenge: 16.6 x 10.6 (flag 20 x 14) -> half: W = 16.6, H = 5.3
    W=H*3.13
    apex=(x+W/2, base-H)
    tri=f"M{x:.2f} {base:.2f}L{apex[0]:.2f} {apex[1]:.2f}L{x+W:.2f} {base:.2f}Z"
    # globe: radius 3.5/5.3 of half-height, centered on the lozenge centre (base midpoint)
    R=H*3.5/5.3
    return tri, (x+W/2, base, R), W

def build(name, layout):
    parts=[]
    if layout in("h","mark"):
        H=CAP*0.5 if layout=="h" else 100
        pad=40
        tri,(cx,cy,R),W=symbol(pad, pad+ (CAP if layout=="h" else H), H)
        # only a small fraction of the ball: a thin crescent band cut from the base
        sliver_r=R; 
        # one compound path: lozenge half minus a small cap of the globe (no clip seams)
        import math
        d=math.sqrt(R*R-(R*0.62)**2)
        tri=tri[:-1]+f"L{cx+d:.2f} {cy:.2f}A{R:.2f} {R:.2f} 0 0 0 {cx-d:.2f} {cy:.2f}Z"
        clip=""
        mark=f'<path d="{tri}" fill="{INK}"/>'
        if layout=="mark":
            w=W+2*pad; h=H+2*pad
            return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}"><defs>{clip}</defs><rect width="100%" height="100%" fill="#fff"/>{mark}</svg>'
        d,endx=text_path(BOLD,"RetLia",SIZE,pad+W+SIZE*0.10,pad+CAP,TRACK,KERN)
        w=endx+pad; h=CAP+2*pad
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}"><defs>{clip}</defs><rect width="100%" height="100%" fill="#fff"/>{mark}<path d="{d}" fill="{INK}"/></svg>'
def invert(svg):
    return svg.replace('fill="#fff"','fill="@W"').replace(f'fill="{INK}"','fill="#fff"').replace('fill="@W"',f'fill="{INK}"')

def lockup():
    # Swiss poster lockup: info line on top, wordmark below, mark ranged left
    base=build("","h")
    import re
    vb=re.search(r'viewBox="0 0 (\d+) (\d+)"',base); w,h=int(vb.group(1)),int(vb.group(2))
    inner=base.split('fill="#fff"/>',1)[1].rsplit('</svg>',1)[0]
    defs=re.search(r'<defs>.*?</defs>',base).group(0)
    small=15
    t1,_=text_path(REG,"Retificação eSocial",small,40,40+small*0.73,0)
    t2,_=text_path(REG,"Brasil",small,w*0.5,40+small*0.73,0)
    t3,e3=text_path(REG,"retlia.com.br",small,0,0,0)
    t3,_=text_path(REG,"retlia.com.br",small,w-40-e3,40+small*0.73,0)
    off=small*0.73+40
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h+int(off)}">{defs}<rect width="100%" height="100%" fill="#fff"/>'
            f'<path d="{t1} {t2} {t3}" fill="{INK}"/><g transform="translate(0 {off:.1f})">{inner}</g></svg>')

open(OUT+"retlia-lockup-suico.svg","w").write(lockup())
open(OUT+"retlia-horizontal-negativo.svg","w").write(invert(build("","h")))
open(OUT+"retlia-simbolo-negativo.svg","w").write(invert(build("","mark")))
for n,l in [("retlia-horizontal","h"),("retlia-simbolo","mark")]:
    open(OUT+n+".svg","w").write(build(n,l))

# give every file an explicit pixel size equal to its viewBox
import glob, re
for p in glob.glob(OUT+"*.svg"):
    svg=open(p).read()
    if 'width="' not in svg.split(">",1)[0]:
        w,h=re.search(r'viewBox="0 0 (\S+) (\S+)"',svg).groups()
        open(p,"w").write(svg.replace("<svg ",f'<svg width="{w}" height="{h}" ',1))
