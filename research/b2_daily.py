"""Daily PD arrays per symbol and trading day, as known at the start of that day (completed days only, same contract):
support = active daily bullish FVGs + bearish FVGs inverted by a daily close above them (IFVG);
resistance = active daily bearish FVGs + bullish FVGs inverted by a daily close below them. An array stops being live once a daily
close goes through it the other way."""
import numpy as np, pandas as pd, pickle
out = {}
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['Open', 'High', 'Low', 'Close', 'tday', 'Contract']]
    g = b.groupby('tday').agg(o=('Open', 'first'), h=('High', 'max'), l=('Low', 'min'), c=('Close', 'last'), ct=('Contract', 'last'), n=('Close', 'size'))
    g = g[g.n >= 600]
    days = g.index.to_list(); A = []    # each: [lo, hi, kind, state, contract]  kind bull/bear; state 'fvg' | 'ifvg' | 'dead'
    for t in range(len(days)):
        d = days[t]; row = g.iloc[t]
        sup = [(a[0], a[1], a[2] + ('-i' if a[3] == 'ifvg' else '')) for a in A if a[4] == row.ct and ((a[2] == 'bull' and a[3] == 'fvg') or (a[2] == 'bear' and a[3] == 'ifvg'))]
        res = [(a[0], a[1], a[2] + ('-i' if a[3] == 'ifvg' else '')) for a in A if a[4] == row.ct and ((a[2] == 'bear' and a[3] == 'fvg') or (a[2] == 'bull' and a[3] == 'ifvg'))]
        out[(sym, d)] = dict(sup=sup, res=res)
        # update states with today's close, then add the FVG that today completes
        for a in A:
            if a[3] == 'dead': continue
            if a[2] == 'bull':
                if a[3] == 'fvg' and row.c < a[0]: a[3] = 'ifvg'
                elif a[3] == 'ifvg' and row.c > a[1]: a[3] = 'dead'
            else:
                if a[3] == 'fvg' and row.c > a[1]: a[3] = 'ifvg'
                elif a[3] == 'ifvg' and row.c < a[0]: a[3] = 'dead'
        if t >= 2:
            a1, a3 = g.iloc[t - 2], row
            if a1.ct == a3.ct == g.iloc[t - 1].ct:
                if a3.l > a1.h: A.append([a1.h, a3.l, 'bull', 'fvg', a3.ct])
                if a3.h < a1.l: A.append([a3.h, a1.l, 'bear', 'fvg', a3.ct])
        A = [a for a in A if a[3] != 'dead'][-60:]
    print(sym, len([k for k in out if k[0] == sym]))
pickle.dump(out, open('daily_arrays.pkl', 'wb'))
x = out[('NQ', pd.Timestamp('2026-08-06'))]; print('NQ 6 Aug support:', [z for z in x['sup'] if z[0] < 29700 and z[1] > 29000])
