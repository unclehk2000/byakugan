"""T1: grading the 07:00 displacement. After a displacement candle D (largest body 07:00-07:14, >= 5x the 06:00-06:59 median body,
leaving an FVG), the grading range runs from the FVG edge of the candle before (1.0) to D's volume-imbalance edge (0).
ICT: price should 'lay bodies above the midpoint' and then overlap the whole move. Test: from the first 1-minute close beyond a
level q of the range, does price reach 1.0 before 0, more than a driftless walk would from that close ((c - 0) / (1 - 0))?
Levels q = 0.25 / 0.375 / 0.5 / 0.625 / 0.75, measured to 11:00. ✓ rule on the excess over that walk."""
import sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
X = pd.read_pickle('disp.pkl'); X = X[(X.rel >= 5) & X.fvg & (X.top != X.bot)].copy()
out = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['Open', 'High', 'Low', 'Close']]
    H, L, C = b.High.to_numpy(), b.Low.to_numpy(), b.Close.to_numpy()
    for r in X[X.sym == sym].itertuples():
        i, e = r.i, r.i11
        # in grading units: 0 = bot (the VI edge), 1 = top; for a bearish D price must rise back; mirror bullish D
        R = r.top - r.bot
        if r.dr < 0:
            u = lambda p: (p - r.bot) / R
            hh, ll, cc = u(H[i + 2:e + 1]), u(L[i + 2:e + 1]), u(C[i + 2:e + 1])
        else:
            u = lambda p: (r.top - p) / R
            hh, ll, cc = u(L[i + 2:e + 1]), u(H[i + 2:e + 1]), u(C[i + 2:e + 1])
        n = len(cc)
        top_hit = np.flatnonzero(hh >= 1.0); t_top = top_hit[0] if len(top_hit) else 10 ** 9
        rec = dict(sym=sym, day=r.day, half=r.half, rel=r.rel, top_by11=t_top < 10 ** 9, ext=float(-min(0, ll.min())))
        for q in (0.25, 0.375, 0.5, 0.625, 0.75):
            k = np.flatnonzero(cc > q)
            if not len(k) or k[0] >= t_top:            # no close beyond q before the top was reached
                rec[f'c{q}'] = np.nan; continue
            k = k[0]; c0 = cc[k]
            after_h, after_l = hh[k + 1:], ll[k + 1:]
            a = np.flatnonzero(after_h >= 1.0); z = np.flatnonzero(after_l <= 0.0)
            ta = a[0] if len(a) else 10 ** 9; tz = z[0] if len(z) else 10 ** 9
            if ta == tz == 10 ** 9: y = np.nan          # neither by 11:00
            else: y = float(ta < tz)
            rec[f'c{q}'] = y; rec[f'p{q}'] = min(max(c0, 0), 1); rec[f'tq{q}'] = k
        # first touch of 0.5 by a wick that did NOT close beyond it
        k = np.flatnonzero(hh >= 0.5)
        if len(k) and k[0] < t_top and cc[k[0]] <= 0.5:
            k = k[0]; a = np.flatnonzero(hh[k + 1:] >= 1.0); z = np.flatnonzero(ll[k + 1:] <= 0.0)
            ta = a[0] if len(a) else 10 ** 9; tz = z[0] if len(z) else 10 ** 9
            rec['w0.5'] = np.nan if ta == tz == 10 ** 9 else float(ta < tz); rec['pw'] = min(max(cc[k], 0), 1)
        out.append(rec)
T = pd.DataFrame(out); T['date'] = T.day; T = T.set_index('date'); T.to_pickle('t1.pkl')
print('displacements', len(T), '| full retrace to 1.0 by 11:00', round(T.top_by11.mean(), 3), '| median extension beyond 0 first (range units)', round(T.ext.median(), 2))
rows = []
for q in (0.25, 0.375, 0.5, 0.625, 0.75):
    g = T.dropna(subset=[f'c{q}']).copy(); g['ex'] = g[f'c{q}'] - g[f'p{q}']
    print(f'close beyond {q}: n {len(g)}  reached 1.0 before 0: {g[f"c{q}"].mean():.3f}  walk from that close: {g[f"p{q}"].mean():.3f}  excess {g.ex.mean():+.3f}')
    rows.append(check(g, 'ex ~ 1', 'Intercept', test=f'close beyond {q}: excess over the walk'))
g = T.dropna(subset=['w0.5']).copy(); g['ex'] = g['w0.5'] - g['pw']
print(f'wick to 0.5, close below: n {len(g)}  reached 1.0 first {g["w0.5"].mean():.3f}  walk {g.pw.mean():.3f}  excess {g.ex.mean():+.3f}')
rows.append(check(g, 'ex ~ 1', 'Intercept', test='wick to 0.5, close below: excess'))
print(table(rows)[['coef', 'p', 'n', '18-24', '25-26', 'ES', 'NQ', 'RTY', 'ok']].to_string())
