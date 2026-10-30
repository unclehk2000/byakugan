"""T2: the 07:00 displacement into a daily PD array. ICT: price ran at 07:00 into a daily inversion FVG, then reversed hard.
Leg extreme = the furthest price from D until price first reaches the grading midpoint (or 09:00). 'Into an array' = that extreme
trades into a daily array (support for a down move: bullish FVG or inverted bearish FVG; resistance for an up move) that price was
not already inside at 07:00. Outcomes: the grading range's 1.0 by 09:00 / 11:00, D's open taken back by 11:00."""
import sys, pickle, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
X = pd.read_pickle('disp.pkl'); X = X[(X.rel >= 5) & X.fvg & (X.top != X.bot)].copy()
DA = pickle.load(open('daily_arrays.pkl', 'rb'))
out = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['Open', 'High', 'Low', 'Close', 'hm']]
    O, H, L, C, hm = (b[c].to_numpy() for c in ('Open', 'High', 'Low', 'Close', 'hm'))
    for r in X[X.sym == sym].itertuples():
        if (sym, r.day) not in DA: continue
        i, e = r.i, r.i11; R = r.top - r.bot; mid = (r.top + r.bot) / 2
        seg = np.arange(i, e + 1); h9 = seg[hm[seg] < 900]
        if r.dr < 0:
            reach = np.flatnonzero(H[i + 1:e + 1] >= mid); k = i + 1 + reach[0] if len(reach) else h9[-1]
            k = min(k, h9[-1]); ext = L[i:k + 1].min(); zones = DA[(sym, r.day)]['sup']
            inz = [z for z in zones if r.o7 > z[1] and ext <= z[1]]
            y9 = bool((H[i + 1:h9[-1] + 1] >= r.top).any()); y11 = bool((H[i + 1:e + 1] >= r.top).any()); yo = bool((H[i + 1:e + 1] >= O[i]).any())
            far = (r.bot - ext) / R
        else:
            reach = np.flatnonzero(L[i + 1:e + 1] <= mid); k = i + 1 + reach[0] if len(reach) else h9[-1]
            k = min(k, h9[-1]); ext = H[i:k + 1].max(); zones = DA[(sym, r.day)]['res']
            inz = [z for z in zones if r.o7 < z[0] and ext >= z[0]]
            y9 = bool((L[i + 1:h9[-1] + 1] <= r.bot).any()); y11 = bool((L[i + 1:e + 1] <= r.bot).any()); yo = bool((L[i + 1:e + 1] <= O[i]).any())
            far = (ext - r.top) / R
        kind = '' if not inz else ('ifvg' if any(z[2].endswith('-i') for z in inz) else 'fvg')
        out.append(dict(sym=sym, day=r.day, half=r.half, dr=r.dr, rel=r.rel, arr=float(bool(inz)), kind=kind, far=max(far, 0), y9=float(y9), y11=float(y11), yo=float(yo)))
T = pd.DataFrame(out); T['date'] = T.day; T = T.set_index('date'); T['lf'] = np.log1p(T.far); T['lr'] = np.log(T.rel); T.to_pickle('t2.pkl')
print(len(T), 'displacements;', f'{T.arr.mean():.1%} ran into a daily array', T.kind.value_counts().to_dict())
print(T.groupby('arr')[['y9', 'y11', 'yo', 'far']].mean().round(3).to_string())
print(T.groupby('kind')[['y9', 'y11', 'yo']].mean().round(3).to_string())
rows = []
for y in ('y9', 'y11', 'yo'):
    rows.append(check(T, f'{y} ~ arr', 'arr', test=f'{y} | into a daily array'))
    rows.append(check(T, f'{y} ~ arr + lf + lr', 'arr', test=f'{y} | into a daily array, leg size held'))
T2 = T.assign(ifv=(T.kind == 'ifvg').astype(float))
rows.append(check(T2, 'y11 ~ ifv + lf + lr', 'ifv', test='y11 | into a daily IFVG, leg size held'))
print(table(rows)[['coef', 'p', 'n', '18-24', '25-26', 'ES', 'NQ', 'RTY', 'ok']].to_string())
print(T.loc[(T.sym == 'NQ') & (T.day == '2026-08-06')].to_string())
