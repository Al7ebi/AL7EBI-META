"""
engine.py — ICT Market Maker Engine (6-Stage Protocol)
All analysis logic extracted from the Colab notebook.
Import this in app.py.
"""

import warnings
warnings.filterwarnings("ignore")

import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from datetime import time
import pytz


# ══════════════════════════════════════════════════════════════
#  CONSTANTS  (overridable via run_engine params)
# ══════════════════════════════════════════════════════════════

HTF_INTERVAL    = "1d"
EXEC_INTERVAL   = "15m"
ENTRY_INTERVAL  = "5m"
HTF_PERIOD      = "6mo"
EXEC_PERIOD     = "5d"

SWING_LB          = 5
HTF_CANDLES       = 100
LIQUIDITY_TOUCHES = 2
SMT_WINDOW        = 20
SMT_TOLERANCE     = 0.003

KILLZONES = {
    "london_open":   (2,  0,  5,  0),
    "ny_open":       (7,  0, 10,  0),
    "silver_bullet": (10, 0, 11,  0),
    "london_close":  (10, 0, 12,  0),
}
JUDAS_WINDOW_MIN = 30
SWEEP_WICK_MIN   = 15.0
MSS_LOOKFORWARD  = 20
FVG_LOOKBACK     = 10
STDDEV_LEVELS    = [0.5, 1.0, 2.0, 4.0]

SCORE_A_PLUS = 10
SCORE_A      = 7
SCORE_MIN    = 5

# ── Watchlists ──────────────────────────────────────────────

TECH_STOCKS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
    "META", "TSLA", "AVGO", "AMD",   "QCOM",
    "ORCL", "CRM",  "ADBE", "INTC",  "TXN",
    "MU",   "AMAT", "LRCX", "KLAC",  "MRVL",
    "NFLX", "PYPL", "SHOP", "SNOW",  "PANW",
    "CRWD", "ZS",   "DDOG", "MSTR",  "PLTR",
]

BLUE_CHIPS = [
    "JPM",  "BAC",  "GS",   "MS",   "BRK-B",
    "V",    "MA",   "AXP",  "WFC",  "C",
    "JNJ",  "UNH",  "LLY",  "ABBV", "PFE",
    "MRK",  "TMO",  "ABT",  "DHR",  "BMY",
    "WMT",  "HD",   "COST", "TGT",  "MCD",
    "SBUX", "NKE",  "LOW",  "TJX",  "AMGN",
    "XOM",  "CVX",  "COP",  "SLB",  "CAT",
    "RTX",  "HON",  "UPS",  "BA",   "GE",
]

CHEAP_STOCKS = [
    "F", "AAL", "SOFI", "RIVN", "LCID",
    "SNAP", "UBER", "LYFT", "PLUG", "NIO",
    "XPEV", "WISH", "CLNE", "NOK",  "BB",
    "SIRI", "VALE", "ITUB", "PBR",  "KGC",
]

CRYPTO_ETF = [
    "MSTR", "COIN", "BITO", "GBTC", "ETHE",
    "ARKK", "BLOK", "BTCW", "HODL", "EZBC",
]

FOREX_PAIRS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X",
    "AUDUSD=X", "USDCAD=X", "USDCHF=X",
]

WATCHLIST_PRESETS = {
    "Options (70 Stocks)": (
        [(t, "QQQ") for t in TECH_STOCKS] +
        [(t, "SPY") for t in BLUE_CHIPS]
    ),
    "Tech Mega-Cap (30)": [(t, "QQQ") for t in TECH_STOCKS],
    "Blue Chips S&P (40)": [(t, "SPY") for t in BLUE_CHIPS],
    "Cheap Stocks (<$20)": [(t, "SPY") for t in CHEAP_STOCKS],
    "Crypto ETFs": [(t, "QQQ") for t in CRYPTO_ETF],
    "Forex Pairs": [(t, "DX-Y.NYB") for t in FOREX_PAIRS],
}


# ══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════

@dataclass
class LiquidityLevel:
    price: float
    kind: str
    touches: int
    formed_at: pd.Timestamp
    timeframe: str
    is_dol: bool = False

@dataclass
class SMTSignal:
    direction: str
    asset1_swing: float
    asset2_swing: float
    detected_at: pd.Timestamp
    description: str
    score: int = 2

@dataclass
class TimeContext:
    in_killzone: bool
    zone_name: str
    judas_detected: bool
    judas_direction: str
    score: int = 0

@dataclass
class SwingPoint:
    index: int
    timestamp: pd.Timestamp
    price: float
    kind: str

@dataclass
class LiqSweep:
    direction: str
    swept_price: float
    swept_at: pd.Timestamp
    swept_idx: int
    close_after: float
    wick_pct: float
    strength: str = field(init=False)
    def __post_init__(self):
        if self.wick_pct > 40:   self.strength = "STRONG"
        elif self.wick_pct > 25: self.strength = "MEDIUM"
        else:                    self.strength = "WEAK"

@dataclass
class StructureBreak:
    kind: str
    direction: str
    break_price: float
    broke_at: pd.Timestamp
    candle_idx: int

@dataclass
class FVG:
    direction: str
    top: float
    bottom: float
    midpoint: float
    formed_at: pd.Timestamp
    candle_idx: int
    size_pct: float
    filled: bool = False

