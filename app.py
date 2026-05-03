"""
╔══════════════════════════════════════════════════════════════╗
║     ICT SMART MONEY DASHBOARD — لوحة تحكم المحرك الكامل    ║
║     Streamlit + Plotly + AgGrid                              ║
╚══════════════════════════════════════════════════════════════╝

التشغيل:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import json
import warnings
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ICT Smart Money Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
#  CUSTOM CSS — Dark Terminal Aesthetic
# ══════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap');

:root {
    --bg-primary:    #0a0e14;
    --bg-secondary:  #0f1520;
    --bg-card:       #131c2a;
    --bg-hover:      #1a2535;
    --accent-cyan:   #00d4ff;
    --accent-green:  #00ff9d;
    --accent-red:    #ff4d6a;
    --accent-gold:   #ffd166;
    --accent-purple: #9d72ff;
    --text-primary:  #e8f0fe;
    --text-muted:    #5a7090;
    --border:        #1e2d42;
    --border-bright: #2a4060;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans Arabic', 'IBM Plex Mono', monospace;
    background: var(--bg-primary);
    color: var(--text-primary);
    direction: rtl;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-left: 1px solid var(--border-bright);
}
[data-testid="stSidebar"] * { font-family: 'IBM Plex Mono', monospace !important; }

/* ── Main header ── */
.dashboard-header {
    background: linear-gradient(135deg, #0a0e14 0%, #0d1928 50%, #0a0e14 100%);
    border: 1px solid var(--border-bright);
    border-radius: 8px;
    padding: 16px 24px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.dashboard-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple), var(--accent-green));
}
.header-title {
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--accent-cyan);
    letter-spacing: 2px;
    font-family: 'IBM Plex Mono', monospace;
    margin: 0;
}
.header-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    letter-spacing: 1px;
    margin: 4px 0 0 0;
}

/* ── Metric cards ── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    position: relative;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: var(--border-bright); }
.metric-label {
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 1.4rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    margin: 0;
}
.metric-green { color: var(--accent-green); }
.metric-red   { color: var(--accent-red);   }
.metric-cyan  { color: var(--accent-cyan);  }
.metric-gold  { color: var(--accent-gold);  }

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 14px;
}
.section-title {
    font-size: 0.8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent-cyan);
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 500;
}

/* ── Trade detail panel ── */
.trade-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    height: 100%;
}
.trade-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.82rem;
}
.trade-row:last-child { border-bottom: none; }
.trade-key   { color: var(--text-muted); font-family: 'IBM Plex Mono'; font-size: 0.72rem; letter-spacing: 1px; }
.trade-val   { color: var(--text-primary); font-family: 'IBM Plex Mono'; font-weight: 500; }
.badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 1px;
    font-family: 'IBM Plex Mono';
}
.badge-aplus  { background: rgba(0,255,157,0.15); color: var(--accent-green); border: 1px solid rgba(0,255,157,0.3); }
.badge-a      { background: rgba(0,212,255,0.15); color: var(--accent-cyan);  border: 1px solid rgba(0,212,255,0.3); }
.badge-b      { background: rgba(255,209,102,0.15); color: var(--accent-gold); border: 1px solid rgba(255,209,102,0.3); }
.badge-c      { background: rgba(255,77,106,0.15);  color: var(--accent-red);  border: 1px solid rgba(255,77,106,0.3);  }
.badge-long   { background: rgba(0,255,157,0.1);  color: var(--accent-green); border: 1px solid rgba(0,255,157,0.25); }
.badge-short  { background: rgba(255,77,106,0.1); color: var(--accent-red);   border: 1px solid rgba(255,77,106,0.25); }
.badge-pending  { background: rgba(255,209,102,0.1); color: var(--accent-gold); border: 1px solid rgba(255,209,102,0.25); }
.badge-active   { background: rgba(0,212,255,0.1); color: var(--accent-cyan);   border: 1px solid rgba(0,212,255,0.25); }
.badge-tp       { background: rgba(0,255,157,0.1); color: var(--accent-green);  border: 1px solid rgba(0,255,157,0.25); }
.badge-sl       { background: rgba(255,77,106,0.1); color: var(--accent-red);   border: 1px solid rgba(255,77,106,0.25); }

/* ── PnL display ── */
.pnl-block {
    background: var(--bg-secondary);
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 8px;
    font-family: 'IBM Plex Mono', monospace;
}
.pnl-title { font-size: 0.65rem; color: var(--text-muted); letter-spacing: 1.5px; text-transform: uppercase; }
.pnl-value { font-size: 1.1rem; font-weight: 600; margin-top: 2px; }
.pnl-pos { color: var(--accent-green); }
.pnl-neg { color: var(--accent-red); }

/* ── Streamlit overrides ── */
.stButton button {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-bright) !important;
    color: var(--text-primary) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    border-radius: 4px !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
}
.stSelectbox label, .stTextInput label, .stNumberInput label,
.stSlider label, .stRadio label, .stCheckbox label {
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
    letter-spacing: 1px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    text-transform: uppercase !important;
}
div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.3rem !important;
}
.stAlert { border-radius: 6px !important; }
div[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  ICT ENGINE (مدمج — نفس كود المستشارين الثلاثة)
# ══════════════════════════════════════════════════════════════

@dataclass
class SwingPoint:
    index: int
    timestamp: pd.Timestamp
    price: float
    kind: str
    confirmed: bool = False

@dataclass
class LiquiditySweep:
    direction: str
    swept_price: float
    swept_at: pd.Timestamp
    swept_candle_index: int
    close_after: float
    swing_origin: pd.Timestamp
    body_rejection: bool
    candle_wick_size: float
    strength: str = field(init=False)
    def __post_init__(self):
        if self.body_rejection and self.candle_wick_size > 40:   self.strength = "قوي جداً ⚡"
        elif self.body_rejection:                                 self.strength = "قوي ✅"
        elif self.candle_wick_size > 30:                         self.strength = "متوسط ⚠️"
        else:                                                     self.strength = "ضعيف ❌"

@dataclass
class FairValueGap:
    direction: str
    top: float
    bottom: float
    midpoint: float
    formed_at: pd.Timestamp
    candle_index: int
    size_pct: float
    filled: bool = False

@dataclass
class StructureBreak:
    kind: str
    direction: str
    break_price: float
    broke_at: pd.Timestamp
    candle_index: int
    confirmed: bool = True

@dataclass
class TradeSetup:
    sweep: LiquiditySweep
    structure_break: Optional[StructureBreak]
    fvg: Optional[FairValueGap]
    bias: str
    zone: str
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    rr_ratio: float
    confidence: str
    notes: str = ""


@st.cache_data(ttl=300)
def fetch_ohlc(ticker, period="6mo", interval="1d"):
    data = yf.download(ticker, period=period, interval=interval,
                       auto_adjust=True, progress=False)
    if data.empty:
        return None
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    data = data[["Open", "High", "Low", "Close", "Volume"]].copy()
    data.dropna(inplace=True)
    return data

@st.cache_data(ttl=60)
def fetch_current_price(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1d", interval="1m")
        if hist.empty:
            hist = t.history(period="2d")
        return float(hist["Close"].iloc[-1]) if not hist.empty else None
    except:
        return None


def detect_swing_points(df, lookback=5, candles=100):
    df_s = df.iloc[-candles:].copy().reset_index()
    swings = []
    def _ts(df_s, i):
        for col in ["Datetime","Date"]:
            if col in df_s.columns: return pd.Timestamp(df_s[col].iloc[i])
        return df_s.index[i] if i < len(df_s.index) else pd.Timestamp.now()
    for i in range(lookback, len(df_s)-lookback):
        wh = df_s["High"].iloc[i-lookback:i+lookback+1]
        wl = df_s["Low"].iloc[i-lookback:i+lookback+1]
        if df_s["High"].iloc[i] == wh.max():
            swings.append(SwingPoint(i, _ts(df_s,i), float(df_s["High"].iloc[i]), "high", True))
        if df_s["Low"].iloc[i] == wl.min():
            swings.append(SwingPoint(i, _ts(df_s,i), float(df_s["Low"].iloc[i]), "low", True))
    return _dedup(swings, lookback)

def _dedup(swings, window):
    def keep(pts, mode):
        if not pts: return []
        res, grp = [], [pts[0]]
        for p in pts[1:]:
            if abs(p.index-grp[-1].index) <= window: grp.append(p)
            else:
                res.append(max(grp,key=lambda x:x.price) if mode=="high" else min(grp,key=lambda x:x.price))
                grp = [p]
        res.append(max(grp,key=lambda x:x.price) if mode=="high" else min(grp,key=lambda x:x.price))
        return res
    h = keep([s for s in swings if s.kind=="high"],"high")
    l = keep([s for s in swings if s.kind=="low"],"low")
    return sorted(h+l, key=lambda x:x.index)

def detect_sweeps(df, swings, candles=100, min_wick=15.0):
    df_s = df.iloc[-candles:].copy().reset_index()
    sweeps = []
    def _ts(row,i):
        for col in ["Datetime","Date"]:
            if col in row.index: return pd.Timestamp(row[col])
        return df_s.index[i] if i < len(df_s.index) else pd.Timestamp.now()
    for i in range(1, len(df_s)):
        row = df_s.iloc[i]
        ch,cl,co,cc = float(row["High"]),float(row["Low"]),float(row["Open"]),float(row["Close"])
        rng = max(ch-cl,0.0001)
        ct = _ts(row,i)
        for sw in swings:
            if sw.index >= i: continue
            if sw.kind=="high" and ch>sw.price and cc<sw.price:
                w=(ch-max(co,cc))/rng*100
                if w>=min_wick: sweeps.append(LiquiditySweep("buyside",sw.price,ct,i,cc,sw.timestamp,True,w))
            elif sw.kind=="low" and cl<sw.price and cc>sw.price:
                w=(min(co,cc)-cl)/rng*100
                if w>=min_wick: sweeps.append(LiquiditySweep("sellside",sw.price,ct,i,cc,sw.timestamp,True,w))
    return sorted(sweeps,key=lambda x:x.swept_candle_index,reverse=True)[:10]

def detect_structure_break(df, sweep, lookforward=15):
    si = sweep.swept_candle_index
    win = df.iloc[si:min(si+lookforward,len(df))]
    if win.empty: return None
    if sweep.direction=="buyside":
        ll = float(win["Low"].iloc[0])
        for i in range(1,len(win)):
            if float(win["Close"].iloc[i]) < ll:
                return StructureBreak("MSS","bearish",ll,win.index[i],si+i)
            ll = min(ll, float(win["Low"].iloc[i]))
    else:
        lh = float(win["High"].iloc[0])
        for i in range(1,len(win)):
            if float(win["Close"].iloc[i]) > lh:
                return StructureBreak("MSS","bullish",lh,win.index[i],si+i)
            lh = max(lh, float(win["High"].iloc[i]))
    return None

def detect_fvg(df, structure, sweep, lookback=10):
    if structure is None: return None
    s,e = max(0,structure.candle_index-lookback), min(structure.candle_index+lookback,len(df))
    win = df.iloc[s:e]
    if len(win)<3: return None
    best, bs = None, 0.0
    for i in range(2,len(win)):
        c1,c3 = win.iloc[i-2], win.iloc[i]
        if structure.direction=="bullish":
            gb,gt = float(c1["High"]),float(c3["Low"])
            if gt>gb:
                sz=(gt-gb)/gb*100
                if sz>bs: bs=sz; best=FairValueGap("bullish",gt,gb,(gt+gb)/2,win.index[i],s+i,round(sz,3))
        else:
            gt,gb = float(c1["Low"]),float(c3["High"])
            if gt>gb:
                sz=(gt-gb)/gb*100
                if sz>bs: bs=sz; best=FairValueGap("bearish",gt,gb,(gt+gb)/2,win.index[i],s+i,round(sz,3))
    if best:
        for _,row in df.iloc[best.candle_index:].iterrows():
            if best.direction=="bullish" and float(row["Low"])<=best.bottom: best.filled=True; break
            if best.direction=="bearish" and float(row["High"])>=best.top:   best.filled=True; break
    return best

def classify_zone(price, df, candles=50):
    win = df.iloc[-candles:]
    rh,rl = float(win["High"].max()),float(win["Low"].min())
    eq = (rh+rl)/2; q = (rh-rl)/4
    if price >= eq+q: return "premium"
    if price <= eq-q: return "discount"
    return "equilibrium"

def confidence_score(sweep,structure,fvg,zone):
    s = 0
    if "قوي جداً" in sweep.strength: s+=3
    elif "قوي" in sweep.strength: s+=2
    elif "متوسط" in sweep.strength: s+=1
    if structure: s+=2
    if fvg and not fvg.filled: s+=2
    elif fvg: s+=1
    if sweep.direction=="sellside" and zone=="discount": s+=2
    elif sweep.direction=="buyside" and zone=="premium": s+=2
    return "A+" if s>=8 else "A" if s>=6 else "B" if s>=4 else "C"

def build_setup(sweep, structure, fvg, df, swings, rr=2.0):
    bias = "long" if sweep.direction=="sellside" else "short"
    entry = fvg.midpoint if (fvg and not fvg.filled) else (structure.break_price if structure else sweep.close_after)
    buf = entry*0.003
    sl = round(sweep.swept_price-buf,4) if bias=="long" else round(sweep.swept_price+buf,4)
    sld = abs(entry-sl)
    if sld==0: return None
    opp = [s for s in swings if (bias=="long" and s.kind=="high" and s.price>entry) or
                                  (bias=="short" and s.kind=="low" and s.price<entry)]
    tgts = sorted([s.price for s in opp]) if bias=="long" else sorted([s.price for s in opp],reverse=True)
    tp1 = round(tgts[0],4) if len(tgts)>=1 else round(entry+sld*rr,4)
    tp2 = round(tgts[1],4) if len(tgts)>=2 else round(entry+sld*rr*2,4)
    rr_r = round(abs(tp1-entry)/sld,2)
    zone = classify_zone(entry, df)
    conf = confidence_score(sweep,structure,fvg,zone)
    parts=[]
    if fvg and not fvg.filled: parts.append(f"FVG [{fvg.bottom:.4f}–{fvg.top:.4f}]")
    if structure: parts.append(f"{structure.kind} {structure.direction}")
    if fvg and fvg.filled: parts.append("FVG مملوء")
    return TradeSetup(sweep,structure,fvg,bias,zone,round(entry,4),sl,tp1,tp2,rr_r,conf," | ".join(parts) or "—")

@st.cache_data(ttl=120)
def run_engine(ticker, period, interval, swing_lb, candles, min_wick):
    df = fetch_ohlc(ticker, period, interval)
    if df is None: return None,None,None,None
    swings = detect_swing_points(df, swing_lb, candles)
    sweeps = detect_sweeps(df, swings, candles, min_wick)
    setups = []
    for sw in sweeps:
        sb  = detect_structure_break(df, sw)
        fvg = detect_fvg(df, sb, sw) if sb else None
        s   = build_setup(sw, sb, fvg, df, swings)
        if s: setups.append(s)
    return df, swings, sweeps, setups


# ══════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════

def init_state():
    defaults = {
        "watchlist": ["TSLA", "AAPL", "NVDA", "2222.SR", "EURUSD=X"],
        "active_ticker": "TSLA",
        "trade_log": pd.DataFrame(columns=[
            "id","ticker","اتجاه","جودة","منطقة","دخول","SL","TP1","TP2",
            "R:R","السعر_الحالي","PnL","PnL%","الحالة","ملاحظات","وقت_الإضافة"
        ]),
        "selected_setup_idx": 0,
        "advisor_status": {"advisor1": "idle", "advisor2": "idle", "advisor3": "idle"},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

CONFIDENCE_BADGE = {
    "A+": '<span class="badge badge-aplus">A+</span>',
    "A":  '<span class="badge badge-a">A</span>',
    "B":  '<span class="badge badge-b">B</span>',
    "C":  '<span class="badge badge-c">C</span>',
}

def get_status_badge(status):
    m = {"Pending":"badge-pending","Active":"badge-active","TP":"badge-tp","SL":"badge-sl"}
    return f'<span class="badge {m.get(status,"badge-pending")}">{status}</span>'

def calc_pnl(row, current_price):
    if pd.isna(current_price) or current_price == 0: return 0.0, 0.0
    entry = row["دخول"]
    if entry == 0: return 0.0, 0.0
    if row["اتجاه"] == "long":
        pnl_pct = (current_price - entry) / entry * 100
    else:
        pnl_pct = (entry - current_price) / entry * 100
    pnl_pts = abs(current_price - entry) * (1 if pnl_pct >= 0 else -1)
    return round(pnl_pts, 4), round(pnl_pct, 2)

def auto_update_status(row):
    cp = row.get("السعر_الحالي", None)
    if cp is None or cp == 0: return row["الحالة"]
    entry, sl, tp1 = row["دخول"], row["SL"], row["TP1"]
    bias = row["اتجاه"]
    if row["الحالة"] in ["TP","SL"]: return row["الحالة"]
    if bias == "long":
        if cp >= tp1: return "TP"
        if cp <= sl:  return "SL"
        if cp > entry: return "Active"
    else:
        if cp <= tp1: return "TP"
        if cp >= sl:  return "SL"
        if cp < entry: return "Active"
    return "Pending"

def setup_to_log_row(setup: TradeSetup, ticker: str, current_price: float) -> dict:
    pnl_pts, pnl_pct = calc_pnl({
        "دخول": setup.entry, "اتجاه": setup.bias,
        "السعر_الحالي": current_price
    }, current_price)
    row = {
        "id": f"{ticker}_{datetime.now().strftime('%H%M%S')}",
        "ticker": ticker,
        "اتجاه": setup.bias,
        "جودة": setup.confidence,
        "منطقة": setup.zone,
        "دخول": setup.entry,
        "SL": setup.stop_loss,
        "TP1": setup.tp1,
        "TP2": setup.tp2,
        "R:R": setup.rr_ratio,
        "السعر_الحالي": current_price or setup.entry,
        "PnL": pnl_pts,
        "PnL%": pnl_pct,
        "الحالة": "Pending",
        "ملاحظات": setup.notes,
        "وقت_الإضافة": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    return row


# ══════════════════════════════════════════════════════════════
#  PLOTLY CHART
# ══════════════════════════════════════════════════════════════

def build_chart(df, swings, sweeps, setups, ticker, selected_idx=0):
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.78, 0.22],
        shared_xaxes=True,
        vertical_spacing=0.02,
    )

    # ── Candlestick ──
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#00ff9d", increasing_fillcolor="rgba(0,255,157,0.7)",
        decreasing_line_color="#ff4d6a", decreasing_fillcolor="rgba(255,77,106,0.7)",
        name="OHLC", line_width=1,
    ), row=1, col=1)

    # ── Volume ──
    colors = ["rgba(0,255,157,0.4)" if c >= o else "rgba(255,77,106,0.4)"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], marker_color=colors, name="Volume", showlegend=False
    ), row=2, col=1)

    # ── Swing Highs ──
    sh = [s for s in swings if s.kind=="high"]
    if sh:
        fig.add_trace(go.Scatter(
            x=[s.timestamp for s in sh], y=[s.price for s in sh],
            mode="markers", marker=dict(symbol="triangle-down", size=10,
                color="rgba(255,77,106,0.8)", line=dict(width=1,color="#ff4d6a")),
            name="Swing High", hovertemplate="H: %{y:.4f}<extra></extra>"
        ), row=1, col=1)

    # ── Swing Lows ──
    sl_pts = [s for s in swings if s.kind=="low"]
    if sl_pts:
        fig.add_trace(go.Scatter(
            x=[s.timestamp for s in sl_pts], y=[s.price for s in sl_pts],
            mode="markers", marker=dict(symbol="triangle-up", size=10,
                color="rgba(0,255,157,0.8)", line=dict(width=1,color="#00ff9d")),
            name="Swing Low", hovertemplate="L: %{y:.4f}<extra></extra>"
        ), row=1, col=1)

    # ── Liquidity Sweeps ──
    for sw in sweeps:
        color = "#ff4d6a" if sw.direction=="buyside" else "#00ff9d"
        fig.add_annotation(
            x=sw.swept_at, y=sw.swept_price, ax=0, ay=-30 if sw.direction=="buyside" else 30,
            arrowhead=2, arrowcolor=color, arrowsize=1.2, arrowwidth=2,
            text=f"Sweep {'↓' if sw.direction=='buyside' else '↑'}",
            font=dict(size=9, color=color, family="IBM Plex Mono"),
            bgcolor="rgba(10,14,20,0.8)", bordercolor=color, borderwidth=1, borderpad=3,
            row=1, col=1,
        )

    # ── Selected Trade Setup Levels ──
    if setups and selected_idx < len(setups):
        s = setups[selected_idx]
        last_x = df.index[-1]
        sw_x   = s.sweep.swept_at

        def add_level(price, color, dash, label, width=1.5):
            fig.add_shape(type="line", x0=sw_x, y0=price, x1=last_x, y1=price,
                          line=dict(color=color, width=width, dash=dash), row=1, col=1)
            fig.add_annotation(x=last_x, y=price, text=f" {label}: {price:.4f}",
                xanchor="left", font=dict(size=9, color=color, family="IBM Plex Mono"),
                showarrow=False, row=1, col=1)

        add_level(s.entry,     "#00d4ff", "solid",  "ENTRY", 2)
        add_level(s.stop_loss, "#ff4d6a", "dot",    "SL",    1.5)
        add_level(s.tp1,       "#00ff9d", "dash",   "TP1",   1.5)
        add_level(s.tp2,       "#9d72ff", "dash",   "TP2",   1.5)

        # FVG zone
        if s.fvg and not s.fvg.filled:
            fig.add_shape(type="rect",
                x0=s.fvg.formed_at, y0=s.fvg.bottom, x1=last_x, y1=s.fvg.top,
                fillcolor="rgba(0,212,255,0.06)", line=dict(color="rgba(0,212,255,0.25)",width=1),
                row=1, col=1)

    # ── Layout ──
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0e14",
        plot_bgcolor="#0a0e14",
        font=dict(family="IBM Plex Mono", color="#5a7090", size=11),
        margin=dict(l=0, r=80, t=30, b=0),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", x=0, y=1.02, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=10, color="#5a7090")),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#131c2a", font_family="IBM Plex Mono", font_size=11),
    )
    fig.update_xaxes(
        gridcolor="#1e2d42", showgrid=True,
        tickfont=dict(size=10, color="#3a5070"),
        zerolinecolor="#1e2d42",
    )
    fig.update_yaxes(
        gridcolor="#1e2d42", showgrid=True,
        tickfont=dict(size=10, color="#3a5070"),
        zerolinecolor="#1e2d42",
        side="right",
    )
    return fig


# ══════════════════════════════════════════════════════════════
#  TRADE LOG TABLE
# ══════════════════════════════════════════════════════════════

def render_trade_log():
    log = st.session_state["trade_log"]

    # تحديث الأسعار والحالات تلقائياً
    if not log.empty:
        for i, row in log.iterrows():
            cp = fetch_current_price(row["ticker"])
            if cp:
                log.at[i, "السعر_الحالي"] = cp
                ppts, ppct = calc_pnl(row, cp)
                log.at[i, "PnL"]  = ppts
                log.at[i, "PnL%"] = ppct
                log.at[i, "الحالة"] = auto_update_status(log.loc[i])
        st.session_state["trade_log"] = log

    if log.empty:
        st.info("📋 سجل الصفقات فارغ — أضف صفقة من لوحة التحليل أعلاه.")
        return

    if AGGRID_AVAILABLE:
        _render_aggrid(log)
    else:
        _render_fallback_table(log)


def _render_aggrid(log):
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

    display = log.copy()
    display["PnL%"] = display["PnL%"].apply(lambda x: f"+{x:.2f}%" if x >= 0 else f"{x:.2f}%")

    pnl_color = JsCode("""
    function(params) {
        if (params.value && params.value.startsWith('+'))
            return {'color': '#00ff9d', 'fontWeight': '600'};
        if (params.value && params.value.startsWith('-'))
            return {'color': '#ff4d6a', 'fontWeight': '600'};
        return {};
    }""")

    status_color = JsCode("""
    function(params) {
        const c = {'Pending':'#ffd166','Active':'#00d4ff','TP':'#00ff9d','SL':'#ff4d6a'};
        return {'color': c[params.value] || '#e8f0fe', 'fontWeight': '600'};
    }""")

    bias_color = JsCode("""
    function(params) {
        return {'color': params.value === 'long' ? '#00ff9d' : '#ff4d6a', 'fontWeight': '600'};
    }""")

    gb = GridOptionsBuilder.from_dataframe(display[[
        "ticker","اتجاه","جودة","دخول","SL","TP1","TP2","R:R",
        "السعر_الحالي","PnL%","الحالة","ملاحظات","وقت_الإضافة"
    ]])
    gb.configure_default_column(
        resizable=True, sortable=True, filter=True,
        cellStyle={"fontFamily":"IBM Plex Mono","fontSize":"12px",
                   "color":"#e8f0fe","background":"#0f1520"}
    )
    gb.configure_column("PnL%",    cellStyle=pnl_color)
    gb.configure_column("الحالة", cellStyle=status_color,
                        editable=True, cellEditor="agSelectCellEditor",
                        cellEditorParams={"values":["Pending","Active","TP","SL"]})
    gb.configure_column("اتجاه",   cellStyle=bias_color)
    gb.configure_column("ملاحظات", editable=True, cellEditor="agTextCellEditor")
    gb.configure_column("وقت_الإضافة", hide=True)
    gb.configure_selection("single", use_checkbox=False)
    gb.configure_grid_options(rowDragManaged=True, animateRows=True)

    custom_css = {
        ".ag-root-wrapper": {"background":"#0f1520","border":"1px solid #1e2d42","border-radius":"6px"},
        ".ag-header": {"background":"#0a0e14","border-bottom":"1px solid #1e2d42"},
        ".ag-header-cell-label": {"color":"#00d4ff","font-family":"IBM Plex Mono","font-size":"11px","letter-spacing":"1px"},
        ".ag-row": {"border-bottom":"1px solid #1e2d42","background":"#0f1520"},
        ".ag-row:hover": {"background":"#131c2a !important"},
        ".ag-row-selected": {"background":"#1a2535 !important"},
        ".ag-cell": {"color":"#e8f0fe","padding":"8px 12px"},
    }

    response = AgGrid(
        display,
        gridOptions=gb.build(),
        height=280,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True,
        custom_css=custom_css,
        theme="balham-dark",
    )
    # تطبيق التعديلات
    if response["data"] is not None:
        updated = response["data"]
        for i, row in updated.iterrows():
            if i < len(st.session_state["trade_log"]):
                st.session_state["trade_log"].at[i, "الحالة"]  = row.get("الحالة","Pending")
                st.session_state["trade_log"].at[i, "ملاحظات"] = row.get("ملاحظات","")


def _render_fallback_table(log):
    """جدول احتياطي إذا لم تكن AgGrid مثبتة"""
    display = log[["ticker","اتجاه","جودة","دخول","SL","TP1","TP2","R:R",
                    "السعر_الحالي","PnL%","الحالة","ملاحظات"]].copy()
    st.dataframe(
        display.style
            .map(lambda v: "color:#00ff9d;font-weight:bold" if isinstance(v,str) and v.startswith("+") else
                           "color:#ff4d6a;font-weight:bold" if isinstance(v,str) and v.startswith("-") else "",
                 subset=["PnL%"] if "PnL%" in display.columns else [])
            .set_properties(**{"font-family":"IBM Plex Mono","font-size":"12px"}),
        use_container_width=True,
        height=260,
    )


# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="section-header"><span class="section-title">⬡ ICT ENGINE</span></div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-family:IBM Plex Mono;font-size:0.65rem;color:#3a5070;letter-spacing:1px;margin-bottom:16px;">
        v2.0 — SMART MONEY DASHBOARD<br>
        {datetime.now().strftime("%Y-%m-%d  %H:%M")}
        </div>""", unsafe_allow_html=True)

        # ── Watchlist ──
        st.markdown('<div class="section-header"><span class="section-title">◈ WATCHLIST</span></div>',
                    unsafe_allow_html=True)

        wl = st.session_state["watchlist"]
        selected = st.radio("", wl, index=wl.index(st.session_state["active_ticker"])
                             if st.session_state["active_ticker"] in wl else 0,
                             label_visibility="collapsed")
        st.session_state["active_ticker"] = selected

        c1, c2 = st.columns(2)
        new_ticker = c1.text_input("إضافة رمز", placeholder="AAPL", label_visibility="visible")
        if c2.button("＋ إضافة", use_container_width=True):
            t = new_ticker.strip().upper()
            if t and t not in st.session_state["watchlist"]:
                st.session_state["watchlist"].append(t)
                st.session_state["active_ticker"] = t
                st.rerun()

        if st.button("× حذف المحدد", use_container_width=True):
            if selected in st.session_state["watchlist"] and len(st.session_state["watchlist"]) > 1:
                st.session_state["watchlist"].remove(selected)
                st.session_state["active_ticker"] = st.session_state["watchlist"][0]
                st.rerun()

        st.markdown("---")

        # ── Engine Parameters ──
        st.markdown('<div class="section-header"><span class="section-title">⚙ ENGINE PARAMS</span></div>',
                    unsafe_allow_html=True)

        period   = st.selectbox("Period",   ["3mo","6mo","1y","2y"], index=1)
        interval = st.selectbox("Interval", ["1d","1h","4h","1wk"], index=0)
        sw_lb    = st.slider("Swing Lookback", 3, 10, 5)
        candles  = st.slider("Analysis Candles", 50, 150, 80)
        min_wick = st.slider("Min Wick %", 10, 40, 15)

        run_btn = st.button("▶  RUN ANALYSIS", use_container_width=True, type="primary")

        st.markdown("---")

        # ── Advisor Status ──
        st.markdown('<div class="section-header"><span class="section-title">◉ ADVISOR STATUS</span></div>',
                    unsafe_allow_html=True)

        statuses = st.session_state["advisor_status"]
        for adv, label in [("advisor1","Liquidity Filter"),("advisor2","Execution Analyzer"),("advisor3","Trade Optimizer")]:
            s = statuses.get(adv,"idle")
            col = {"idle":"#3a5070","running":"#ffd166","done":"#00ff9d","error":"#ff4d6a"}.get(s,"#3a5070")
            dot = {"idle":"○","running":"◎","done":"●","error":"✗"}.get(s,"○")
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1e2d42;">
                <span style="font-family:IBM Plex Mono;font-size:0.7rem;color:#5a7090;">{label}</span>
                <span style="font-family:IBM Plex Mono;font-size:0.7rem;color:{col};font-weight:600;">{dot} {s.upper()}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🗑 مسح سجل الصفقات", use_container_width=True):
            st.session_state["trade_log"] = pd.DataFrame(columns=st.session_state["trade_log"].columns)
            st.rerun()

    return run_btn, period, interval, sw_lb, candles, min_wick


