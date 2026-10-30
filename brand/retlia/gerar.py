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

# --- Variante lateral: metade lateral do losango atrás do nome, com borda branca ---
import math
def lateral(dark=False):
    ink, paper = ("#fff", INK) if dark else (INK, "#fff")
    pad=40
    H=CAP*1.45                    # altura total do losango (metade lateral)
    W=H*8.3/10.6                  # metade da largura do losango
    top=pad; base_y=pad+(H-CAP)/2+CAP   # nome centrado na altura do símbolo
    x0=pad; cy=top+H/2
    f=TTFont(BOLD); gs=f.getGlyphSet(); sc=SIZE/f['head'].unitsPerEm
    bp=BoundsPen(gs); gs[f.getBestCmap()[ord("I")]].draw(bp); ix0,_,ix1,_=bp.bounds
    lsb=f['hmtx'][f.getBestCmap()[ord("R")]][1]*sc; stem=(ix1-ix0)*sc
    border=SIZE*0.045
    # ponta para a esquerda; o lado reto fica escondido atrás da haste do R
    flat=x0+W
    tx=flat-lsb-stem
    # bola: corpo sólido (o globo), separado do losango pela mesma borda branca do R;
    # só uma fração aparece à esquerda do R
    Rb=(H/2)*3.5/5.3*0.82         # bola um pouco menor que a da bandeira
    Rw=Rb+border                  # recorte branco em volta da bola
    r_left=tx+lsb-border
    cx=r_left-Rb*0.40+Rb
    dy=math.sqrt(Rw*Rw-(flat-cx)**2)
    hb=math.sqrt(Rb*Rb-(r_left-cx)**2)
    # a descida do losango continua até ser interrompida pela borda branca do R
    slope=(H/2)/W
    band_top=base_y-CAP-border; band_bot=base_y+border
    e=(band_top-top)/slope
    sym=(f"M{flat:.2f} {top:.2f}L{flat+e:.2f} {band_top:.2f}"
         f"L{flat:.2f} {band_top:.2f}L{flat:.2f} {cy-dy:.2f}"
         f"A{Rw:.2f} {Rw:.2f} 0 1 0 {flat:.2f} {cy+dy:.2f}"
         f"L{flat:.2f} {band_bot:.2f}L{flat+e:.2f} {band_bot:.2f}"
         f"L{flat:.2f} {top+H:.2f}L{x0:.2f} {cy:.2f}Z"
         f"M{r_left:.2f} {cy-hb:.2f}A{Rb:.2f} {Rb:.2f} 0 0 0 {r_left:.2f} {cy+hb:.2f}Z")
    t,endx=text_path(BOLD,"RetLia",SIZE,tx,base_y,TRACK,KERN)
    w=endx+pad; h=H+2*pad
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}">'
            f'<rect width="100%" height="100%" fill="{paper}"/>'
            f'<path d="{sym}" fill="{ink}"/>'
            # borda branca: recorte reto em volta da haste do R, quinas vivas
            f'<rect x="{r_left:.2f}" y="{base_y-CAP-border:.2f}" width="{flat+0.3-r_left:.2f}" height="{CAP+2*border:.2f}" fill="{paper}"/>'
            f'<path d="{t}" fill="{ink}"/></svg>')

open(OUT+"retlia-lateral.svg","w").write(lateral())
open(OUT+"retlia-lateral-negativo.svg","w").write(lateral(True))
for p in glob.glob(OUT+"retlia-lateral*.svg"):
    svg=open(p).read()
    w,h=re.search(r'viewBox="0 0 (\S+) (\S+)"',svg).groups()
    open(p,"w").write(svg.replace("<svg ",f'<svg width="{w}" height="{h}" ',1))
