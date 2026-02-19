import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import time

# 1. 페이지 설정
st.set_page_config(page_title="삼성전자", layout="wide")

# 버튼 스타일 및 레이아웃 커스텀 CSS
st.markdown("""
    <style>
    div.stButton > button:first-child { height: 70px; font-weight: bold; font-size: 20px; color: white; border-radius: 10px; }
    /* LONG 버튼 (빨간색) */
    div[data-testid="column"]:nth-of-type(1) button { background-color: #FF1E1E; border: none; }
    /* SHORT 버튼 (파란색) */
    div[data-testid="column"]:nth-of-type(2) button { background-color: #1E90FF; border: none; }
    /* CLOSE 버튼 (회색) */
    div[data-testid="column"]:nth-of-type(3) button { background-color: #2C2C2C; border: none; }
    /* 대시보드 폰트 크기 조절 */
    [data-testid="stMetricValue"] { font-size: 26px !important; font-family: 'Consolas', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("삼성전자")

# 2. 데이터 로드 (한 달치)
@st.cache_data
def load_data():
    df = fdr.DataReader('005930').tail(30)
    raw_prices = []
    for _, row in df.iterrows():
        raw_prices.extend([int(row['Open']), int(row['High']), int(row['Low']), int(row['Close'])])
    
    x = np.arange(len(raw_prices))
    total_points = len(raw_prices) * 8
    x_smooth = np.linspace(0, len(raw_prices) - 1, total_points)
    f = interp1d(x, raw_prices, kind='linear')
    return f(x_smooth), total_points

prices, total_points = load_data()

# 3. 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.update({
        'step': 0, 
        'current_position': "없음", 
        'entry_price': 0, 
        'total_profit_rate': 0.0,
        'running': False
    })

# 4. 상단 대시보드
dash_col1, dash_col2, dash_col3 = st.columns(3)
price_val = dash_col1.empty()
status_val = dash_col2.empty()
total_val = dash_col3.empty()

# 5. 차트 영역
chart_holder = st.empty()

# 6. 트레이딩 함수 (파이썬 버전과 로직 일치)
def handle_trade(side):
    if st.session_state.step == 0: return
    curr_p = int(prices[st.session_state.step - 1])
    
    if side == "CLOSE":
        if st.session_state.current_position != "없음":
            diff = curr_p - st.session_state.entry_price
            rate = (diff/st.session_state.entry_price*100) if st.session_state.current_position == "LONG" else (-diff/st.session_state.entry_price*100)
            st.session_state.total_profit_rate += rate
            st.session_state.current_position = "없음"
    else:
        # 스위칭 로직: 이미 포지션이 있으면 청산 후 진입
        if st.session_state.current_position != "없음":
            handle_trade("CLOSE")
        st.session_state.current_position = side
        st.session_state.entry_price = curr_p

# 7. 조작 버튼
btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 0.6])
if btn_col1.button("LONG"): handle_trade("LONG")
if btn_col2.button("SHORT"): handle_trade("SHORT")
if btn_col3.button("CLOSE"): handle_trade("CLOSE")
if btn_col4.button("START / RESET"):
    st.session_state.step = 0
    st.session_state.total_profit_rate = 0.0
    st.session_state.current_position = "없음"
    st.session_state.running = True

# 8. 실행 루프 (1.5배 속도 반영)
if st.session_state.running:
    while st.session_state.step < total_points:
        curr_p = prices[st.session_state.step]
        
        # 정보 업데이트
        price_val.metric("현재가", f"{int(curr_p):,} 원")
        
        if st.session_state.current_position != "없음":
            diff = curr_p - st.session_state.entry_price
            rate = (diff/st.session_state.entry_price*100) if st.session_state.current_position == "LONG" else (-diff/st.session_state.entry_price*100)
            status_val.metric("실시간 수익률", f"{st.session_state.current_position}", f"{rate:+.2f}%")
        else:
            status_val.metric("실시간 수익률", "WAITING", "0.00%")
            
        total_val.metric("누적 수익률", f"{st.session_state.total_profit_rate:+.2f}%")

        # 차트 업데이트 (Y축 범위 고정 효과를 위해 현재 스텝까지 표시)
        if st.session_state.step % 5 == 0:
            chart_holder.line_chart(prices[:st.session_state.step], height=400)

        st.session_state.step += 1
        time.sleep(0.01) # 16ms에 근접한 속도
