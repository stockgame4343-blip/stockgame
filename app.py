import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import time

st.set_page_config(page_title="StockGirl Web", layout="wide")
st.title("🚀 삼성전자 한 달 초고속 트레이딩 (Web 버전)")

# 1. 데이터 가져오기 및 보간
@st.cache_data
def load_data():
    df = fdr.DataReader('005930').tail(30)
    raw = []
    for _, row in df.iterrows():
        raw.extend([int(row['Open']), int(row['High']), int(row['Low']), int(row['Close'])])
    x = np.arange(len(raw))
    x_smooth = np.linspace(0, len(raw)-1, len(raw)*10)
    f = interp1d(x, raw, kind='linear')
    return f(x_smooth)

prices = load_data()

# 2. 상태 유지 (새로고침 방지)
if 'step' not in st.session_state:
    st.session_state.update({'step': 0, 'pos': "없음", 'entry': 0, 'total': 0.0})

# 3. 상단 대시보드
c1, c2, c3 = st.columns(3)
p_box = c1.empty()
s_box = c2.empty()
t_box = c3.empty()

chart_box = st.empty()

# 4. 버튼 액션
b1, b2, b3, b4 = st.columns(4)
if b1.button("LONG", use_container_width=True):
    st.session_state.pos, st.session_state.entry = "LONG", prices[st.session_state.step]
if b2.button("SHORT", use_container_width=True):
    st.session_state.pos, st.session_state.entry = "SHORT", prices[st.session_state.step]
if b3.button("CLOSE", use_container_width=True):
    if st.session_state.pos != "없음":
        curr = prices[st.session_state.step]
        diff = curr - st.session_state.entry
        rate = (diff/st.session_state.entry*100) if st.session_state.pos=="LONG" else (-diff/st.session_state.entry*100)
        st.session_state.total += rate
        st.session_state.pos = "없음"
if b4.button("RESET"):
    st.session_state.step = 0
    st.session_state.total = 0

# 5. 실행 루프
while st.session_state.step < len(prices):
    curr = prices[st.session_state.step]
    p_box.metric("현재가", f"{int(curr):,}원")
    
    rate = 0.0
    if st.session_state.pos != "없음":
        diff = curr - st.session_state.entry
        rate = (diff/st.session_state.entry*100) if st.session_state.pos=="LONG" else (-diff/st.session_state.entry*100)
    
    s_box.metric("현재 수익률", st.session_state.pos, f"{rate:.2f}%")
    t_box.metric("누적 수익률", f"{st.session_state.total:.2f}%")
    
    # 차트 업데이트 (웹 성능을 위해 10스텝마다)
    if st.session_state.step % 10 == 0:
        chart_box.line_chart(prices[:st.session_state.step], height=400)
    
    st.session_state.step += 1
    time.sleep(0.01) # 하이퍼 패스트 속도