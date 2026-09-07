"""The five readings of R4b's chord rule, built side by side.  SPEC R4b, "how literally to
take the ring", is the write-up; this is what produced it and what will rebuild it.

    A  capped rise (SHIPPED)      tilt falls with span, 19.87 deg -> 9.34 at an H
    B  the ring's own angle       constant 19.87 deg, rise scales with span
    C  B + the ring's profile     R4's arch, but the width swells x1.265 at an H's midspan
    D  the annulus, normalised    both edges off the two ellipses, midspan scaled to R4
    E  the annulus, verbatim      the same, at the mark's own weight (50 units at midspan)

D and E are the literal ones: the chord is a real piece of the ring's annulus, put into font
space by build_A's OWN transform (rotate off the 5.63 deg lean, scale 7.888 units/pt), then
translated so the ring's centre sits on the chord's centre.  That placement is the rule and not
a fit -- under B..E a chord IS the piece of ring its span exposes, so the two centres coincide
by definition.  The transform is verified point-for-point against the built A's bar below.

    python3 measure/ring_readings.py          # numbers, and /tmp/ring_readings.json

Run from the font/ directory.
"""

import sys, os, math, json
HERE=os.path.dirname(os.path.abspath(__file__)); FONT=os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FONT,'lib')); sys.path.insert(0, FONT); os.chdir(FONT)
import ring, rules, glyphs.core as core, glyphs.set_straight as SS, glyphs.set_round as SR
from pen import (Contour, add, sub, mul, unit, perp, norm, ang, rot, from_ang, fit_cubics,
                 clip_half, source_contours, from_poly)
from rules import glyph, stem, w_stem, w_horizontal
from metrics import CAP, OVER_POINT, SB_STRAIGHT, SB_ROUND

OBJ=core.OBJ
tipL,cutL,cApex,cutR,tipR,apex=[tuple(x) for x in OBJ['A']['vertices']]
_b=unit(add(unit(sub(apex,tipL)),unit(sub(apex,tipR)))); _lean=ang(_b)-90.0
_xp=lambda p: add(rot(sub(p,apex),-_lean),apex)
_yf=(_xp(tipL)[1]+_xp(tipR)[1])/2
_s=(CAP+OVER_POINT)/(apex[1]-_yf)
T=lambda p:(lambda q:((q[0]-apex[0])*_s,(q[1]-_yf)*_s))(_xp(p))

RG=OBJ['bar']['ring']; RCs=tuple(RG['centre']); tl=math.radians(RG['tilt_deg'])
ao,bo,ai,bi=RG['a_outer'],RG['b_outer'],RG['a_inner'],RG['b_inner']
ct,st=math.cos(tl),math.sin(tl)
def EL(a,b,th):
    x,y=a*math.cos(th),b*math.sin(th)
    return (RCs[0]+x*ct-y*st, RCs[1]+x*st+y*ct)
def th_at(a,b,x):
    lo,hi=math.radians(8),math.radians(172)
    for _ in range(70):
        m=(lo+hi)/2
        if EL(a,b,m)[0]>x: lo=m
        else: hi=m
    return (lo+hi)/2
RC=T(RCs)
S=_s

def annulus(x0, x1, y_mid, norm_mode, mid, sign=1.0, end0=None, end1=None, N=110, ext=90.0):
    """The band, straight off the two ellipses.  norm_mode: 'mid' scales the band so its
    midspan equals R4's nominal there; 'raw' leaves the mark's own weight."""
    L=x1-x0
    # the piece of ring this span exposes, centred on the ring, in SOURCE pt
    half=(L/2+ext)/S
    # the inner ellipse is the narrower of the two; never sample past where it exists
    lim=ai-1e-3
    x_lo=max(RCs[0]-half, min(EL(ai,bi,th)[0] for th in [math.radians(8+164*i/400) for i in range(401)])+0.02)
    x_hi=min(RCs[0]+half, max(EL(ai,bi,th)[0] for th in [math.radians(8+164*i/400) for i in range(401)])-0.02)
    xs=[x_lo+(x_hi-x_lo)*i/N for i in range(N+1)]
    up=[T(EL(ao,bo,th_at(ao,bo,x))) for x in xs]
    lo=[T(EL(ai,bi,th_at(ai,bi,x))) for x in xs]
    cen=[mul(add(u,l),0.5) for u,l in zip(up,lo)]
    # weight normalisation, about the centre line
    if norm_mode=='mid':
        j=N//2
        k=w_horizontal(L,0.5,mid)/norm(sub(up[j],lo[j]))
    else:
        k=1.0
    up=[add(c,mul(sub(u,c),k)) for c,u in zip(cen,up)]
    lo=[add(c,mul(sub(l,c),k)) for c,l in zip(cen,lo)]
    # place: ring centre -> (chord midpoint, y_mid)
    dx,dy=(x0+x1)/2-RC[0], y_mid-RC[1]
    mv=lambda p:(p[0]+dx,p[1]+dy)
    up=[mv(p) for p in up]; lo=[mv(p) for p in lo]
    if sign<0:
        M=lambda p:(p[0], 2*y_mid-p[1])
        up,lo=[M(p) for p in lo],[M(p) for p in up]
    tg=lambda P:[unit(sub(P[min(i+1,len(P)-1)],P[max(i-1,0)])) for i in range(len(P))]
    su,_=fit_cubics(up,tg(up),tol=0.04); sl,_=fit_cubics(lo[::-1],tg(lo[::-1]),tol=0.04)
    k2=Contour(up[0])
    for sg in su: k2.curve_to(*sg)
    k2.line_to(lo[-1])
    for sg in sl: k2.curve_to(*sg)
    k2=k2.ccw()
    inside=((x0+x1)/2, y_mid)
    for e in (end0,end1):
        if e is not None: k2=clip_half(k2,e[0],e[1],inside)
    return k2

