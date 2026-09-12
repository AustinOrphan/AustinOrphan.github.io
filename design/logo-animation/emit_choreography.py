#!/usr/bin/env python3
"""src/components/logo-choreography.ts -- when every piece of the write-on happens.

The timeline used to be eight delays and eight durations, each chosen by eye against the
clip.  It is now three authored numbers and one rule:

    the pen goes faster where the stroke it is laying is thicker,   v = k * width**P

Everything else is measured.  Each piece's duration is its own arc length divided by that
speed, so the boundaries fall out rather than being set; and because consecutive pieces
SHARE their end face -- the two legs share the A's apex face, the right leg and the trail
share the foot cut, the trail and the crossbar share the hoop's left hook face -- the speed
is continuous across every join with nothing to tune.  The face's own length is the one
width the two pieces agree on, so it is written into both ends.

The three authored numbers are PEN_START, PEN_END and RING_CLOSE.  P is the fourth dial and
1.0 is the natural reading of the rule.

Run:  <venv python> design/logo-animation/emit_choreography.py
"""
from pathlib import Path
import json
import math
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'font' / 'measure'))
import swash_derived as sd                                          # noqa: E402

GEOM = json.load(open(HERE / 'geometry.json'))
OBJ = {o['role']: o for o in json.load(open(HERE / 'ai_objects_derived.json'))['AO'][0]['objects']}
OUT = ROOT / 'src' / 'components' / 'logo-choreography.ts'

PEN_START = 0.240           # the pen touches down
PEN_END = 1.030             # the last stroke lands
RING_CLOSE = 1.090          # the ring shuts its own gap, alone, after everything else
P = 1.0                     # v proportional to width ** P

TRF = GEOM['transform']
SCALE = TRF['scale']
AFF = SCALE * np.exp(1j * math.radians(TRF['rotation_deg']))
OFF = complex(TRF['translate']['x'], TRF['translate']['y'])
V = {k: complex(v['x'], v['y']) for k, v in GEOM['A']['vertices'].items()}
RO, RI = GEOM['ring']['outer'], GEOM['ring']['inner']
CO, CI = complex(RO['cx'], RO['cy']), complex(RI['cx'], RI['cy'])
CC = (CO + CI) / 2
TH0 = math.atan2((V['apex'] - CC).imag, (V['apex'] - CC).real)


def flatten(d, n=140):
    """An SVG path of M/L/C into a dense polyline."""
    import re
    toks = re.findall(r'[MLCZz]|-?\d+\.?\d*', d)
    i, cur, out, cmd = 0, None, [], None
    while i < len(toks):
        if toks[i] in 'MLCZz':
            cmd = toks[i]; i += 1
            if cmd in 'Zz':
                continue
        nums = []
        while i < len(toks) and toks[i] not in 'MLCZz':
            nums.append(float(toks[i])); i += 1
        if cmd == 'M':
            cur = complex(nums[0], nums[1]); out.append(cur)
        elif cmd == 'L':
            for k in range(0, len(nums), 2):
                p = complex(nums[k], nums[k + 1])
                out += [cur + (p - cur) * (j / (n - 1.)) for j in range(1, n)]
                cur = p
        elif cmd == 'C':
            for k in range(0, len(nums), 6):
                Pp = [cur, complex(nums[k], nums[k + 1]), complex(nums[k + 2], nums[k + 3]),
                      complex(nums[k + 4], nums[k + 5])]
                for j in range(1, n):
                    t = j / (n - 1.)
                    out.append((1 - t) ** 3 * Pp[0] + 3 * (1 - t) ** 2 * t * Pp[1]
                               + 3 * (1 - t) * t * t * Pp[2] + t ** 3 * Pp[3])
                cur = Pp[3]
    return np.array(out)


def resample(C, n=400):
    L = np.r_[0.0, np.cumsum(np.abs(np.diff(C)))]
    return (np.interp(np.linspace(0, 1, n), L / L[-1], C.real)
            + 1j * np.interp(np.linspace(0, 1, n), L / L[-1], C.imag)), float(L[-1])


