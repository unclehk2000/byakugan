"""T3: the suspension block (ICT: a candle body with a volume imbalance at both ends; entry at its CE).
All 1-minute candles 07:00-08:59 with body >= 2x the 06:00-06:59 median body. SB = body gaps (volume imbalances) to the
candle before and after, in the candle's direction. Placebo = same-size candles with no volume imbalance either side.
First return to the CE (body midpoint) after the next candle, to 11:00: does price then go through to the far end of the body
(through) or back to the near end (held) first? A driftless walk gives 50%."""
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
        end = np.flatnonzero(h < 1100); 
        if len(pre) < 50 or len(win) < 110 or not len(end): continue
        e11 = s + end[-1]
        mb = np.median(np.abs(C[pre] - O[pre]))
        if mb <= 0: continue
        for j in win:
            if j - 1 < s or j + 2 > e11: continue
            bt, bb = max(O[j], C[j]), min(O[j], C[j]); body = bt - bb
            if body < 2 * mb: continue
            d = 1 if C[j] > O[j] else -1
            p_t, p_b = max(O[j - 1], C[j - 1]), min(O[j - 1], C[j - 1]); n_t, n_b = max(O[j + 1], C[j + 1]), min(O[j + 1], C[j + 1])
            if d > 0: va, vb = bb > p_t, n_b > bt
            else: va, vb = bt < p_b, n_t < bb
            kind = 'SB' if (va and vb) else ('none' if not (va or vb) else 'one')
            ce = (bt + bb) / 2
            # after the next candle, the first bar back to the CE
            hh, ll = H[j + 2:e11 + 1], L[j + 2:e11 + 1]
            if d > 0: k = np.flatnonzero(ll <= ce)         # price came back down into a bullish block
            else: k = np.flatnonzero(hh >= ce)
            if not len(k): rows.append(dict(sym=sym, day=pd.Timestamp(td[s]), kind=kind, ret=0.0, thr=np.nan, rel=body / mb, d=d)); continue
            k = k[0]
            ck = C[j + 2 + k]                               # judged from the close of the bar that came back to the CE
            pw = (bt - ck) / body if d > 0 else (ck - bb) / body   # driftless odds of the far end first, from that close
            pw = min(max(pw, 0.0), 1.0)
            hh2, ll2 = hh[k + 1:], ll[k + 1:]
            if d > 0: thr_i, hold_i = np.flatnonzero(ll2 <= bb), np.flatnonzero(hh2 >= bt)
            else: thr_i, hold_i = np.flatnonzero(hh2 >= bt), np.flatnonzero(ll2 <= bb)
            a = thr_i[0] if len(thr_i) else 10 ** 9; z = hold_i[0] if len(hold_i) else 10 ** 9
            if pw in (0.0, 1.0): thr = pw
            else: thr = np.nan if a == z else float(a < z)
            rows.append(dict(sym=sym, day=pd.Timestamp(td[s]), kind=kind, ret=1.0, thr=thr, pw=pw, rel=body / mb, d=d))
T = pd.DataFrame(rows); T['half'] = np.where(T.day.dt.year >= 2025, '25-26', '18-24'); T['date'] = T.day; T = T.set_index('date'); T.to_pickle('t3.pkl')
print(T.kind.value_counts().to_dict())
print(T.groupby('kind').agg(n=('ret', 'size'), returned=('ret', 'mean'), through=('thr', 'mean'), rel=('rel', 'median')).round(3).to_string())
G = T.dropna(subset=['thr']).copy(); G['x'] = G.thr - G.pw
print(G.groupby('kind')[['thr', 'pw']].mean().round(3).to_string())
rr = [check(G[G.kind == 'SB'], 'x ~ 1', 'Intercept', test='SB: through, excess over the walk'), check(G[G.kind == 'none'], 'x ~ 1', 'Intercept', test='no-VI candle: through, excess over the walk')]
H2 = G[G.kind.isin(['SB', 'none'])].assign(sb=lambda d: (d.kind == 'SB').astype(float), lr=lambda d: np.log(d.rel))
rr.append(check(H2.assign(x=H2.thr - H2.pw), 'x ~ sb + lr', 'sb', test='SB vs no-VI candle excess, size held'))
R2 = T[T.kind.isin(['SB', 'none'])].assign(sb=lambda d: (d.kind == 'SB').astype(float), lr=lambda d: np.log(d.rel))
rr.append(check(R2, 'ret ~ sb + lr', 'sb', test='returns to its CE by 11:00: SB vs no-VI'))
print(table(rr)[['coef', 'p', 'n', '18-24', '25-26', 'ES', 'NQ', 'RTY', 'ok']].to_string())
