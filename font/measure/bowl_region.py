"""Where the bowl letters build, mapped rather than assumed.

B D P R are the face's most constrained glyphs -- each is a round solved against a horizontal
on one or both faces -- so they, not the diagonals, set how far the WEIGHT and PUSH axes can
run.  build_variable.py's grid is chosen from this map.

    python3 measure/bowl_region.py        # run from font/

A dot means all four build.  Letters name the ones that failed.  The two real limits, once the
solver's own two faults were out of the way (SPEC R1 / set_bowl._bury_edge and _wedge_x):

  low push   the counter has moved so far from the cap line that a cap-line arm's inner edge
             never reaches it, so there is no wedge to solve for at all;
  high push  ROUND_THIN runs out -- the round is closing into a C, which is the ceiling the
             knobs have anyway (PUSH 1.674*WEIGHT);
  high weight the bowl's outer circle and its horizontal's outer edge stop meeting.
"""
import sys, os, subprocess
code = ("import sys;sys.path.insert(0,'lib');sys.path.insert(0,'.')\n"
        "import glyphs.set_bowl as SB\n"
        "bad=[]\n"
        "for g in ('B','D','P','R'):\n"
        "    try: getattr(SB,'build_'+g)()\n"
        "    except Exception as e: bad.append(g)\n"
        "print('OK' if not bad else ''.join(bad))")
W=[0.60,0.70,0.85,1.00,1.20,1.45,1.70,2.00]
P=[0.12,0.20,0.30,0.50,0.65,0.85,1.00,1.20,1.40,1.60]
print('         ' + ''.join('%6s'%p for p in P) + '    <- PUSH')
for w in W:
    row=''
    for p in P:
        e=dict(os.environ); e['ORPHAN_WEIGHT']=str(w); e['ORPHAN_PUSH']=str(p)
        r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,env=e,
                         cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        o=r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'x'
        row += '%6s'%('.' if o=='OK' else o)
    print('W %-6s'%w + row + '   ceiling P=%.2f'%(1.674*w))
print('\n  .  = B D P R all build      letters = which failed')
import sys, os, subprocess
code = ("import sys;sys.path.insert(0,'lib');sys.path.insert(0,'.')\n"
        "import glyphs.set_bowl as SB\n"
        "bad=[]\n"
        "for g in ('B','D','P','R'):\n"
        "    try: getattr(SB,'build_'+g)()\n"
        "    except Exception as e: bad.append(g)\n"
        "print('OK' if not bad else ''.join(bad))")
W=[0.60,0.70,0.85,1.00,1.20,1.45,1.70,2.00]
P=[0.12,0.20,0.30,0.50,0.65,0.85,1.00,1.20,1.40,1.60]
print('         ' + ''.join('%6s'%p for p in P) + '    <- PUSH')
for w in W:
    row=''
    for p in P:
        e=dict(os.environ); e['ORPHAN_WEIGHT']=str(w); e['ORPHAN_PUSH']=str(p)
        r=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,env=e,
                         cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        o=r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'x'
        row += '%6s'%('.' if o=='OK' else o)
    print('W %-6s'%w + row + '   ceiling P=%.2f'%(1.674*w))
print('\n  .  = B D P R all build      letters = which failed')
