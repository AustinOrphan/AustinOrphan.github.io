#!/usr/bin/env python3
"""
The pen trail, from the Illustrator source rather than from the video.

AO.ai page 1 carries a fourth filled object beside the ring, the bar and the A: a white
swash lying under them, invisible on the white artboard.  It is the pen trail.  Its outline
is a band whose two long edges start at the A's right-foot cut and end in a point where the
bar's centre-line begins, so the mark is authored as ONE pen gesture: right leg -> trail ->
bar.  Fitting the trail to the video instead is fitting to a different drawing: the clip's A
is narrower than the source's (registration IoU 0.55 at best), while the swash joins the
source's own A exactly, to 0.00 pt.

This writes design/logo-animation/geometry.json's `trail_from_swash` block:
  outline_d     the swash outline itself, in site path units (y-up, for the same
                <g transform="translate(0,1084) scale(0.1,-0.1)"> group as Logo.astro's path)
  centre_d      its centre-line, the sweep path for a mask stroke
  width_path    the band's width along that centre-line, path units
  marks         fractions of arc length at the gesture's landmarks

Run:  <venv python> design/logo-animation/derive_trail.py
"""
from pathlib import Path
import os
import json, math, re, sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FONT = ROOT.parent / 'font' / 'font'
sys.path.insert(0, str(FONT / 'lib'))
from pen import source_contours                                     # noqa: E402

SRC = json.load(open(FONT / 'source' / 'ai_objects.json'))['AO'][0]
OBJ = {o['role']: o for o in SRC['objects']}
(sw,) = source_contours(OBJ['white']['items'])
(bar,) = source_contours(OBJ['bar']['items'])
pts = [sw.start] + [sg[-1] for sg in sw.segs]
V = [tuple(v) for v in OBJ['A']['vertices']]

# ---- the two long edges, by segment index in the source's own order ------------------
def seg_pts(k, n=160):
    p0 = pts[k]; sg = sw.segs[k]
    if sg[0] == 'l':
        return [tuple(np.array(p0)*(1-t) + np.array(sg[1])*t) for t in np.linspace(0, 1, n)]
    P = [np.array(q) for q in (p0, sg[1], sg[2], sg[3])]
    return [tuple((1-t)**3*P[0] + 3*(1-t)**2*t*P[1] + 3*(1-t)*t*t*P[2] + t**3*P[3])
            for t in np.linspace(0, 1, n)]
def run(ks, rev=False):
    out = []
    for k in (reversed(ks) if rev else ks):
        s = seg_pts(k); out += (s[::-1] if rev else s)
    return np.array(out)

INNER = [6, 7, 8, 9, 10]                 # foot tip -> left end, the loop's inner edge then the run
OUTER = ([0, 1, 2, 3], [12, 13, 14])     # foot cut -> loop outer -> left end (walked backwards)
A_edge = run(INNER)
B_edge = np.vstack([run(OUTER[0], rev=True), run(OUTER[1], rev=True)])

def arclen(P):
    d = np.r_[0.0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    return d / d[-1]
u = np.linspace(0, 1, 900)
Ai = np.c_[np.interp(u, arclen(A_edge), A_edge[:, 0]), np.interp(u, arclen(A_edge), A_edge[:, 1])]
Bi = np.c_[np.interp(u, arclen(B_edge), B_edge[:, 0]), np.interp(u, arclen(B_edge), B_edge[:, 1])]
centre = (Ai + Bi) / 2
width = np.hypot(*(Ai - Bi).T)

# ---- source points -> site path units: the similarity Logo.astro's path was made with ----
S_APEX, S_FOOT = (54.669, 99.415), (81.207, 4.778)      # source apex and right foot tip (pt)
P_APEX, P_FOOT = (5916.0, 10247.0), (8737.0, 194.0)     # the same two in the site path
scale = math.dist(P_APEX, P_FOOT) / math.dist(S_APEX, S_FOOT)
rot = (math.atan2(P_FOOT[1]-P_APEX[1], P_FOOT[0]-P_APEX[0])
       - math.atan2(S_FOOT[1]-S_APEX[1], S_FOOT[0]-S_APEX[0]))
ca, sa = math.cos(rot), math.sin(rot)
def to_path(p):
    x, y = (p[0]-S_APEX[0])*scale, (p[1]-S_APEX[1])*scale
    return (x*ca - y*sa + P_APEX[0], x*sa + y*ca + P_APEX[1])

Cp = np.array([to_path(p) for p in centre])
Wp = width * scale
L = np.r_[0.0, np.cumsum(np.hypot(*np.diff(Cp, axis=0).T))]
frac = L / L[-1]

def thin(P, step, keep=()):
    """Subsample a polyline, ALWAYS keeping its first and last point, plus any index in
    `keep`.  Striding a concatenated band with P[::step] silently drops samples whenever
    the edge's length is not a multiple of the stride.  That first cost the pinned end
    corner and opened a gap on one side of the join; once OVERLAP was added the pinned
    corners became INTERIOR points (the overlap sits after them), so they need naming
    explicitly or the same gap comes back at a different corner."""
    idx = set(range(0, len(P), step)) | {0, len(P) - 1}
    idx |= {i % len(P) for i in keep}
    return P[sorted(idx)]

def poly_d(P, step=6):
    return 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in thin(P, step))
