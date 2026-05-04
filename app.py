import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# --- 1. إعدادات الهوية والقوانين الصارمة ---
st.set_page_config(page_title="منصة الحبي للتداول v6", layout="wide")

# منع التعديل التلقائي عبر تثبيت الخطوط والألوان
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; }
    .stMetric { background-color: #1e2130; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_loader=True)

# --- 2. محرك جلب البيانات الحية (لضمان أسعار جديدة) ---
def get_live_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1mo", interval="1d") # جلب بيانات شهر لضمان دقة المؤشرات
        if not df.empty:
            return df
        return None
    except Exception as e:
        st.error(f"خطأ في جلب بيانات {symbol}: {e}")
        return None

# --- 3. محرك تحليل ICT (الخوارزمية الصارمة) ---
def analyze_market(df):
    # حساب المؤشرات الفنية الأساسية
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['EMA_20'] = ta.ema(df['Close'], length=20)
    
    # تحديد مناطق السيولة (Order Blocks / Support & Resistance)
    support = df['Low'].rolling(window=10).min().iloc[-1]
    resistance = df['High'].rolling(window=10).max().iloc[-1]
    last_price = df['Close'].iloc[-1]
    
    # قانون تحديد القوة (Grade)
    grade = "WAIT"
    color = "white"
    
    if last_price <= support * 1.01 and df['RSI'].iloc[-1] < 40:
        grade = "A+ (منطقة طلب ICT)"
        color = "#00ff00"
    elif last_price >= resistance * 0.99 and df['RSI'].iloc[-1] > 70:
        grade = "Short (منطقة عرض)"
        color = "#ff4b4b"
    
    return last_price, grade, color

# --- 4. واجهة المستخدم الرئيسية ---
st.title("🚀 منصة الحبي للتداول الاحترافي v6")
st.write("---")

# تقسيم القوائم (سوق سعودي وأمريكي)
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("⚙️ التحكم والرادار")
    market_type = st.radio("اختر السوق:", ["السوق السعودي (TASI)", "السوق الأمريكي (US)"])
    
    if market_type == "السوق السعودي (TASI)":
        symbol_input = st.selectbox("اختر السهم:", ["2222.SA", "1120.SA", "1150.SA", "2010.SA"])
    else:
        symbol_input = st.selectbox("اختر السهم:", ["AAPL", "TSLA", "NVDA", "MSFT", "BTC-USD"])

    btn_scan = st.button("تشغيل مسح الرادار المباشر")

# --- 5. عرض النتائج والشارت الاحترافي ---
with col2:
    if btn_scan:
        with st.spinner("جاري تحليل السيولة الحية..."):
            data = get_live_data(symbol_input)
            if data is not None:
                price, grade, grade_color = analyze_market(data)
                
                # عرض السعر والحالة
                c1, c2, c3 = st.columns(3)
                c1.metric("السعر المباشر", f"{price:.2f}")
                c2.markdown(f"### التقييم: <span style='color:{grade_color}'>{grade}</span>", unsafe_allow_html=True)
                c3.write(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
                
                st.write("---")
                
                # زرع شارت تريدنق فيو (TradingView Widget)
                st.subheader(f"📊 التحليل الفني لـ {symbol_input}")
                chart_code = f"""
                <div id="tradingview_chart" style="height: 500px;"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({{
                  "autosize": true,
                  "symbol": "{symbol_input}",
                  "interval": "D",
                  "timezone": "Asia/Riyadh",
                  "theme": "dark",
                  "style": "1",
                  "locale": "ar",
                  "toolbar_bg": "#f1f3f6",
                  "enable_publishing": false,
                  "hide_side_toolbar": false,
                  "allow_symbol_change": true,
                  "container_id": "tradingview_chart"
                }});
                </script>
                """
                st.components.v1.html(chart_code, height=520)
            else:
                st.warning("تعذر جلب البيانات. تأكد من اتصال الإنترنت أو رمز السهم.")
    else:
        st.info("قم باختيار السهم واضغط على 'تشغيل مسح الرادار' لبدء التحليل.")

# قانون صارم: تذييل المنصة لمنع التلاعب
st.markdown("---")
st.caption("منصة الحبي v6 - تعمل ببيانات ياهو فاينانس الرسمية | التحليل يعتمد على خوارزمية ICT المدمجة")
