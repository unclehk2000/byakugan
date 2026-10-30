"""Follow-up: from the 09:30 open (inside the 7-9 range), which 7-9 extreme is taken first, against a driftless walk from the open
((open - low) / range for the high). Does the 07:00-07:30 EQ above / below the 7-9 EQ add anything beyond that walk?
Non-event days (FOMC / CPI / NFP excluded)."""
import sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
sys.path.insert(0, '/home/claude/hm'); from events import FOMC, CPI, NFP
EV = set(pd.DatetimeIndex(FOMC).normalize()) | set(pd.DatetimeIndex(CPI).normalize()) | set(pd.DatetimeIndex(NFP).normalize())
rows = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['Open', 'High', 'Low', 'Close', 'tday', 'hm']]
    for d, g in b[(b.hm >= 700) & (b.hm < 1600)].groupby('tday'):
        if pd.Timestamp(d) in EV: continue
        o = g[g.hm < 730]; r = g[g.hm < 900]; n9 = g[g.hm >= 930]
        if len(o) < 25 or len(r) < 110 or len(n9) < 380: continue
        H, L = r.High.max(), r.Low.min(); R = H - L; EQ = (H + L) / 2; oEQ = (o.High.max() + o.Low.min()) / 2
        O = n9.Open.iloc[0]
        if R <= 0 or oEQ == EQ or not (L < O < H): continue
        hiF = n9.High.values > H; loF = n9.Low.values < L
        th = np.argmax(hiF) if hiF.any() else 10 ** 9; tl = np.argmax(loF) if loF.any() else 10 ** 9
        if th == tl: continue
        rows.append(dict(sym=sym, day=pd.Timestamp(d), up=float(oEQ > EQ), rel=(oEQ - EQ) / R, first=float(th < tl), pw=(O - L) / R,
                         upT=float(r.High.idxmax() >= r.Low.idxmin())))
Y = pd.DataFrame(rows); Y['half'] = np.where(Y.day.dt.year >= 2025, '25-26', '18-24'); Y['date'] = Y.day; Y = Y.set_index('date'); Y['x'] = Y['first'] - Y.pw
print(len(Y), 'days (open inside the 7-9 range)')
print(Y.groupby('up')[['first', 'pw', 'x']].mean().round(3).to_string())
rr = [check(Y, 'x ~ up', 'up', test='high first: excess over the walk | OR EQ above'),
      check(Y, 'x ~ up + upT', 'up', test='same, Byakugan travel held'),
      check(Y[Y.up == 1].assign(i=1.0), 'x ~ 1', 'Intercept', test='OR EQ above: excess (high first) vs walk'),
      check(Y[Y.up == 0].assign(i=1.0), 'x ~ 1', 'Intercept', test='OR EQ below: excess (high first) vs walk')]
print(table(rr)[['coef', 'p', 'n', '18-24', '25-26', 'ES', 'NQ', 'RTY', 'ok']].to_string())
Y['band'] = pd.cut(Y.rel, [-0.5, -0.25, -0.1, 0, 0.1, 0.25, 0.5], include_lowest=True)
print(Y.groupby('band')[['first', 'pw', 'x']].mean().round(3).assign(n=Y.groupby('band').size()).to_string())
