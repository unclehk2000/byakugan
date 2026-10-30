"""T4: 'a small portion of a gap staying open is an unwillingness to go lower' (upper half held = strength).
1-minute FVGs formed 07:00-08:59 (gap >= 1x the 06:00-06:59 median body). Swing extreme = furthest price after the gap before
its first retrace into it. On that retrace, until price closes back beyond the gap's outer edge: held the half nearest the move
(upper half of a bullish gap) or went deeper (but not through the far edge). From that close: swing extreme taken before the
far edge, against a driftless walk from the close. ✓ rule on the difference between the two groups."""
import sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
rows = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['Open', 'High', 'Low', 'Close', 'tday', 'hm']].reset_index(drop=True)
    O, H, L, C, hm, td = (b[c].to_numpy() for c in ('Open', 'High', 'Low', 'Close', 'hm', 'tday'))
    ds = np.r_[0, np.flatnonzero(td[1:] != td[:-1]) + 1]; de = np.r_[ds[1:], len(b)]
    for s, e in zip(ds, de):
        h = hm[s:e]
        pre = np.flatnonzero((h >= 600) & (h < 700)) + s; win = np.flatnonzero((h >= 700) & (h < 900)) + s
        end = np.flatnonzero(h < 1100)
        if len(pre) < 50 or len(win) < 110 or not len(end): continue
        e11 = s + end[-1]; mb = np.median(np.abs(C[pre] - O[pre]))
        if mb <= 0: continue
        for j in win:                       # j = middle candle; gap between j-1 and j+1
            if j - 1 < s or j + 3 > e11: continue
            for d in (1, -1):
                lo, hi = (H[j - 1], L[j + 1]) if d > 0 else (H[j + 1], L[j - 1])
                if hi - lo < mb: continue
                ce = (lo + hi) / 2
                # mirror to a bullish frame: x = d * price
                hh = d * (H if d > 0 else L)[j + 2:e11 + 1]; ll = d * (L if d > 0 else H)[j + 2:e11 + 1]; cc = d * C[j + 2:e11 + 1]
                top, bot, mid = (hi, lo, ce) if d > 0 else (-lo, -hi, -ce)       # top = outer edge, bot = far edge
                ent = np.flatnonzero(ll <= top)
                if not len(ent) or ent[0] == 0: continue
                k0 = ent[0]; sw = max(hh[:k0].max(), d * (H[j + 1] if d > 0 else L[j + 1]))
                # from the retrace, until a close back above the gap top; stop if price goes through the far edge first
                deep = ll[k0]; k = k0; ok = True
                while k < len(cc) and cc[k] <= top:
                    deep = min(deep, ll[k])
                    if deep < bot: ok = False; break
                    k += 1
                if not ok or k >= len(cc) - 1: continue
                held = float(deep >= mid); c0 = cc[k]
                pw = (c0 - bot) / (sw - bot) if sw > bot else np.nan
                if c0 >= sw: y = 1.0; pw = 1.0
                else:
                    a = np.flatnonzero(hh[k + 1:] >= sw); z = np.flatnonzero(ll[k + 1:] < bot)
                    ta = a[0] if len(a) else 10 ** 9; tz = z[0] if len(z) else 10 ** 9
                    y = np.nan if ta == tz else float(ta < tz)
                rows.append(dict(sym=sym, day=pd.Timestamp(td[s]), held=held, y=y, pw=min(max(pw, 0), 1), depth=(top - deep) / (top - bot)))
T = pd.DataFrame(rows).dropna(); T['half'] = np.where(T.day.dt.year >= 2025, '25-26', '18-24'); T['date'] = T.day; T = T.set_index('date'); T['x'] = T.y - T.pw
T.to_pickle('t4.pkl')
print(len(T), 'retraces;', T.groupby('held')[['y', 'pw', 'x']].mean().round(3).to_string())
rr = [check(T, 'x ~ held', 'held', test='upper half held vs deeper: excess over the walk'), check(T, 'y ~ held + pw', 'held', test='upper half held, walk odds held')]
# is the CE special? depth bands
T['band'] = pd.cut(T.depth, [0, .25, .375, .5, .625, .75, 1.0001], labels=False, include_lowest=True)
print(T.groupby('band')[['y', 'pw', 'x']].mean().round(3).to_string())
print(table(rr)[['coef', 'p', 'n', '18-24', '25-26', 'ES', 'NQ', 'RTY', 'ok']].to_string())
