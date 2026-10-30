"""The first 30 minutes of the 7-9 range (07:00-07:29 ET): how often it already holds the 7-9 high / low, and how often its
high / low is taken by 09:00 and by 11:00. NQ + ES + RTY 1-minute 2018-26, by period and symbol."""
import numpy as np, pandas as pd
rows = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['High', 'Low', 'tday', 'hm']]
    for d, g in b[(b.hm >= 700) & (b.hm < 1100)].groupby('tday'):
        o = g[g.hm < 730]; r = g[(g.hm >= 730) & (g.hm < 900)]; a = g[(g.hm >= 730) & (g.hm < 1100)]
        if len(o) < 25 or len(r) < 80 or len(a) < 200: continue
        H, L = o.High.max(), o.Low.min()
        rows.append(dict(sym=sym, day=d, hiHeld=r.High.max() <= H, loHeld=r.Low.min() >= L, hi9=r.High.max() > H, lo9=r.Low.min() < L,
                         hi11=a.High.max() > H, lo11=a.Low.min() < L, orR=H - L, rngR=max(H, r.High.max()) - min(L, r.Low.min())))
X = pd.DataFrame(rows); X['half'] = np.where(pd.to_datetime(X.day).dt.year >= 2025, '25-26', '18-24')
X['both9'] = X.hi9 & X.lo9; X['none9'] = ~X.hi9 & ~X.lo9; X['one9'] = X.hi9 ^ X.lo9; X['any11'] = X.hi11 | X.lo11; X['both11'] = X.hi11 & X.lo11
X['share'] = X.orR / X.rngR
cols = ['hiHeld', 'loHeld', 'none9', 'one9', 'both9', 'any11', 'both11', 'share']
print(len(X)); print((X[cols].mean() * [100] * 7 + [0]).round(1).to_string() if False else X[cols].mean().round(3).to_string())
print(X.groupby('half')[cols].mean().round(3).to_string()); print(X.groupby('sym')[cols].mean().round(3).to_string())
