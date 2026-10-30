"""Byakugan v2 research, step 1: the 07:00 displacement (ICT, The Science of Anticipation, 6 Aug 2026).
Per day: the largest-body 1-minute candle in 07:00-07:14 ET (D), its size against the 06:00-06:59 median body, whether it leaves
a fair value gap with its neighbours, the grading range (FVG edge of the candle before -> the volume-imbalance edge of the
candle after), and the suspension block (D's own body when volume imbalances sit on both sides of it). Then the path to 11:00."""
import numpy as np, pandas as pd
rows = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['ts', 'Open', 'High', 'Low', 'Close', 'tday', 'hm']].reset_index(drop=True)
    O, H, L, C, hm, td = (b[c].to_numpy() for c in ('Open', 'High', 'Low', 'Close', 'hm', 'tday'))
    ds = np.r_[0, np.flatnonzero(td[1:] != td[:-1]) + 1]; de = np.r_[ds[1:], len(b)]
    for s, e in zip(ds, de):
        h = hm[s:e]
        pre = np.flatnonzero((h >= 600) & (h < 700)) + s
        win = np.flatnonzero((h >= 700) & (h < 715)) + s
        run = np.flatnonzero((h >= 700) & (h < 1100)) + s
        if len(pre) < 50 or len(win) < 14 or len(run) < 230: continue
        if not (np.all(np.diff(run) == 1) and run[0] - 1 == pre[-1]): continue
        mb = np.median(np.abs(C[pre] - O[pre])); mr = np.median(H[pre] - L[pre])
        if mb <= 0: continue
        bod = np.abs(C[win] - O[win]); i = win[bod.argmax()]
        dr = 1 if C[i] > O[i] else -1
        fvg = (L[i + 1] > H[i - 1]) if dr > 0 else (H[i + 1] < L[i - 1])
        # grading range: bearish D -> top = low of the candle before (FVG top), bottom = the lower of D's close and the next open
        if dr < 0:
            top, bot = L[i - 1], min(C[i], O[i + 1])
            viA = max(O[i], C[i]) < min(O[i - 1], C[i - 1]); viB = max(O[i + 1], C[i + 1]) < min(O[i], C[i])
        else:
            bot, top = H[i - 1], max(C[i], O[i + 1])
            viA = min(O[i], C[i]) > max(O[i - 1], C[i - 1]); viB = min(O[i + 1], C[i + 1]) > max(O[i], C[i])
        rows.append(dict(sym=sym, day=pd.Timestamp(td[s]), i=i, t=int(hm[i]), dr=dr, body=abs(C[i] - O[i]), rel=abs(C[i] - O[i]) / mb, mr=mr, mb=mb,
                         fvg=bool(fvg), top=top, bot=bot, viA=bool(viA), viB=bool(viB), sbH=max(O[i], C[i]), sbL=min(O[i], C[i]),
                         o7=O[run[0]], i11=run[-1], px=C[i + 1]))
X = pd.DataFrame(rows); X['half'] = np.where(X.day.dt.year >= 2025, '25-26', '18-24'); X.to_pickle('disp.pkl')
print(X.shape); print(X.groupby('sym').rel.describe(percentiles=[.5, .75, .9]).round(2))
for k in (3, 5, 8):
    g = X[(X.rel >= k) & X.fvg]
    print(f'rel >= {k} with FVG: {len(g)} days ({len(g) / len(X):.1%}); with VI both sides (suspension block) {(g.viA & g.viB).mean():.1%}; at 07:00 {(g.t == 700).mean():.1%}')
r = X[(X.sym == 'NQ') & (X.day == '2026-08-06')].iloc[0]; print(r.to_dict())