@dataclass
class PDArray:
    kind: str
    direction: str
    top: float
    bottom: float
    midpoint: float
    formed_at: pd.Timestamp
    priority: int
    timeframe: str

@dataclass
class StdDevTarget:
    level: float
    price: float
    label: str
    is_tp: bool = True

@dataclass
class DecisionLog:
    stage: str
    finding: str
    score_delta: int
    reasoning: str
    risk_note: str = ""

@dataclass
class TradeSetup:
    ticker: str
    bias: str
    entry: float
    stop_loss: float
    targets: List[StdDevTarget]
    pd_array: PDArray
    score: int
    grade: str
    decision_log: List[DecisionLog]
    dol: Optional[LiquidityLevel]
    smt: Optional[SMTSignal]
    sweep: Optional[LiqSweep]
    mss: Optional[StructureBreak]
    fvg_entry: Optional[FVG]
    time_ctx: Optional[TimeContext]
    risk_summary: str = ""


# ══════════════════════════════════════════════════════════════
#  TZ HELPERS
# ══════════════════════════════════════════════════════════════

def to_naive(ts):
    if ts is None:
        return None
    try:
        t = pd.Timestamp(ts)
        return t.tz_localize(None) if t.tzinfo is not None else t
    except Exception:
        return None

def naive_index(idx):
    try:
        if hasattr(idx, "tz") and idx.tz is not None:
            return idx.tz_localize(None)
        return idx
    except Exception:
        try:
            return idx.tz_convert(None)
        except Exception:
            return idx


# ══════════════════════════════════════════════════════════════
#  DATA LAYER
# ══════════════════════════════════════════════════════════════

