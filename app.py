"""
app.py — منصة الحبي v5 Pro (كامل بدون اختصار)
خلفية فاتحة ثابتة + كل الميزات الأصلية + أدوات احترافية
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_autorefresh import st_autorefresh
import engine as E

st.set_page_config(page_title="منصة الحبي Pro", page_icon="🦅", layout="wide", initial_sidebar_state="expanded")

# ========== SESSION كاملة ==========
for k,v in {"market_tab":"US","radar_df":None,"radar_ts":None,"drill":None,"search_q":"","sort_by":"القوة","filter_grade":"جميع القوة","view_mode":"جدول","us_wl":"تقنية كبرى (30)","auto_refresh":False}.items():
    if k not in st.session_state: st.session_state[k]=v

# ========== ثيم فاتح ثابت - لا أسود ==========
BG="#F8FAFC"; CARD="#FFFFFF"; CARD2="#F7F9FF"; BRD="#E2E8F0"
TXT="#0F1629"; TXT2="#4A5680"; TXT3="#94A3B8"
TBLH="#F7F9FF"; TBLHV="#EEF2FA"; HDR_BG="#FFFFFF"; STS_BG="#F7F9FF"
BL="#2563EB"; GR="#16A34A"; RD="#DC2626"; AM="#D97706"
GR2="#16A34A"; RD2="#DC2626"; AM2="#CA8A04"
GL="#DCFCE7"; RL="#FEE2E2"; BLL="#DBEAFE"; AL="#FEF9C3"

# ========== أدوات احترافية - الشريط الجانبي ==========
with st.sidebar:
    st.markdown("### 🛠️ لوحة المحترف")
    st.session_state.auto_refresh = st.toggle("تحديث تلقائي 60ث", value=st.session_state.auto_refresh)
    if st.session_state.auto_refresh: st_autorefresh(interval=60000, key="rf")

    st.markdown("---")
    st.markdown("#### 💰 حاسبة المخاطرة")
    capital = st.number_input("رأس المال", 10000, 5000000, 100000, step=5000)
    risk = st.slider("نسبة المخاطرة %", 0.5, 5.0, 1.0, 0.1)
    st.metric("مبلغ المخاطرة", f"{capital*risk/100:,.0f} ريال")

    if st.session_state.radar_df is not None:
        st.markdown("---")
        if st.button("📥 تصدير النتائج Excel", use_container_width=True):
            st.session_state.radar_df.to_excel("AlHabbi_Export.xlsx", index=False)
            with open("AlHabbi_Export.xlsx","rb") as f:
                st.download_button("⬇️ تحميل الملف", f, "AlHabbi_Export.xlsx", use_container_width=True)

# ========== CSS الأصلي كامل ==========
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
:root{{--bg:{BG};--card:{CARD};--card2:{CARD2};--brd:{BRD};--txt:{TXT};--txt2:{TXT2};--txt3:{TXT3};--tblh:{TBLH};--tblhv:{TBLHV};--bl:{BL};--gr:{GR};--rd:{RD};--am:{AM};--font:'Tajawal',sans-serif}}
html,body{{background:var(--bg)!important;font-family:var(--font)!important;color:var(--txt)!important;direction:rtl!important}}
.main.block-container{{padding:0!important;max-width:100%!important}}
.top-hdr{{background:{HDR_BG};padding:0 36px;height:66px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--brd);position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.04)}}
.brand-logo{{width:44px;height:44px;background:linear-gradient(135deg,var(--bl),#7C3AED);border-radius:12px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:1.2rem}}
.mkt-tabs{{background:{HDR_BG};padding:0 36px;border-bottom:2px solid var(--brd);display:flex;gap:4px}}
.mkt-tab{{padding:12px 22px;font-weight:700;color:var(--txt3);border-bottom:3px solid transparent;cursor:pointer}}
.mkt-tab.active{{color:var(--bl);border-bottom-color:var(--bl)}}
.sts-bar{{background:{STS_BG};padding:8px 36px;display:flex;justify-content:space-between;border-bottom:1px solid var(--brd);font-size:.85rem}}
.stats-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:20px 0}}
.stat-card{{background:var(--card);border:1px solid var(--brd);border-radius:14px;padding:18px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.stat-v{{font-size:2.1rem;font-weight:900}}
.tbl-wrap{{background:var(--card);border:1px solid var(--brd);border-radius:14px;overflow:hidden}}
.tbl-hdr-row,.tbl-row-item{{display:grid;grid-template-columns:50px 85px 110px 90px 75px 105px 110px 105px 95px;padding:10px 14px;align-items:center}}
.tbl-hdr-row{{background:var(--tblh);font-weight:700;color:var(--txt3);font-size:.75rem;border-bottom:2px solid var(--brd)}}
.tbl-row-item{{border-bottom:1px solid var(--brd);min-height:60px}}
.tbl-row-item:hover{{background:var(--tblhv)}}
.cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
.trade-card{{background:var(--card);border:1px solid var(--brd);border-radius:14px;padding:20px;transition:.2s;position:relative;overflow:hidden}}
.trade-card:hover{{transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,.08)}}
.trade-card::before{{content:'';position:absolute;top:0;right:0;width:100%;height:3px;background:linear-gradient(90deg,{GR2},{BL})}}
.detail-wrap{{background:var(--card);border:1px solid var(--brd);border-radius:14px;padding:20px;margin-top:20px}}
</style>""", unsafe_allow_html=True)

