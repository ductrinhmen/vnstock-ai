# 📈 AI PHÂN TÍCH KỸ THUẬT CỔ PHIẾU VIỆT NAM (có cập nhật giá mới nhất)

import streamlit as st
import pandas as pd
import pandas_ta as ta
import openai
import requests
from datetime import datetime
import matplotlib.pyplot as plt

# --- Cấu hình API KEY ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- Giao diện nhập ---
st.set_page_config(page_title="Phân tích cổ phiếu bằng AI", layout="wide")
st.title("📊 Phân tích kỹ thuật & AI nhận định cổ phiếu")
symbol = st.text_input("Nhập mã cổ phiếu (ví dụ: HPG, VNM, FPT):", "HPG").upper()

# --- Lấy dữ liệu giá từ VNDIRECT ---
url = f"https://finfo-api.vndirect.com.vn/v4/stock_prices?symbol={symbol}&sort=date&size=300"
res = requests.get(url)

if res.status_code == 200 and res.json()["data"]:
    df = pd.DataFrame(res.json()["data"])
    df = df.sort_values("date")
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df[["open", "close", "high", "low", "volume"]] = df[["open", "close", "high", "low", "volume"]].astype(float)

    # --- Tính chỉ báo kỹ thuật ---
    df["EMA20"] = ta.ema(df["close"], length=20)
    df["EMA50"] = ta.ema(df["close"], length=50)
    df["EMA200"] = ta.ema(df["close"], length=200)
    df["RSI"] = ta.rsi(df["close"], length=14)

    # --- Xác định tín hiệu giao cắt ---
    df["Signal"] = 0
    df.loc[(df["EMA20"] > df["EMA50"]) & (df["EMA20"].shift(1) <= df["EMA50"].shift(1)), "Signal"] = 1
    df.loc[(df["EMA20"] < df["EMA50"]) & (df["EMA20"].shift(1) >= df["EMA50"].shift(1)), "Signal"] = -1

    # --- Dữ liệu mới nhất ---
    latest = df.iloc[-1]
    st.subheader(f"📌 Dữ liệu mới nhất ({latest.name.date()}):")
    st.metric("Giá hiện tại (close)", f"{latest['close']:.0f} VND")
    st.write(f"EMA20: {latest['EMA20']:.0f} | EMA50: {latest['EMA50']:.0f} | EMA200: {latest['EMA200']:.0f}")
    st.write(f"RSI(14): {latest['RSI']:.2f}")

    # --- Nhận định từ GPT ---
    prompt = f"""
    Bạn là chuyên gia phân tích kỹ thuật.
    Hãy nhận định cổ phiếu {symbol} với các thông số:
    - Giá hiện tại: {latest['close']:.2f} VND
    - RSI(14): {latest['RSI']:.2f}
    - EMA20: {latest['EMA20']:.2f}
    - EMA50: {latest['EMA50']:.2f}
    - EMA200: {latest['EMA200']:.2f}
    - Tín hiệu EMA: {"MUA" if latest['Signal']==1 else "BÁN" if latest['Signal']==-1 else "CHỜ"}

    Viết nhận định ngắn gọn bằng tiếng Việt và gợi ý hành động.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        st.subheader("🧠 Nhận định từ AI")
        st.info(response["choices"][0]["message"]["content"])
    except Exception as e:
        st.warning(f"⚠️ Lỗi gọi OpenAI: {e}")

    # --- Biểu đồ giá & EMA ---
    st.subheader("📉 Biểu đồ giá & đường trung bình động")
    fig, ax = plt.subplots(figsize=(12,5))
    ax.plot(df.index, df["close"], label="Giá đóng cửa", color="gray")
    ax.plot(df.index, df["EMA20"], label="EMA20", color="red")
    ax.plot(df.index, df["EMA50"], label="EMA50", color="blue")
    ax.plot(df.index, df["EMA200"], label="EMA200", color="black")
    ax.legend()
    ax.set_title(f"{symbol} - Biểu đồ kỹ thuật")
    st.pyplot(fig)

    # --- Dữ liệu bảng gần nhất ---
    st.subheader("📄 Bảng dữ liệu 10 phiên gần nhất")
    st.dataframe(df[["open", "high", "low", "close", "EMA20", "EMA50", "EMA200", "RSI"]].tail(10).round(2))

else:
    st.error("Không tìm thấy dữ liệu cho mã cổ phiếu này.")