# ══════════════════════════════════════════════════════════════
#  TRADE DETAIL PANEL
# ══════════════════════════════════════════════════════════════

def render_trade_detail(setup: TradeSetup, current_price: float):
    bias_badge = f'<span class="badge badge-{"long" if setup.bias=="long" else "short"}">{"🔺 LONG" if setup.bias=="long" else "🔻 SHORT"}</span>'
    conf_badge = CONFIDENCE_BADGE.get(setup.confidence,"")
    zone_ar    = {"discount":"Discount 🟩","premium":"Premium 🟥","equilibrium":"Equilibrium 🟨"}.get(setup.zone,setup.zone)

    # PnL
    pnl_pts, pnl_pct = calc_pnl({"دخول":setup.entry,"اتجاه":setup.bias}, current_price)
    pnl_class = "pnl-pos" if pnl_pct >= 0 else "pnl-neg"
    pnl_sign  = "+" if pnl_pct >= 0 else ""

    fvg_info = f"{setup.fvg.bottom:.4f} – {setup.fvg.top:.4f}" if setup.fvg else "—"
    mss_info = f"{setup.structure_break.kind} @ {setup.structure_break.break_price:.4f}" if setup.structure_break else "—"

    st.markdown(f"""
    <div class="trade-panel">
      <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-family:IBM Plex Mono;font-size:0.75rem;color:#5a7090;letter-spacing:2px;">SETUP DETAIL</span>
        <div>{bias_badge} {conf_badge}</div>
      </div>

      <div class="trade-row">
        <span class="trade-key">ENTRY</span>
        <span class="trade-val" style="color:#00d4ff">{setup.entry:.4f}</span>
      </div>
      <div class="trade-row">
        <span class="trade-key">STOP LOSS</span>
        <span class="trade-val" style="color:#ff4d6a">{setup.stop_loss:.4f}</span>
      </div>
      <div class="trade-row">
        <span class="trade-key">TP1</span>
        <span class="trade-val" style="color:#00ff9d">{setup.tp1:.4f}</span>
      </div>
      <div class="trade-row">
        <span class="trade-key">TP2</span>
        <span class="trade-val" style="color:#9d72ff">{setup.tp2:.4f}</span>
      </div>
      <div class="trade-row">
        <span class="trade-key">R:R RATIO</span>
        <span class="trade-val" style="color:#ffd166">{setup.rr_ratio:.2f}</span>
      </div>
      <div class="trade-row">
        <span class="trade-key">ZONE</span>
        <span class="trade-val">{zone_ar}</span>
      </div>
      <div class="trade-row">
        <span class="trade-key">MSS/BOS</span>
        <span class="trade-val" style="font-size:0.78rem">{mss_info}</span>
      </div>
      <div class="trade-row">
        <span class="trade-key">FVG ZONE</span>
        <span class="trade-val" style="font-size:0.78rem">{fvg_info}</span>
      </div>
      <div class="trade-row">
        <span class="trade-key">SWEEP STRENGTH</span>
        <span class="trade-val" style="font-size:0.78rem">{setup.sweep.strength}</span>
      </div>

      <div class="pnl-block">
        <div class="pnl-title">UNREALIZED P&L (CURRENT: {current_price:.4f})</div>
        <div class="pnl-value {pnl_class}">{pnl_sign}{pnl_pts:.4f} pts &nbsp;&nbsp; {pnl_sign}{pnl_pct:.2f}%</div>
      </div>

      <div style="margin-top:10px;padding:8px;background:#0a0e14;border-radius:4px;
                  font-family:IBM Plex Mono;font-size:0.7rem;color:#5a7090;line-height:1.6;">
        {setup.notes}
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════

def main():

    # ── Sidebar ──
    run_btn, period, interval, sw_lb, candles, min_wick = render_sidebar()

    # ── Header ──
    st.markdown(f"""
    <div class="dashboard-header">
      <p class="header-title">⬡ ICT SMART MONEY ENGINE</p>
      <p class="header-sub">
        LIQUIDITY FILTER · EXECUTION ANALYZER · TRADE OPTIMIZER
        &nbsp;|&nbsp; TICKER: <span style="color:#00d4ff">{st.session_state["active_ticker"]}</span>
        &nbsp;|&nbsp; {interval} · {period}
      </p>
    </div>
    """, unsafe_allow_html=True)

    ticker = st.session_state["active_ticker"]

    # ── Run Engine ──
    if run_btn or "engine_result" not in st.session_state:
        with st.spinner(f"جارٍ تحليل {ticker}..."):
            st.session_state["advisor_status"] = {"advisor1":"running","advisor2":"idle","advisor3":"idle"}
            df, swings, sweeps, setups = run_engine(ticker, period, interval, sw_lb, candles, min_wick)
            if df is None:
                st.error(f"❌ لا توجد بيانات للرمز: {ticker}")
                return
            st.session_state["advisor_status"] = {"advisor1":"done","advisor2":"done","advisor3":"done"}
            st.session_state["engine_result"] = {"df":df,"swings":swings,"sweeps":sweeps,"setups":setups}

    result  = st.session_state.get("engine_result", {})
    df      = result.get("df")
    swings  = result.get("swings", [])
    sweeps  = result.get("sweeps", [])
    setups  = result.get("setups", [])

    if df is None:
        st.warning("اضغط 'RUN ANALYSIS' لبدء التحليل.")
        return

    current_price = fetch_current_price(ticker) or float(df["Close"].iloc[-1])

    # ── KPI Row ──
    k1, k2, k3, k4, k5 = st.columns(5)
    price_chg = (float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-2])) / float(df["Close"].iloc[-2]) * 100
    pc_color  = "#00ff9d" if price_chg >= 0 else "#ff4d6a"
    pc_sign   = "+" if price_chg >= 0 else ""

    for col, label, value, cls in [
        (k1, "PRICE",      f"{current_price:.4f}",    "metric-cyan"),
        (k2, "CHANGE 1D",  f"{pc_sign}{price_chg:.2f}%",
                           "metric-green" if price_chg>=0 else "metric-red"),
        (k3, "SWEEPS",     str(len(sweeps)),           "metric-gold"),
        (k4, "SETUPS",     str(len(setups)),           "metric-cyan"),
        (k5, "BEST GRADE", setups[0].confidence if setups else "—", "metric-green"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <p class="metric-value {cls}">{value}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Setup Selector ──
    if setups:
        setup_labels = [f"[{i+1}] {'LONG' if s.bias=='long' else 'SHORT'} @ {s.entry:.4f}  |  {s.confidence}  |  RR {s.rr_ratio}"
                        for i, s in enumerate(setups)]
        sel_idx = st.selectbox("🎯 اختر الإعداد للعرض على الشارت",
                               range(len(setup_labels)),
                               format_func=lambda i: setup_labels[i])
        st.session_state["selected_setup_idx"] = sel_idx
    else:
        sel_idx = 0
        st.info("⚪ لم يُعثر على إعدادات صفقات — جرّب تخفيض Min Wick أو توسيع الـ Candles.")

    # ── Chart + Detail ──
    chart_col, detail_col = st.columns([2.4, 1], gap="medium")

    with chart_col:
        st.markdown('<div class="section-header"><span class="section-title">◈ PRICE ACTION CHART</span></div>',
                    unsafe_allow_html=True)
        fig = build_chart(df, swings, sweeps, setups, ticker, sel_idx)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with detail_col:
        st.markdown('<div class="section-header"><span class="section-title">◉ TRADE DETAIL</span></div>',
                    unsafe_allow_html=True)
        if setups:
            render_trade_detail(setups[sel_idx], current_price)

            # زر إضافة للسجل
            if st.button("＋ إضافة للسجل", use_container_width=True):
                row = setup_to_log_row(setups[sel_idx], ticker, current_price)
                new_row = pd.DataFrame([row])
                st.session_state["trade_log"] = pd.concat(
                    [st.session_state["trade_log"], new_row], ignore_index=True
                )
                st.success("✅ تمت الإضافة لسجل الصفقات")
        else:
            st.markdown("""
            <div class="trade-panel" style="text-align:center;padding:40px 20px;">
              <p style="color:#3a5070;font-family:IBM Plex Mono;font-size:0.8rem;letter-spacing:1px;">
                NO SETUP SELECTED<br><br>
                قم بتشغيل المحرك<br>أو تعديل المعاملات
              </p>
            </div>""", unsafe_allow_html=True)

    # ── Trade Log ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header"><span class="section-title">◈ TRADE LOG — سجل الصفقات</span></div>',
                unsafe_allow_html=True)

    if not AGGRID_AVAILABLE:
        st.caption("💡 لتفعيل الجدول التفاعلي: `pip install streamlit-aggrid`")

    render_trade_log()

    # ── PnL Summary ──
    log = st.session_state["trade_log"]
    if not log.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header"><span class="section-title">◈ P&L SUMMARY</span></div>',
                    unsafe_allow_html=True)

        s1,s2,s3,s4,s5,s6 = st.columns(6)
        total_trades = len(log)
        wins  = log[log["PnL%"] > 0]
        losses= log[log["PnL%"] < 0]
        tp_count  = len(log[log["الحالة"]=="TP"])
        sl_count  = len(log[log["الحالة"]=="SL"])
        win_rate  = tp_count/(tp_count+sl_count)*100 if (tp_count+sl_count)>0 else 0
        total_pnl = log["PnL%"].sum()

        for col, lbl, val, cls in [
            (s1,"TOTAL TRADES",str(total_trades),"metric-cyan"),
            (s2,"TP HIT",str(tp_count),"metric-green"),
            (s3,"SL HIT",str(sl_count),"metric-red"),
            (s4,"WIN RATE",f"{win_rate:.1f}%","metric-gold"),
            (s5,"TOTAL PnL%",f"{'+' if total_pnl>=0 else ''}{total_pnl:.2f}%",
              "metric-green" if total_pnl>=0 else "metric-red"),
            (s6,"AVG RR",f"{log['R:R'].mean():.2f}","metric-cyan"),
        ]:
            col.markdown(f"""
            <div class="metric-card">
              <div class="metric-label">{lbl}</div>
              <p class="metric-value {cls}">{val}</p>
            </div>""", unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="margin-top:40px;padding:12px;border-top:1px solid #1e2d42;
                text-align:center;font-family:IBM Plex Mono;font-size:0.65rem;
                color:#2a4060;letter-spacing:1px;">
    ICT SMART MONEY ENGINE v2.0  ·  للأغراض التعليمية فقط  ·  ليس نصيحة مالية
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
