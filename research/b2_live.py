"""Live odds the 07:00 displacement is fully retraced (price back to the grading 1.0) by 11:00, from checkpoints every 15 minutes
(07:15 → 10:45) while it has not been: distance from price to the 1.0 in grading ranges, or in 06:00-06:59 median bodies."""
import sys, json, numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/gh2/stats-kit'); from stats_kit import check, table
X = pd.read_pickle('disp.pkl'); X = X[(X.rel >= 5) & X.fvg & (X.top != X.bot)]
CK = [715, 730, 745, 800, 815, 830, 845, 900, 915, 930, 945, 1000, 1015, 1030, 1045]
rows = []
for sym in ('NQ', 'ES', 'RTY'):
    b = pd.read_pickle(f'/home/claude/kyw/bars_{sym}_all.pkl')[['High', 'Low', 'Close', 'hm']]
    H, L, Cl, hm = (b[c].to_numpy() for c in ('High', 'Low', 'Close', 'hm'))
    for r in X[X.sym == sym].itertuples():
        i, e = r.i, r.i11; R = r.top - r.bot
        tgt = r.top if r.dr < 0 else r.bot
        seg = np.arange(i + 1, e + 1)
        hit = (H[seg] >= tgt) if r.dr < 0 else (L[seg] <= tgt)
        th = seg[hit][0] if hit.any() else 10 ** 12
        for ck in CK:
            j = seg[hm[seg] == ck]
            if not len(j): continue
            j = j[0]
            if th < j or j <= i + 1: continue                      # already back, or too early
            px = Cl[j - 1]; d = (tgt - px) / R if r.dr < 0 else (px - tgt) / R
            rows.append(dict(sym=sym, day=r.day, half=r.half, ck=ck, y=float(th <= e), dU=max(d, 0), dB=max(d * R / r.mb, 0)))
K = pd.DataFrame(rows); K['date'] = K.day; K = K.set_index('date'); K['ckf'] = K.ck.astype(str)
K['dU'] = K.dU.clip(0, 20); K['dB'] = K.dB.clip(0, 60); K['sU'] = np.sqrt(K.dU); K['sB'] = np.sqrt(K.dB)
print(K.shape, K.groupby('ck').y.mean().round(3).to_dict())
tr, te = K[K.half == '18-24'], K[K.half == '25-26'].copy()
for f in ('y ~ C(ckf)', 'y ~ dU + sU + C(ckf)', 'y ~ dB + sB + C(ckf)'):
    m = smf.logit(f, tr).fit(disp=0); print(f'{f:24s} OOS Brier {np.mean((m.predict(te) - te.y) ** 2):.4f}')
best = 'y ~ dU + sU + C(ckf)'
m = smf.logit(best, tr).fit(disp=0); te['p'] = m.predict(te); te['dec'] = pd.qcut(te.p.rank(method='first'), 6, labels=False)
print(te.groupby('dec').agg(pred=('p', 'mean'), obs=('y', 'mean'), n=('y', 'size')).round(3).T.to_string())
print(table([check(K, 'y ~ dU + sU + C(ckf)', 'dU', test='retrace by 11:00 ~ distance (grading ranges)')])[['coef', 'p', 'n', '18-24', '25-26', 'ES', 'NQ', 'RTY', 'ok']].to_string())
mf = smf.logit(best, K).fit(disp=0); p = mf.params
out = dict(ck=CK, ints=[round(p['Intercept'] + p.get(f'C(ckf)[T.{c}]', 0.0), 4) for c in map(str, CK)], a=round(p['dU'], 4), b=round(p['sU'], 4))
json.dump(out, open('live_coef.json', 'w')); print(out)

print('--- distance in median bodies, log form')
K['lB'] = np.log1p(K.dB); tr, te = K[K.half == '18-24'], K[K.half == '25-26'].copy()
for f in ('y ~ lB + C(ckf)', 'y ~ dB + sB + C(ckf)'):
    m = smf.logit(f, tr).fit(disp=0); te['p'] = m.predict(te); print(f'{f:24s} OOS Brier {np.mean((te.p - te.y) ** 2):.4f}')
m = smf.logit('y ~ lB + C(ckf)', tr).fit(disp=0); te['p'] = m.predict(te); te['dec'] = pd.qcut(te.p.rank(method='first'), 6, labels=False)
print(te.groupby('dec').agg(pred=('p', 'mean'), obs=('y', 'mean'), n=('y', 'size')).round(3).T.to_string())
print(table([check(K, 'y ~ lB + C(ckf)', 'lB', test='retrace by 11:00 ~ log distance (median bodies)')])[['coef', 'p', 'n', '18-24', '25-26', 'ES', 'NQ', 'RTY', 'ok']].to_string())
mf = smf.logit('y ~ lB + C(ckf)', K).fit(disp=0); p = mf.params
out = dict(ck=CK, ints=[round(float(p['Intercept'] + p.get(f'C(ckf)[T.{c}]', 0.0)), 4) for c in map(str, CK)], a=round(float(p['lB']), 4))
json.dump(out, open('live_coef.json', 'w')); print(out)
print('median dB at 07:15:', K[K.ck == 715].dB.median().round(1), '| 09:00:', K[K.ck == 900].dB.median().round(1))
