"""Byakugan v2 mock: the 07:00 displacement graded in eighths (with its live odds), suspension blocks, and, once 09:00 has
passed, the usual 7–9 box, levels, 09:30 bias, AL target and first presented FVG. Values computed the way
Byakugan_FPFVG.pine computes them, from 1-minute data.  python3 mock_byk2.py OUTDIR SYM DAY 'HH:MM' [t0 'HH:MM']"""
import sys, json
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams['font.family'] = 'DejaVu Sans'
OUT, SYM, DAY, HM = sys.argv[1:5]; T0 = sys.argv[5] if len(sys.argv) > 5 else '06:30'
NOW = pd.Timestamp(f'{DAY} {HM}'); X0 = pd.Timestamp(f'{DAY} {T0}')
BG, MU, GRID, CHT = '#ffffff', '#9aa1b2', '#eef1f6', '#131722'
UPC, DNC = '#089981', '#f23645'; RNG, MID, EXT, AL = '#1e88e5', '#ff9800', '#7fb7f0', '#8e24aa'
C01, C50, C8, SBC = '#131722', '#880e4f', '#9e9e9e', '#ff7043'
J = json.load(open('/home/claude/byk2/live_coef.json')); DX = [15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225]; DI, DA = J['ints'], J['a']
TICK = 0.1 if SYM == 'RTY' else 0.25
fmt = lambda v: f'{np.floor(v / TICK + 0.5) * TICK:,.2f}'
hh = lambda t: f'{t:%H:%M}'


def pDsp(m, d):
    if m >= 240: return None
    if m <= 15: it = DI[0]
    elif m >= 225: it = DI[14] + (DI[14] - DI[13]) * (m - 225) / 15
    else:
        i = 0
        while i < 13 and m >= DX[i + 1]: i += 1
        f = (m - DX[i]) / (DX[i + 1] - DX[i]); it = DI[i] * (1 - f) + DI[i + 1] * f
    return 100 / (1 + np.exp(-(it + DA * np.log1p(min(max(d, 0), 60)))))


b = pd.read_pickle(f'/home/claude/kyw/bars_{SYM}_all.pkl'); d = b[b.tday == pd.Timestamp(DAY)].set_index('ts'); d = d[d.index < NOW]
first = lambda m: m.index[m.values][0] if m.any() else None
pre = d[(d.hm >= 600) & (d.hm < 700)]; mbd = float(np.median(np.abs(pre.Close - pre.Open)))
w = d[(d.hm >= 700) & (d.hm < 715)]
# the displacement: the largest body in the window (needs the next candle)
w = w[w.index < NOW - pd.Timedelta(minutes=1)]
iD = (w.Close - w.Open).abs().idxmax(); k = d.index.get_loc(iD); D, Pv, Nx = d.iloc[k], d.iloc[k - 1], d.iloc[k + 1]
dr = 1 if D.Close > D.Open else -1; body = abs(D.Close - D.Open)
ok = body >= 5 * mbd and ((Nx.Low > Pv.High) if dr > 0 else (Nx.High < Pv.Low))
top, bot = (Pv.Low, min(D.Close, Nx.Open)) if dr < 0 else (max(D.Close, Nx.Open), Pv.High)
fib = lambda q: bot + q * (top - bot) if dr < 0 else top - q * (top - bot)
tgt = top if dr < 0 else bot
aft = d[d.index > iD]; hitT = first(aft.High >= tgt) if dr < 0 else first(aft.Low <= tgt)
px = d.Close.iloc[-1]; tL = d.index[-1]
m = (tL - pd.Timestamp(f'{DAY} 07:00')).total_seconds() / 60 + 1
pD = pDsp(m, ((tgt - px) if dr < 0 else (px - tgt)) / mbd) if hitT is None else None
print(dict(mbd=mbd, D=iD, body=body, rel=round(body / mbd, 1), ok=ok, top=top, bot=bot, mid=(top + bot) / 2, hit=hitT, pD=pD))
# suspension blocks 07:00-08:59
SB = []
win = d[(d.hm >= 700) & (d.hm < 900)]
for t in win.index:
    j = d.index.get_loc(t)
    if j + 1 >= len(d) or j < 1: continue
    c, p, n = d.iloc[j], d.iloc[j - 1], d.iloc[j + 1]
    bt, bb = max(c.Open, c.Close), min(c.Open, c.Close)
    if bt - bb < 2 * mbd: continue
    up = c.Close > c.Open
    va = bb > max(p.Open, p.Close) if up else bt < min(p.Open, p.Close)
    vb = min(n.Open, n.Close) > bt if up else max(n.Open, n.Close) < bb
    mid = (top + bot) / 2; back = first(aft.High >= mid) if dr < 0 else first(aft.Low <= mid)
    inleg = ok and ((c.Close > c.Open) == (dr > 0)) and t >= iD and (back is None or t < back)
    if va and vb and inleg: SB.append((t, bt, bb))