outline_d = ' '.join(c.map(to_path).to_svg() for c in source_contours(OBJ['white']['items']))

# ---- landmarks: where the gesture crosses the A's legs, in fractions of arc length -------
def cross(pa, pb):
    a, b = np.array(to_path(pa)), np.array(to_path(pb))
    n = np.array([-(b-a)[1], (b-a)[0]]); n /= np.linalg.norm(n)
    s = (Cp - a) @ n
    idx = np.nonzero(np.diff(np.sign(s)))[0]
    return [float(frac[i]) for i in idx]
legR = cross(V[4], V[5]); legL = cross(V[0], V[5])
tipR = np.array(to_path(((V[4][0]+V[3][0])/2, (V[4][1]+V[3][1])/2)))
# the bar's centre-line start, from the existing geometry block, is where the pen picks the
# bar up; the outline's leftmost point is the hook's outer extreme and is NOT that join
_g = json.load(open(HERE / 'geometry.json')) if (HERE / 'geometry.json').exists() else {}
_cd = (_g.get('bar') or {}).get('centre_d', '')
_m = re.match(r'\s*M\s*(-?[\d.]+)[ ,]+(-?[\d.]+)', _cd)
hookL = np.array([float(_m.group(1)), float(_m.group(2))]) if _m else np.array(to_path(min(
    [bar.start] + [sg[-1] for sg in bar.segs], key=lambda p: p[0])))
out = dict(
    note='AUTHORITATIVE. The pen trail the component renders. Use centre_joined_d (the sweep path, and '
         'the trail="stroke" line), outline_joined_d (the filled swash) and mask (the reveal path and its '
         'fractions); outline_d / centre_d are the same shape before the join fix, kept for reference. '
         'geometry.json\'s trail_from_video is a superseded earlier pass; nothing derives it.',
    source='AO.ai page 1, the white swash object (15 cubic segments, one closed contour)',
    transform=dict(scale=scale, rotation_deg=math.degrees(rot),
                   anchors=dict(source_apex=S_APEX, path_apex=P_APEX,
                                source_right_foot=S_FOOT, path_right_foot=P_FOOT)),
    outline_d=outline_d,
    centre_d=poly_d(Cp),
    arc_length_path=float(L[-1]),
    width_path=dict(at_foot=float(Wp[0]), max=float(Wp.max()), median=float(np.median(Wp)),
                    at_left_end=float(Wp[-1]),
                    profile=[[round(float(f), 4), round(float(w), 1)] for f, w in zip(frac[::30], Wp[::30])]),
    joins=dict(start_path=[float(Cp[0][0]), float(Cp[0][1])],
               start_offset_from_A_right_foot=float(np.linalg.norm(Cp[0]-tipR)),
               end_path=[float(Cp[-1][0]), float(Cp[-1][1])],
               end_offset_from_bar_centre_start=float(np.linalg.norm(Cp[-1]-hookL))),
    marks=dict(crosses_right_leg=legR, crosses_left_leg=legL),
)
gp = HERE / 'geometry.json'
G = json.load(open(gp)) if gp.exists() else {}
G['trail_from_swash'] = out
json.dump(G, open(gp, 'w'), indent=1)
print(f"  swash -> site path: scale {scale:.4f}, rotation {math.degrees(rot):+.4f} deg")
print(f"  centre-line {L[-1]:.0f} path units, ({Cp[0][0]:.0f},{Cp[0][1]:.0f}) -> ({Cp[-1][0]:.0f},{Cp[-1][1]:.0f})")
print(f"  joins: {out['joins']['start_offset_from_A_right_foot']:.1f} units from the A's right foot,"
      f" {out['joins']['end_offset_from_bar_centre_start']:.1f} from the bar's centre-line start")
print(f"  width {Wp[0]:.0f} at the foot, {Wp.max():.0f} max, {np.median(Wp):.0f} median, {Wp[-1]:.0f} at the left end")
print(f"  crosses the right leg at t={legR}, the left leg at t={legL}")
print(f"  wrote {gp.relative_to(ROOT)} -> trail_from_swash")

