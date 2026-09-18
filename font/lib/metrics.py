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
# ---- lowercase.  D6-class constants: the mark supplies none of these either.
#
# 55% of the cap is small for a geometric sans -- the kind usually sits at 65-73% -- and it is
# chosen knowing that.  R1's band and counter displacement are ABSOLUTE, so a smaller x-height
# makes the lowercase o's band a larger share of its own diameter (10.05% against the cap O's
# 5.65%).  That is the ordinary typographic relationship and needs no correction; scaling the
# band to match would put it at 22.88 against a displacement of 24.31 and open the o into a C.
XH          = 385     # x-height
ASC_LC      = 700     # ascenders sit level with the cap line, not above it
DESC_LC     = -185    # descender line; rounds overshoot it by OVER_ROUND as they do the baseline

SB_STRAIGHT = 60      # side bearing next to a straight stem
SB_ROUND    = 40      # side bearing next to a round or a pointed/lobed extreme
EYE_PUSH    = 4       # how far a hook's eye is pushed past the (absent) ring so it opens
SPACE_ADV   = 260     # word space
