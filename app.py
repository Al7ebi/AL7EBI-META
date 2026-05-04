"""
app_1.py — منصة الحبي للتداول v5
جميع الملاحظات مطبّقة
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import engine as E

st.set_page_config(
    page_title="منصة الحبي للتداول",
    page_icon="ح",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════
for k,v in {
    "theme":"light","market_tab":"US","radar_df":None,
    "radar_ts":None,"drill":None,"search_q":"",
    "sort_by":"القوة","filter_grade":"جميع القوة","view_mode":"جدول",
    "us_wl":"تقنية كبرى (30)",
}.items():
    if k not in st.session_state: st.session_state[k]=v

DARK = st.session_state.theme == "dark"

# ══════════════════════════════════════════════════════
# WATCHLISTS
# ══════════════════════════════════════════════════════
SA_STOCKS = [
    ("2222","أرامكو"),("1120","الراجحي"),("2010","سابك"),("7010","STC"),
    ("1180","الأهلي"),("1211","معادن"),("2350","سافكو"),("4190","جرير"),
    ("2380","بترو رابغ"),("4003","التعاونية"),("2030","بنك الجزيرة"),
    ("1150","الأول"),("1060","بنك الرياض"),("2280","شركة المراعي"),
    ("4321","بوان"),
]
SA_WATCHLIST = [(t,"2222.SR") for t,_ in SA_STOCKS]

TECH_30 = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","AMD","QCOM",
            "ORCL","CRM","ADBE","INTC","TXN","MU","AMAT","LRCX","KLAC","MRVL",
            "NFLX","PYPL","SHOP","SNOW","PANW","CRWD","ZS","DDOG","MSTR","PLTR"]
BLUE_40 = ["JPM","BAC","GS","MS","BRK-B","V","MA","AXP","WFC","C",
            "JNJ","UNH","LLY","ABBV","PFE","MRK","TMO","ABT","DHR","BMY",
            "WMT","HD","COST","TGT","MCD","SBUX","NKE","LOW","TJX","AMGN",
            "XOM","CVX","COP","SLB","CAT","RTX","HON","UPS","BA","GE"]
# الأسهم الرخيصة: فقط الاتجاه الصاعد (Long only)
CHEAP_20 = ["F","AAL","SOFI","RIVN","SNAP","UBER","LYFT","PLUG","NIO",
            "XPEV","CLNE","NOK","BB","SIRI","VALE","ITUB","PBR","KGC","BTG","LCID"]

US_WATCHLIST_MAP = {
    "تقنية كبرى (30)": [(t,"QQQ") for t in TECH_30],
    "قيادية S&P (40)": [(t,"SPY") for t in BLUE_40],
    "الكل (70 سهم)": [(t,"QQQ") for t in TECH_30]+[(t,"SPY") for t in BLUE_40],
    "رخيصة (<$20) — صاعد فقط": [(t,"SPY") for t in CHEAP_20],
    "كريبتو ETF": [(t,"QQQ") for t in ["MSTR","COIN","BITO","GBTC","ETHE","ARKK","BLOK","BTCW"]],
}
CHEAP_KEY = "رخيصة (<$20) — صاعد فقط"

# ══════════════════════════════════════════════════════
# TOKENS
# ══════════════════════════════════════════════════════
if DARK:
    BG="#0B0D16"; CARD="#11141F"; CARD2="#171B2A"; BRD="#1C2136"
    TXT="#E2E8F5"; TXT2="#8896B2"; TXT3="#3A4560"
    TBLH="#0B0D16"; TBLHV="#171B2A"
    HDR_BG="#0E1120"; STS_BG="#0E1120"
else:
    BG="#F1F4FA"; CARD="#FFFFFF"; CARD2="#F7F9FF"; BRD="#E2E8F0"
    TXT="#0F1629"; TXT2="#4A5680"; TXT3="#9AA3BA"
    TBLH="#F7F9FF"; TBLHV="#EEF2FA"
    HDR_BG="#FFFFFF"; STS_BG="#F7F9FF"

BL="#3B82F6"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"
GR2="#22C55E"; RD2="#F87171"; AM2="#FCD34D"
GL = "#052E1C" if DARK else "#DCFCE7"
RL = "#2D0A0A" if DARK else "#FEE2E2"
BLL = "#0F1E4A" if DARK else "#DBEAFE"
AL = "#2D1A00" if DARK else "#FEF9C3"

# ══════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800;900&display=swap');
:root{{
  --bg:{BG};--card:{CARD};--card2:{CARD2};--brd:{BRD};
  --txt:{TXT};--txt2:{TXT2};--txt3:{TXT3};
  --tblh:{TBLH};--tblhv:{TBLHV};
  --bl:{BL};--gr:{GR};--rd:{RD};--am:{AM};
  --font:'Tajawal',sans-serif;
  --sh:0 1px 3px rgba(0,0,0,{"0.45" if DARK else "0.07"});
  --sh2:0 4px 16px rgba(0,0,0,{"0.55" if DARK else "0.09"});
}}
html,body,[class*="css"]{{
  background:var(--bg)!important;
  font-family:var(--font)!important;
  color:var(--txt)!important;
  direction:rtl!important;
}}
*{{box-sizing:border-box;}}
[data-testid="collapsedControl"],[data-testid="stSidebar"],
section[data-testid="stSidebar"]{{display:none!important;}}
.main.block-container{{padding:0!important;max-width:100%!important;}}
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-thumb{{background:var(--brd);border-radius:4px;}}

/* ── HEADER ── */
.top-hdr{{
  background:{HDR_BG};
  padding:0 clamp(14px,3vw,36px);
  height:62px;
  display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--brd);
  position:sticky;top:0;z-index:100;
}}
.hdr-brand{{display:flex;align-items:center;gap:12px;}}
.brand-logo{{
  width:42px;height:42px;background:var(--bl);border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  font-size:1.2rem;font-weight:900;color:#fff;flex-shrink:0;
  box-shadow:0 4px 12px rgba(59,130,246,0.4);
}}
.brand-name{{
  font-size:clamp(1.1rem,2.5vw,1.5rem);
  font-weight:900;color:var(--txt);line-height:1.1;
}}
.brand-sub{{font-size:0.7rem;color:var(--txt3);letter-spacing:0.3px;margin-top:1px;}}
.hdr-controls{{
  display:flex;align-items:center;gap:8px;
}}
.hdr-clock{{
  font-size:1.05rem;font-weight:800;
  color:var(--bl);letter-spacing:2px;
  font-variant-numeric:tabular-nums;
  padding:0 6px;
}}
.hdr-icon-btn{{
  width:36px;height:36px;border-radius:10px;
  background:var(--card2);border:1px solid var(--brd);
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;font-size:1.05rem;transition:all.15s;
  flex-shrink:0;
}}
.hdr-icon-btn:hover{{background:var(--brd);border-color:var(--bl);}}
.hdr-icon-btn.active{{background:rgba(59,130,246,.15);border-color:var(--bl);}}

/* ── MARKET TABS — خط فقط ── */
.mkt-tabs{{
  background:{HDR_BG};
  padding:0 clamp(14px,3vw,36px);
  border-bottom:2px solid var(--brd);
  display:flex;align-items:flex-end;gap:4px;
}}
.mkt-tab{{
  padding:11px 20px 9px;
  font-size:0.95rem;font-weight:700;
  color:var(--txt3);cursor:pointer;
  border-bottom:3px solid transparent;
  margin-bottom:-2px;
  transition:all.18s;white-space:nowrap;
  display:flex;align-items:center;gap:6px;
}}
.mkt-tab.mkt-tag{{
  font-size:0.62rem;font-weight:800;
  padding:1px 5px;border-radius:4px;
  background:var(--brd);color:var(--txt3);
}}
.mkt-tab.active{{color:var(--bl);border-bottom-color:var(--bl);}}
.mkt-tab.active.mkt-tag{{background:rgba(59,130,246,.18);color:var(--bl);}}
.mkt-tab:hover:not(.active){{color:var(--txt2);}}

/* ── STATUS BAR ── */
.sts-bar{{
  background:{STS_BG};
  padding:7px clamp(14px,3vw,36px);
  display:flex;align-items:center;justify-content:space-between;
  flex-wrap:wrap;gap:6px;border-bottom:1px solid var(--brd);
  font-size:0.82rem;
}}
.sts-l{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}}
.sts-r{{display:flex;align-items:center;gap:14px;color:var(--txt3);font-size:0.76rem;}}
.mkt-status{{display:flex;align-items:center;gap:7px;font-weight:700;}}
.mkt-status.open{{color:{GR2};}}
.mkt-status.closed{{color:{RD};}}
.sts-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;}}
.sts-dot.open{{background:{GR2};animation:pg 1.8s infinite;}}
.sts-dot.closed{{background:{RD};animation:pr 1.8s infinite;}}
@keyframes pg{{0%,100%{{box-shadow:0 0 0 0 rgba(34,197,94,.5)}}50%{{box-shadow:0 0 0 5px rgba(34,197,94,0)}}}}
@keyframes pr{{0%,100%{{box-shadow:0 0 0 0 rgba(239,68,.5)}}50%{{box-shadow:0 0 0 5px rgba(239,68,68,0)}}}}
.sts-next{{color:{RD2};font-weight:700;}}
.sts-prog{{height:4px;background:var(--brd);border-radius:2px;overflow:hidden;width:80px;}}
.sts-prog-fill{{height:100%;background:linear-gradient(90deg,{BL},{GR2});animation:prog 5s linear infinite;border-radius:2px;}}
@keyframes prog{{0%{{width:5%}}100%{{width:100%}}}}

/* ── MAIN WRAP ── */
.main-wrap{{padding:clamp(14px,2.5vw,24px) clamp(14px,3vw,36px);max-width:1500px;margin:0 auto;}}

/* ── CONTROLS ROW ── */
.ctrl-area{{margin-bottom:clamp(12px,2vw,18px);}}

/* ── STAT CARDS ── */
.stats-row{{
  display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
  gap:clamp(8px,1.5vw,12px);margin-bottom:clamp(14px,2.5vw,20px);
}}
@media(max-width:600px){{.stats-row{{grid-template-columns:repeat(2,1fr);}}}}
.stat-card{{
  background:var(--card);border:1px solid var(--brd);
  border-radius:14px;padding:clamp(12px,2vw,18px);
  text-align:center;box-shadow:var(--sh);
}}
.stat-lbl{{font-size:0.78rem;color:var(--txt3);margin-bottom:6px;}}
.stat-v{{font-size:clamp(1.6rem,3.5vw,2.2rem);font-weight:900;line-height:1;}}
.sv-wh{{color:var(--txt);}}.sv-gr{{color:{GR2};}}.sv-am{{color:{AM2};}}.sv-bl{{color:{BL};}}

/* ── TABLE ── */
.tbl-wrap{{
  background:var(--card);border:1px solid var(--brd);
  border-radius:14px;overflow:hidden;box-shadow:var(--sh);
}}
.tbl-hdr-row{{
  display:grid;
  grid-template-columns:50px 80px 110px 90px 70px 110px 100px 90px;
  padding:8px clamp(8px,1.5vw,16px);
  border-bottom:1px solid var(--brd);
  background:var(--tblh);
}}
.tbl-row-item{{
  display:grid;
  grid-template-columns:50px 80px 110px 90px 70px 110px 110px 110px 100px 90px;
  padding:0 clamp(8px,1.5vw,16px);
  border-bottom:1px solid var(--brd);
  align-items:center;min-height:58px;
  transition:background.14s;
}}
.tbl-row-item:last-child{{border-bottom:none;}}
.tbl-row-item:hover{{background:var(--tblhv);}}
.th{{
  font-size:0.72rem;font-weight:700;color:var(--txt3);
  text-align:right;padding:2px 6px;
  letter-spacing:0.5px;
}}
.td{{font-size:0.92rem;text-align:right;padding:2px 6px;}}
.td.bold{{font-weight:800;color:var(--txt);font-size:1rem;}}
.td.num{{font-variant-numeric:tabular-nums;}}
.td.c-gr{{color:{GR2};font-weight:700;}}
.td.c-rd{{color:{RD2};font-weight:700;}}
.td.c-am{{color:{AM2};font-weight:700;}}
.td.c-bl{{color:{BL};font-weight:700;}}
.td.muted{{color:var(--txt3);}}

/* Stars */
.stars-row{{display:flex;gap:3px;justify-content:flex-end;}}
.star-on{{color:{AM2};font-size:1.05rem;}}
.star-off{{color:var(--brd);font-size:1.05rem;}}

/* Status badge */
.sb{{display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:700;white-space:nowrap;}}
.sb-active{{background:rgba(34,197,94,.15);color:{GR2};border:1px solid rgba(34,197,94,.3);}}
.sb-wait {{background:rgba(245,158,11,.15);color:{AM2};border:1px solid rgba(245,158,11,.3);}}
.sb-closed{{background:rgba(148,163,184,.1);color:var(--txt3);border:1px solid var(--brd);}}

/* Grade pill */
.gp{{display:inline-flex;align-items:center;font-size:0.72rem;font-weight:700;letter-spacing:1px;padding:3px 10px;border-radius:20px;}}
.gp-ap{{background:{GL};color:{"#4ADE80" if DARK else "#15803D"};}}
.gp-a {{background:{BLL};color:{"#93C5FD" if DARK else "#1D4ED8"};}}
.gp-b {{background:{AL};color:{"#FCD34D" if DARK else "#854D0E"};}}
.gp-sk{{background:var(--card2);color:var(--txt3);}}

/* ── CARD VIEW ── */
.cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;}}
.trade-card{{
  background:var(--card);border:1px solid var(--brd);border-radius:14px;
  padding:18px;box-shadow:var(--sh);transition:box-shadow.2s,transform.18s;
  position:relative;overflow:hidden;
}}
.trade-card:hover{{box-shadow:var(--sh2);transform:translateY(-2px);}}
.trade-card::before{{
  content:'';position:absolute;top:0;right:0;
  width:100%;height:3px;border-radius:14px 14px 0 0;
}}
.tc-long::before {{background:linear-gradient(90deg,{GR2},{BL});}}
.tc-short::before{{background:linear-gradient(90deg,{RD},{AM});}}
.card-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;}}
.card-sym{{font-size:1.15rem;font-weight:900;color:var(--txt);}}
.card-name{{font-size:0.73rem;color:var(--txt3);margin-top:2px;}}
.card-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;}}
.cf-l{{font-size:0.72rem;color:var(--txt3);margin-bottom:1px;}}
.cf-v{{font-size:0.92rem;font-weight:700;}}
.card-bot{{margin-top:12px;padding-top:10px;border-top:1px solid var(--brd);display:flex;justify-content:space-between;align-items:center;}}
.card-date{{font-size:0.7rem;color:var(--txt3);}}

/* ── DETAIL PANEL ── */
.detail-wrap{{
  background:var(--card);border:1px solid var(--brd);
  border-radius:14px;padding:clamp(14px,2vw,22px);
  box-shadow:var(--sh);margin-top:18px;
}}
.detail-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px;}}
.detail-sym{{font-size:1.3rem;font-weight:900;color:var(--bl);}}
.levels-g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:10px;margin-top:12px;}}
.lev-card{{background:var(--card2);border:1px solid var(--brd);border-radius:10px;padding:10px 13px;}}
.lev-lbl{{font-size:0.65rem;color:var(--txt3);letter-spacing:1px;text-transform:uppercase;margin-bottom:5px;}}
.lev-v{{font-size:1rem;font-weight:800;}}
.lev-entry{{color:{BL};}}.lev-sl{{color:{RD};}}.lev-tp{{color:{GR};}}.lev-ext{{color:{AM};}}
.lev-sub{{font-size:0.67rem;color:var(--txt3);margin-top:2px;}}

/* ── FRESHNESS ── */
.f-ok {{background:{"#052E1C" if DARK else "#ECFDF5"};border:1px solid {"#166534" if DARK else "#A7F3D0"};border-radius:10px;padding:8px 14px;font-size:0.8rem;color:{"#4ADE80" if DARK else "#059669"};margin-bottom:12px;}}
.f-warn{{background:{AL};border:1px solid {AM};border-radius:10px;padding:8px 14px;font-size:0.8rem;color:{AM};margin-bottom:12px;}}
.f-exp {{background:{RL};border:1px solid {"#7F1D1D" if DARK else "#FECACA"};border-radius:10px;padding:8px 14px;font-size:0.8rem;color:{"#F87171" if DARK else "#DC2626"};margin-bottom:12px;}}

/* ── EMPTY ── */
.empty{{text-align:center;padding:60px 20px;}}
.empty-i{{font-size:2.8rem;opacity:.4;display:block;margin-bottom:12px;}}
.empty-t{{font-size:1.05rem;font-weight:700;color:var(--txt3);margin-bottom:6px;}}
.empty-s{{font-size:0.85rem;color:var(--txt3);opacity:.7;}}

/* ── FOOTER ── */
.habbi-footer{{
  background:{"#0A0C14" if DARK else "#0F172A"};
  padding:22px clamp(14px,3vw,36px);
  border-top:1px solid rgba(59,130,246,.2);
  margin-top:36px;
}}
.ft-top{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:14px;}}
.ft-brand{{font-size:1.1rem;font-weight:800;color:#fff;}}
.ft-contact{{
  display:flex;align-items:center;gap:8px;
  background:rgba(59,130,246,.15);border:1px solid rgba(59,130,246,.35);
  border-radius:20px;padding:6px 16px;font-size:0.82rem;color:#93C5FD;
  text-decoration:none;transition:background.15s;
}}
.ft-contact:hover{{background:rgba(59,130,246,.25);}}
.ft-links{{display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin-bottom:12px;}}
.ft-link{{font-size:0.78rem;color:rgba(255,255,255,.45);text-decoration:none;}}
.ft-link:hover{{color:rgba(255,255,.75);text-decoration:underline;}}
.ft-disc{{
  font-size:0.75rem;color:rgba(255,255,255,.35);
  text-align:center;line-height:1.6;
}}
.ft-disc-bar{{
  background:#000;padding:8px 16px;
  border-radius:6px;margin-top:10px;
  font-size:0.72rem;color:rgba(255,255,255,.55);text-align:center;
}}

/* Streamlit overrides */
div[data-testid="stProgressBar"]>div>div{{background:linear-gradient(90deg,#1D4ED8,#22C55E)!important;border-radius:3px!important;}}
div[data-testid="stProgressBar"]>div{{background:var(--brd)!important;border-radius:3px!important;}}
div[data-testid="stSuccess"]{{background:{"#052E1C" if DARK else "#F0FDF4"}!important;border:1px solid {"#166534" if DARK else "#A7F3D0"}!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;}}
div[data-testid="stError"] {{background:{"#2D0A0A" if DARK else "#FEF2"}!important;border:1px solid {"#7F1D1D" if DARK else "#FECACA"}!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;}}
div[data-testid="stWarning"]{{background:{"#1F1300" if DARK else "#FFFBEB"}!important;border:1px solid {"#78350F" if DARK else "#FDE68A"}!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;}}
div[data-testid="stInfo"] {{background:{"#0F1E4A" if DARK else "#EFF6FF"}!important;border:1px solid {"#1E3A8A" if DARK else "#BFDBFE"}!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;}}
.stButton>button{{font-family:var(--font)!important;font-size:0.9rem!important;font-weight:700!important;border-radius:10px!important;padding:10px 20px!important;transition:all.18s!important;border:none!important;min-height:42px!important;}}
.stButton>button[kind="primary"]{{background:linear-gradient(135deg,#1D4ED8,#7C3AED)!important;color:#fff!important;box-shadow:0 4px 14px rgba(29,78,216,.4)!important;}}
.stButton>button[kind="primary"]:hover{{transform:translateY(-1px)!important;}}
.stButton>button:not([kind="primary"]){{background:var(--card2)!important;color:var(--txt2)!important;border:1px solid var(--brd)!important;}}
div[data-baseweb="select"]>div{{background:var(--card)!important;border:1px solid var(--brd)!important;border-radius:10px!important;font-family:var(--font)!important;font-size:0.88rem!important;color:var(--txt)!important;min-height:40px!important;}}
div[data-baseweb="select"]>div:focus-within{{border-color:var(--bl)!important;box-shadow:0 0 0 3px rgba(59,130,246,.15)!important;}}
div[data-baseweb="input"]>div{{background:var(--card)!important;border:1px solid var(--brd)!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;min-height:40px!important;}}
.stSelectbox label,.stTextInput label,.stMultiSelect label,.stRadio label{{font-family:var(--font)!important;font-size:0.8rem!important;font-weight:600!important;color:var(--txt3)!important;}}
hr{{border:none!important;border-top:1px solid var(--brd)!important;margin:6px 0!important;}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# CACHED ENGINE
# ══════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def _run(ticker, smt):
    return E.run_engine(ticker, smt)

@st.cache_data(ttl=300, show_spinner=False)
def _row(ticker, smt):
    try:
        res = _run(ticker, smt)
        row = E.extract_row(res[0], ticker, smt)
        # سجّل السعر الحالي
        try: row["_cur"] = float(res[1]["Close"].iloc[-1])
        except: row["_cur"] = None
        return row
    except Exception:
        r = E.extract_row(None, ticker, smt)
        r["_cur"] = None
        return r

# ══════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════
def _age_h(ts):
    if ts is None: return 9999
    u = ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc)-u).total_seconds()/3600

def _is_exp(ts, h=24): return _age_h(ts)>=h
def _rr(v):
    try: return float(str(v).replace("1:",""))
    except: return 0.0

def _stars(grade):
    n={"A+":3,"A":3,"B":2,"C":1}.get(grade,0)
    return "".join(
        [f'<span class="star-on">★</span>' if i<n
         else f'<span class="star-off">☆</span>' for i in range(3)])

def _sbadge(grade):
    if grade in ("A+","A"): return '<span class="sb sb-active">نشط</span>'
    if grade=="B": return '<span class="sb sb-wait">منتظر</span>'
    return '<span class="sb sb-closed">مغلق</span>'

def _gpill(g):
    c={"A+":"gp-ap","A":"gp-a","B":"gp-b"}.get(g,"gp-sk")
    return f'<span class="gp {c}">{g}</span>'

def _sa_name(ticker):
    m={t:n for t,n in SA_STOCKS}
    return m.get(ticker,ticker)

# ══════════════════════════════════════════════════════
# MARKET STATUS — ساعات صحيحة
# ══════════════════════════════════════════════════════
def _us_market():
    try:
        import pytz; now=datetime.now(pytz.timezone("US/Eastern"))
    except: now=datetime.now(timezone.utc)-timedelta(hours=4)
    wd=now.weekday(); h,m,s=now.hour,now.minute,now.second
    is_open=wd<5 and (h,m)>=(9,30) and (h,m)<(16,0)
    def secs(hh,mm): return hh*3600+mm*60
    ns=secs(h,m)+s
    if is_open:
        rem=max(secs(16,0)-ns,0); hh2,r=divmod(rem,3600); mm2,ss2=divmod(r,60)
        return True, f"يغلق بعد: {hh2:02d}:{mm2:02d}:{ss2:02d}"
    if wd<5 and (h,m)<(9,30):
        nxt=secs(9,30)-ns
    else:
        days_ahead=(7-wd)%7
        if days_ahead==0: days_ahead=7
        nxt=days_ahead*86400+secs(9,30)-ns%86400
    nxt=max(int(nxt),1); hh2,r=divmod(nxt,3600); mm2,ss2=divmod(r,60)
    if hh2>=24:
        days=hh2//24; hh2=hh2%24
        return False, f"يفتح بعد: {days}ي {hh2}س {mm2}د"
    return False, f"يفتح بعد: {hh2}س {mm2}د {ss2}ث"

def _sa_market():
    try:
        import pytz; now=datetime.now(pytz.timezone("Asia/Riyadh"))
    except: now=datetime.now(timezone.utc)+timedelta(hours=3)
    wd=now.weekday(); h,m,s=now.hour,now.minute,now.second
    sa_work=wd in (6,0,1,2,3)
    is_open=sa_work and (h,m)>=(10,0) and (h,m)<(15,0)
    def secs(hh,mm): return hh*3600+mm*60
    ns=secs(h,m)+s
    if is_open:
        rem=max(secs(15,0)-ns,0); hh2,r=divmod(rem,3600); mm2,ss2=divmod(r,60)
        return True, f"يغلق بعد: {hh2:02d}:{mm2:02d}:{ss2:02d}"
    if sa_work and (h,m)<(10,0):
        nxt=secs(10,0)-ns
    else:
        if wd==3 and (h,m)>=(15,0): days_ahead=3
        elif wd==4: days_ahead=2
        elif wd==5: days_ahead=1
        else: days_ahead=1
        nxt=days_ahead*86400+secs(10,0)-ns%86400
    nxt=max(int(nxt),1); hh2,r=divmod(nxt,3600); mm2,ss2=divmod(r,60)
    if hh2>=24:
        days=hh2//24; hh2=hh2%24
        return False, f"يفتح بعد: {days}ي {hh2}س {mm2}د"
    return False, f"يفتح بعد: {hh2}س {mm2}د"

# ══════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════
def render_header():
    now_s = datetime.now(timezone.utc).strftime("%H:%M:%S")
    st.markdown(f"""
