"""
app.py — منصة الحبي للتداول v7 Pro
نسخة احترافية كاملة - خلفية فاتحة فقط
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="منصة الحبي Pro", page_icon="🦅", layout="wide", initial_sidebar_state="expanded")

# ========== SESSION ==========
for k,v in {
    "market_tab":"US","radar_df":None,"radar_ts":None,"drill":None,"search_q":"",
    "sort_by":"القوة","filter_grade":"جميع القوة","view_mode":"جدول","us_wl":"تقنية كبرى (30)",
    "auto_refresh":False,"capital":100000,"risk_pct":1.0,"journal":pd.DataFrame(columns=["التاريخ","الرمز","الاتجاه","دخول","وقف","هدف","نتيجة %"])
}.items():
    if k not in st.session_state: st.session_state[k]=v

# ========== ثيم فاتح ثابت - لا أسود ==========
BG="#F8FAFC"; CARD="#FFFFFF"; CARD2="#F7F9FF"; BRD="#E2E8F0"
TXT="#0F1629"; TXT2="#4A5680"; TXT3="#9AA3BA"
TBLH="#F7F9FF"; TBLHV="#EEF2FA"; HDR_BG="#FFFFFF"; STS_BG="#F7F9FF"
BL="#2563EB"; GR="#16A34A"; RD="#DC2626"; AM="#D97706"
GR2="#16A34A"; RD2="#DC2626"; AM2="#CA8A04"
GL="#DCFCE7"; RL="#FEE2E2"; BLL="#DBEAFE"; AL="#FEF9C3"

# ========== CSS الأصلي كامل ==========
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
:root{{--bg:{BG};--card:{CARD};--card2:{CARD2};--brd:{BRD};--txt:{TXT};--txt2:{TXT2};--txt3:{TXT3};--tblh:{TBLH};--tblhv:{TBLHV};--bl:{BL};--gr:{GR};--rd:{RD};--am:{AM};--font:'Tajawal',sans-serif;}}
html,body{{background:var(--bg)!important;font-family:var(--font)!important;color:var(--txt)!important;direction:rtl!important}}
.main.block-container{{padding:0!important;max-width:100%!important}}
.top-hdr{{background:{HDR_BG};padding:0 36px;height:68px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--brd);position:sticky;top:0;z-index:100;box-shadow:0 2px 10px rgba(0,0,0,.05)}}
.brand-logo{{width:46px;height:46px;background:linear-gradient(135deg,var(--bl),#7C3AED);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;font-weight:900;color:#fff}}
.brand-name{{font-size:1.5rem;font-weight:900}}
.stats-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}}
.stat-card{{background:var(--card);border:1px solid var(--brd);border-radius:16px;padding:18px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.stat-v{{font-size:2.2rem;font-weight:900}}
.tbl-wrap{{background:var(--card);border:1px solid var(--brd);border-radius:16px;overflow:hidden}}
.tbl-hdr-row,.tbl-row-item{{display:grid;grid-template-columns:50px 90px 110px 95px 80px 110px 115px 110px 115px 100px;padding:10px 16px;align-items:center}}
.tbl-hdr-row{{background:var(--tblh);border-bottom:2px solid var(--brd);font-weight:700;color:var(--txt3);font-size:.8rem}}
.tbl-row-item{{border-bottom:1px solid var(--brd);min-height:62px;transition:.15s}}
.tbl-row-item:hover{{background:var(--tblhv)}}
.sb{{padding:5px 14px;border-radius:20px;font-size:.8rem;font-weight:700}}
.sb-active{{background:#DCFCE7;color:#15803D}}.sb-wait{{background:#FEF9C3;color:#854D0E}}.sb-closed{{background:#F1F5F9;color:#64748B}}
.cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:16px}}
.trade-card{{background:var(--card);border:1px solid var(--brd);border-radius:16px;padding:20px;transition:.2s;position:relative}}
.trade-card:hover{{transform:translateY(-3px);box-shadow:0 12px 24px rgba(0,0,0,.08)}}
.trade-card::before{{content:'';position:absolute;top:0;right:0;width:100%;height:4px;background:linear-gradient(90deg,var(--bl),var(--gr))}}
</style>
""", unsafe_allow_html=True)