def stem_width(a0, a1, b0, b1, n=400):
    """A straight leg: its centre-line, and the gap between its two long edges."""
    c = np.linspace(0, 1, n)
    mid = (a0 + (a1 - a0) * c + b0 + (b1 - b0) * c) / 2
    e = (b1 - b0) / abs(b1 - b0)
    return mid, np.abs(((mid - b0) / e).imag) * 2


def near_width(C, poly, radius=1400.0):
    """Band width at each sample: the nearest boundary point on each side of the normal.

    A ray cast is exact and the wrong tool -- the hoop closes into a loop, so a ray finds the
    far branch before its own.  Nearest-each-side inside a radius cannot.
    """
    Q = np.asarray(poly, dtype=complex)
    d = np.gradient(C); d /= np.abs(d); nrm = 1j * d
    out = []
    for k in range(len(C)):
        v = Q - C[k]; r = np.abs(v); m = r < radius
        side = v.real * nrm[k].real + v.imag * nrm[k].imag
        a_, b_ = r[m & (side > 0)], r[m & (side < 0)]
        out.append((a_.min() + b_.min()) if len(a_) and len(b_) else np.nan)
    w = np.array(out); ok = np.isfinite(w)
    return np.interp(np.arange(len(w)), np.flatnonzero(ok), w[ok])


def blend_face(w, value, at_start, k=40):
    """Write a shared face's own length into one end of a width profile."""
    r = np.linspace(0, 1, k); r = 3 * r ** 2 - 2 * r ** 3
    if at_start:
        w[:k] = value + (w[:k] - value) * r
    else:
        w[-k:] = value + (w[-k:] - value) * r[::-1]


# ---- the four pieces of the pen's gesture ------------------------------------------------
LQ = [complex(5916, 10247), complex(1232, 1018), complex(2324, 1335), complex(5905, 9411)]
RQ = [complex(5916, 10247), complex(5845, 9416), complex(7752, 730), complex(8712, 283)]
mL, wL = stem_width(LQ[1], LQ[0], LQ[2], LQ[3])
mR, wR = stem_width(RQ[0], RQ[3], RQ[1], RQ[2])
CL, LL = resample(mL); CR, LR = resample(mR)
wL = np.interp(np.linspace(0, 1, 400), np.linspace(0, 1, len(wL)), wL)
wR = np.interp(np.linspace(0, 1, 400), np.linspace(0, 1, len(wR)), wR)

items = [list(t) for t in OBJ['white']['items']]
outer, inner = sd._walk(items, sd.EDGE_OUTER, 400), sd._walk(items, sd.EDGE_INNER, 400)
t_pair = np.clip(np.maximum.accumulate(
    sd._smooth(sd._arcfrac(inner)[sd._pair(outer, inner)], 0.02)), 0, 1)
sw_mid = AFF * ((outer + sd._at(inner, t_pair)) / 2) + OFF
_, wsec, usec = sd._section(outer, inner, 3)
ok = np.isfinite(wsec)
CT, LT = resample(sw_mid)
wT = np.interp(np.linspace(0, 1, 400), usec[ok], wsec[ok]) * SCALE

bar_poly = flatten(GEOM['bar']['outline_d'])
CB, LB = resample(flatten(GEOM['bar']['centre_d']))
wB = near_width(CB, bar_poly)

FACE_APEX = abs(complex(5916, 10247) - complex(5845, 9416))
FACE_FOOT = 9.9763 * SCALE
FACE_HOOK = 4.1037 * SCALE
blend_face(wL, FACE_APEX, False); blend_face(wR, FACE_APEX, True)
blend_face(wR, FACE_FOOT, False); blend_face(wT, FACE_FOOT, True)
blend_face(wT, FACE_HOOK, False); blend_face(wB, FACE_HOOK, True)
wB[-40:] = wB[-41]

PIECES = [('legL', CL, LL, wL), ('legR', CR, LR, wR), ('trail', CT, LT, wT), ('bar', CB, LB, wB)]


def walk_time(L, w):
    """Cumulative time along a piece under v = width ** P, and the progress at each step."""
    ds = L / (len(w) - 1)
    v = np.maximum(w, 60.0) ** P
    dt = np.r_[0.0, np.cumsum(ds / ((v[1:] + v[:-1]) / 2))]
    return dt, np.linspace(0, 1, len(dt))


