import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import time

# 1. 페이지 설정
st.set_page_config(page_title="삼성전자", layout="wide")

# CSS: 버튼 색상 및 대시보드 스타일 (파이썬 버전과 일치)
st.markdown("""
    <style>
    div.stButton > button { height: 70px; font-weight: bold; font-size: 20px; color: white; border-radius: 10px; width: 100%; }
    /* LONG (Red) */
    div[data-testid="column"]:nth-of-type(1) button { background-color: #FF1E1E; }
    /* SHORT (Blue) */
    div[data-testid="column"]:nth-of-type(2) button { background-color: #1E90FF; }
    /* CLOSE (Grey) */
    div[data-testid="column"]:nth-of-type(3) button { background-color: #2C2C2C; }
    /* Metric Font */
    [data-testid="stMetricValue"] { font-size: 28px !important; font-family: 'Consolas', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("삼성전자")

# 2. 데이터 준비
@st.cache_data
def load_data():
    df = fdr.DataReader('005930').tail(30)
    raw_prices = []
    for _, row in df.iterrows():
        raw_prices.extend([int(row['Open']), int(row['High']), int(row['Low']), int(row['Close'])])
    x = np.arange(len(raw_prices))
    total_pts = len(raw_prices) * 8
    x_smooth = np.linspace(0, len(raw_prices) - 1, total_pts)
    f = interp1d(x, raw_prices, kind='linear')
    return f(x_smooth).astype(int), total_pts

prices, total_pts = load_data()

# 3. 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.pos = "없음"
    st.session_state.entry = 0
    st.session_state.total_profit = 0.0
    st.session_state.running = False

# 4. 상단 대시보드 레이아웃
dash_cols = st.columns(3)
p_metric = dash_cols[0].empty()
s_metric = dash_cols[1].empty()
t_metric = dash_cols[2].empty()

# 5. 차트 레이아웃
chart_container = st.empty()

# 6. 트레이딩 로직 (스위칭 포함)
def handle_trade(side):
    if st.session_state.step == 0: return
    curr_p = prices[st.session_state.step - 1]
    
    if side == "CLOSE":
        if st.session_state.pos != "없음":
            diff = curr_p - st.session_state.entry
            rate = (diff/st.session_state.entry*100) if st.session_state.pos == "LONG" else (-diff/st.session_state.entry*100)
            st.session_state.total_profit += rate
            st.session_state.pos = "없음"
    else:
        if st.session_state.pos != "없음": handle_trade("CLOSE")
        st.session_state.pos = side
        st.session_state.entry = curr_p

# 7. 하단 컨트롤 버튼
btn_cols = st.columns([1, 1, 1, 0.6])
if btn_cols[0].button("LONG"): handle_trade("LONG")
if btn_cols[1].button("SHORT"): handle_trade("SHORT")
if btn_cols[2].button("CLOSE"): handle_trade("CLOSE")
if btn_cols[3].button("START/RESET"):
    st.session_state.step = 0
    st.session_state.total_profit = 0.0
    st.session_state.pos = "없음"
    st.session_state.running = True
    st.rerun() # 즉시 재시작

# 8. 메인 루프 (핵심 수정 부분)
if st.session_state.running and st.session_state.step < total_pts:
    # 한 번의 렌더링 세션에서 데이터를 조금씩 보여줌
    curr_p = prices[st.session_state.step]
    
    # 정보 업데이트
    p_metric.metric("현재가", f"{curr_p:,} 원")
    
    # 실시간 수익률 계산
    curr_rate = 0.0
    if st.session_state.pos != "없음":
        diff = curr_p - st.session_state.entry
        curr_rate = (diff/st.session_state.entry*100) if st.session_state.pos == "LONG" else (-diff/st.session_state.entry*100)
        s_metric.metric("실시간 수익률", f"{st.session_state.pos}", f"{curr_rate:+.2f}%")
    else:
        s_metric.metric("실시간 수익률", "WAITING", "0.00%")
    
    t_metric.metric("누적 수익률", f"{st.session_state.total_profit:+.2f}%")

    # 차트 업데이트 (X축 고정 효과를 위해 빈 공간을 None으로 채운 DF 사용)
    plot_data = pd.DataFrame({'Price': prices[:st.session_state.step]})
    chart_container.line_chart(plot_data, height=400, y_label="Price")

    st.session_state.step += 1
    time.sleep(0.01) # 1.5배 빠른 속도
    st.rerun() # 화면을 강제로 다시 그려 루프 구현
