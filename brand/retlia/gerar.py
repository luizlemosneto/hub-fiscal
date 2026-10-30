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
def lateral(dark=False, loz=None, ball=None, text=None, fold=False, flapc=None):
    ink, paper = ("#fff", INK) if dark else (INK, "#fff")
    loz=loz or ink; ball=ball or ink; text=text or ink
    flapc=flapc or (('#8E8E8E','#5A5A5A') if dark else ('#E6E6E6','#A4A4A4'))
    defs=''
    pad=40
    H=CAP*1.75                    # altura total do losango (metade lateral)
    W=H*8.3/10.6                  # metade da largura do losango
    top=pad; base_y=pad+(H-CAP)/2+CAP   # nome centrado na altura do símbolo
    x0=pad; cy=top+H/2
    f=TTFont(BOLD); gs=f.getGlyphSet(); sc=SIZE/f['head'].unitsPerEm
    bp=BoundsPen(gs); gs[f.getBestCmap()[ord("I")]].draw(bp); ix0,_,ix1,_=bp.bounds
    lsb=f['hmtx'][f.getBestCmap()[ord("R")]][1]*sc; stem=(ix1-ix0)*sc
    border=SIZE*0.07
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
    # a ponta aguda onde a descida encontra o branco ganha um arredondamento
    a=math.atan(slope); fr=border*0.45; d=fr/math.tan(a/2)
    ca,sa=math.cos(a),math.sin(a)
    px=flat+e
    sym=(f"M{flat:.2f} {top:.2f}L{px-d*ca:.2f} {band_top-d*sa:.2f}"
         f"A{fr:.2f} {fr:.2f} 0 0 1 {px-d:.2f} {band_top:.2f}"
         f"L{flat:.2f} {band_top:.2f}L{flat:.2f} {cy-dy:.2f}"
         f"A{Rw:.2f} {Rw:.2f} 0 1 0 {flat:.2f} {cy+dy:.2f}"
         f"L{flat:.2f} {band_bot:.2f}L{px-d:.2f} {band_bot:.2f}"
         f"A{fr:.2f} {fr:.2f} 0 0 1 {px-d*ca:.2f} {band_bot+d*sa:.2f}"
         f"L{flat:.2f} {top+H:.2f}L{x0:.2f} {cy:.2f}Z")
    globe=(f"M{r_left:.2f} {cy-hb:.2f}A{Rb:.2f} {Rb:.2f} 0 0 0 {r_left:.2f} {cy+hb:.2f}Z")
    t,endx=text_path(BOLD,"RetLia",SIZE,tx,base_y,TRACK,KERN)
    w=endx+pad; h=H+2*pad
    rx=tx+lsb; rtop=base_y-CAP
    if fold:
        # orelha de página de verdade: o canto A-B-C é cortado na diagonal (vinco B-C) e a ponta
        # dobrada cai sobre a folha como o reflexo exato do canto, com o ângulo reto em A'
        fs=stem*0.92
        Ax,Ay=rx,rtop; Bx,By=rx+fs,rtop; Cx,Cy=rx,rtop+fs; Px,Py=rx+fs,rtop+fs
        rr=fs*0.10                          # quina da aba levemente arredondada
        c0=Ax+Ay+fs                          # reta do vinco: x + y = c0
        cut=(f'<path d="M{Ax-1:.2f} {Ay-1:.2f}L{Bx+1:.2f} {Ay-1:.2f}L{Ax-1:.2f} {Cy+1:.2f}Z" fill="{paper}"/>')
        flap_d=(f"M{Bx:.2f} {By:.2f}L{Px:.2f} {Py-rr:.2f}A{rr:.2f} {rr:.2f} 0 0 1 {Px-rr:.2f} {Py:.2f}L{Cx:.2f} {Cy:.2f}Z")
        mx,my=(Bx+Cx)/2,(By+Cy)/2
        sh=fs*0.06
        defs=(f'<defs><linearGradient id="fg" gradientUnits="userSpaceOnUse" x1="{mx:.2f}" y1="{my:.2f}" x2="{Px:.2f}" y2="{Py:.2f}">'
              f'<stop offset="0" stop-color="{flapc[0]}"/><stop offset="1" stop-color="{flapc[1]}"/></linearGradient>'
              f'<filter id="fb" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="{fs*0.045:.2f}"/></filter>'
              f'<clipPath id="fc"><path d="M{Bx+40:.2f} {By-40:.2f}L{Bx+40:.2f} {Cy+40:.2f}L{Ax-40:.2f} {Cy+40:.2f}Z"/></clipPath></defs>')
        flap=(cut
              # sombra suave da aba sobre a folha (só do lado de baixo do vinco)
              +f'<g clip-path="url(#fc)"><path d="{flap_d}" transform="translate({sh:.2f} {sh:.2f})" fill="#000" fill-opacity="0.38" filter="url(#fb)"/></g>'
              +f'<path d="{flap_d}" fill="url(#fg)"/>')
        knockout=(f'<path d="M{flat+0.3:.2f} {band_top:.2f}H{r_left+border:.2f}A{border:.2f} {border:.2f} 0 0 0 {r_left:.2f} {band_top+border:.2f}'
                  f'V{band_bot-border:.2f}A{border:.2f} {border:.2f} 0 0 0 {r_left+border:.2f} {band_bot:.2f}H{flat+0.3:.2f}Z" fill="{paper}"/>')
    else:
        # cantos do lado aparente arredondados, concêntricos às quinas do R
        knockout=(f'<path d="M{flat+0.3:.2f} {band_top:.2f}H{r_left+border:.2f}A{border:.2f} {border:.2f} 0 0 0 {r_left:.2f} {band_top+border:.2f}'
                  f'V{band_bot-border:.2f}A{border:.2f} {border:.2f} 0 0 0 {r_left+border:.2f} {band_bot:.2f}H{flat+0.3:.2f}Z" fill="{paper}"/>')
        flap=""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}">'+defs+
            f'<rect width="100%" height="100%" fill="{paper}"/>'
            f'<path d="{sym}" fill="{loz}"/><path d="{globe}" fill="{ball}"/>'
            + knockout +
            f'<path d="{t}" fill="{text}"/>' + flap + '</svg>')