times = [walk_time(L, w) for _, _, L, w in PIECES]
total = sum(dt[-1] for dt, _ in times)
k = (PEN_END - PEN_START) / total
starts, acc = [], PEN_START
for dt, _ in times:
    starts.append(acc); acc += k * dt[-1]


def ease(dt, fr, stops=14):
    """A CSS linear() timing function from a time -> progress map."""
    g = np.linspace(0, 1, stops)
    x = np.interp(g, dt / dt[-1], fr)
    inner = ', '.join('%.4f %.1f%%' % (x[i], 100 * g[i]) for i in range(1, stops - 1))
    return 'linear(0, %s, 1)' % inner


# ---- the ring -----------------------------------------------------------------------------
TURNS = 2.0
SPAN = 2 * math.pi * TURNS


def ray(c, r, th):
    d = np.exp(1j * th); f = CC - c
    b = 2 * (f.real * d.real + f.imag * d.imag)
    return (-b + math.sqrt(max(b * b - 4 * (abs(f) ** 2 - r * r), 0))) / 2


def coil(n=1600):
    """The coil: opens from 34% of the ring's radius to the ring itself over its last turn.

    Its final turn IS the annulus -- the two edges there are the ring's own outer and inner
    circles, read along the ray from the band's centre, so the eccentric counter comes out
    right and the shape the mask finally uncovers is the ring exactly.
    """
    th = TH0 + np.linspace(-SPAN, 0, n)
    hits = np.array([[ray(CO, RO['r'], t), ray(CI, RI['r'], t)] for t in th])
    r_mid, r_half = (hits[:, 0] + hits[:, 1]) / 2, (hits[:, 0] - hits[:, 1]) / 2
    e = np.clip((th - th[0]) / (SPAN - 2 * math.pi), 0, 1)
    e = e * e * (3 - 2 * e)
    rad = r_mid * (0.34 + 0.66 * e)
    half = r_half * np.clip(0.34 + 0.70 * e, 0, 1)
    d = np.exp(1j * th)
    return th, CC + rad * d, CC + (rad + half) * d, CC + (rad - half) * d, 2 * half


th, coil_c, coil_o, coil_i, coil_w = coil()

# The coil and the ring are TWO elements, not one band, and that is not a tidiness choice.
# A mask stroke is a spatial tube: one wide enough to uncover the annulus (764 units at its
# thickest) also reaches 440 units inward, and the coil's approach runs 200-400 units inside
# the ring for most of a quarter turn.  As one shape that showed as a crescent sitting inside
# the ring and never went away.  Split, each mask can only ever reach its own element's ink.
OPEN = th < TH0 - 2 * math.pi                    # the coil's opening; the rest IS the ring
coil_open_c = coil_c[OPEN]
coil_open_o, coil_open_i = coil_o[OPEN], coil_i[OPEN]
coil_open_w = coil_w[OPEN]

# The ring's own centre circle -- swept the SAME way the coil was, which is the whole point
# of the coil.  Run the other way it reverses the pen through 175.7 degrees at the apex: the
# coil arrives travelling left and the ring sets off travelling right, and the one gesture
# the ending is built on becomes two.
ring_th = TH0 + np.linspace(0, 2 * math.pi, 900)
ring_rc = np.array([(ray(CO, RO['r'], t) + ray(CI, RI['r'], t)) / 2 for t in ring_th])
ring_c = CC + ring_rc * np.exp(1j * ring_th)
ring_band = np.array([abs(ray(CO, RO['r'], t) - ray(CI, RI['r'], t)) for t in ring_th])

# the coil opens first, then the ring draws while the coil retracts behind it
open_ds = np.abs(np.diff(coil_open_c))
open_v = np.maximum((coil_open_w[1:] + coil_open_w[:-1]) / 2, 60.0) ** P
open_dt = np.r_[0.0, np.cumsum(open_ds / open_v)]
ring_ds = np.abs(np.diff(ring_c))
ring_v = np.maximum((ring_band[1:] + ring_band[:-1]) / 2, 60.0) ** P
ring_only_dt = np.r_[0.0, np.cumsum(ring_ds / ring_v)]
T_OPEN = open_dt[-1]
T_RING = ring_only_dt[-1]
SPLIT = T_OPEN / (T_OPEN + T_RING)               # of the ring's window, spent opening out