# ========== WATCHLISTS كاملة ==========
SA_STOCKS = [("2222","أرامكو"),("1120","الراجحي"),("2010","سابك"),("7010","STC"),("1180","الأهلي"),("1211","معادن"),("2350","سافكو"),("4190","جرير"),("2380","بترو رابغ"),("4003","التعاونية"),("2030","بنك الجزيرة"),("1150","الأول"),("1060","بنك الرياض"),("2280","المراعي"),("4321","بوان")]
SA_WATCHLIST = [(t,"2222.SR") for t,_ in SA_STOCKS]
TECH_30 = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","AMD","QCOM","ORCL","CRM","ADBE","INTC","TXN","MU","AMAT","LRCX","KLAC","MRVL","NFLX","PYPL","SHOP","SNOW","PANW","CRWD","ZS","DDOG","MSTR","PLTR"]
BLUE_40 = ["JPM","BAC","GS","MS","BRK-B","V","MA","AXP","WFC","C","JNJ","UNH","LLY","ABBV","PFE","MRK","TMO","ABT","DHR","BMY","WMT","HD","COST","TGT","MCD","SBUX","NKE","LOW","TJX","AMGN","XOM","CVX","COP","SLB","CAT","RTX","HON","UPS","BA","GE"]
CHEAP_20 = ["F","AAL","SOFI","RIVN","SNAP","UBER","LYFT","PLUG","NIO","XPEV","CLNE","NOK","BB","SIRI","VALE","ITUB","PBR","KGC","BTG","LCID"]
US_WATCHLIST_MAP = {"تقنية كبرى (30)":[(t,"QQQ") for t in TECH_30],"قيادية S&P (40)":[(t,"SPY") for t in BLUE_40],"الكل (70)":[(t,"QQQ") for t in TECH_30]+[(t,"SPY") for t in BLUE_40],"رخيصة (<$20)":[(t,"SPY") for t in CHEAP_20],"كريبتو ETF":[(t,"QQQ") for t in ["MSTR","COIN","BITO","GBTC"]]}

# ========== أدوات احترافية - جديد ==========
with st.sidebar:
    st.markdown("### 🛠️ لوحة التحكم الاحترافية")
    st.session_state.auto_refresh = st.toggle("تحديث تلقائي", value=st.session_state.auto_refresh)
    if st.session_state.auto_refresh: st_autorefresh(interval=60000, key="auto")

    st.markdown("---")
    st.markdown("#### 💰 حاسبة المخاطرة")
    st.session_state.capital = st.number_input("رأس المال", 10000, 5000000, st.session_state.capital, step=10000)
    st.session_state.risk_pct = st.slider("مخاطرة %", 0.5, 3.0, st.session_state.risk_pct, 0.1)
    risk_amount = st.session_state.capital * st.session_state.risk_pct / 100
    st.success(f"مبلغ المخاطرة: {risk_amount:,.0f} ريال")

    st.markdown("---")
    st.markdown("#### 📊 المفكرة")
    st.session_state.journal = st.data_editor(st.session_state.journal, num_rows="dynamic", use_container_width=True, hide_index=True)

    if st.session_state.radar_df is not None:
        st.markdown("---")
        if st.button("📥 تصدير Excel", use_container_width=True):
            st.session_state.radar_df.to_excel("radar.xlsx", index=False)
            with open("radar.xlsx","rb") as f: st.download_button("تحميل الملف", f, "AlHabbi_Radar.xlsx", use_container_width=True)

# ========== ENGINE محسن - لا استدعاء مزدوج ==========
@st.cache_data(ttl=300, show_spinner=False)
def get_analysis(ticker, smt):
    try:
        res = E.run_engine(ticker, smt)
        setup, df_d, df_h1, df_m15, liq, sw, dol = res
        row = E.extract_row(res[0], ticker, smt)
        row["_cur"] = float(df_d["Close"].iloc[-1]) if not df_d.empty else None
        row["_df"] = df_d; row["_setup"] = setup; row["_liq"] = liq; row["_sw"] = sw; row["_dol"] = dol
        row["_scan_date"] = datetime.now().strftime("%Y-%m-%d")
        return row
    except Exception as e:
        r = E.extract_row(None, ticker, smt); r["_cur"]=None; r["_df"]=pd.DataFrame(); r["_setup"]=None
        return r