open(OUT+"retlia-lateral.svg","w").write(lateral())
open(OUT+"retlia-lateral-negativo.svg","w").write(lateral(True))
# tons de cinza: nome no preto, losango no cinza médio, bola no cinza escuro
open(OUT+"retlia-lateral-cinza.svg","w").write(lateral(loz="#ABABAB", ball="#6E6E6E", text="#3D3D3D"))
open(OUT+"retlia-lateral-cinza-negativo.svg","w").write(lateral(True, loz="#5E5E5E", ball="#A6A6A6", text="#D6D6D6"))
# cores da bandeira em tom pastel (losango amarelo, globo azul) e nome em verde-musgo
open(OUT+"retlia-lateral-musgo.svg","w").write(lateral(loz="#EBDC92", ball="#9DB7D5", text="#4A5A2C"))
open(OUT+"retlia-lateral-musgo-negativo.svg","w").write(lateral(True, loz="#E3D58C", ball="#8DA9C8", text="#C2CFA0"))
# variante eSocial: o R vira uma folha com a orelha dobrada
open(OUT+"retlia-dobra.svg","w").write(lateral(fold=True))
open(OUT+"retlia-dobra-negativo.svg","w").write(lateral(True, fold=True))
open(OUT+"retlia-dobra-cinza.svg","w").write(lateral(loz="#ABABAB", ball="#6E6E6E", text="#3D3D3D", fold=True))
open(OUT+"retlia-dobra-cinza-negativo.svg","w").write(lateral(True, loz="#5E5E5E", ball="#A6A6A6", text="#D6D6D6", fold=True))
for p in glob.glob(OUT+"retlia-lateral*.svg")+glob.glob(OUT+"retlia-dobra*.svg"):
    svg=open(p).read()
    w,h=re.search(r'viewBox="0 0 (\S+) (\S+)"',svg).groups()
    open(p,"w").write(svg.replace("<svg ",f'<svg width="{w}" height="{h}" ',1))