# The ring's last act is shutting its own gap at the apex, and it does that with its rate
# falling to zero -- 1-(1-p)^2 -- so it settles into the join rather than arriving at it.
# Held at a constant rate the close is an event; decelerating, it is a landing.
_p = ring_only_dt / ring_only_dt[-1]
ring_close_fr = 1.0 - (1.0 - _p) ** 2

def path_d(pts, step=8):
    P_ = list(pts[::step])
    if abs(P_[-1] - pts[-1]) > 1e-9:
        P_.append(pts[-1])          # the last sample is the junction; never drop it
    return 'M' + ' L'.join('%d %d' % (round(z.real), round(z.imag)) for z in P_)


def band_d(o, i, step=6):
    return (path_d(o, step) + ' L'
            + ' L'.join('%d %d' % (round(z.real), round(z.imag)) for z in i[::step][::-1]) + ' Z')


ring_span = RING_CLOSE - starts[0] if False else RING_CLOSE - PEN_START
RING_T0 = starts[1]                      # the ring opens at the apex, on the pen's one pivot
ring_d = RING_CLOSE - RING_T0

lines = []
w = lines.append
w('// GENERATED by design/logo-animation/emit_choreography.py. Do not edit by hand.')
w('//')
w('// The write-on\'s timing, derived rather than chosen. One rule sets it:')
w('//')
w('//     the pen goes faster where the stroke it is laying is thicker,  v = k * width')
w('//')
w('// Each piece\'s duration is its own arc length divided by that speed, so the boundaries')
w('// fall out of the geometry. Consecutive pieces share their end face -- the legs share the')
w('// A\'s apex face, the right leg and the trail share the foot cut, the trail and the')
w('// crossbar share the hoop\'s left hook face -- so the speed is continuous across every')
w('// join with nothing tuned: the face\'s own length is the width both sides agree on.')
w('//')
w('// Seconds from the start of play. The easings are linear() timing functions carrying the')
w('// speed law itself, so a piece\'s progress is never linear in its own window.')
w('')
w('export interface Beat { t: number; d: number; ease: string }')
w('')
w('export const BEATS = {')
for (name, _, _, _), t0, (dt, fr) in zip(PIECES, starts, times):
    w('  %s: { t: %.3f, d: %.3f, ease: %r },' % (name, t0, k * dt[-1], ease(dt, fr)))
w('  /** the trail retracts over exactly the crossbar\'s window: the pen\'s path is spent')
w('   *  drawing the crossbar, so the two read as one action rather than two. */')
w('  tail: { t: %.3f, d: %.3f, ease: \'linear\' },' % (starts[3], k * times[3][0][-1]))
w('  /** the ring opens at the apex, the pen\'s one pivot, and closes alone after the last')
w('   *  stroke lands -- the only thing still moving, and slowing, at the end. */')
w('  coil: { t: %.3f, d: %.3f, ease: %r },'
  % (RING_T0, ring_d * SPLIT, ease(open_dt, np.linspace(0, 1, len(open_dt)))))
# The coil retracts from its START, so the stretch lying alongside the ring is the last to
# go -- and that stretch is a hairline beside a finished edge, which reads as a stray hair.
# Clearing it over 60% of the ring's draw puts the coil away well before the close, and
# leaves the ring alone for its last beat, which is the point of the ending.
w('  coilOut: { t: %.3f, d: %.3f, ease: %r },'
  % (RING_T0 + ring_d * SPLIT, ring_d * (1 - SPLIT) * 0.60,
     ease(ring_only_dt, np.linspace(0, 1, len(ring_only_dt)))))
w('  ring: { t: %.3f, d: %.3f, ease: %r },'
  % (RING_T0 + ring_d * SPLIT, ring_d * (1 - SPLIT), ease(ring_only_dt, ring_close_fr)))
