"""
Typographic constants.  These are the numbers that do NOT come from the mark:
a mark has no baseline, cap line, or spacing, so a typeface has to supply them.
Everything measured from the mark lives in measure/measurements.json instead.
"""
UPM         = 1000
CAP         = 700     # flat cap height
ASCENT      = 800
DESCENT     = 200
OVER_ROUND  = 10      # round forms overshoot the cap line and baseline (1.4% of cap)
OVER_POINT  = 16      # pointed apexes overshoot the cap line (2.3% of cap)
SB_STRAIGHT = 60      # side bearing next to a straight stem
SB_ROUND    = 40      # side bearing next to a round or a pointed/lobed extreme
EYE_PUSH    = 4       # how far a hook's eye is pushed past the (absent) ring so it opens
SPACE_ADV   = 260     # word space