print('SB', [(hh(t), bb, bt, (bt + bb) / 2) for t, bt, bb in SB])

# ── chart
x = d[d.index >= X0]; n = len(x)
fig = plt.figure(figsize=(18, 10.4), dpi=100, facecolor=BG); ax = fig.add_axes([0.01, 0.05, 0.93, 0.86])
for sp in ax.spines.values(): sp.set_visible(False)
ax.set_facecolor(BG); ax.yaxis.tick_right(); ax.tick_params(axis='y', colors=MU, labelsize=8); ax.tick_params(axis='x', length=0); ax.grid(color=GRID, lw=0.7, zorder=0)
ix = lambda t: float(np.searchsorted(x.index, t))
for i, (t, q) in enumerate(x.iterrows()):
    c = UPC if q.Close >= q.Open else DNC
    ax.plot([i, i], [q.Low, q.High], color=c, lw=0.7, zorder=4)
    ax.add_patch(Rectangle((i - 0.35, min(q.Open, q.Close)), 0.7, max(abs(q.Close - q.Open), 0.25), fc=c, ec=c, lw=0.2, zorder=5))
cut = pd.Timestamp(f'{DAY} 11:00'); xe = min(ix(tL), ix(cut)) if tL < cut else ix(cut) - 1
lab = lambda y, t, c, xx=None: ax.text((xe if xx is None else xx) + 1, y, t, color=c, fontsize=7.2, va='center', clip_on=True, zorder=8)
if ok:
    for q in (0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1):
        y = fib(q); c = C50 if q == 0.5 else C01 if q in (0, 1) else C8
        ax.plot([ix(iD), xe], [y, y], color=c, lw=2 if q == 0.5 else 1, zorder=3)
        tx = f'{q:g} ({fmt(y)})'
        if q == 1: tx += f' ✓ {hh(hitT)}' if hitT is not None else f' · back by 11:00 {round(pD)}%'
        lab(y, tx, c)
    ax.annotate(f"{'▼' if dr < 0 else '▲'} 07:00 displacement · {body / mbd:.0f}×", (ix(iD), D.High if dr < 0 else D.Low), xytext=(0, 8 if dr < 0 else -8), textcoords='offset points', fontsize=7.2, ha='center', va='bottom' if dr < 0 else 'top', color=CHT, bbox=dict(fc=DNC if dr < 0 else UPC, alpha=0.18, ec='none', boxstyle='round,pad=0.3'), zorder=9)
for t, bt, bb in SB:
    a = ix(t); ax.add_patch(Rectangle((a - 0.4, bb), xe - a + 0.4, bt - bb, fc=SBC, alpha=0.28, ec=SBC, lw=0.6, zorder=2))
    ce = (bt + bb) / 2; ax.plot([a, xe], [ce, ce], color=CHT, lw=0.9, ls=':', zorder=3); lab(ce, f'SB CE {fmt(ce)}', CHT, xe + 22)