# =====================================================================================
# The join at the bar.
#
# The swash's tail end face IS the left hook's return end face: the two objects share
# that edge exactly (bar points 7-8 equal swash points 11-12, to three decimals).  But
# the pen changes direction across it.  The hook's return is travelling at +3.50 deg
# where it stops; the swash leaves at +16.98 deg.  That 13.5 deg kink reads as a notch
# on the lower edge, where the swash's underside meets the hook's outer edge.
#
# DELIBERATE CHANGE, the only edit to the authored swash: over the last BLEND pt of its
# length the centre-line is replaced by a cubic that leaves the face at EXIT_DEG and
# rejoins the authored centre-line with matching position and tangent.  The width is
# ramped smoothly but ENDS AT THE FACE WIDTH: narrowing the tip below 3.35 pt opens a
# visible step against the hook's face, which is worse than the notch it fixes.
#
# EXIT_DEG was chosen by rendering the join at 17 (authored), 12, 8 and 3.5 deg
# (design/logo-animation/join-variants.png).  Aiming all the way at the hook's own
# +3.50 deg, or at 8 deg, over-flattens the tail into a visible S; 12 deg closes most
# of the notch and still leaves the tail reading as one curve.  BLEND = 0 restores the
# authored shape exactly.
# =====================================================================================
# ---- the leftward run is the ring's back half ----------------------------------------
# The crossbar is the front half of a planetary ring (font/SPEC.md section 2.2 fits it:
# an elliptical annulus whose centre ellipse is 48.4 x 8.2 pt, tilted 14 deg).  The pen
# comes round the BACK of that ring, which is why the swash's leftward run lies along it:
# the run touches the ring's centre ellipse at both ends, 0.28 pt out at t=0.60 and
# 0.26 pt at the face.  In between, though, the authored run cuts a chord INSIDE the arc,
# by as much as 3.99 pt at t=0.75, so it reads as a straight stretch that then has to
# bend to meet the bar.
#
# TRIED AND REJECTED: moving the centre-line onto that arc from FOLLOW_FROM to the end
# does give a tangent-continuous handover (the exit comes out at +2.44 deg against the
# hook's +3.50), but the arc runs well above the authored path through the middle of the
# stretch, so the run humps up and back down.  That reads far worse than the straightness
# it was meant to cure.  Kept as a switch, off by default: FOLLOW_FROM = None.
FOLLOW_FROM = None      # 0.58 pulls the run onto the arc; tried and rejected, see below
FOLLOW_LEAD = 0.07

def follow_ring(C, W):
    if FOLLOW_FROM is None: return C, {}
    R = OBJ['bar']['ring']
    O = np.array(R['centre']); ax = np.array(R['axis']); nv = np.array([-ax[1], ax[0]])
    a_m = (R['a_outer'] + R['a_inner']) / 2; b_m = (R['b_outer'] + R['b_inner']) / 2
    back = -R['front_sign']
    th = np.linspace(0, 2*math.pi, 20000)
    E = O + np.outer(np.cos(th), ax*a_m) + np.outer(np.sin(th), nv*b_m)
    E = E[np.sign((E - O) @ nv) == np.sign(back)]                  # the back half only
    L = np.r_[0.0, np.cumsum(np.hypot(*np.diff(C, axis=0).T))]; f = L / L[-1]
    w = np.clip((f - FOLLOW_FROM) / FOLLOW_LEAD, 0, 1); w = 3*w**2 - 2*w**3
    before = []
    Cn = C.copy()
    for i in range(len(C)):
        if w[i] <= 0: continue
        k = int(np.argmin(np.hypot(E[:, 0] - C[i, 0], E[:, 1] - C[i, 1])))
        before.append(float(np.linalg.norm(E[k] - C[i])))
        Cn[i] = C[i] + w[i] * (E[k] - C[i])
    # The arc passes 0.26 pt from the face midpoint.  Pulling the centre-line's last
    # samples onto that midpoint would buy 0.26 pt at the cost of bending the exit by
    # about 6 deg, so it is left on the arc; PIN below puts the BAND's corners on the
    # face exactly, which is what the join actually needs.
    return Cn, dict(follow_from=FOLLOW_FROM, lead=FOLLOW_LEAD,
                    max_pull_pt=float(max(before)) if before else 0.0,
                    samples_moved=len(before))

centre, ring_note = follow_ring(centre, width)

# With the run on the ring's arc the exit direction comes from the ring itself, so the
# artificial re-aim is off.  Set BLEND > 0 to force a different exit angle instead.
# ---- the approach to the hook -------------------------------------------------------
# Measured along the run, the authored path curves steadily at a radius of 40-90 pt until
# about 80% of the way, then goes flat: roughly 800 pt for the last third, right where it
# has to meet the bar.  That tenfold change of curvature inside one stroke is what read as
# "too straight for a period".
#
# DELIBERATE CHANGE: from ANCHOR onward the centre-line is replaced by a single curve that
# leaves the anchor with the path's own position, tangent AND curvature, and arrives at the
# hook's face along the direction the hook's return is travelling.  Because it matches
# curvature at the anchor there is no joint anywhere, and because it matches the hook's
# tangent the pen curves back into the ring instead of stabbing at it.  A quintic Hermite
# is the lowest order that can carry all five conditions.
#
# ANCHOR is the only choice: it sets how much of the run is rebuilt and what curvature the
# new stretch inherits.  Anchors from 0.82 down to 0.41 were rendered as a uniform line
# (design/logo-animation/, the cont_* sheets); 0.50 was chosen.  ANCHOR = None restores the
# authored path.  Tried and set aside on the way: a single arc, which cannot satisfy both
# ends and arrived 20.8 deg off the hook, and a biarc, tangent at both ends but with a
# curvature jump at its joint.
ANCHOR = 0.50

