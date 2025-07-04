import requests
import pandas as pd
import pandas_ta as ta
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Phân tích kỹ thuật cổ phiếu Việt Nam", layout="wide")
st.title("📈 AI PHÂN TÍCH KỸ THUẬT CỔ PHIẾU VIỆT NAM")

symbol = st.text_input("Nhập mã cổ phiếu (ví dụ: HPG, VNM, FPT):", "HPG").upper()

url = f"https://finfo-api.vndirect.com.vn/v4/stock_prices?sort=date&size=300&symbol={symbol}"
response = requests.get(url)

if response.status_code == 200 and response.json()['data']:
    data = response.json()["data"]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df.set_index("date", inplace=True)
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

    df["EMA20"] = ta.ema(df["close"], length=20)
    df["EMA50"] = ta.ema(df["close"], length=50)
    df["EMA200"] = ta.ema(df["close"], length=200)
    df["RSI"] = ta.rsi(df["close"], length=14)
    df.ta.bbands(close='close', length=20, std=2, append=True)

    df["Signal"] = 0
    df.loc[(df["EMA20"] > df["EMA50"]) & (df["EMA20"].shift(1) <= df["EMA50"].shift(1)), "Signal"] = 1
    df.loc[(df["EMA20"] < df["EMA50"]) & (df["EMA20"].shift(1) >= df["EMA50"].shift(1)), "Signal"] = -1

    latest = df.iloc[-1]
    st.subheader("📊 Kết quả phân tích mới nhất")
    st.write(f"**Mã**: {symbol}")
    st.write(f"**Ngày**: {latest.name.date()}")
    st.write(f"**Giá đóng cửa**: {latest['close']:.0f} VND")
    st.write(f"**EMA20**: {latest['EMA20']:.0f} | EMA50: {latest['EMA50']:.0f} | EMA200: {latest['EMA200']:.0f}")
    st.write(f"**RSI(14)**: {latest['RSI']:.2f}")

    if latest['Signal'] == 1:
        st.success("✅ Tín hiệu: **NÊN MUA** (EMA20 cắt lên EMA50)")
    elif latest['Signal'] == -1:
        st.error("❌ Tín hiệu: **NÊN BÁN** (EMA20 cắt xuống EMA50)")
    else:
        st.info("🤔 Chưa có tín hiệu rõ ràng.")

    st.subheader("📉 Biểu đồ giá và các đường EMA")
    fig, ax = plt.subplots(figsize=(14,6))
    ax.plot(df.index, df["close"], label="Giá đóng cửa", color='gray')
    ax.plot(df.index, df["EMA20"], label="EMA20", color='red')
    ax.plot(df.index, df["EMA50"], label="EMA50", color='blue')
    ax.plot(df.index, df["EMA200"], label="EMA200", color='black')
    ax.legend()
    ax.set_title(f"Phân tích kỹ thuật cổ phiếu {symbol}")
    st.pyplot(fig)

    st.subheader("📅 Dữ liệu 10 phiên gần nhất")
    st.dataframe(df[["open", "high", "low", "close", "EMA20", "EMA50", "EMA200", "RSI"]].tail(10).round(2))
else:
    st.warning("⚠️ Không tìm thấy dữ liệu cho mã cổ phiếu này. Vui lòng kiểm tra lại.")