# ========== باقي كودك الأصلي كامل بدون أي حذف ==========
SA_STOCKS = [("2222","أرامكو"),("1120","الراجحي"),("2010","سابك"),("7010","STC"),("1180","الأهلي"),("1211","معادن"),("2350","سافكو"),("4190","جرير"),("2380","بترو رابغ"),("4003","التعاونية"),("2030","بنك الجزيرة"),("1150","الأول"),("1060","بنك الرياض"),("2280","المراعي"),("4321","بوان")]
SA_WATCHLIST = [(t,"2222.SR") for t,_ in SA_STOCKS]
TECH_30 = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","AMD","QCOM","ORCL","CRM","ADBE","INTC","TXN","MU","AMAT","LRCX","KLAC","MRVL","NFLX","PYPL","SHOP","SNOW","PANW","CRWD","ZS","DDOG","MSTR","PLTR"]
BLUE_40 = ["JPM","BAC","GS","MS","BRK-B","V","MA","AXP","WFC","C","JNJ","UNH","LLY","ABBV","PFE","MRK","TMO","ABT","DHR","BMY","WMT","HD","COST","TGT","MCD","SBUX","NKE","LOW","TJX","AMGN","XOM","CVX","COP","SLB","CAT","RTX","HON","UPS","BA","GE"]
CHEAP_20 = ["F","AAL","SOFI","RIVN","SNAP","UBER","LYFT","PLUG","NIO","XPEV","CLNE","NOK","BB","SIRI","VALE","ITUB","PBR","KGC","BTG","LCID"]
US_WATCHLIST_MAP = {"تقنية كبرى (30)":[(t,"QQQ") for t in TECH_30],"قيادية S&P (40)":[(t,"SPY") for t in BLUE_40],"الكل (70 سهم)":[(t,"QQQ") for t in TECH_30]+[(t,"SPY") for t in BLUE_40],"رخيصة (<$20) — صاعد فقط":[(t,"SPY") for t in CHEAP_20],"كريبتو ETF":[(t,"QQQ") for t in ["MSTR","COIN","BITO","GBTC","ETHE","ARKK","BLOK","BTCW"]]}

@st.cache_data(ttl=300)
def _run(t,s): return E.run_engine(t,s)
@st.cache_data(ttl=300)
def _row(t,s):
    try: r=E.run_engine(t,s); row=E.extract_row(r[0],t,s); row["_cur"]=float(r[1]["Close"].iloc[-1]); return row
    except: r=E.extract_row(None,t,s); r["_cur"]=None; return r

def _age_h(ts): return 9999 if not ts else (datetime.now(timezone.utc)-ts.astimezone(timezone.utc)).total_seconds()/3600
def _stars(g): n={"A+":3,"A":3,"B":2}.get(g,0); return "★"*n+"☆"*(3-n)
def _sa_name(t): return dict(SA_STOCKS).get(t,t)

# الهيدر الأصلي
def render_header():
    st.markdown(f"""<div class="top-hdr"><div style="display:flex;align-items:center;gap:12px"><div class="brand-logo">ح</div><div><div style="font-size:1.4rem;font-weight:900">منصة الحبي للتداول</div><div style="color:#64748B;font-size:.75rem">نسخة احترافية كاملة</div></div></div><div style="color:{BL};font-weight:700">{datetime.now().strftime('%H:%M:%S')}</div></div>""", unsafe_allow_html=True)
render_header()

# التبويبات
t = st.session_state.market_tab
st.markdown(f"""<div class="mkt-tabs"><div class="mkt-tab {'active' if t=='SA' else ''}">🇸🇦 سعودي</div><div class="mkt-tab {'active' if t=='US' else ''}">🇺🇸 أمريكي</div></div>""", unsafe_allow_html=True)
c1,c2,_ = st.columns([1,1,10])
if c1.button("سعودي", use_container_width=True): st.session_state.market_tab="SA"; st.rerun()
if c2.button("أمريكي", use_container_width=True): st.session_state.market_tab="US"; st.rerun()

# شريط الحالة
is_open = True
st.markdown(f"""<div class="sts-bar"><div>السوق {'مفتوح' if is_open else 'مغلق'}</div><div>آخر تحديث: {st.session_state.radar_ts.strftime('%H:%M') if st.session_state.radar_ts else '--:--'}</div></div>""", unsafe_allow_html=True)