def _hook_arrival_dir():
    """The direction the pen should be travelling as it reaches the hook's face: the
    reverse of the hook's own return, which is the mean of its outer edge arriving at the
    face and its inner edge leaving it."""
    bpx = [bar.start] + [sg[-1] for sg in bar.segs]
    def dir_end(k):
        sg = bar.segs[k]; v = np.array(sg[-1]) - np.array(sg[2] if sg[0] == 'c' else bpx[k]); return v/np.linalg.norm(v)
    def dir_start(k):
        sg = bar.segs[k]; v = np.array(sg[1] if sg[0] == 'c' else sg[-1]) - np.array(bpx[k]); return v/np.linalg.norm(v)
    d = dir_end(6) - dir_start(8)
    return -d/np.linalg.norm(d)

def _curvature(C, i, k=30):
    a, b, c = C[max(0, i-k)], C[i], C[min(len(C)-1, i+k)]
    A = np.linalg.norm(b-a); B = np.linalg.norm(c-b); D = np.linalg.norm(c-a)
    cr = (b-a)[0]*(c-a)[1] - (b-a)[1]*(c-a)[0]
    return 2*cr/(A*B*D) if A*B*D > 0 else 0.0

def continue_to_hook(C, W):
    if ANCHOR is None:
        return C, W, dict(anchor=None, note='authored path, unmodified')
    L = np.r_[0.0, np.cumsum(np.hypot(*np.diff(C, axis=0).T))]; f = L/L[-1]
    i0 = int(np.searchsorted(f, ANCHOR))
    P0 = C[i0]; T0 = C[i0] - C[i0-25]; T0 /= np.linalg.norm(T0)
    k0 = _curvature(C, i0); T1 = _hook_arrival_dir(); P1 = C[-1]
    d = np.linalg.norm(P1 - P0)
    m0, m1 = T0*d, T1*d
    a0 = k0 * d * d * np.array([-T0[1], T0[0]])          # second derivative giving curvature k0
    u = np.linspace(0, 1, 700)[:, None]
    h0 = 1 - 10*u**3 + 15*u**4 - 6*u**5; h1 = u - 6*u**3 + 8*u**4 - 3*u**5
    h2 = 0.5*u**2 - 1.5*u**3 + 1.5*u**4 - 0.5*u**5
    h3 = 10*u**3 - 15*u**4 + 6*u**5;    h4 = -4*u**3 + 7*u**4 - 3*u**5
    B = h0*P0 + h1*m0 + h2*a0 + h3*P1 + h4*m1
    dd = np.r_[0.0, np.cumsum(np.hypot(*np.diff(B, axis=0).T))]; dd /= dd[-1]
    n = len(C) - i0; uu = np.linspace(0, 1, n)
    Cn = C.copy(); Cn[i0:] = np.c_[np.interp(uu, dd, B[:, 0]), np.interp(uu, dd, B[:, 1])]
    tan = Cn[-1] - Cn[-4]; tan /= np.linalg.norm(tan)
    ang_of = lambda v: math.degrees(math.atan2(v[1], v[0]))
    return Cn, W, dict(anchor=ANCHOR, inherited_radius_pt=float(1/abs(k0)),
                       rebuilt_fraction=float(1 - ANCHOR),
                       arrival_deg=float(ang_of(tan)), hook_deg=float(ang_of(T1)),
                       note="curvature-continuous approach; no joint, arrives tangent to the hook")

centre_j, width_j, join_note = continue_to_hook(centre, width)

# ---- the width along the trail -------------------------------------------------------
# The authored swash is heavy through the loop (12.3 pt) and thin at the hook (2.8), which
# is more contrast than the trail wants when it is only on screen for half a second and
# has to sit under the bar without competing with it.
#
# Decompose rather than interpolate: a straight taper from the pen's landing weight to the
# hook, plus the authored profile's departure from that taper, which IS the loop's swell.
# BULGE scales the swell (0 = a plain taper, 1 = the authored swash) and LEVEL scales the
# whole thing.  Both ends are held at the authored widths over HOLD of the length, so the
# foot and hook joins are unaffected by either knob.
BULGE, LEVEL = 0.40, 0.90