# ========== باقي الكود الأصلي كامل مع إصلاح ==========
def _age_h(ts):
    if not ts: return 9999
    return (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds()/3600

def render_header():
    now = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""<div class="top-hdr"><div style="display:flex;align-items:center;gap:14px"><div class="brand-logo">ح</div><div><div class="brand-name">منصة الحبي Pro v7</div><div style="color:#64748B;font-size:.8rem">تداول احترافي • {now}</div></div></div><div style="color:#2563EB;font-weight:700">السوق السعودي والأمريكي</div></div>""", unsafe_allow_html=True)

render_header()

# تبويبات السوق
c1,c2,c3 = st.columns([1,1,8])
with c1:
    if st.button("🇸🇦 سعودي", type="primary" if st.session_state.market_tab=="SA" else "secondary", use_container_width=True):
        st.session_state.market_tab="SA"; st.rerun()
with c2:
    if st.button("🇺🇸 أمريكي", type="primary" if st.session_state.market_tab=="US" else "secondary", use_container_width=True):
        st.session_state.market_tab="US"; st.rerun()

# اختيار القائمة
watchlist = SA_WATCHLIST if st.session_state.market_tab=="SA" else US_WATCHLIST_MAP[st.session_state.us_wl]
if st.session_state.market_tab=="US":
    st.session_state.us_wl = st.selectbox("اختر القائمة", list(US_WATCHLIST_MAP.keys()), label_visibility="collapsed")

# أدوات البحث
s1,s2,s3,s4 = st.columns([2,1.2,1.2,1])
st.session_state.search_q = s1.text_input("بحث", placeholder="ابحث بالرمز...", label_visibility="collapsed").upper()
st.session_state.filter_grade = s2.selectbox("الفلتر", ["جميع القوة","A+ ذهبي فقط","A+ و A","B فأعلى"], label_visibility="collapsed")
st.session_state.sort_by = s3.selectbox("ترتيب", ["القوة","R:R","الرمز"], label_visibility="collapsed")
scan = s4.button("📡 مسح الرادار", type="primary", use_container_width=True)

if scan:
    prog = st.progress(0, "جاري المسح...")
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(get_analysis, t, s): t for t,s in watchlist}
        for i,f in enumerate(as_completed(futs)):
            results.append(f.result()); prog.progress((i+1)/len(watchlist))
    df = pd.DataFrame(results).sort_values(["_grade_rank","_score_num"], ascending=[True,False])
    st.session_state.radar_df = df; st.session_state.radar_ts = datetime.now(timezone.utc)
    prog.empty(); st.success(f"✅ تم تحليل {len(df)} سهم")

df = st.session_state.radar_df
if df is not None and not df.empty:
    # إحصائيات
    total, a_plus, a, b = len(df), len(df[df.Grade=="A+"]), len(df[df.Grade=="A"]), len(df[df.Grade=="B"])
    st.markdown(f"""<div class="stats-row"><div class="stat-card"><div>إجمالي</div><div class="stat-v">{total}</div></div><div class="stat-card"><div>A+</div><div class="stat-v" style="color:{GR}">{a_plus}</div></div><div class="stat-card"><div>A</div><div class="stat-v" style="color:{BL}">{a}</div></div><div class="stat-card"><div>B</div><div class="stat-v" style="color:{AM}">{b}</div></div></div>""", unsafe_allow_html=True)

    # فلترة
    if st.session_state.search_q: df = df[df.Ticker.str.contains(st.session_state.search_q)]
    if st.session_state.filter_grade == "A+ ذهبي فقط": df = df[df.Grade=="A+"]

    # عرض الجدول الكامل - مع إصلاح الخطأ
    st.markdown('<div class="tbl-wrap"><div class="tbl-hdr-row"><div>#</div><div>الرمز</div><div>الاسم</div><div>التاريخ</div><div>الحالة</div><div>القوة</div><div>دخول</div><div>حالي</div><div>وقف</div><div>هدف1</div><div>موجة</div><div>سيولة</div></div>', unsafe_allow_html=True)
    for i,r in df.iterrows():
        # إصلاح الخطأ الأصلي هنا
        cur = r.get("_cur")
        try: cur_str = f"{float(cur):.3f}" if cur not in (None,"") else str(r.get("Entry","—"))
        except: cur_str = str(r.get("Entry","—"))
        name = dict(SA_STOCKS).get(r.Ticker, r.Ticker) if st.session_state.market_tab=="SA" else r.Ticker
        badge = '<span class="sb sb-active">نشط</span>' if r.Grade in ["A+","A"] else '<span class="sb sb-wait">منتظر</span>'
        stars = "★"*3 if r.Grade=="A+" else "★"*2 if r.Grade=="A" else "★"
        st.markdown(f"""<div class="tbl-row-item"><div>{i+1}</div><div><b>{r.Ticker}</b></div><div>{name}</div><div>{r.get('_scan_date','')}</div><div>{badge}</div><div style="color:#F59E0B">{stars}</div><div>{r.Entry}</div><div style="color:{GR}">{cur_str}</div><div style="color:{RD}">{r.SL}</div><div style="color:{GR}">{r.TP1}</div><div>{r.get('Wave Target','—')}</div><div>{r.get('نوع السيولة','—')}</div></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # تفاصيل مع شارت
    pick = st.selectbox("تحليل تفصيلي", df.Ticker.tolist())
    if pick:
        row = df[df.Ticker==pick].iloc[0]
        if row["_setup"]:
            s = row["_setup"]
            st.markdown(f"### {pick} - دخول: {s.entry:.2f} | وقف: {s.stop_loss:.2f} | هدف: {s.targets[0].price:.2f}")
            fig = E.build_chart(row["_df"], s, row["_liq"], row["_sw"], row["_dol"], ticker=pick)
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("اضغط 'مسح الرادار' لبدء التحليل")

# فوتر
st.markdown("""<div style="text-align:center;padding:30px;color:#94A3B8;border-top:1px solid #E2E8F0;margin-top:40px">منصة الحبي Pro v7 © 2026 - جميع البيانات تعليمية</div>""", unsafe_allow_html=True)
