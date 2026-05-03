"""
منصة الحبي للتداول — Pro v6
تصميم احترافي + Lightweight Charts v5 + أداء محسن
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz
import engine as E

# استيراد الشارت الحديث
from lightweight_charts_v5 import lightweight_charts_v5_component

st.set_page_config(
    page_title="منصة الحبي Pro",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== SESSION ==========
for k,v in {
    "theme":"dark","market":"US","radar_df":None,"radar_ts":None,
    "drill":None,"search":"","grade":"الكل","sort":"القوة",
    "us_list":"تقنية كبرى (30)","view":"بطاقات"
}.items():
    if k not in st.session_state: st.session_state[k]=v

DARK = st.session_state.theme == "dark"

# ========== WATCHLISTS ==========
SA = [("2222","أرامكو"),("1120","الراجحي"),("2010","سابك"),("7010","STC"),("1180","الأهلي")]
US_TECH = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","AMD","QCOM","ORCL","CRM","ADBE","INTC","MU"]
US_BLUE = ["JPM","BAC","V","MA","JNJ","UNH","LLY","WMT","COST","XOM","CVX"]
US_CHEAP = ["F","SOFI","PLTR","SNAP","UBER","NIO","LCID"]

WL = {
    "تقنية كبرى (30)": [(t,"QQQ") for t in US_TECH],
    "قيادية (40)": [(t,"SPY") for t in US_BLUE],
    "رخيصة - صاعد فقط": [(t,"SPY") for t in US_CHEAP],
}

# ========== TOKENS ==========
if DARK:
    BG,CARD,BRD,TXT,TXT2 = "#070B14","#0F1524","#1E293B","#E2E8F0","#94A3B8"
    ACC,GR,RD,AM = "#3B82F6","#22C55E","#EF4444","#F59E0B"
else:
    BG,CARD,BRD,TXT,TXT2 = "#F8FAFC","#FFFFFF","#E2E8F0","#0F172A","#64748B"
    ACC,GR,RD,AM = "#2563EB","#16A34A","#DC2626","#D97706"

# ========== CSS مختصر احترافي ==========
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
:root{{--bg:{BG};--card:{CARD};--brd:{BRD};--txt:{TXT};--txt2:{TXT2};--acc:{ACC};--gr:{GR};--rd:{RD};--am:{AM};}}
html,body{{background:var(--bg)!important;font-family:'Tajawal',sans-serif!important;direction:rtl}}
.main.block-container{{padding:0!important;max-width:1400px}}
.glass{{background:rgba(15,21,36,0.7);backdrop-filter:blur(12px);border:1px solid var(--brd);border-radius:16px}}
.header{{position:sticky;top:0;z-index:99;padding:14px 28px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--brd);background:var(--bg)}}
.logo{{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--acc),#7C3AED);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:20px;box-shadow:0 8px 20px rgba(59,130,246,.3)}}
.brand{{font-size:1.4rem;font-weight:900;color:var(--txt)}}
.tab{{padding:10px 18px;border-bottom:3px solid transparent;cursor:pointer;font-weight:700;color:var(--txt2)}}
.tab.active{{color:var(--acc);border-color:var(--acc)}}
.card{{background:var(--card);border:1px solid var(--brd);border-radius:16px;padding:18px;transition:.2s}}
.card:hover{{transform:translateY(-2px);box-shadow:0 10px 30px rgba(0,0,0,.15)}}
.badge{{padding:4px 10px;border-radius:20px;font-size:.75rem;font-weight:700}}
.badge-a{{background:rgba(34,197,94,.15);color:var(--gr);border:1px solid rgba(34,197,94,.3)}}
.badge-b{{background:rgba(245,158,11,.15);color:var(--am);border:1px solid rgba(245,158,11,.3)}}
.stat{{text-align:center}}
.stat-v{{font-size:2rem;font-weight:900}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
</style>
""", unsafe_allow_html=True)

# ========== CACHE محسن ==========
@st.cache_data(ttl=300, show_spinner=False)
def analyze(ticker, smt):
    try:
        res = E.run_engine(ticker, smt)
        setup, df_d, *_ = res
        row = E.extract_row(res[0], ticker, smt)
        row["_cur"] = float(df_d["Close"].iloc[-1]) if not df_d.empty else None
        row["_df"] = df_d
        row["_setup"] = setup
        return row
    except Exception:
        r = E.extract_row(None, ticker, smt); r["_cur"]=None; r["_df"]=pd.DataFrame(); r["_setup"]=None
        return r

# ========== MARKET STATUS ==========
def market_status(mkt):
    tz = pytz.timezone("Asia/Riyadh") if mkt=="SA" else pytz.timezone("US/Eastern")
    now = datetime.now(tz)
    if mkt=="SA":
        open = now.weekday() in [6,0,1,2,3] and 10 <= now.hour < 15
    else:
        open = now.weekday()<5 and (9,30) <= (now.hour,now.minute) < (16,0)
    return open, now.strftime("%H:%M:%S")