def shape_width(C, W):
    """taper + BULGE * (the authored profile's SWELL above that taper), all times LEVEL.

    Two things the obvious version got wrong, both visible as a nip just before the hook:

    1. The authored swash PINCHES below its own taper near the hook (2.55 pt against 3.35
       at the face).  Scaling that alongside the swell narrowed the trail and then made it
       climb back, so only the swell is carried over.
    2. The trail MUST be the hook's own width, 355.6, where they meet, or the join stops
       being smooth.  Forcing that with an end-ramp reintroduced the pinch, because the
       ramp blended back toward the authored profile.  Instead the taper is built to
       W/LEVEL at both ends, so that after LEVEL it lands exactly on the authored end
       widths and needs no correction at all.  The approach is then monotone.
    """
    taper = np.linspace(W[0]/LEVEL, W[-1]/LEVEL, len(C))
    swell = np.maximum(W - taper*LEVEL, 0.0)              # the loop's swell, never the pinch
    return (taper + BULGE*swell/LEVEL) * LEVEL

width_j = shape_width(centre_j, width_j)
Cpj = np.array([to_path(p) for p in centre_j]); Wpj = width_j * scale
d = np.gradient(Cpj, axis=0); d /= np.hypot(d[:, 0], d[:, 1])[:, None]
nrm = np.c_[-d[:, 1], d[:, 0]]
left = Cpj + nrm*(Wpj[:, None]/2); right = Cpj - nrm*(Wpj[:, None]/2)

# ---- pin the tail's end cross-section back onto the hook's face -----------------------
# Re-aiming the centre-line turns the end cross-section with it, so the band's last edge
# stops coinciding with the hook's face; the same happens at the head, and worse, because
# the A's right-foot cut crosses the pen 31.5 deg off its normal.
#
# What a pen actually does at an obliquely cut end is simple: the two offset curves run
# undisturbed right up to the cut, and the cut chops them off.  So that is what happens
# here -- the band is extended past each face and TRIMMED on it.  Nothing is blended, so
# the edges keep the shape the width profile gives them all the way to the corner.
#
# Two earlier versions blended instead and both left a visible defect.  Displacing each
# edge by its own vector is a shear: it dragged the centre-line 180 units sideways at the
# foot and put a spike on the A's foot vertex.  Rotating the cross-section into the face
# over 12 pt is symmetric and fixed the spike, but smearing the rotation into the body
# gave the inner edge an S-kink and an elbow that the authored swash does not have.
#
# The trim needs one correction to land on the artwork's own corners.  width_path was
# measured ACROSS THE OUTLINE, so at an obliquely cut end it reports the chord, not the
# perpendicular width; used as a perpendicular width it makes the band 1/cos(31.5) = 17%
# too fat at the foot, and the cut then overshoots the A's corners by 57 units a side.
# Scaling the width by that cosine, ramped out over PIN pt, is symmetric -- both edges
# move together, so it cannot kink -- and it puts the corners on the vertices exactly.
PIN = 12.0
OVERLAP = 60.0                                   # path units (about 0.56 pt) buried past each face
Lp = np.r_[0.0, np.cumsum(np.hypot(*np.diff(Cpj, axis=0).T))]

def order_face(a, b, p):
    """Return the face's two corners with the one nearest `p` (a point on the left edge) first."""
    return (a, b) if np.linalg.norm(a - p) <= np.linalg.norm(b - p) else (b, a)

def fit_end_width(left, right, a, b, ramp):
    """Scale the band's width near one end so its CHORD on the face is exactly |a-b|."""
    i = 0 if ramp[0] > ramp[-1] else -1
    off = (left - right) / 2
    h = np.linalg.norm(off[i])
    cos = abs(float(np.dot(off[i]/h, (b - a)/np.linalg.norm(b - a))))
    k = np.linalg.norm(b - a) * cos / (2*h)
    w = (3*ramp**2 - 2*ramp**3)[:, None]
    off = off * (1 + w*(k - 1))
    mid = (left + right) / 2                     # == Cpj; the width change is symmetric
    return mid + off, mid - off, float(k), float(math.degrees(math.acos(cos)))

