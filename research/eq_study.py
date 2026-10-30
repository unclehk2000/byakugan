"""Does it matter whether the 07:00-07:30 range's EQ sits above or below the Byakugan EQ (the 7-9 midpoint)?
NQ + ES + RTY 1-minute 2018-26, FOMC / CPI / NFP days excluded (hm/events.py). Known at 09:00.
s = +1 when the 07:00-07:30 EQ is above the 7-9 EQ (the first 30 minutes sat in the upper part; the range then grew lower),
    -1 when below; days where they are equal (the first 30 minutes are the whole range) are left out.
Outcomes after 09:00: which 7-9 extreme is taken first (to 16:00), the 09:30 -> 11:00 and 09:30 -> 16:00 direction,
16:00 close vs the 7-9 EQ, the 09:30 bias (open vs 7-9 EQ) being right on the close.
✓ = p < 0.05 clustered by date, same sign in 2018-24 and 2025-26 and on each symbol."""
import sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
sys.path.insert(0, '/home/claude/hm'); from events import FOMC, CPI, NFP
EV = set(pd.DatetimeIndex(FOMC).normalize()) | set(pd.DatetimeIndex(CPI).normalize()) | set(pd.DatetimeIndex(NFP).normalize())
rows = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['Open', 'High', 'Low', 'Close', 'tday', 'hm']]
    for d, g in b[(b.hm >= 700) & (b.hm < 1600)].groupby('tday'):
        o = g[g.hm < 730]; r = g[g.hm < 900]; a = g[g.hm >= 900]; n9 = g[g.hm >= 930]
        if len(o) < 25 or len(r) < 110 or len(n9) < 380 or len(a) < 410: continue
        H, L = r.High.max(), r.Low.min(); R = H - L; EQ = (H + L) / 2
        oEQ = (o.High.max() + o.Low.min()) / 2
        if R <= 0: continue
        up_t = r.High.idxmax() >= r.Low.idxmin()                      # the extreme that formed later (Byakugan's travel)
        hiF = a.High.values > H; loF = a.Low.values < L
        th = np.argmax(hiF) if hiF.any() else 10 ** 9; tl = np.argmax(loF) if loF.any() else 10 ** 9
        first = np.nan if th == tl else float(th < tl)                 # 1 = 7-9 high taken first
        O930 = n9.Open.iloc[0]; C11 = n9[n9.hm < 1100].Close.iloc[-1]; C16 = n9.Close.iloc[-1]; C9 = r.Close.iloc[-1]
        rows.append(dict(sym=sym, day=pd.Timestamp(d), ev=pd.Timestamp(d) in EV, s=np.sign(oEQ - EQ), rel=(oEQ - EQ) / R, upT=float(up_t),
                         c9=(C9 - EQ) / R, o930=(O930 - EQ) / R, first=first, am=float(C11 > O930), rth=float(C16 > O930),
                         cls=float(C16 > EQ), bias=np.sign(O930 - EQ), R=R))
X = pd.DataFrame(rows); X['half'] = np.where(X.day.dt.year >= 2025, '25-26', '18-24'); X['date'] = X.day; X = X.set_index('date')
print('days', len(X), '| event days', int(X.ev.sum()))
Y = X[~X.ev & (X.s != 0)].copy(); Y['up'] = (Y.s > 0).astype(float)
Y['biasOK'] = np.where(Y.bias > 0, Y.cls, 1 - Y.cls)
print('non-event days with a signal', len(Y), '| EQ above', round(Y.up.mean(), 3), '| agrees with the later extreme (EQ above <-> low formed later)', round(((Y.s > 0) == (Y.upT == 0)).mean(), 3))
cols = ['first', 'am', 'rth', 'cls', 'biasOK']
print(Y.groupby('up')[cols].mean().round(3).to_string())
rows = []
for y in ('first', 'am', 'rth', 'cls', 'biasOK'):
    rows.append(check(Y, f'{y} ~ up', 'up', test=f'{y} | OR EQ above the 7-9 EQ'))
    rows.append(check(Y, f'{y} ~ up + upT + c9', 'up', test=f'{y} | OR EQ above, travel and 09:00 close held'))
T = table(rows)[['coef', 'p', 'n', '18-24', '25-26', 'ES', 'NQ', 'RTY', 'ok']]
print(T.to_string())
# by how far apart, in 7-9 ranges
Y['band'] = pd.cut(Y.rel, [-0.5, -0.25, -0.1, 0, 0.1, 0.25, 0.5], include_lowest=True)
print(Y.groupby('band')[cols].mean().round(3).assign(n=Y.groupby('band').size()).to_string())
# event days, for contrast
Z = X[X.ev & (X.s != 0)].copy(); Z['up'] = (Z.s > 0).astype(float); Z['biasOK'] = np.where(Z.bias > 0, Z.cls, 1 - Z.cls)
print('event days', len(Z)); print(Z.groupby('up')[cols].mean().round(3).to_string())
X.to_pickle('eq.pkl')
