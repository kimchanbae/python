import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from lotto.lotto_date import (
    load_data,
    collect_all,
    train_model,
    get_number_scores,
    NUMBER_COLS
)

from io import StringIO

import json

st.set_page_config(
    page_title="Lotto AI Analyzer",
    page_icon="🎱",
    layout="wide"
)

# ----------------------------------
# 디자인
# ----------------------------------
st.markdown("""
<style>
/* 전체 배경 */
.stApp {
    background-color: #F4F7FC;
    color: #25344A;
}

/* 메인 영역 */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* 제목 */
h1, h2, h3 {
    color: #1E3A5F !important;
    font-weight: 700;
}

/* 일반 텍스트 */
p, label, span {
    color: #334155;
}

/* 카드 및 Metric */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #DCE5F0;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(30, 58, 95, 0.06);
}

/* Metric 값 */
[data-testid="stMetricValue"] {
    color: #2563EB;
    font-weight: 700;
}

/* Metric 라벨 */
[data-testid="stMetricLabel"] {
    color: #64748B;
}

/* 로또 번호 카드 */
.game-card {
    background: #FFFFFF;
    border: 1px solid #DCE5F0;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 12px;
}

/* 로또 번호 */
.lotto-ball {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 49px;
    height: 49px;
    border-radius: 50%;
    color: #FFFFFF !important;
    font-size: 19px;
    font-weight: bold;
    margin: 4px;
    box-shadow: 0 3px 6px rgba(0,0,0,0.12);
}

/* 버튼 */
.stButton > button {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 10px 18px;
}

.stButton > button:hover {
    background-color: #1D4ED8;
    color: #FFFFFF;
}

/* 다운로드 버튼 */
.stDownloadButton > button {
    background-color: #16A34A;
    color: #FFFFFF;
    border-radius: 8px;
}

/* 탭 */
.stTabs [data-baseweb="tab"] {
    color: #475569;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    color: #2563EB !important;
}

/* 구분선 */
hr {
    border-color: #DCE5F0;
}
""", unsafe_allow_html=True)


# ----------------------------------
# 캐시
# ----------------------------------
@st.cache_data(ttl=3600)
def get_data():
    return load_data()


@st.cache_resource
def get_trained_model(data_json):

    df = pd.read_json(
        StringIO(data_json),
        orient="split"
    )

    return train_model(df)


# ----------------------------------
# 번호 공 출력
# ----------------------------------
def show_balls(numbers):

    html = ""

    for n in numbers:

        if n <= 10:
            color = "#FBC02D"
        elif n <= 20:
            color = "#2196F3"
        elif n <= 30:
            color = "#E53935"
        elif n <= 40:
            color = "#777777"
        else:
            color = "#43A047"

        html += f"""
        <span class="lotto-ball"
        style="background:{color}">
        {n}
        </span>
        """

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# ----------------------------------
# 제목
# ----------------------------------
st.title("🎱 LOTTO AI ANALYZER")

st.caption(
    "Machine Learning · Pattern Analysis · Lotto 6/45"
)

# ----------------------------------
# 데이터 수집
# ----------------------------------
with st.spinner("최신 회차 및 데이터 확인 중..."):

    try:
        df = get_data()
    except Exception as e:
        st.error(f"데이터 수집 오류: {e}")
        st.stop()

latest = int(df["draw_no"].max())

last_row = df.iloc[-1]

st.success(
    f"데이터 준비 완료 | 최신 {latest}회 | "
    f"총 {len(df):,}회 데이터"
)

# ----------------------------------
# 상단 통계
# ----------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "최신 회차",
    f"{latest:,}회"
)

c2.metric(
    "누적 데이터",
    f"{len(df):,}회"
)

c3.metric(
    "최신 추첨일",
    str(last_row["date"])
)

c4.metric(
    "추천 게임",
    "5 GAME"
)

with st.expander("최신 당첨번호 확인"):

    show_balls(
        [int(last_row[c]) for c in NUMBER_COLS]
    )

st.divider()

# ----------------------------------
# 데이터 새로고침
# ----------------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("🧠 AI 머신러닝 분석")

with col2:

    if st.button(
        "🔄 데이터 최신화",
        use_container_width=True
    ):

        with st.spinner("최신 회차 수집 중..."):

            try:
                collect_all()
                get_data.clear()
                get_trained_model.clear()

                st.success("데이터 업데이트 완료")
                st.rerun()

            except Exception as e:
                st.error(f"업데이트 실패: {e}")


# ----------------------------------
# 분석 범위
# ----------------------------------
analysis_range = st.selectbox(
    "분석 데이터 범위",
    [
        "전체 회차",
        "최근 300회",
        "최근 100회",
        "최근 50회"
    ]
)

if analysis_range == "최근 300회":
    analysis_df = df.tail(300).reset_index(drop=True)

elif analysis_range == "최근 100회":
    analysis_df = df.tail(100).reset_index(drop=True)

elif analysis_range == "최근 50회":
    analysis_df = df.tail(50).reset_index(drop=True)

else:
    analysis_df = df.copy().reset_index(drop=True)


if len(analysis_df) < 101:
    st.warning("머신러닝 분석에는 최소 101회 이상의 데이터가 필요합니다.")
    st.stop()