# ========== HEADER ==========
def header():
    open_us,_ = market_status("US")
    open_sa,_ = market_status("SA")
    st.markdown(f"""
    <div class="header glass">
      <div style="display:flex;gap:12px;align-items:center">
        <div class="logo">ح</div>
        <div>
          <div class="brand">منصة الحبي Pro</div>
          <div style="font-size:.75rem;color:var(--txt2)">تداول ذكي • تحليل لحظي</div>
        </div>
      </div>
      <div style="display:flex;gap:8px">
        <div class="tab {'active' if st.session_state.market=='SA' else ''}" onclick="window.parent.postMessage({{type:'sa'}},'*')">🇸🇦 سعودي {'🟢' if open_sa else '🔴'}</div>
        <div class="tab {'active' if st.session_state.market=='US' else ''}" onclick="window.parent.postMessage({{type:'us'}},'*')">🇺🇸 أمريكي {'🟢' if open_us else '🔴'}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

header()
c1,c2 = st.columns([1,1])
if c1.button("سعودي", use_container_width=True): st.session_state.market="SA"; st.rerun()
if c2.button("أمريكي", use_container_width=True): st.session_state.market="US"; st.rerun()

# ========== CONTROLS ==========
watch = [(t,f"{t}.SR") for t,_ in SA] if st.session_state.market=="SA" else WL[st.session_state.us_list]
if st.session_state.market=="US":
    st.session_state.us_list = st.selectbox("القائمة", list(WL.keys()))

col1,col2,col3 = st.columns([2,1,1])
st.session_state.search = col1.text_input("بحث", placeholder="رمز...")
st.session_state.grade = col2.selectbox("القوة", ["الكل","A+","A","B"])
if col3.button("📡 مسح", type="primary", use_container_width=True):
    prog = st.progress(0)
    rows=[]
    with ThreadPoolExecutor(6) as ex:
        futs = {ex.submit(analyze,t,s):t for t,s in watch}
        for i,f in enumerate(as_completed(futs)):
            rows.append(f.result()); prog.progress((i+1)/len(watch))
    df = pd.DataFrame(rows).sort_values(["_grade_rank","_score_num"], ascending=[True,False])
    st.session_state.radar_df = df
    st.session_state.radar_ts = datetime.now(timezone.utc)
    prog.empty(); st.success(f"تم مسح {len(df)} سهم")

df = st.session_state.radar_df
if df is not None and not df.empty:
    # فلترة
    if st.session_state.search: df = df[df["Ticker"].str.contains(st.session_state.search.upper())]
    if st.session_state.grade!= "الكل": df = df[df["Grade"]==st.session_state.grade]

    # إحصائيات
    a = len(df[df.Grade=="A+"]); b = len(df[df.Grade=="A"]); c = len(df[df.Grade=="B"])
    s1,s2,s3,s4 = st.columns(4)
    for col,lbl,val,clr in [(s1,"إجمالي",len(df),TXT),(s2,"A+",a,GR),(s3,"A",b,ACC),(s4,"B",c,AM)]:
        col.markdown(f"<div class='card stat'><div style='color:var(--txt2);font-size:.8rem'>{lbl}</div><div class='stat-v' style='color:{clr}'>{val}</div></div>", unsafe_allow_html=True)

    # عرض بطاقات
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    for _,r in df.head(24).iterrows():
        tkr = r["Ticker"]; grd = r["Grade"]; bias = r["Bias"]
        entry = r["Entry"]; sl = r["SL"]; tp1 = r["TP1"]
        badge = "badge-a" if grd in ["A+","A"] else "badge-b"
        clr = GR if bias=="Long" else RD
        st.markdown(f"""
        <div class="card">
          <div style="display:flex;justify-content:space-between">
            <div style="font-weight:900;font-size:1.1rem">{tkr}</div>
            <div class="badge {badge}">{grd}</div>
          </div>
          <div style="margin:10px 0;color:{clr};font-weight:700">{'شراء ▲' if bias=='Long' else 'بيع ▼'}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.9rem">
            <div>دخول<br><b>{entry}</b></div>
            <div>وقف<br><b style="color:var(--rd)">{sl}</b></div>
            <div>هدف1<br><b style="color:var(--gr)">{tp1}</b></div>
            <div>حالي<br><b>{r['_cur']:.2f if r['_cur'] else '—'}</b></div>
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # تفاصيل الشارت
    pick = st.selectbox("اختر سهم للتحليل العميق", df["Ticker"].tolist())
    if pick:
        row = next(r for _,r in df.iterrows() if r["Ticker"]==pick)
        setup = row["_setup"]; df_d = row["_df"]
        if setup is not None and not df_d.empty:
            # تحويل للشارت
            candles = [{"time":d.strftime("%Y-%m-%d"),"open":float(o),"high":float(h),"low":float(l),"close":float(c)}
                       for d,o,h,l,c in zip(df_d.index, df_d.Open, df_d.High, df_d.Low, df_d.Close)]

            charts = [{
                "chart": {"layout":{"background":{"color":CARD},"textColor":TXT}},
                "series": [
                    {"type":"Candlestick","data":candles,"options":{"upColor":GR,"downColor":RD}},
                    {"type":"Line","data":[{"time":c["time"],"value":float(setup.entry)} for c in candles[-60:]],"options":{"color":ACC,"lineWidth":2}},
                ],
                "priceLines": [
                    {"price":float(setup.entry),"color":ACC,"title":"دخول"},
                    {"price":float(setup.stop_loss),"color":RD,"title":"وقف"},
                ],
                "height": 420
            }]

            lightweight_charts_v5_component(
                name=f"{pick} chart",
                charts=charts,
                height=440
            ) # الاستدعاء كما في الوثائق الرسمية

            st.info(f"نوع السيولة: {setup.liquidity_type} | R:R {setup.targets[0].rr:.1f}x")
else:
    st.markdown("<div style='text-align:center;padding:60px;color:var(--txt2)'>ابدأ بمسح الرادار لعرض الفرص</div>", unsafe_allow_html=True)