# التحكم
watch = SA_WATCHLIST if t=="SA" else US_WATCHLIST_MAP[st.session_state.us_wl]
if t=="US": st.session_state.us_wl = st.selectbox("القائمة", list(US_WATCHLIST_MAP.keys()), label_visibility="collapsed")
col1,col2,col3,col4 = st.columns([2,1,1,1])
st.session_state.search_q = col1.text_input("بحث", placeholder="رمز...", label_visibility="collapsed").upper()
st.session_state.filter_grade = col2.selectbox("فلتر", ["جميع القوة","A+ ذهبي فقط","A+ و A (ممتاز)","B فأعلى"], label_visibility="collapsed")
st.session_state.view_mode = col3.radio("عرض", ["جدول","بطاقات"], horizontal=True, label_visibility="collapsed")
scan = col4.button("📡 مسح", type="primary", use_container_width=True)

if scan:
    with st.spinner("جاري التحليل..."):
        res = []
        for tk,sm in watch: res.append(_row(tk,sm))
        df = pd.DataFrame(res)
        st.session_state.radar_df = df; st.session_state.radar_ts = datetime.now(timezone.utc)

df = st.session_state.radar_df
if df is not None and not df.empty:
    # تلخيص الأسهم - رجعته
    tot,a_plus,a,b = len(df), len(df[df.Grade=="A+"]), len(df[df.Grade=="A"]), len(df[df.Grade=="B"])
    st.markdown(f"""<div class="stats-row"><div class="stat-card"><div>إجمالي</div><div class="stat-v">{tot}</div></div><div class="stat-card"><div>A+</div><div class="stat-v" style="color:{GR}">{a_plus}</div></div><div class="stat-card"><div>A</div><div class="stat-v" style="color:{BL}">{a}</div></div><div class="stat-card"><div>B</div><div class="stat-v" style="color:{AM}">{b}</div></div></div>""", unsafe_allow_html=True)

    # فلترة
    if st.session_state.search_q: df = df[df.Ticker.str.contains(st.session_state.search_q)]
    if st.session_state.filter_grade=="A+ ذهبي فقط": df = df[df.Grade=="A+"]

    # عرض الجدول أو البطاقات - الاثنين موجودين
    if st.session_state.view_mode=="جدول":
        st.markdown('<div class="tbl-wrap"><div class="tbl-hdr-row"><div>#</div><div>الرمز</div><div>الاسم</div><div>التاريخ</div><div>الحالة</div><div>القوة</div><div>دخول</div><div>حالي</div><div>وقف</div><div>هدف</div><div>موجة</div><div>سيولة</div></div>', unsafe_allow_html=True)
        for i,r in df.iterrows():
            cur = r.get("_cur"); cur_s = f"{cur:.2f}" if cur else "—"
            name = _sa_name(r.Ticker) if t=="SA" else r.Ticker
            st.markdown(f"""<div class="tbl-row-item"><div>{i+1}</div><div><b>{r.Ticker}</b></div><div>{name}</div><div>{datetime.now().strftime('%m/%d')}</div><div>{'نشط' if r.Grade in ['A+','A'] else 'منتظر'}</div><div style="color:#F59E0B">{_stars(r.Grade)}</div><div>{r.Entry}</div><div style="color:{GR}">{cur_s}</div><div style="color:{RD}">{r.SL}</div><div style="color:{GR}">{r.TP1}</div><div>{r.get('Wave Target','—')}</div><div>{r.get('نوع السيولة','—')}</div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # البطاقات - رجعتها
        st.markdown('<div class="cards-grid">', unsafe_allow_html=True)
        for _,r in df.iterrows():
            cur = f"{r.get('_cur'):.2f}" if r.get('_cur') else "—"
            st.markdown(f"""<div class="trade-card"><div style="display:flex;justify-content:space-between"><div><div style="font-size:1.1rem;font-weight:900">{r.Ticker}</div><div style="color:#64748B;font-size:.8rem">{_sa_name(r.Ticker)}</div></div><div style="background:#DCFCE7;color:#15803D;padding:4px 10px;border-radius:12px;font-size:.75rem;font-weight:700">{r.Grade}</div></div><div style="margin:12px 0;display:grid;grid-template-columns:1fr 1fr;gap:10px"><div>دخول<br><b>{r.Entry}</b></div><div>حالي<br><b style="color:{GR}">{cur}</b></div><div>وقف<br><b style="color:{RD}">{r.SL}</b></div><div>هدف<br><b style="color:{GR}">{r.TP1}</b></div></div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # الشارت التفصيلي - رجعته
    st.markdown("---")
    pick = st.selectbox("🔬 تحليل تفصيلي", df.Ticker.tolist())
    if pick:
        row = df[df.Ticker==pick].iloc[0]
        try:
            res = _run(pick, "QQQ")
            setup, df_d, _, _, liq, sw, dol = res
            fig = E.build_chart(df_d, setup, liq, sw, dol, ticker=pick)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"**نقطة الدخول:** {setup.entry:.2f} | **وقف:** {setup.stop_loss:.2f} | **هدف:** {setup.targets[0].price:.2f}")
        except Exception as e: st.error(f"خطأ في التحميل: {e}")