# ----------------------------------
# 모델 학습
# ----------------------------------
with st.spinner("Random Forest 모델 학습 중..."):

    try:
        # 학습용 데이터는 전체 누적 데이터 사용
        data_json = df.to_json(orient="split")

        model = get_trained_model(data_json)

        # 점수 분석 범위는 선택한 기간 사용
        scores = get_number_scores(
            analysis_df,
            model
        )

    except Exception as e:
        st.error(f"AI 분석 실패: {e}")
        st.stop()


# ----------------------------------
# 번호 분석
# ----------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🎱 AI 번호 추천",
    "📊 번호 패턴 분석",
    "🔥 출현 빈도",
    "📋 회차 데이터"
])


# ==================================
# TAB 1
# ==================================
with tab1:

    st.subheader("🍀 AI 추천 번호 5게임")

    st.caption(
        "Random Forest 점수를 이용한 가중 랜덤 조합입니다. "
        "당첨 가능성을 예측하거나 보장하지 않습니다."
    )

    # 게임별 번호 조합 생성
    def make_games(scores, count=5):

        weights = scores["ML 점수"].to_numpy()

        # 모든 번호에 최소 가중치를 주어 다양성 확보
        weights = np.maximum(weights, 0.1)
        weights = weights / weights.sum()

        games = set()
        attempts = 0

        while len(games) < count and attempts < 10000:

            selected = np.random.choice(
                np.arange(1, 46),
                size=6,
                replace=False,
                p=weights
            )

            game = tuple(sorted(selected.tolist()))

            # 게임 간 완전 동일 조합 방지
            if game not in games:
                games.add(game)

            attempts += 1

        return sorted(games)


    if st.button(
        "🎲 AI 추천 번호 5게임 생성",
        use_container_width=True,
        type="primary"
    ):

        st.session_state["ai_games"] = make_games(
            scores,
            5
        )

    games = st.session_state.get("ai_games", [])

    if games:

        for i, game in enumerate(games):

            st.markdown(
                f'<div class="game-card">'
                f'<b>GAME {i+1}</b>'
                f'</div>',
                unsafe_allow_html=True
            )

            show_balls(game)

            st.caption(
                f"합계: {sum(game)} | "
                f"홀수: {sum(n % 2 for n in game)} | "
                f"짝수: {sum(n % 2 == 0 for n in game)}"
            )

        st.divider()

        result_df = pd.DataFrame(
            games,
            columns=[
                "번호1", "번호2", "번호3",
                "번호4", "번호5", "번호6"
            ]
        )

        csv = result_df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "📥 추천 번호 CSV 다운로드",
            data=csv,
            file_name="lotto_ai_5games.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:
        st.info("AI 추천 번호 생성 버튼을 눌러주세요.")


# ==================================
# TAB 2
# ==================================
with tab2:

    st.subheader("📊 번호별 머신러닝 분석")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### AI 점수 TOP 10")

        top = scores.nlargest(
            10,
            "ML 점수"
        )

        st.dataframe(
            top,
            use_container_width=True,
            hide_index=True
        )

    with col2:

        st.markdown("### AI 번호 점수")

        fig = px.bar(
            scores,
            x="번호",
            y="ML 점수",
            color="ML 점수",
            color_continuous_scale="Viridis"
        )

        fig.update_layout(
            template="plotly_white",
            height=400,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(
                color="#334155",
                family="Arial"
            ),
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.info(
        "AI 점수는 과거 패턴에 대한 모델의 상대적 분류 점수이며 "
        "실제 추첨 확률이 아닙니다."
    )


# ==================================
# TAB 3
# ==================================
with tab3:

    st.subheader("🔥 번호 출현 빈도")

    all_numbers = (
        analysis_df[NUMBER_COLS]
        .values.flatten()
    )

    freq = (
        pd.Series(all_numbers)
        .value_counts()
        .reindex(range(1, 46), fill_value=0)
        .sort_index()
    )

    freq_df = pd.DataFrame({
        "번호": freq.index,
        "출현 횟수": freq.values
    })

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 많이 나온 번호")

        st.dataframe(
            freq_df.nlargest(
                10,
                "출현 횟수"
            ),
            use_container_width=True,
            hide_index=True
        )

    with col2:

        st.markdown("### 적게 나온 번호")

        st.dataframe(
            freq_df.nsmallest(
                10,
                "출현 횟수"
            ),
            use_container_width=True,
            hide_index=True
        )

    fig = px.bar(
        freq_df,
        x="번호",
        y="출현 횟수",
        color="출현 횟수",
        color_continuous_scale="Turbo"
    )

    fig.update_layout(
        template="plotly_white",
        height=400,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(
            color="#334155",
            family="Arial"
        ),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==================================
# TAB 4
# ==================================
with tab4:

    st.subheader("📋 전체 회차 당첨 데이터")

    st.dataframe(
        df.sort_values(
            "draw_no",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "전체 당첨번호 CSV 다운로드",
        csv,
        file_name="lotto_all_history.csv",
        mime="text/csv"
    )


st.divider()

st.caption(
    "Lotto AI Analyzer | 통계 및 머신러닝 기반 참고용 번호 분석 시스템"
)