<div class="top-hdr">
  <div class="hdr-brand">
    <div class="brand-logo">ح</div>
    <div>
      <div class="brand-name">منصة الحبي للتداول</div>
      <div class="brand-sub">تداول ذكي • تحليل متقدم</div>
    </div>
  </div>
  <div class="hdr-controls">
    <div class="hdr-icon-btn" title="🔕 تنبيهات">🔔</div>
    <div class="hdr-icon-btn" title="🔊 صوت">🔊</div>
    <div class="hdr-clock" id="hdr-clk">{now_s}</div>
  </div>
</div>
<script>
(function(){{
  function tick(){{
    var d=new Date();
    var el=document.getElementById('hdr-clk');
    if(el){{
      var h=String(d.getUTCHours()).padStart(2,'0');
      var m=String(d.getUTCMinutes()).padStart(2,'0');
      var s=String(d.getUTCSeconds()).padStart(2,'0');
      el.textContent=h+':'+m+':'+s;
    }}
  }}
  setInterval(tick,1000);
}})();
</script>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# MARKET TABS
# ══════════════════════════════════════════════════════
def render_tabs():
    t = st.session_state.market_tab
    sa_cls = "mkt-tab active" if t=="SA" else "mkt-tab"
    us_cls = "mkt-tab active" if t=="US" else "mkt-tab"

    st.markdown(f"""
<div class="mkt-tabs">
  <span class="{sa_cls}">
    <span class="mkt-tag">SA</span>السوق السعودي
  </span>
  <span class="{us_cls}">
    <span class="mkt-tag">US</span>السوق الأمريكي
  </span>
</div>""", unsafe_allow_html=True)

    c1, c2, _ = st.columns([1,1,10])
    with c1:
        if st.button("🇸🇦 سعودي", use_container_width=True,
                     type="primary" if t=="SA" else "secondary", key="btn_sa"):
            st.session_state.market_tab="SA"
            st.session_state.radar_df=None
            st.session_state.radar_ts=None
            st.rerun()
    with c2:
        if st.button("🇺🇸 أمريكي", use_container_width=True,
                     type="primary" if t=="US" else "secondary", key="btn_us"):
            st.session_state.market_tab="US"
            st.session_state.radar_df=None
            st.session_state.radar_ts=None
            st.rerun()