# after 09:00: the 7–9 box and levels; after 09:30: bias, AL target, first presented FVG
if NOW >= pd.Timestamp(f'{DAY} 09:01'):
    r = d[(d.hm >= 700) & (d.hm < 900)]; bH, bL = r.High.max(), r.Low.min(); R = bH - bL; bM = (bH + bL) / 2
    upT = r.High.idxmax() >= r.Low.idxmin(); endE, orgE, s = (bH, bL, 1) if upT else (bL, bH, -1)
    i7, i9 = ix(pd.Timestamp(f'{DAY} 07:00')), ix(pd.Timestamp(f'{DAY} 09:00'))
    ax.add_patch(Rectangle((i7, bL), i9 - i7, R, fc=RNG, alpha=0.07, ec='none', zorder=1))
    for y, t_, c, w_ in ((bH, '7–9 high', RNG, 1), (bL, '7–9 low', RNG, 1), (bM, 'Byakugan 0.5', MID, 2)):
        ax.plot([i7, xe], [y, y], color=c, lw=w_, zorder=3); lab(y, t_, c, xe + 22)
    for v, nm in ((endE + s * 0.5 * R, '1.5'), (endE + s * 1.0 * R, '2.0'), (orgE - s * 0.25 * R, '−0.25'), (orgE - s * 0.5 * R, '−0.5')):
        ax.plot([i7, xe], [v, v], color=EXT, lw=1, ls=':', zorder=3); lab(v, 'Byakugan ' + nm, EXT, xe + 22)
    if NOW >= pd.Timestamp(f'{DAY} 09:31'):
        o930 = d.loc[f'{DAY} 09:30', 'Open']; bull = o930 > bM
        prev = b[(b.tday == pd.Timestamp(DAY))].set_index('ts'); al = prev[(prev.hm >= 2000) | (prev.hm < 500)]
        alT = al.High.max() if bull else al.Low.min(); dist = 100 * abs(alT - o930) / o930
        zone = 'under 0.15%' if dist < .15 else '0.15–0.30%' if dist < .30 else '0.30–1.00% zone' if dist <= 1 else 'over 1.00%'
        po = prev[(prev.hm >= 500) & (prev.hm < 930)]; swept = (po.High.max() >= alT) if bull else (po.Low.min() <= alT)
        ax.plot([i7, xe], [alT, alT], color=AL, lw=1, ls='--', zorder=3); lab(alT, f"AL {'high' if bull else 'low'} target · " + ('swept pre-open' if swept else zone), AL, xe + 22)
        i930 = ix(pd.Timestamp(f'{DAY} 09:30'))
        ax.annotate('▲ Byakugan bias: BULL' if bull else '▼ Byakugan bias: BEAR', (i930, x.loc[f'{DAY} 09:30'].Low if bull else x.loc[f'{DAY} 09:30'].High), xytext=(0, -10 if bull else 10), textcoords='offset points', fontsize=7.2, ha='center', va='top' if bull else 'bottom', color=CHT, bbox=dict(fc=UPC if bull else DNC, alpha=0.18, ec='none', boxstyle='round,pad=0.3'), zorder=9)
        s9 = d[(d.hm >= 930) & (d.hm < 1600)]
        for kk in range(2, len(s9)):
            if s9.index[kk] - s9.index[0] >= pd.Timedelta(minutes=30): break
            c3, c1 = s9.iloc[kk], s9.iloc[kk - 2]
            g = (c1.High, c3.Low, True) if c3.Low > c1.High else (c3.High, c1.Low, False) if c3.High < c1.Low else None
            if g:
                a = ix(s9.index[kk - 2]); col = UPC if g[2] else DNC
                ax.add_patch(Rectangle((a, g[0]), xe - a, g[1] - g[0], fc=col, alpha=0.2, ec='none', zorder=2)); ce = (g[0] + g[1]) / 2
                ax.plot([a, xe], [ce, ce], color=CHT, lw=0.8, ls=':', zorder=3); lab(g[1], f'{hh(s9.index[kk - 2])} First presented', CHT, xe + 22)
                break
step = 15 if n < 200 else 30
ticks = [i for i, t in enumerate(x.index) if t.minute % step == 0]
ax.set_xticks(ticks); ax.set_xticklabels([hh(x.index[i]) for i in ticks], color=MU, fontsize=8)
ys = [x.Low.min(), x.High.max()] + ([fib(0), fib(1)] if ok else [])
lo, hi = min(ys), max(ys); ax.set_xlim(-2, xe + 52); ax.set_ylim(lo - (hi - lo) * 0.04, hi + (hi - lo) * 0.04)
fig.text(0.01, 0.955, f'Byakugan · 07:00 displacement and suspension blocks · {SYM} 1-minute, {NOW:%a %-d %b %Y %H:%M} ET', color=CHT, fontsize=13, weight='bold')
fig.text(0.01, 0.928, "The 07:00 displacement graded in eighths (1 = the gap edge of the candle before it, 0 = its volume-imbalance edge), suspension blocks with their CE, then Byakugan's usual levels. Mock-up from 1-minute data; TradingView will differ.", color='#5d6476', fontsize=9)
f = f'{OUT}/Byakugan_{SYM}_{DAY}_{NOW:%H%M}.png'; plt.savefig(f, dpi=100, facecolor=BG); plt.close(fig); print('saved', f)