w('  /** the finished mark crosses in only once EVERYTHING has come to rest: a crossfade')
w('   *  over motion reads as a blur, not a landing. */')
w('  final: { t: %.3f, d: %.3f, ease: \'linear\' },' % (RING_CLOSE, 0.060))
w('} as const;')
w('')
w('/** Seconds, authored rather than derived: when the drawn pieces switch off, when the')
w(' *  hero treatment settles out from under the mark, and when the whole thing is over. */')
w('export const AFTER = { pieces: %.3f, treatT: %.3f, treatD: %.3f, done: %.3f } as const;'
  % (RING_CLOSE + 0.070, RING_CLOSE + 0.010, 0.260, RING_CLOSE + 0.290))
w('')
# The trail's two easings stay in TRAIL FRACTIONS, not dash fractions: LogoAnimated maps
# them through the mask's own lead-in and lead-out, and that mapping is already tested.  All
# this contributes is the curve.
def stops(dt, fr, n=12):
    g = np.linspace(0, 1, n)
    x = np.interp(g, dt / dt[-1], fr)
    return '[' + ', '.join('[%.4f, %.2f]' % (x[i], 100 * g[i]) for i in range(1, n - 1)) + ']'


_tdt, _tfr = walk_time(LT, wT)
w('/** The trail head and its retracting tail, as (trail fraction, percent of the window)')
w(' *  stops. Both are the SAME curve -- the tail retracts under the same speed law the head')
w(' *  was laid down with, so the comet moves the way the pen did. */')
w('export const TRAIL_HEAD_STOPS: [number, number][] = %s;' % stops(_tdt, _tfr))
w('export const TRAIL_TAIL_STOPS: [number, number][] = %s;' % stops(_tdt, _tfr))
w('')
w('')
w('/** The coil that opens out of the middle, and then the ring itself. Two elements: a')
w(' *  mask stroke is a spatial tube, so one wide enough to uncover the annulus also reaches')
w(' *  inside it, and as a single band the coil\'s approach showed as a crescent that never')
w(' *  cleared. Masked separately, neither can reach the other. */')
w('export const RING_COIL_D = %r;' % band_d(coil_open_o, coil_open_i))
w('export const RING_COIL_CENTRE_D = %r;' % path_d(coil_open_c))
w('export const RING_COIL_WIDTH = %d;' % int(math.ceil(coil_open_w.max() * 1.10)))
w('export const RING_ANNULUS_D = %r;'
  % ('M%d %d A%d %d 0 1 0 %d %d A%d %d 0 1 0 %d %d Z M%d %d A%d %d 0 1 1 %d %d A%d %d 0 1 1 %d %d Z'
     % (CO.real - RO['r'], CO.imag, RO['r'], RO['r'], CO.real + RO['r'], CO.imag,
        RO['r'], RO['r'], CO.real - RO['r'], CO.imag,
        CI.real - RI['r'], CI.imag, RI['r'], RI['r'], CI.real + RI['r'], CI.imag,
        RI['r'], RI['r'], CI.real - RI['r'], CI.imag)))
w('export const RING_CIRCLE_D = %r;' % path_d(ring_c, 6))
w('export const RING_CIRCLE_WIDTH = %d;' % int(math.ceil(ring_band.max() * 1.10)))
w('/** Of the ring\'s window, the share spent opening the coil out before the ring draws. */')
w('export const RING_SPLIT = %.4f;' % SPLIT)
w('')
OUT.write_text('\n'.join(lines) + '\n')

print('  v = width ** %.2f, %.3f -> %.3fs' % (P, PEN_START, PEN_END))
for (name, _, L, wd), t0, (dt, _) in zip(PIECES, starts, times):
    print('    %-6s %.3f -> %.3f  (%.3fs, %.0f units, width %.0f..%.0f)'
          % (name, t0, t0 + k * dt[-1], k * dt[-1], L, wd.min(), wd.max()))
print('    %-6s %.3f -> %.3f  (%.3fs)' % ('ring', RING_T0, RING_CLOSE, ring_d))
print('  joins:')
for a, b in zip(PIECES, PIECES[1:]):
    print('    %-5s -> %-5s  width %5.0f -> %5.0f  speed %+.2f%%'
          % (a[0], b[0], a[3][-1], b[3][0], 100 * ((b[3][0] / a[3][-1]) ** P - 1)))
print('  wrote %s' % OUT.relative_to(ROOT))