def trim(P, a, b, at_start, pad=600.0):
    """Extend one end of an edge past the line a--b and cut it there."""
    m = np.array([-(b - a)[1], (b - a)[0]]); m /= np.linalg.norm(m)
    keep = np.sign(float((P[len(P)//2] - a) @ m))
    d = _u(P[0] - P[1]) if at_start else _u(P[-1] - P[-2])
    P = np.vstack([P[0] + d*pad, P]) if at_start else np.vstack([P, P[-1] + d*pad])
    f = (P - a) @ m
    on = np.where(np.sign(f) == keep)[0]
    if at_start:
        k = on[0]; t = f[k-1] / (f[k-1] - f[k])
        return np.vstack([P[k-1] + t*(P[k] - P[k-1]), P[k:]])
    k = on[-1]; t = f[k] / (f[k] - f[k+1])
    return np.vstack([P[:k+1], P[k] + t*(P[k+1] - P[k])])

def _u(v): return v / np.linalg.norm(v)

bar_pts_ = [bar.start] + [sg[-1] for sg in bar.segs]
face = list(order_face(np.array(to_path(bar_pts_[7])), np.array(to_path(bar_pts_[8])), left[-1]))
foot = list(order_face(np.array(to_path(V[3])), np.array(to_path(V[4])), left[0]))   # rcut, rtip

gap_before = (float(np.linalg.norm(face[0] - left[-1])), float(np.linalg.norm(face[1] - right[-1])))
start_gap_before = (float(np.linalg.norm(foot[0] - left[0])), float(np.linalg.norm(foot[1] - right[0])))

left, right, k_end, ang_end = fit_end_width(
    left, right, *face, np.clip((Lp - (Lp[-1] - PIN*scale)) / (PIN*scale), 0, 1))
k_foot = ang_foot = float('nan')

# The HEAD gets none of that, because the foot cut is not an end cap: it lies only 22.3 deg
# off the pen's own direction, so it runs nearly ALONG the trail rather than across it.
# width_path's first samples are the chord of that near-tangential cut, which is not a pen
# width at all, and no width the band could have would make a perpendicular cross-section
# reach both of the A's foot vertices.  The authored outline already solves that end -- it
# starts on rcut and rtip to 0.1 units -- so the band is simply blended back onto the
# AUTHORED EDGES over the first HOLD_FOOT of its length.  The foot is then the artwork,
# exactly, and BULGE and LEVEL shape only the body.
HOLD_FOOT = (0.05, 0.32)                         # hold fully to the first, released by the second
Aip = np.array([to_path(p) for p in Ai]); Bip = np.array([to_path(p) for p in Bi])
if np.linalg.norm(Aip[0] - left[0]) > np.linalg.norm(Bip[0] - left[0]):
    Aip, Bip = Bip, Aip                          # Aip is the left edge
_h0, _h1 = (float(x) for x in os.environ.get('HOLD', '').split(',')) if os.environ.get('HOLD') else HOLD_FOOT
_h = np.clip((np.linspace(0, 1, len(left)) - _h0) / (_h1 - _h0), 0, 1)[:, None]
_h = 3*_h**2 - 2*_h**3
left = _h*left + (1 - _h)*Aip[:len(left)]
right = _h*right + (1 - _h)*Bip[:len(right)]
left0, right0 = left, right                      # the band before the cut, for the width report

left = trim(left, *face, at_start=False)
right = trim(right, *face, at_start=False)

gap_after = (float(np.linalg.norm(face[0] - left[-1])), float(np.linalg.norm(face[1] - right[-1])))
start_gap_after = (float(np.linalg.norm(foot[0] - left[0])), float(np.linalg.norm(foot[1] - right[0])))
print(f"  head: authored edges held to {100*_h0:.0f}% and released by {100*_h1:.0f}% of the trail;"
      f"  tail: cut straight on the hook's face, {ang_end:.1f} deg off the cross-section (width x{k_end:.3f})")

def inside(pt, P):
    """Even-odd point-in-polygon, for checking an overlap lands inside the shape it hides in."""
    x, y = pt; c = False; j = len(P) - 1
    for i in range(len(P)):
        if ((P[i][1] > y) != (P[j][1] > y)) and \
           (x < (P[j][0]-P[i][0])*(y-P[i][1])/(P[j][1]-P[i][1]) + P[i][0]): c = not c
        j = i
    return c

# ---- overlap the A and the hook so the fills do not merely abut ----------------------
# With the corners pinned the two shapes share the face exactly, but abutting fills are
# antialiased independently and a hairline of background shows along the seam.  Extending
# the tail a little way PAST the face, along the direction the hook's return was
# travelling, puts the overlap inside the hook's own body where it cannot be seen, and the
# seam goes away.  OVERLAP = 0 restores the exact butt joint.
if OVERLAP > 0:
    # _hook_arrival_dir() points the way the pen ARRIVES, i.e. into the hook's body, which
    # is exactly the way the overlap must go.
    ext = _hook_arrival_dir()
    ext = np.array([ext[0]*ca - ext[1]*sa, ext[0]*sa + ext[1]*ca]); ext /= np.linalg.norm(ext)
    left = np.vstack([left, left[-1] + ext*OVERLAP])
    right = np.vstack([right, right[-1] + ext*OVERLAP])
    barPoly = np.array([to_path(q) for q in bar.flatten(0.05)])
    covered = [inside(left[-1], barPoly), inside(right[-1], barPoly),
               inside((left[-1]+right[-1])/2, barPoly)]
    if not all(covered):
        raise SystemExit(f"  overlap of {OVERLAP:.0f} units is not hidden inside the hook: {covered}; "
                         "reduce OVERLAP or check the direction")
    # The same at the head, into the A's foot.  Each corner slides back along ITS OWN leg
    # edge (the corner is a vertex of that edge, so the extension stays on the A's outline
    # rather than crossing it, which sliding both along the leg's axis would do).
    aPoly = np.array([to_path(V[k]) for k in (0, 1, 2, 3, 4, 5)])
    apex = np.array(to_path(V[5]))
    up = lambda c: (apex - c) / np.linalg.norm(apex - c)
    left = np.vstack([left[0] + up(left[0])*OVERLAP, left])
    right = np.vstack([right[0] + up(right[0])*OVERLAP, right])
    mid0 = (left[0] + right[0]) / 2
    covered = [inside(left[0] + 0.02*(mid0 - left[0]), aPoly),
               inside(right[0] + 0.02*(mid0 - right[0]), aPoly), inside(mid0, aPoly)]
    if not all(covered):
        raise SystemExit(f"  overlap of {OVERLAP:.0f} units is not hidden inside the A's foot: {covered}; "
                         "reduce OVERLAP or check the direction")
    print(f"  overlap {OVERLAP:.0f} units into the hook and into the A's foot, hidden inside both")

# The pinned corners are the ones that must land exactly on the A's foot cut and the
# hook's face.  The overlap prepends one point at the head and appends one at the tail,
# so after it they sit one in from each end.
PINNED_L = [1, len(left) - 2] if OVERLAP > 0 else [0, len(left) - 1]
PINNED_R = [1, len(right) - 2] if OVERLAP > 0 else [0, len(right) - 1]

# ---- the reveal sweep's own path: the centre-line with a lead-in and a lead-out --------
# The trail is inked by sweeping a stroke along the centre-line inside a <mask>.  With ROUND
# caps that sweep runs half a stroke width (680 units, 5.5 % of the trail) AHEAD of the dash
# position at the head and the same distance BEHIND it at the tail: every landmark fires
# early, and 5.8 % of the trail pops in on the frame the layer switches on.  BUTT caps put
# the ink boundary exactly at the dash position - but then the boundary at each END of the
# path is a perpendicular cut too, and neither of the swash's end faces is perpendicular
# (the foot cut crosses the pen at 68 deg, and both ends carry the OVERLAP above).  So the
# sweep runs along the centre-line EXTENDED past both ends, far enough that the
# perpendicular at each extension's tip clears the whole face; with butt caps the head and
# the tail then sit exactly where the dash says they do, and the component's easing stops
# are the trail's own landmark fractions, mapped onto the extended path by `mask`.
def _unit(v): return v / np.linalg.norm(v)
def _polyline_dist(P, A):
    """Distance from each point of P to the polyline A (segments, not just vertices)."""
    d = A[1:] - A[:-1]; L2 = (d * d).sum(1)
    t = np.clip(((P[:, None, :] - A[None, :-1, :]) * d[None]).sum(-1) / L2[None], 0, 1)
    return np.sqrt(((P[:, None, :] - (A[None, :-1, :] + t[..., None] * d[None])) ** 2).sum(-1)).min(1)

band = np.vstack([left, right])
nearest = np.array([int(np.argmin(((Cpj - q) ** 2).sum(1))) for q in band])
T0 = _unit(Cpj[1] - Cpj[0]); T1 = _unit(Cpj[-1] - Cpj[-2])
LEAD_MARGIN = 1.5                                # of what the end faces actually need
lead_in = float(math.ceil(max(0.0, -((band[nearest < 5] - Cpj[0]) @ T0).min()) * LEAD_MARGIN / 50) * 50)
lead_out = float(math.ceil(max(((band[nearest > len(Cpj) - 6] - Cpj[-1]) @ T1).max() * LEAD_MARGIN, 100) / 50) * 50)
mask_pts = np.vstack([Cpj[0] - T0 * lead_in, Cpj, Cpj[-1] + T1 * lead_out])
mask_stroke = float(math.ceil(2 * _polyline_dist(band, mask_pts).max() * 1.04 / 10) * 10)

# an extension must not sweep over some LATER part of the swash and ink it early
for _name, _P0, _T, _lead, _own in (('lead-in', Cpj[0], -T0, lead_in, nearest < 5),
                                    ('lead-out', Cpj[-1], T1, lead_out, nearest > len(Cpj) - 6)):
    _rel = band - _P0
    _hit = (_rel @ _T > 0) & (_rel @ _T <= _lead) & (np.abs(_rel @ np.array([-_T[1], _T[0]])) <= mask_stroke / 2)
    if (_hit & ~_own).any():
        raise SystemExit(f"  the {_name} of {_lead:.0f} units sweeps over {(_hit & ~_own).sum()} outline points "
                         "belonging elsewhere on the trail; shorten it or narrow the mask stroke")

_Lc = float(np.hypot(*np.diff(Cpj, axis=0).T).sum()); _tot = lead_in + _Lc + lead_out
mask = dict(lead_in_path=lead_in, lead_out_path=lead_out,
            lead_in_point=[round(float(v), 1) for v in (Cpj[0] - T0 * lead_in)],
            lead_out_point=[round(float(v), 1) for v in (Cpj[-1] + T1 * lead_out)],
            length_path=_tot, stroke_path=mask_stroke,
            start_fraction=lead_in / _tot, span_fraction=_Lc / _tot, end_fraction=(lead_in + _Lc) / _tot,
            note='sweep path for the reveal mask: prepend lead_in_point and append lead_out_point to '
                 'centre_joined_d, stroke it stroke_path wide with BUTT caps, and dash it with '
                 'pathLength="1". A point at fraction f of the trail is at start_fraction + '
                 'span_fraction * f of this path, which is what the component eases the head and the '
                 'tail through; butt caps mean the ink boundary is exactly there.')
print(f"  mask sweep: lead-in {lead_in:.0f}, lead-out {lead_out:.0f} units, stroke {mask_stroke:.0f};"
      f" the trail occupies [{mask['start_fraction']:.4f}, {mask['end_fraction']:.4f}] of it")

# ---- diagnostic: the width the band ACTUALLY has, after the pins and the overlap ------
_L = np.r_[0.0, np.cumsum(np.hypot(*np.diff(Cpj, axis=0).T))]; _f = _L/_L[-1]
_lo, _ro = left0, right0
_true = np.hypot(*(np.array(_lo) - np.array(_ro)).T)
_want = Wpj
print("  width along the last quarter: intended vs what the band actually has")
for _fr in (0.75, 0.80, 0.85, 0.90, 0.94, 0.97, 0.99, 1.00):
    _k = min(int(_fr*(len(_true)-1)), len(_true)-1)
    _kw = min(int(_fr*(len(_want)-1)), len(_want)-1)
    print(f"    t={_fr:.2f}  intended {_want[_kw]:6.1f}   actual {_true[_k]:6.1f}   {_true[_k]-_want[_kw]:+6.1f}")
print(f"    narrowest anywhere in the last quarter: {_true[int(0.75*len(_true)):].min():.1f} units")

G = json.load(open(gp))
G['trail_from_swash'].update(
    join=dict(**join_note, **ring_note, pin_pt=PIN, hold_foot=[_h0, _h1],
              end_gap_before_cut=gap_before, end_gap_after_cut=gap_after,
              start_gap_before_hold=start_gap_before, start_gap_after_hold=start_gap_after,
              overlap_path=OVERLAP, face_path=[face[0].tolist(), face[1].tolist()],
              foot_cut_path=[foot[0].tolist(), foot[1].tolist()]),
    centre_joined_d=poly_d(Cpj),
    outline_joined_d='M' + ' L'.join(
        f'{x:.1f} {y:.1f}' for x, y in np.vstack([
            thin(left, 4, keep=PINNED_L), thin(right[::-1], 4, keep=[len(right)-1-i for i in PINNED_R])])) + ' Z',
    width_joined_path=dict(at_foot=float(Wpj[0]), max=float(Wpj.max()), at_left_end=float(Wpj[-1])),
    mask=mask)
json.dump(G, open(gp, 'w'), indent=1)
print(f"\n  approach: curvature-continuous from t={join_note['anchor']}, inheriting radius "
      f"{join_note['inherited_radius_pt']:.0f} pt and rebuilding the last "
      f"{100*join_note['rebuilt_fraction']:.0f}% of the trail; arrives {join_note['arrival_deg']:+.2f} deg "
      f"against the hook's {join_note['hook_deg']:+.2f}")
print(f"  width: bulge {BULGE:.2f} at level {LEVEL:.2f} (swell only); foot {Wpj[0]:.0f}, loop {Wpj[int(0.22*len(Wpj))]:.0f}, "
      f"mid {Wpj[int(0.7*len(Wpj))]:.0f}, hook {Wpj[-1]:.0f} path units")
print(f"  tail cut on the hook's face (width corrected over the last {PIN:.0f} pt):"
      f" corners {gap_before[0]:.1f}/{gap_before[1]:.1f} -> {gap_after[0]:.3f}/{gap_after[1]:.3f} units from its vertices")
print(f"  head held on the authored edges to {100*_h0:.0f}%, released by {100*_h1:.0f}%:"
      f" corners {start_gap_before[0]:.1f}/{start_gap_before[1]:.1f}"
      f" -> {start_gap_after[0]:.3f}/{start_gap_after[1]:.3f} units from the A's foot vertices")
print( "  wrote trail_from_swash.centre_joined_d / outline_joined_d  (use these, not the raw outline_d)")