_SHIPPED_TILT = ring.tilt_for

def H(kind):
    xl=SS._stem_x(); xr=SS.BODY_MEDIUM-w_stem(0)/2
    # A alone keeps the shipped capped-rise tilt; B..E take the ring's own constant angle.
    ring.tilt_for = _SHIPPED_TILT if kind=='A' else (lambda length: core.RING_TILT)
    b0=ring.solve_span(xl,'left',xr+200,ring.MID_LINE)
    b1=ring.solve_span(xr,'right',b0,ring.MID_LINE)
    b0=ring.solve_span(xl,'left',b1,ring.MID_LINE)
    e0,e1=ring.stem_edge_line(xl,'left'),ring.stem_edge_line(xr,'right')
    if kind in ('A','B','C'):
        bar,_=ring.ring_chord(b0,b1,ring.MID_LINE,mid=rules.HORIZ_FREE,end0=e0,end1=e1)
    else:
        bar=annulus(b0,b1,ring.MID_LINE,kind,rules.HORIZ_FREE,1.0,e0,e1)
    g=glyph(ord('H'),[stem(xl,0,CAP,bottom='right',top='right'),
                      stem(xr,0,CAP,bottom='left',top='left'),bar],sb=(SB_STRAIGHT,SB_STRAIGHT))
    return g, b1-b0

out={}
_ow=rules.w_horizontal
d=json.load(open('source/ai_objects.json'))
# C, as before
RGx=[o for o in d['AO'][0]['objects'] if o['role']=='bar'][0]['ring']
LOS=[EL(ai,bi,math.radians(8)+math.radians(164)*i/2000) for i in range(2001)]
def rband(x):
    p=EL(ao,bo,th_at(ao,bo,x)); return min(math.hypot(p[0]-q[0],p[1]-q[1]) for q in LOS)
def profile(L,n=41):
    Lp=L/S; xs=[RCs[0]-Lp/2+Lp*i/(n-1) for i in range(n)]
    w=[rband(x) for x in xs]; lin=[w[0]+(w[-1]-w[0])*i/(n-1) for i in range(n)]
    return [a/b for a,b in zip(w,lin)]
# A and B: R4's plain widths, no profile
for _k in ('A','B'):
    g,L=H(_k); out[_k]=dict(adv=g['adv'],c=[x.to_json() for x in g['contours']])
    print(_k,'adv',g['adv'],' tilt %.2f deg'%ring.tilt_for(L))

P=profile(551.6)
def wh(length,t,mid=None):
    u=min(max(t,0.0),1.0)*(len(P)-1); i=int(u); f=u-i
    k=P[i] if i>=len(P)-1 else P[i]*(1-f)+P[i+1]*f
    return _ow(length,t,mid)*k
rules.w_horizontal=wh; ring.w_horizontal=wh
g,L=H('C'); out['C']=dict(adv=g['adv'],c=[x.to_json() for x in g['contours']])
rules.w_horizontal=_ow; ring.w_horizontal=_ow
for kind,lbl in (('mid','D'),('raw','E')):
    g,L=H(kind); out[lbl]=dict(adv=g['adv'],c=[x.to_json() for x in g['contours']])
    print(lbl,'adv',g['adv'])
# measure the bands
for lbl,kind in (('D','mid'),('E','raw')):
    xs=[RCs[0]-(551.6/2)/S + (551.6/S)*i/8 for i in range(9)]
    w=[rband(x)*S for x in xs]
    if kind=='mid': k=w_horizontal(551.6,0.5,rules.HORIZ_FREE)/w[4]; w=[v*k for v in w]
    print(' ',lbl,'band across the H bar:', ' '.join('%.1f'%v for v in w))
out['_mark']=[c.to_json() for c in [c.map(T) for role in ('white','ring','bar') for c in source_contours(OBJ[role]['items'])] + [from_poly([T(tuple(v)) for v in OBJ['A']['vertices']])]]
out['_rc']=RC
json.dump(out,open('/tmp/ring_readings.json','w'))