def fetch(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval,
                     auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data: {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df = df[["Open","High","Low","Close","Volume"]].dropna()
    return df

def detect_swings(df, lookback=5, n=100):
    sl = df.iloc[-n:].copy().reset_index()
    swings = []
    def _ts(i):
        for c in ["Datetime","Date"]:
            if c in sl.columns:
                return pd.Timestamp(sl[c].iloc[i])
        return sl.index[i]
    for i in range(lookback, len(sl)-lookback):
        wh = sl["High"].iloc[i-lookback:i+lookback+1]
        wl = sl["Low"].iloc[i-lookback:i+lookback+1]
        if sl["High"].iloc[i] == wh.max():
            swings.append(SwingPoint(i, _ts(i), float(sl["High"].iloc[i]), "high"))
        if sl["Low"].iloc[i] == wl.min():
            swings.append(SwingPoint(i, _ts(i), float(sl["Low"].iloc[i]),  "low"))
    return _dedup(swings, lookback)

def _dedup(swings, w):
    def keep(pts, mode):
        if not pts: return []
        res, grp = [], [pts[0]]
        for p in pts[1:]:
            if abs(p.index - grp[-1].index) <= w: grp.append(p)
            else:
                res.append(max(grp, key=lambda x: x.price) if mode=="high"
                           else min(grp, key=lambda x: x.price))
                grp = [p]
        res.append(max(grp, key=lambda x: x.price) if mode=="high"
                   else min(grp, key=lambda x: x.price))
        return res
    h = keep([s for s in swings if s.kind=="high"], "high")
    l = keep([s for s in swings if s.kind=="low"],  "low")
    return sorted(h+l, key=lambda x: x.index)


# ══════════════════════════════════════════════════════════════
#  STAGE 1 — Draw on Liquidity
# ══════════════════════════════════════════════════════════════

def stage1_draw_on_liquidity(df_htf, swings, tolerance=0.002):
    levels = []
    current = float(df_htf["Close"].iloc[-1])
    highs = [s for s in swings if s.kind=="high"]
    lows  = [s for s in swings if s.kind=="low"]

    def count_touches(price, df, side, tol=tolerance):
        count = 0
        for i in range(len(df)):
            ref = float(df["High"].iloc[i]) if side=="high" else float(df["Low"].iloc[i])
            if abs(ref - price) / max(price, 0.0001) <= tol:
                count += 1
        return count

    for h in highs:
        t = count_touches(h.price, df_htf, "high")
        if t >= LIQUIDITY_TOUCHES:
            levels.append(LiquidityLevel(h.price, "BSL", t, h.timestamp, HTF_INTERVAL))
    for l in lows:
        t = count_touches(l.price, df_htf, "low")
        if t >= LIQUIDITY_TOUCHES:
            levels.append(LiquidityLevel(l.price, "SSL", t, l.timestamp, HTF_INTERVAL))

    if not levels:
        for h in highs[-5:]:
            levels.append(LiquidityLevel(h.price, "BSL", 1, h.timestamp, HTF_INTERVAL))
        for l in lows[-5:]:
            levels.append(LiquidityLevel(l.price, "SSL", 1, l.timestamp, HTF_INTERVAL))

    bsl = sorted([l for l in levels if l.kind=="BSL" and l.price > current],
                 key=lambda x: (-x.touches, x.price))
    ssl = sorted([l for l in levels if l.kind=="SSL" and l.price < current],
                 key=lambda x: (-x.touches, -x.price))

    htf_h   = float(df_htf["High"].max())
    htf_l   = float(df_htf["Low"].min())
    htf_mid = (htf_h + htf_l) / 2
    htf_bias = "bearish" if current > htf_mid else "bullish"

    dol = None
    if htf_bias=="bearish" and ssl: dol = ssl[0]
    elif htf_bias=="bullish" and bsl: dol = bsl[0]
    elif bsl: dol = bsl[0]
    elif ssl: dol = ssl[0]
    if dol: dol.is_dol = True

    bias = ("long" if dol and dol.price > current else
            "short" if dol and dol.price < current else
            "long" if htf_bias=="bullish" else "short")

    return levels, dol, bias


# ══════════════════════════════════════════════════════════════
#  STAGE 2 — SMT Divergence
# ══════════════════════════════════════════════════════════════

def stage2_smt_divergence(df1, df2, bias, window=None, tol=None):
    if window is None: window = SMT_WINDOW
    if tol is None:    tol    = SMT_TOLERANCE

    common = df1.index.intersection(df2.index)
    if len(common) < window * 2:
        return None, "insufficient_data"

    a1 = df1.loc[common].iloc[-window:]
    a2 = df2.loc[common].iloc[-window:]
    half = window // 2

    a1_prev_h = float(a1.iloc[:half]["High"].max())
    a2_prev_h = float(a2.iloc[:half]["High"].max())
    a1_cur_h  = float(a1.iloc[half:]["High"].max())
    a2_cur_h  = float(a2.iloc[half:]["High"].max())

    a1_prev_l = float(a1.iloc[:half]["Low"].min())
    a2_prev_l = float(a2.iloc[:half]["Low"].min())
    a1_cur_l  = float(a1.iloc[half:]["Low"].min())
    a2_cur_l  = float(a2.iloc[half:]["Low"].min())

    detected_at = a1.index[-1]

    if a1_cur_h > a1_prev_h*(1+tol) and a2_cur_h < a2_prev_h*(1-tol):
        pct = abs(a1_cur_h/a1_prev_h - a2_cur_h/a2_prev_h) * 100
        return SMTSignal("bearish", a1_cur_h, a2_cur_h, detected_at,
                         f"Higher High vs Lower High | Div: {pct:.2f}%"), "bearish_divergence"

    if a1_cur_l < a1_prev_l*(1-tol) and a2_cur_l > a2_prev_l*(1+tol):
        pct = abs(a1_cur_l/a1_prev_l - a2_cur_l/a2_prev_l) * 100
        return SMTSignal("bullish", a1_cur_l, a2_cur_l, detected_at,
                         f"Lower Low vs Higher Low | Div: {pct:.2f}%"), "bullish_divergence"

    if (a1_cur_h > a1_prev_h and a2_cur_h > a2_prev_h) or \
       (a1_cur_l < a1_prev_l and a2_cur_l < a2_prev_l):
        return None, "aligned_move"

    return None, "no_divergence"


# ══════════════════════════════════════════════════════════════
#  STAGE 3 — Time Filter + Judas
# ══════════════════════════════════════════════════════════════

def stage3_time_filter(df_exec, bias):
    et_zone = pytz.timezone("US/Eastern")

    last_ts = df_exec.index[-1]
    if last_ts.tzinfo is None:
        last_ts = last_ts.tz_localize("UTC")
    last_et   = last_ts.astimezone(et_zone)
    last_time = last_et.time()

    in_zone   = False
    zone_name = "outside_killzone"
    for name, (h1, m1, h2, m2) in KILLZONES.items():
        if time(h1, m1) <= last_time <= time(h2, m2):
            in_zone   = True
            zone_name = name
            break

    judas_detected  = False
    judas_direction = "none"
    judas_candles   = []
    for i in range(len(df_exec)):
        ts = df_exec.index[i]
        if ts.tzinfo is None: ts = ts.tz_localize("UTC")
        t_et = ts.astimezone(et_zone).time()
        if time(7, 0) <= t_et <= time(7, JUDAS_WINDOW_MIN):
            judas_candles.append(i)

    if judas_candles:
        open_p  = float(df_exec.iloc[judas_candles[0]]["Open"])
        close_p = float(df_exec.iloc[judas_candles[-1]]["Close"])
        move    = "up" if close_p > open_p else "down"
        if (bias=="long" and move=="down") or (bias=="short" and move=="up"):
            judas_detected  = True
            judas_direction = move

    score = 0
    if in_zone:
        score = 3 if zone_name=="silver_bullet" else 2
    if judas_detected:
        score = max(0, score - 1)

    return TimeContext(in_zone, zone_name, judas_detected, judas_direction, score)


# ══════════════════════════════════════════════════════════════
#  STAGE 4 — Fractal Drill-Down
# ══════════════════════════════════════════════════════════════

def stage4_fractal_drill(df_h1, df_m15, df_m5, bias):
    swings_h1 = detect_swings(df_h1, lookback=SWING_LB, n=60)
    sweep = _find_latest_sweep(df_h1, swings_h1, bias)

    if not sweep:
        return None, None, None, 0

    mss = _find_mss(df_m15, sweep, bias)
    if not mss:
        return sweep, None, None, 1

    fvg = _find_fvg(df_m5, mss, bias)
    if not fvg:
        return sweep, mss, None, 2

    score = 2 if fvg.filled else 3
    return sweep, mss, fvg, score

def _find_latest_sweep(df, swings, bias, min_wick=None):
    if min_wick is None: min_wick = SWEEP_WICK_MIN
    sl = df.iloc[-80:].copy().reset_index()
    sweeps = []
    def _ts(row):
        for c in ["Datetime","Date"]:
            if c in row.index: return pd.Timestamp(row[c])
        return sl.index[0]
    for i in range(1, len(sl)):
        row = sl.iloc[i]
        ch,cl,co,cc = float(row["High"]),float(row["Low"]),float(row["Open"]),float(row["Close"])
        rng = max(ch-cl, 0.0001)
        for sw in swings:
            if sw.index >= i: continue
            if sw.kind=="high" and ch>sw.price and cc<sw.price:
                w=(ch-max(co,cc))/rng*100
                if w>=min_wick: sweeps.append(LiqSweep("buyside",sw.price,_ts(row),i,cc,w))
            elif sw.kind=="low" and cl<sw.price and cc>sw.price:
                w=(min(co,cc)-cl)/rng*100
                if w>=min_wick: sweeps.append(LiqSweep("sellside",sw.price,_ts(row),i,cc,w))
    if not sweeps: return None
    relevant = [s for s in sweeps if
                (bias=="long" and s.direction=="sellside") or
                (bias=="short" and s.direction=="buyside")]
    if not relevant: relevant = sweeps
    return sorted(relevant, key=lambda x: x.swept_idx, reverse=True)[0]

def _find_mss(df, sweep, bias, lf=None):
    if lf is None: lf = MSS_LOOKFORWARD
    win = df.iloc[-50:]
    if win.empty: return None
    if bias=="long":
        lh = float(win["High"].iloc[0])
        for i in range(1, min(lf, len(win))):
            if float(win["Close"].iloc[i]) > lh:
                return StructureBreak("MSS","bullish",lh,win.index[i],i)
            lh = max(lh, float(win["High"].iloc[i]))
    else:
        ll = float(win["Low"].iloc[0])
        for i in range(1, min(lf, len(win))):
            if float(win["Close"].iloc[i]) < ll:
                return StructureBreak("MSS","bearish",ll,win.index[i],i)
            ll = min(ll, float(win["Low"].iloc[i]))
    return None

def _find_fvg(df, mss, bias, lb=None):
    if lb is None: lb = FVG_LOOKBACK
    win = df.iloc[-30:]
    if len(win) < 3: return None
    best, bs = None, 0.0
    for i in range(2, len(win)):
        c1,c3 = win.iloc[i-2], win.iloc[i]
        if mss.direction=="bullish":
            gb,gt = float(c1["High"]),float(c3["Low"])
            if gt>gb:
                sz=(gt-gb)/gb*100
                if sz>bs: bs=sz; best=FVG("bullish",gt,gb,(gt+gb)/2,win.index[i],i,round(sz,3))
        else:
            gt,gb = float(c1["Low"]),float(c3["High"])
            if gt>gb:
                sz=(gt-gb)/gb*100
                if sz>bs: bs=sz; best=FVG("bearish",gt,gb,(gt+gb)/2,win.index[i],i,round(sz,3))
    if best:
        for _,row in df.iloc[-10:].iterrows():
            if best.direction=="bullish" and float(row["Low"])<=best.bottom: best.filled=True; break
            if best.direction=="bearish" and float(row["High"])>=best.top:   best.filled=True; break
    return best


# ══════════════════════════════════════════════════════════════
#  STAGE 5 — PD Arrays + StdDev
# ══════════════════════════════════════════════════════════════

PD_PRIORITY = {"breaker":1,"ob":2,"fvg":3,"sibi":4,"equilibrium":5}

def stage5_pd_arrays_and_stddev(df_htf, df_exec, swings, sweep, mss, fvg, bias):
    current = float(df_exec["Close"].iloc[-1])
    pds = []

    for i in range(3, len(df_exec)-1):
        row  = df_exec.iloc[i]
        prev = df_exec.iloc[i-1]
        c,o   = float(row["Close"]),float(row["Open"])
        pc,po = float(prev["Close"]),float(prev["Open"])
        if bias=="long" and c<o and pc>po and pc>c*1.004:
            pds.append(PDArray("ob","bullish",float(row["High"]),float(row["Low"]),
                               (float(row["High"])+float(row["Low"]))/2,
                               df_exec.index[i],2,EXEC_INTERVAL))
        elif bias=="short" and c>o and pc<po and pc<c*0.996:
            pds.append(PDArray("ob","bearish",float(row["High"]),float(row["Low"]),
                               (float(row["High"])+float(row["Low"]))/2,
                               df_exec.index[i],2,EXEC_INTERVAL))

    for pd_ in pds[:]:
        if pd_.kind=="ob":
            later = df_exec[df_exec.index > pd_.formed_at]
            if not later.empty:
                if pd_.direction=="bullish" and float(later["Low"].min())<pd_.bottom:
                    pd_.kind="breaker"; pd_.priority=1
                elif pd_.direction=="bearish" and float(later["High"].max())>pd_.top:
                    pd_.kind="breaker"; pd_.priority=1

    if fvg and not fvg.filled:
        pds.append(PDArray("fvg",fvg.direction,fvg.top,fvg.bottom,fvg.midpoint,
                           fvg.formed_at,3,ENTRY_INTERVAL))

    htf_h = float(df_htf["High"].iloc[-50:].max())
    htf_l = float(df_htf["Low"].iloc[-50:].min())
    eq    = (htf_h+htf_l)/2
    pds.append(PDArray("equilibrium",bias,eq*1.001,eq*0.999,eq,
                       df_htf.index[-1],5,HTF_INTERVAL))

    valid = [p for p in pds if
             (bias=="long"  and p.direction in ["bullish","long"]  and p.top<current) or
             (bias=="short" and p.direction in ["bearish","short"] and p.bottom>current)]
    if not valid: valid = pds

    valid.sort(key=lambda x: (x.priority, abs(x.midpoint-current)))
    best_pd = valid[0] if valid else None

    recent = df_exec.iloc[-20:]
    mh, ml = float(recent["High"].max()), float(recent["Low"].min())
    rng    = mh - ml

    label_map = {0.5:"EQ (50%)",1.0:"TP1 +1σ",2.0:"TP2 +2σ (BSL/SSL)",4.0:"TP3 +4σ"}
    targets = []
    for lvl in STDDEV_LEVELS:
        price = ml + rng*lvl if bias=="long" else mh - rng*lvl
        targets.append(StdDevTarget(lvl, round(price,4),
                                    label_map.get(lvl,f"+{lvl}σ"), lvl>=1.0))

    score_map = {"breaker":2,"ob":2,"fvg":1,"sibi":1,"equilibrium":1}
    pd_score  = score_map.get(best_pd.kind,1) if best_pd else 0

    return best_pd, targets, pd_score


# ══════════════════════════════════════════════════════════════
#  STAGE 6 — Confidence Gate
# ══════════════════════════════════════════════════════════════

def stage6_confidence_gate(dol, smt, smt_status, time_ctx,
                            fractal_score, sweep, mss, fvg,
                            pd_array, pd_score, targets,
                            df_exec, bias, ticker, smt_ticker=""):
    logs   = []
    total  = 0
    current = float(df_exec["Close"].iloc[-1])

    # Stage 1
    dol_score = 2 if dol else 0
    total += dol_score
    if dol:
        dist = abs(dol.price-current)/current*100
        logs.append(DecisionLog(
            "Stage 1 — DOL",
            f"{dol.kind} @ {dol.price:.4f} ({dol.touches} touches)",
            dol_score,
            f"Price {current:.4f} is {dist:.1f}% from DOL. "
            f"Bias locked: {'Long' if bias=='long' else 'Short'}.",
            f"If price doesn't reach {dol.price:.4f}, DOL may be wrong."
        ))
    else:
        logs.append(DecisionLog("Stage 1 — DOL","No clear DOL",0,
                                "HTF bias based on range position only.",
                                "Weaker signal without explicit DOL."))

    # Stage 2
    if smt:
        smt_score = 2 if ((smt.direction=="bullish" and bias=="long") or
                          (smt.direction=="bearish" and bias=="short")) else -1
        smt_tag = ("⚡ DIVERGENCE DETECTED" if smt_score==2
                   else "⚠️ SMT contradicts bias")
    elif smt_status=="aligned_move":
        smt_score = 1
        smt_tag   = "✓ Assets aligned (partial confirm)"
    else:
        smt_score = 0
        smt_tag   = "○ No SMT divergence"
    total += smt_score
    logs.append(DecisionLog(
        "Stage 2 — SMT",
        smt_tag,
        smt_score,
        smt.description if smt else f"Relationship with {smt_ticker}: {smt_status}",
        "SMT is not a guarantee. Must combine with Fractal."
    ))

    # Stage 3
    total += time_ctx.score
    judas_note = ""
    if time_ctx.judas_detected:
        judas_note = (f"MANIPULATIVE MOVE: {time_ctx.judas_direction} "
                      f"against bias in first {JUDAS_WINDOW_MIN}min. Wait for reversal.")
    zone_names = {
        "london_open":"London Open","ny_open":"NY Open",
        "silver_bullet":"Silver Bullet (highest accuracy)",
        "london_close":"London Close","outside_killzone":"Outside all Killzones",
    }
    logs.append(DecisionLog(
        "Stage 3 — Time",
        zone_names.get(time_ctx.zone_name, time_ctx.zone_name),
        time_ctx.score,
        "Inside Killzone — valid for trading." if time_ctx.in_killzone
        else "Outside Killzone — any pattern here is noise.",
        judas_note or "No Judas Swing detected."
    ))

    # Stage 4
    total += fractal_score
    parts = []
    if sweep: parts.append(f"Sweep({sweep.direction}@{sweep.swept_price:.2f})")
    if mss:   parts.append(f"MSS({mss.direction}@{mss.break_price:.2f})")
    if fvg:   parts.append(f"FVG({'active' if not fvg.filled else 'filled'})")
    logs.append(DecisionLog(
        "Stage 4 — Fractal",
        " → ".join(parts) if parts else "No fractal chain",
        fractal_score,
        f"Chain {'complete ✅' if fractal_score>=3 else 'partial ⚠️' if fractal_score>0 else 'missing ❌'}. "
        "Full chain requires: H1 Sweep + M15 MSS + M5 FVG.",
        "FVG filled — entry less precise." if (fvg and fvg.filled) else
        "FVG active — ideal entry point." if fvg else
        "No FVG — entry from OB or EQ."
    ))

    # Stage 5
    total += pd_score
    if pd_array:
        pd_names = {1:"Breaker Block",2:"Order Block",3:"Fair Value Gap",
                    4:"SIBI/BISI",5:"Equilibrium"}
        logs.append(DecisionLog(
            "Stage 5 — PD Arrays",
            f"{pd_names.get(pd_array.priority,pd_array.kind)} [{pd_array.bottom:.4f}–{pd_array.top:.4f}]",
            pd_score,
            f"Highest priority zone available: priority {pd_array.priority}/5. "
            f"Entry at midpoint: {pd_array.midpoint:.4f}.",
            {1:"Breaker: if price breaks it again, trend has changed.",
             2:"OB: risk of re-break if HTF bias is opposing.",
             3:"FVG: may fill before true reversal.",
             4:"SIBI: weaker confirmation needed.",
             5:"EQ: weakest zone. Requires strong other confirmations."
             }.get(pd_array.priority,"")
        ))

    # Judas penalty
    if time_ctx.judas_detected:
        total = max(0, total - 2)
        logs.append(DecisionLog("Judas Penalty","-2 points applied",-2,
                                "Manipulative opening move against DOL bias.",
                                "Do NOT enter. Wait for full candle reversal above/below open."))

    # Grade
    grade = ("A+" if total>=SCORE_A_PLUS else
             "A"  if total>=SCORE_A else
             "B"  if total>=SCORE_MIN else "SKIP")

    if grade=="SKIP":
        return None

    # Entry / SL
    if pd_array and not fvg: entry = pd_array.midpoint
    elif fvg and not fvg.filled: entry = fvg.midpoint
    elif mss: entry = mss.break_price
    else: entry = current

    buf = entry * 0.003
    sl = round(sweep.swept_price - buf, 4) if (bias=="long" and sweep) else \
         round(sweep.swept_price + buf, 4) if (bias=="short" and sweep) else \
         round(entry * 0.985 if bias=="long" else entry * 1.015, 4)

    risk_notes = [l.risk_note for l in logs if l.risk_note]

    return TradeSetup(
        ticker=ticker, bias=bias,
        entry=round(entry,4), stop_loss=sl,
        targets=targets, pd_array=pd_array,
        score=total, grade=grade,
        decision_log=logs,
        dol=dol, smt=smt, sweep=sweep,
        mss=mss, fvg_entry=fvg,
        time_ctx=time_ctx,
        risk_summary=" | ".join(r for r in risk_notes if r)
    )


# ══════════════════════════════════════════════════════════════
#  MASTER ENGINE
# ══════════════════════════════════════════════════════════════

def run_engine(ticker, smt_ticker,
               htf_interval=None, exec_interval=None,
               entry_interval=None, htf_period=None, exec_period=None):
    """
    Run the full 6-stage ICT Market Maker engine.
    Returns (TradeSetup|None, df_htf, df_exec, df_m5, liq_levels, swings_htf, dol)
    """
    _htf  = htf_interval  or HTF_INTERVAL
    _exec = exec_interval or EXEC_INTERVAL
    _ent  = entry_interval or ENTRY_INTERVAL
    _hp   = htf_period    or HTF_PERIOD
    _ep   = exec_period   or EXEC_PERIOD

    df_htf  = fetch(ticker, _hp,  _htf)
    df_exec = fetch(ticker, _ep,  _exec)
    df_m5   = fetch(ticker, "2d", _ent)
    df_smt  = fetch(smt_ticker, _hp, _htf)

    swings_htf = detect_swings(df_htf, SWING_LB, HTF_CANDLES)

    liq_levels, dol, bias = stage1_draw_on_liquidity(df_htf, swings_htf)
    smt_sig, smt_status   = stage2_smt_divergence(df_htf, df_smt, bias)
    time_ctx               = stage3_time_filter(df_exec, bias)
    sweep, mss, fvg, fscore = stage4_fractal_drill(df_exec, df_exec, df_m5, bias)
    pd_arr, targets, pd_sc = stage5_pd_arrays_and_stddev(
        df_htf, df_exec, swings_htf, sweep, mss, fvg, bias)

    setup = stage6_confidence_gate(
        dol, smt_sig, smt_status, time_ctx,
        fscore, sweep, mss, fvg,
        pd_arr, pd_sc, targets,
        df_exec, bias, ticker, smt_ticker
    )

    return setup, df_htf, df_exec, df_m5, liq_levels, swings_htf, dol


# ══════════════════════════════════════════════════════════════
#  CHART BUILDER
# ══════════════════════════════════════════════════════════════

def build_chart(df_plot, setup, liq_levels, swings, dol,
                ticker="", n_candles=80, htf_interval="1d"):
    """Build full ICT Plotly chart. TZ-safe, each element in try/except."""
    df_plot = df_plot.copy()
    df_plot.index = naive_index(df_plot.index)
    df = df_plot.iloc[-n_candles:].copy()
    x0 = to_naive(df.index[0])
    x1 = to_naive(df.index[-1])

    fig = make_subplots(
        rows=2, cols=1, row_heights=[0.80, 0.20],
        shared_xaxes=True, vertical_spacing=0.02,
    )

    # Candlesticks
    try:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"],   close=df["Close"],
            increasing=dict(line=dict(color="#26a69a",width=1),
                            fillcolor="rgba(38,166,154,0.8)"),
            decreasing=dict(line=dict(color="#ef5350",width=1),
                            fillcolor="rgba(239,83,80,0.8)"),
            name="OHLC", showlegend=False,
        ), row=1, col=1)
    except Exception: pass

    # Volume
    try:
        vc = ["rgba(38,166,154,0.3)" if c>=o else "rgba(239,83,80,0.3)"
              for c,o in zip(df["Close"],df["Open"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
                             marker_color=vc, showlegend=False), row=2, col=1)
    except Exception: pass

    # Liquidity lines
    for lv in liq_levels:
        try:
            if lv.price < float(df["Low"].min())*0.97: continue
            if lv.price > float(df["High"].max())*1.03: continue
            is_dol = lv.is_dol
            color = ("#ff6b6b" if lv.kind=="BSL" else "#51cf66") if is_dol else \
                    ("rgba(255,100,100,0.45)" if lv.kind=="BSL" else "rgba(80,200,100,0.45)")
            w = 2.0 if is_dol else 0.8
            d = "solid" if is_dol else "dot"
            label = (f"◆ DOL-{lv.kind} {lv.price:.2f}({lv.touches}x)" if is_dol
                     else f"{lv.kind} {lv.price:.2f}")
            fig.add_shape(type="line", x0=x0,y0=lv.price,x1=x1,y1=lv.price,
                          line=dict(color=color,width=w,dash=d), row=1, col=1)
            if is_dol or lv.touches>=3:
                fig.add_annotation(x=x1, y=lv.price, text=f"  {label}",
                                   xanchor="left", showarrow=False,
                                   font=dict(size=9,color=color,family="monospace"),
                                   bgcolor="rgba(13,17,23,0.8)",
                                   bordercolor=color, borderwidth=1, borderpad=3,
                                   row=1, col=1)
        except Exception: pass

    # Swing points
    try:
        sh = [s for s in swings if s.kind=="high"
              and to_naive(s.timestamp) is not None
              and to_naive(s.timestamp) >= x0]
        sl_pts = [s for s in swings if s.kind=="low"
                  and to_naive(s.timestamp) is not None
                  and to_naive(s.timestamp) >= x0]
        if sh:
            fig.add_trace(go.Scatter(
                x=[to_naive(s.timestamp) for s in sh],
                y=[s.price*1.002 for s in sh], mode="markers",
                marker=dict(symbol="triangle-down",size=9,color="rgba(239,83,80,0.85)"),
                name="SH", hovertemplate="SH: %{y:.4f}<extra></extra>"), row=1, col=1)
        if sl_pts:
            fig.add_trace(go.Scatter(
                x=[to_naive(s.timestamp) for s in sl_pts],
                y=[s.price*0.998 for s in sl_pts], mode="markers",
                marker=dict(symbol="triangle-up",size=9,color="rgba(38,166,154,0.85)"),
                name="SL", hovertemplate="SL: %{y:.4f}<extra></extra>"), row=1, col=1)
    except Exception: pass

    if setup:
        sl_dist = abs(setup.entry - setup.stop_loss)

        def add_level(price, color, dash, label, width=1.8):
            try:
                fig.add_shape(type="line", x0=x0,y0=price,x1=x1,y1=price,
                              line=dict(color=color,width=width,dash=dash), row=1, col=1)
                fig.add_annotation(x=x1, y=price,
                                   text=f"  ◀ {label}: {price:.4f}",
                                   xanchor="left", showarrow=False,
                                   font=dict(size=10,color=color,family="monospace"),
                                   bgcolor="rgba(13,17,23,0.85)",
                                   bordercolor=color, borderwidth=1, borderpad=4,
                                   row=1, col=1)
            except Exception: pass

        add_level(setup.entry,     "#00b4d8","solid","ENTRY",2.2)
        add_level(setup.stop_loss, "#ef5350","dot",  "SL",  1.5)
        tp_c = ["#26a69a","#4caf50","#8bc34a"]
        for i,t in enumerate([t for t in setup.targets if t.is_tp][:3]):
            add_level(t.price, tp_c[i],"dash",f"TP{i+1}(+{t.level}σ)",1.5)

        # FVG box
        try:
            if setup.fvg_entry:
                fvg = setup.fvg_entry
                fill   = "rgba(0,180,216,0.07)" if not fvg.filled else "rgba(100,100,100,0.05)"
                border = "rgba(0,180,216,0.4)"  if not fvg.filled else "rgba(100,100,100,0.3)"
                fn = to_naive(fvg.formed_at)
                fx0 = fn if (fn is not None and fn >= x0) else x0
                fig.add_shape(type="rect", x0=fx0,y0=fvg.bottom,x1=x1,y1=fvg.top,
                              fillcolor=fill, line=dict(color=border,width=1), row=1, col=1)
                fig.add_annotation(x=fx0, y=(fvg.top+fvg.bottom)/2,
                                   text=f"  FVG {'✅' if not fvg.filled else '⚠️'}",
                                   xanchor="left", showarrow=False,
                                   font=dict(size=9,color="#00b4d8",family="monospace"),
                                   bgcolor="rgba(13,17,23,0.7)", row=1, col=1)
        except Exception: pass

        # Sweep arrow
        try:
            if setup.sweep:
                sw = setup.sweep
                sn = to_naive(sw.swept_at)
                if sn is not None:
                    sx = sn if sn >= x0 else x0
                    sc = "#ef5350" if sw.direction=="buyside" else "#26a69a"
                    say = -40 if sw.direction=="buyside" else 40
                    fig.add_annotation(
                        x=sx, y=sw.swept_price, ax=0, ay=say,
                        arrowhead=2, arrowcolor=sc, arrowsize=1.2, arrowwidth=2,
                        text=f"{'⬇' if sw.direction=='buyside' else '⬆'} Sweep",
                        font=dict(size=9,color=sc,family="monospace"),
                        bgcolor="rgba(13,17,23,0.8)",
                        bordercolor=sc, borderwidth=1, borderpad=3, row=1, col=1)
        except Exception: pass

        # Badge
        try:
            gs = {"A+":"⭐⭐⭐","A":"⭐⭐","B":"⭐"}.get(setup.grade,"")
            bs = "🔺 LONG" if setup.bias=="long" else "🔻 SHORT"
            rr = "—"
            if len(setup.targets)>1 and sl_dist>0:
                rr = round(abs(setup.targets[1].price-setup.entry)/sl_dist,1)
            fig.add_annotation(
                x=df.index[min(4,len(df)-1)],
                y=float(df["High"].max())*0.995,
                text=f"<b>{bs}</b><br>Grade: {setup.grade} {gs}<br>Score: {setup.score}/13<br>R:R ≈ {rr}",
                showarrow=False, align="left",
                font=dict(size=11,color="#e8eaed",family="monospace"),
                bgcolor="rgba(13,17,23,0.88)",
                bordercolor="#2a4060", borderwidth=1, borderpad=8, row=1, col=1)
        except Exception: pass

    grade_str = f" | GRADE {setup.grade} | Score {setup.score}/13" if setup else ""
    fig.update_layout(
        height=640, template="plotly_dark",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(family="monospace",color="#8b949e",size=11),
        margin=dict(l=10,r=160,t=50,b=10),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        title=dict(
            text=f"<b>{ticker.upper()}</b> — ICT Market Maker{grade_str}  |  {htf_interval}",
            font=dict(size=13,color="#58a6ff",family="monospace"), x=0.01),
        hoverlabel=dict(bgcolor="#161b22",font=dict(family="monospace",size=11)),
        legend=dict(orientation="h",x=0,y=1.02,bgcolor="rgba(0,0,0,0)",font=dict(size=10)),
    )
    for row in [1,2]:
        fig.update_xaxes(gridcolor="#21262d",showgrid=True,
                         tickfont=dict(size=10,color="#484f58"),
                         zerolinecolor="#21262d",row=row,col=1)
        fig.update_yaxes(gridcolor="#21262d",showgrid=True,
                         tickfont=dict(size=10,color="#484f58"),
                         side="right",row=row,col=1)
    return fig


# ══════════════════════════════════════════════════════════════
#  SAFE EXTRACTION HELPERS  (for batch scan table)
# ══════════════════════════════════════════════════════════════

def safe_price(val, dec=4):
    try: return "—" if val is None else round(float(val),dec)
    except Exception: return "—"

def extract_row(setup, ticker, smt_ticker):
    """Turn a TradeSetup into a flat dict for the radar table."""
    if setup is None:
        return {"Ticker":ticker,"SMT":smt_ticker,"Grade":"SKIP","Score":"<5",
                "Bias":"—","Entry":"—","SL":"—","TP1":"—","TP2":"—",
                "Potential R:R":"—","DOL":"—","SMT Signal":"—",
                "Fractal":"—","Killzone":"—","PD Array":"—",
                "_score_num":0,"_grade_rank":99}
    tps   = [t for t in setup.targets if t.is_tp]
    tp1_v = safe_price(tps[0].price) if len(tps)>=1 else "—"
    tp2_v = safe_price(tps[1].price) if len(tps)>=2 else "—"
    rr_v  = "—"
    try:
        e,sl = float(setup.entry), float(setup.stop_loss)
        tp2  = float(tps[1].price) if len(tps)>=2 else float(tps[0].price) if tps else None
        if tp2 and abs(e-sl)>0:
            rr_v = f"1:{round(abs(tp2-e)/abs(e-sl),1)}"
    except Exception: pass

    fractal = ("H1+M15+M5" if (setup.sweep and setup.mss and setup.fvg_entry) else
               "H1+M15"    if (setup.sweep and setup.mss) else
               "H1 only"   if setup.sweep else "none")
    kz = "—"
    try:
        if setup.time_ctx:
            kz = (setup.time_ctx.zone_name if setup.time_ctx.in_killzone
                  else "outside")
    except Exception: pass
    pd_n = "—"
    try:
        if setup.pd_array:
            pd_n = {1:"Breaker⚡",2:"OB",3:"FVG",4:"SIBI",5:"EQ"}.get(
                setup.pd_array.priority, setup.pd_array.kind)
    except Exception: pass
    smt_sig = "—"
    try:
        if setup.smt:
            smt_sig = "Bearish Div" if setup.smt.direction=="bearish" else "Bullish Div"
    except Exception: pass

    return {
        "Ticker":       ticker,
        "SMT":          smt_ticker,
        "Grade":        setup.grade,
        "Score":        f"{setup.score}/13",
        "Bias":         "Long" if setup.bias=="long" else "Short",
        "Entry":        safe_price(setup.entry),
        "SL":           safe_price(setup.stop_loss),
        "TP1":          tp1_v,
        "TP2":          tp2_v,
        "Potential R:R":rr_v,
        "DOL":          safe_price(setup.dol.price) if setup.dol else "—",
        "SMT Signal":   smt_sig,
        "Fractal":      fractal,
        "Killzone":     kz,
        "PD Array":     pd_n,
        "_score_num":   setup.score,
        "_grade_rank":  {"A+":1,"A":2,"B":3,"C":4}.get(setup.grade,99),
    }