# ══════════════════════════════════════════════════════
# STATUS BAR
# ══════════════════════════════════════════════════════
def render_status(ts):
    mkt=st.session_state.market_tab
    is_open, cd_str = _sa_market() if mkt=="SA" else _us_market()
    dot="open" if is_open else "closed"
    stxt="السوق مفتوح" if is_open else "السوق مغلق"
    scls="open" if is_open else "closed"
    ts_str=ts.astimezone(timezone.utc).strftime("%H:%M:%S") if ts else "--:--"

    st.markdown(f"""
<div class="sts-bar">
  <div class="sts-l">
    <div class="mkt-status {scls}">
      <div class="sts-dot {dot}"></div>{stxt}
    </div>
    <span class="sts-next">{cd_str}</span>
    <div class="sts-prog"><div class="sts-prog-fill"></div></div>
  </div>
  <div class="sts-r">
    <span>آخر تحديث: {ts_str}</span>
    <span>التحديث كل 5 دقائق</span>
  </div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# STAT CARDS
# ══════════════════════════════════════════════════════
def render_stat_cards(df, search_active=False):
    if df is None or df.empty or search_active:
        return
    total = len(df)
    active = len(df[df["Grade"].isin(["A+","A"])])
    wait = len(df[df["Grade"]=="B"])
    skip = len(df[df["Grade"].isin(["SKIP","C","ERR","TIMEOUT"])])
    st.markdown(f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-lbl">إجمالي الصفقات</div><div class="stat-v sv-wh">{total}</div></div>
  <div class="stat-card"><div class="stat-lbl">صفقات نشطة</div><div class="stat-v sv-gr">{active}</div></div>
  <div class="stat-card"><div class="stat-lbl">صفقات منتظرة</div><div class="stat-v sv-am">{wait}</div></div>
  <div class="stat-card"><div class="stat-lbl">غير مؤهلة</div><div class="stat-v sv-wh">{skip}</div></div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# CONTROLS ROW
# ══════════════════════════════════════════════════════
def render_controls():
    c1,c2,c3,c4,c5 = st.columns([2,1.4,1.4,1.2,1.1])
    with c1:
        s=st.text_input("بحث","",placeholder="ابحث بالرمز…",
                         label_visibility="collapsed",key="srch_inp")
        st.session_state.search_q=s.strip().upper()
    with c2:
        GO=["جميع القوة","A+ ذهبي فقط","A+ و A (ممتاز)","B فأعلى"]
        gf=st.selectbox("قوة",GO,index=GO.index(st.session_state.filter_grade)
                         if st.session_state.filter_grade in GO else 0,
                         label_visibility="collapsed",key="gf_dd")
        st.session_state.filter_grade=gf
    with c3:
        SO=["ترتيب بالقوة","ترتيب بـ R:R","ترتيب بالرمز"]
        sv=st.selectbox("ترتيب",SO,index=SO.index(st.session_state.sort_by)
                         if st.session_state.sort_by in SO else 0,
                         label_visibility="collapsed",key="sort_dd")
        st.session_state.sort_by=sv
    with c4:
        scan=st.button("📡 مسح الرادار",type="primary",
                        use_container_width=True,key="scan_main")
    with c5:
        if st.button("🔄 تحديث",use_container_width=True,key="ref_main"):
            _run.clear(); _row.clear()
            st.session_state.radar_df=None
            st.session_state.radar_ts=None
            st.rerun()

    vc1,vc2,_ = st.columns([1.5,2,8])
    with vc1:
        vm=st.radio("عرض",["جدول","بطاقات"],
                     index=["جدول","بطاقات"].index(st.session_state.view_mode),
                     horizontal=True,label_visibility="collapsed",key="vm_r")
        st.session_state.view_mode=vm
    with vc2:
        if st.session_state.market_tab=="US":
            us_k=st.selectbox("قائمة",list(US_WATCHLIST_MAP.keys()),
                               index=list(US_WATCHLIST_MAP.keys()).index(
                                   st.session_state.us_wl)
                               if st.session_state.us_wl in US_WATCHLIST_MAP else 0,
                               label_visibility="collapsed",key="us_wl_dd")
            st.session_state.us_wl=us_k

    return scan

# ══════════════════════════════════════════════════════
# SCAN
# ══════════════════════════════════════════════════════
def do_scan(watchlist, cheap_mode=False):
    E.SWEEP_WICK_MIN=8.0
    total,results=len(watchlist),[]
    pb=st.progress(0,text="جارٍ المسح…")
    done=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs={pool.submit(_row,p[0],p[1]):p for p in watchlist}
        for fut in as_completed(futs):
            tkr,smt=futs[fut]
            try: r=fut.result(timeout=25)
            except TimeoutError:
                r=E.extract_row(None,tkr,smt); r["Grade"]="TIMEOUT"; r["_cur"]=None
            if cheap_mode and r.get("Bias","")=="Short":
                r["Grade"]="SKIP"; r["_grade_rank"]=99; r["_score_num"]=0
            r["_scan_date"]=datetime.now().strftime("%Y-%m-%d")
            results.append(r); done+=1
            g=r.get("Grade","?"); sym={"A+":"⭐","A":"✅","B":"⚠️"}.get(g,"·")
            pb.progress(done/total,text=f"مسح {done}/{total} · {tkr} {sym}")
    pb.empty()
    df=(pd.DataFrame(results)
         .sort_values(by=["_grade_rank","_score_num"],ascending=[True,False])
         .reset_index(drop=True))
    st.session_state.radar_df=df
    st.session_state.radar_ts=datetime.now(timezone.utc)
    n_ap=len(df[df["Grade"]=="A+"]); n_a=len(df[df["Grade"]=="A"]); n_b=len(df[df["Grade"]=="B"])
    st.success(f"✅ اكتمل المسح · {len(df)} رمزاً · A+: {n_ap} · A: {n_a} · B: {n_b}")

# ══════════════════════════════════════════════════════
# FILTER
# ══════════════════════════════════════════════════════
def apply_filters(df):
    if df is None or df.empty: return pd.DataFrame()
    if _is_exp(st.session_state.radar_ts,24): return pd.DataFrame()
    d=df.copy()
    q=st.session_state.search_q
    if q: d=d[d["Ticker"].str.contains(q,na=False)]
    gf=st.session_state.filter_grade
    if gf=="A+ ذهبي فقط": d=d[d["Grade"]=="A+"]
    elif gf=="A+ و A (ممتاز)": d=d[d["Grade"].isin(["A+","A"])]
    elif gf=="B فأعلى": d=d[d["Grade"].isin(["A+","A","B"])]
    sv=st.session_state.sort_by
    if sv=="ترتيب بـ R:R":
        d["_rr_n"]=d["Best R:R"].apply(_rr); d=d.sort_values("_rr_n",ascending=False)
    elif sv=="ترتيب بالرمز": d=d.sort_values("Ticker")
    return d.reset_index(drop=True)

# ══════════════════════════════════════════════════════
# TABLE VIEW
# ══════════════════════════════════════════════════════
def render_table(df, sa_mode=False):
    if df is None or df.empty:
        st.markdown('<div class="empty"><span class="empty-i">📭</span>'
                    '<div class="empty-t">لا توجد صفقات مطابقة</div>'
                    '<div class="empty-s">ابدأ مسح الرادار أو عدّل الفلاتر</div></div>',
                    unsafe_allow_html=True)
        return

    html = '<div class="tbl-wrap">'
    html += ('<div class="tbl-hdr-row">'
             '<div class="th">#</div>'
             '<div class="th">الرمز</div>'
             '<div class="th">الاسم</div>'
             '<div class="th">التاريخ</div>'
             '<div class="th">الحالة</div>'
             '<div class="th">القوة</div>'
             '<div class="th">نقطة الدخول</div>'
             '<div class="th">السعر الحالي</div>'
             '<div class="th">وقف الخسارة</div>'
             '<div class="th">هدف 1</div>'
             '<div class="th">الموجة الكاملة</div>'
             '<div class="th">نوع السيولة</div>'
             '</div>')

    for idx, row in df.iterrows():
        row_num = idx+1
        ticker = str(row.get("Ticker","?"))
        grade = str(row.get("Grade","?"))
        bias = str(row.get("Bias","—"))
        entry = row.get("Entry","—")
        sl = row.get("SL","—")
        tp1 = row.get("TP1","—")
        wave = row.get("Wave Target","—")
        if wave in (None,"","—",0,0.0): wave = row.get("TP2 (Ext)","—")
        liq = str(row.get("نوع السيولة","—"))
        cur = row.get("_cur",None)
        scan_dt = row.get("_scan_date",datetime.now().strftime("%Y-%m-%d"))

        name = _sa_name(ticker) if sa_mode else ticker
        try:
            cur_str = f"{float(cur):.3f}" if cur not in (None, "", 0) else str(entry)
        except:
            cur_str = str(entry)
        if wave in (None,"","—","0","0.0",0,0.0): wave="—"

        try:
            e_f=float(str(entry)); c_f=float(str(cur or entry))
            pnl=(c_f-e_f)/e_f*100 if bias=="Long" else (e_f-c_f)/e_f*100
            cur_cls="c-gr" if pnl>=0 else "c-rd"
        except:
            cur_cls="muted"

        stars_h = f'<div class="stars-row">{_stars(grade)}</div>'
        badge_h = _sbadge(grade)
        bias_cls = "c-gr" if bias=="Long" else "c-rd"

        html += (f'<div class="tbl-row-item">'
                 f'<div class="td muted">{row_num}</div>'
                 f'<div class="td bold">{ticker}</div>'
                 f'<div class="td">{name}</div>'
                 f'<div class="td muted">{scan_dt}</div>'
                 f'<div class="td">{badge_h}</div>'
                 f'<div class="td">{stars_h}</div>'
                 f'<div class="td num {bias_cls}">{entry}</div>'
                 f'<div class="td num {cur_cls}">{cur_str}</div>'
                 f'<div class="td num c-rd">{sl}</div>'
                 f'<div class="td num c-gr">{tp1}</div>'
                 f'<div class="td num c-am">{wave}</div>'
                 f'<div class="td muted" style="font-size:.82rem;">{liq}</div>'
                 f'</div>')

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# CARD VIEW
# ══════════════════════════════════════════════════════
def render_cards(df, sa_mode=False):
    if df is None or df.empty:
        st.markdown('<div class="empty"><span class="empty-i">📭</span>'
                    '<div class="empty-t">لا توجد صفقات</div></div>',
                    unsafe_allow_html=True)
        return

    html = '<div class="cards-grid">'
    for _, row in df.iterrows():
        ticker = str(row.get("Ticker","?"))
        grade = str(row.get("Grade","?"))
        bias = str(row.get("Bias","—"))
        entry = row.get("Entry","—")
        sl = row.get("SL","—")
        tp1 = row.get("TP1","—")
        wave = row.get("Wave Target","—")
        if wave in (None,"","—","0","0.0",0,0.0): wave=row.get("TP2 (Ext)","—")
        if wave in (None,"","—","0","0.0",0,0.0): wave="—"
        rr = row.get("Best R:R","—")
        liq = str(row.get("نوع السيولة","—"))
        mss = str(row.get("MSS","—"))
        scan_dt= row.get("_scan_date",datetime.now().strftime("%Y-%m-%d"))
        name = _sa_name(ticker) if sa_mode else ticker

        bc = "tc-long" if bias=="Long" else "tc-short"
        bias_ar= "شراء ▲" if bias=="Long" else "بيع ▼"
        bias_c = GR2 if bias=="Long" else RD2
        stars_h= f'<div class="stars-row">{_stars(grade)}</div>'
        badge_h= _sbadge(grade)
        pill_h = _gpill(grade)

        html += (f'<div class="trade-card {bc}">'
                 f'<div class="card-top">'
                 f'<div><div class="card-sym">{ticker}</div>'
                 f'<div class="card-name">{name}</div></div>'
                 f'<div style="text-align:left;">{pill_h}<div style="margin-top:4px;">{stars_h}</div></div>'
                 f'</div>'
                 f'<div class="card-grid">'
                 f'<div><div class="cf-l">الاتجاه</div>'
                 f'<div class="cf-v" style="color:{bias_c}">{bias_ar}</div></div>'
                 f'<div><div class="cf-l">نقطة الدخول</div>'
                 f'<div class="cf-v">{entry}</div></div>'
                 f'<div><div class="cf-l">وقف الخسارة</div>'
                 f'<div class="cf-v" style="color:{RD2}">{sl}</div></div>'
                 f'<div><div class="cf-l">هدف 1</div>'
                 f'<div class="cf-v" style="color:{GR}">{tp1}</div></div>'
                 f'<div><div class="cf-l">الموجة الكاملة</div>'
                 f'<div class="cf-v" style="color:{AM}">{wave}</div></div>'
                 f'<div><div class="cf-l">أفضل R:R</div>'
                 f'<div class="cf-v">{rr}</div></div>'
                 f'<div><div class="cf-l">نوع السيولة</div>'
                 f'<div class="cf-v" style="font-size:.82rem">{liq}</div></div>'
                 f'<div><div class="cf-l">MSS</div>'
                 f'<div class="cf-v" style="font-size:.82rem">{mss}</div></div>'
                 f'</div>'
                 f'<div class="card-bot">'
                 f'<span class="card-date">📅 {scan_dt}</span>{badge_h}'
                 f'</div></div>')
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# DETAIL PANEL
# ══════════════════════════════════════════════════════
def render_detail(df, watchlist):
    if df is None or df.empty: return
    tickers=df["Ticker"].tolist()
    if not tickers: return

    dc1,dc2,_ = st.columns([2,1,9])
    with dc1:
        sel=st.selectbox("🔬 اختر الرمز للتحليل",tickers,
                          key="drill_sel",label_visibility="visible")
    with dc2:
        st.markdown("<br>",unsafe_allow_html=True)
        load=st.button("تحميل الشارت",use_container_width=True,key="drill_load")

    if load and sel: st.session_state.drill=sel

    if st.session_state.drill and st.session_state.drill in tickers:
        tkr=st.session_state.drill
        smt_p=next((s for t,s in watchlist if t==tkr),"QQQ")
        row=df[df["Ticker"]==tkr]
        grade=row["Grade"].values[0] if not row.empty else "—"

        with st.spinner(f"تحميل {tkr}…"):
            try:
                res=_run(tkr,smt_p)
                setup,df_d,df_h1,df_m15,liq_lvls,sw_d,dol=res
                cur=float(df_d["Close"].iloc[-1])
            except Exception as ex:
                st.error(f"خطأ: {ex}"); return

        if setup:
            wave_str=f"{setup.wave_target:.4f}" if setup.wave_target else "—"
            tp_cards=""
            for t in setup.targets[:4]:
                cls="lev-ext" if t.kind in ("ext_liq","ext_ext") else "lev-tp"
                lbl=t.label[:22] if len(t.label)>22 else t.label
                tp_cards+=(f'<div class="lev-card">'
                           f'<div class="lev-lbl">{lbl}</div>'
                           f'<div class="lev-v {cls}">{t.price:.4f}</div>'
                           f'<div class="lev-sub">R:R {t.rr:.1f}x</div></div>')

            st.markdown(f"""
<div class="detail-wrap">
  <div class="detail-top">
    <div style="display:flex;align-items:center;gap:10px;">
      <span class="detail-sym">{tkr}</span>
      {_gpill(grade)}
      <span style="font-size:.82rem;color:{TXT3};">نوع السيولة: {setup.liquidity_type}</span>
    </div>
  </div>
  <div class="levels-g">
    <div class="lev-card">
      <div class="lev-lbl">نقطة الدخول</div>
      <div class="lev-v lev-entry">{setup.entry:.4f}</div>
      <div class="lev-sub">50% EQ · IFVG</div>
    </div>
    <div class="lev-card">
      <div class="lev-lbl">وقف الخسارة</div>
      <div class="lev-v lev-sl">{setup.stop_loss:.4f}</div>
    </div>
    {tp_cards}
    <div class="lev-card">
      <div class="lev-lbl">🎯 الموجة الكاملة</div>
      <div class="lev-v lev-ext">{wave_str}</div>
      <div class="lev-sub">External Liquidity</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        cc,lc = st.columns([2.8,1],gap="medium")
        with cc:
            fig=E.build_chart(df_d,setup,liq_lvls,sw_d,dol,
                               ticker=tkr,n_candles=80,htf_interval="1d")
            st.plotly_chart(fig,use_container_width=True,
                            config={"displayModeBar":True,"displaylogo":False,
                                    "modeBarButtonsToRemove":["select2d","lasso2d"]})
        with lc:
            if setup:
                st.markdown("**سجل القرار**")
                for lg in setup.decision_log:
                    ico="🟢" if lg.score_delta>0 else "🔴" if lg.score_delta<0 else "⚪"
                    st.markdown(f"{ico} **{lg.stage}** \n{lg.finding} \n*{lg.score_delta:+d} نقطة*")
                    st.markdown("---")

# ══════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════
def render_footer():
    st.markdown("""
<div class="habbi-footer">
  <div class="ft-top">
    <div class="ft-brand">🦅 منصة الحبي للتداول</div>
    <a href="mailto:support@alhabbi.com" class="ft-contact">
      ✉️ &nbsp;تواصل مع الإدارة
    </a>
  </div>
  <div class="ft-links">
    <span class="ft-link">إخلاء المسؤولية واتفاقية الاستخدام</span>
    <span style="color:rgba(255,255,255,.2)">•</span>
    <span class="ft-link">سياسة الخصوصية</span>
    <span style="color:rgba(255,255,255,.2)">•</span>
    <span class="ft-link">منصة تعليمية – ليست نصيحة مالية</span>
    <span style="color:rgba(255,255,255,.2)">•</span>
    <span style="font-size:.78rem;color:rgba(255,255,255,.4);">© 2026</span>
  </div>
  <div class="ft-disc-bar">
    جميع البيانات لأغراض تثقيفية وتعليمية فقط وليست توصية مالية.
    التداول ينطوي على مخاطر عالية. استخدامك للمنصة يعني موافقتك على
    <span style="text-decoration:underline;cursor:pointer;">إخلاء المسؤولية</span>.
  </div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
def main():
    render_header()
    render_tabs()

    mkt=st.session_state.market_tab

    if mkt=="SA":
        watchlist=SA_WATCHLIST; sa_mode=True; cheap_mode=False
    else:
        wl_key=st.session_state.us_wl
        watchlist=US_WATCHLIST_MAP.get(wl_key,US_WATCHLIST_MAP["تقنية كبرى (30)"])
        sa_mode=False
        cheap_mode=(wl_key==CHEAP_KEY)

    render_status(st.session_state.radar_ts)

    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

    scan=render_controls()

    if scan:
        do_scan(watchlist, cheap_mode=cheap_mode)

    ts=st.session_state.radar_ts; df=st.session_state.radar_df
    search_active = bool(st.session_state.search_q.strip())

    if ts is not None:
        h=_age_h(ts)
        if h>=24:
            st.markdown('<div class="f-exp">⏰ البيانات انتهت صلاحيتها (أكثر من 24 ساعة) — يُرجى إعادة المسح.</div>',
                        unsafe_allow_html=True)
            df=None
        elif h>=12:
            st.markdown(f'<div class="f-warn">⚠️ البيانات عمرها {h:.0f} ساعة — يُنصح بالتحديث.</div>',
                        unsafe_allow_html=True)
        else:
            ts_s=ts.astimezone(timezone.utc).strftime("%H:%M UTC")
            st.markdown(f'<div class="f-ok">✅ بيانات حية · آخر مسح: {ts_s} (منذ {h:.1f} ساعة)</div>',
                        unsafe_allow_html=True)

    render_stat_cards(df, search_active=search_active)

    filtered=apply_filters(df) if df is not None else None

    if st.session_state.view_mode=="جدول":
        render_table(filtered, sa_mode=sa_mode)
    else:
        render_cards(filtered, sa_mode=sa_mode)

    if filtered is not None and not filtered.empty:
        st.markdown("<br>",unsafe_allow_html=True)
        render_detail(filtered, watchlist)

    st.markdown('</div>', unsafe_allow_html=True)
    render_footer()

if __name__=="__main__":
    main()
