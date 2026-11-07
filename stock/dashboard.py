import json
import os
import re
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ==========================================
# 1. 기본 설정
# ==========================================
st.set_page_config(
    page_title="주식 관심종목 대시보드",
    page_icon="📈",
    layout="wide"
)

FILE_NAME="watchlist.json"

DEFAULT_STOCKS={}

# ==========================================
# 2. 관심종목 파일 관리
# ==========================================
def load_watchlist():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_STOCKS.copy()

def save_watchlist(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "watchlist" not in st.session_state:
    st.session_state.watchlist=load_watchlist()


# ==========================================
# 3. 주가 데이터 조회
# ==========================================
@st.cache_data(ttl=30, show_spinner=False)
def get_stock_data(symbol):

    try:
        stock = yf.Ticker(symbol)

        # 최근 5일 일봉 데이터
        daily = stock.history(
            period="5d",
            interval="1d",
            auto_adjust=False,
            raise_errors=True
        )

        if daily.empty:
            return {
                "error": f"{symbol}:일봉 데이터가 없습니다."
            }

        daily_close = daily["Close"].dropna()

        if daily_close.empty:
            return {
                "error": f"{symbol}: 종가 데이터가 없습니다."
            }

        current_daily = float(daily_close.iloc[-1])

        previous = (
            float(daily_close.iloc[-2])
            if len(daily_close) >= 2
            else current_daily
        )

        # 최근 1분봉 데이터
        try:
            intraday = stock.history(
                period="1d",
                interval="1m",
                auto_adjust=False
            )

            intraday_close = (
                intraday["Close"].dropna()
                if not intraday.empty
                else pd.Series(dtype=float)
            )

        except Exception:
            intraday_close = pd.Series(dtype=float)

        # 1분봉이 없으면 일봉 종가 사용
        current = (
            float(intraday_close.iloc[-1])
            if not intraday_close.empty
            else current_daily
        )

        if previous <= 0:
            return {"error": "전일 종가가 0 이하입니다."}

        change = current - previous
        rate = (change / previous) * 100

        # 3. 거래량
        volume_data = daily["Volume"].dropna()

        volume = (
            int(volume_data.iloc[-1])
            if not volume_data.empty
            else 0
        )

        # 4. 차트 데이터
        try:
            chart = stock.history(
                period="1mo",
                interval="1d",
                auto_adjust=False
            )
        except Exception:
            chart = pd.DataFrame()

        return {
            "price": current,
            "previous": previous,
            "change": change,
            "rate": rate,
            "volume": volume,
            "chart": chart
        }

    except Exception as e:
        return {
            "error": (
                f"{symbol}: {type(e).__name__}: {str(e)}"
            )
        }


# ==========================================
# 4. 종목 추가
# ==========================================
def add_stock(name, symbol):

    name = name.strip()
    symbol = symbol.strip().upper()

    if not name or not symbol:
        return False, "종목명과 종목코드를 입력하세요."

    if name in st.session_state.watchlist:
        return False, "이미 등록된 종목입니다."

    # 종목코드 입력 검증
    if not re.fullmatch(r"[A-Z0-9^=.\-]+", symbol):
        return False, "올바른 종목코드를 입력하세요."

    st.session_state.watchlist[name] = symbol
    save_watchlist(st.session_state.watchlist)

    get_stock_data.clear()

    return True, f"{name} 종목이 추가되었습니다."


# ==========================================
# 5. 종목 삭제
# ==========================================
def delete_stock(name):

    if name in st.session_state.watchlist:
        del st.session_state.watchlist[name]
        save_watchlist(st.session_state.watchlist)
        get_stock_data.clear()    

# ==========================================
# 6. 화면 디자인
# ==========================================
st.markdown("""
<style>
.main {
    background-color: #f7f9fc;
}

.stock-title {
    font-size: 30px;
    font-weight: 800;
    color: #17365d;
}

.stMetric {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #e5e9f0;
}

div[data-testid="stMetricValue"] {
    font-size: 24px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 7. 헤더
# ==========================================
st.markdown(
    '<div class="stock-title">📈 MY STOCK WATCH</div>',
    unsafe_allow_html=True
)

st.caption("나만의 관심종목 주식 조회 시스템")

st.divider()

# ==========================================
# 8. 사이드바 설정
# ==========================================
st.sidebar.title("⚙️ 설정")

auto_refresh = st.sidebar.toggle(
    "자동새로고침",
    value=True
)

refresh_interval = st.sidebar.selectbox(
    "새로고침간격",
    [10, 30, 60, 120, 300],
    index=1,
    format_func=lambda x: f"{x}초"
)

st.sidebar.divider()

st.sidebar.subheader("➕ 관심종목 추가")

# 한국 주요 종목 빠른 선택
stock_names = ["직접 입력"] + list(DEFAULT_STOCKS.keys())

selected_name = st.sidebar.selectbox(
    "종목 선택",
    stock_names
)

with st.sidebar.form("add_stock_form"):

    if selected_name == "직접 입력":
        new_name = st.text_input("종목명")
        new_symbol = st.text_input(
            "종목코드",
            placeholder="예: 005930.KS"
        )
    else:
        new_name = selected_name
        new_symbol = DEFAULT_STOCKS[selected_name]

    submitted = st.form_submit_button(
        "관심종목 추가",
        use_container_width=True
    )

    if submitted:
        success, message = add_stock(new_name, new_symbol)

        if success:
            st.sidebar.success(message)

            # 대시보드 전체 갱신
            st.rerun()
        else:
            st.sidebar.error(message)


st.sidebar.divider()

st.sidebar.subheader("🗑️ 관심종목 삭제")

watchlist = st.session_state.watchlist

if watchlist:

    delete_name = st.sidebar.selectbox(
        "삭제할 종목",
        list(watchlist.keys()),
        key="delete_stock"
    )

    if st.sidebar.button(
        "종목 삭제",
        use_container_width=True
    ):
        delete_stock(delete_name)
        st.rerun()

else:
    st.sidebar.info("등록된 관심종목이 없습니다.")


st.sidebar.divider()

if st.sidebar.button(
    "🔄 지금 새로고침",
    use_container_width=True
):
    
    get_stock_data.clear()
    st.rerun()

# ==========================================
# 9. 주가 대시보드
# ==========================================
@st.fragment(
    run_every=refresh_interval if auto_refresh else None
)

def stock_dashboard():
    watchlist = st.session_state.watchlist

    st.subheader("📊 관심종목 현황")

    if not watchlist:
        st.warning("관심종목을 추가해 주세요.")
        return
    
    results = {}
    failed_stocks = []

    # 주가 데이터 조회
    for name, symbol in watchlist.items():
        data = get_stock_data(symbol)

        if data is not None and "error" not in data:
            results[name] = data
        else:
            failed_stocks.append({
                "종목명": name,
                "종목코드": symbol,
                "오류내용": data.get("error", "알수 없는 오류") if data else "데이터 조회 실패"
            })

    # 조회 실패 종목 표시
    if failed_stocks:
        st.warning("일부 종목의 주가 조회에 실패하였습니다.")
        st.dataframe(
            pd.DataFrame(failed_stocks),
            use_container_width=True,
            hide_index=True
        )
    
    if not results:
        st.error(
            "주가 데이터를 가져오지 못했습니다."
            "인터넷 열결 또는 주가코드를 확인하세요."
        )

        return

    # ======================================
    # 전체 종목 요약
    # ======================================
    total = len(watchlist)
    success_count = len(results)

    col1, col2, col3 = st.columns(3)

    col1.metric("등록종목", f"{total}개")
    col2.metric("조회성공", f"{success_count}개")
    col3.metric("조회실패", f"{total-success_count}개")

    st.divider()

    # ======================================
    # 종목별 가격 카드
    # ======================================
    st.subheader("💰 현재 주가")

    items = list(results.items())

    for i in range(0, len(items), 3):

        cols = st.columns(3)

        for j, (name, data) in enumerate(items[i:i+3]):

            with cols[j]:

                rate = data["rate"]

                st.markdown(f"**{name}**")

                st.metric(
                    label="현재가",
                    value=f"{data['price']:,.0f}원",
                    delta=f"{data['change']:+,.0f}원 ({rate:+.2f}%)"
                )

                st.caption(
                    f"거래량: {data['volume']:,}주"
                )

    st.divider()

    # ======================================
    # 종목 전체 테이블
    # ======================================
    st.subheader("📋 관심종목 상세 현황")

    table_data = []

    for name, data in results.items():

        table_data.append({
            "종목명": name,
            "현재가": f"{data['price']:,.0f}원",
            "전일 종가": f"{data['previous']:,.0f}원",
            "전일 대비": f"{data['change']:+,.0f}원",
            "등락률(%)": round(data["rate"], 2),
            "거래량(주)": data["volume"]
        })

    df = pd.DataFrame(table_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ======================================
    # 주가 차트
    # ======================================
    st.subheader("📈 주가 차트")

    chart_name = st.selectbox(
        "차트 종목 선택",
        list(results.keys()),
        key="chart_stock"
    )

    chart_data = results[chart_name]["chart"]

    if chart_data.empty:
        st.warning("차트 데이터가 없습니다.")
    else:

        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=chart_data.index,
                open=chart_data["Open"],
                high=chart_data["High"],
                low=chart_data["Low"],
                close=chart_data["Close"],
                name=chart_name
            )
        )

        fig.update_layout(
            title=f"{chart_name} 주가 차트",
            xaxis_title="날짜",
            yaxis_title="주가 (원)",
            height=500,
            template="plotly_white",
            xaxis_rangeslider_visible=False,
            hovermode="x unified"
        )

        fig.update_xaxes(
            tickformat="%Y-%m-%d",
            hoverformat="%Y-%m-%d"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ======================================
    # 업데이트 시간
    # ======================================
    st.caption(
        "마지막 조회 시간: "
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    st.caption(
        f"자동 새로고침: "
        f"{'ON (' + str(refresh_interval) + '초)' if auto_refresh else 'OFF'}"
    )

# 대시보드 실행
stock_dashboard()

# ==========================================
# 10. 하단 안내
# ==========================================
st.divider()

st.caption("""
본 프로그램은 yfinance를 이용한 주가 정보 조회용입니다.

실제 거래소 실시간 시세와 차이가 있을 수 있으며,
투자 판단 및 자동매매 목적으로 사용하기 전
데이터 정확성과 지연 여부를 확인하세요.
""")