import streamlit as st
from pathlib import Path

# 프로젝트 기본 경로
BASE_DIR = Path(__file__).resolve().parent

# 전체 페이지 공통 설정
st.set_page_config(
    page_title="통합 대시보드",
    page_icon="🖥️",
    layout="wide"
)

# 페이지 등록
dashboard_page = st.Page(
    BASE_DIR / "dashboard.py",
    title="메인 대시보드",
    icon="🏠",
    default=True
)

pcmonitor_page = st.Page(
    BASE_DIR / "pcmonitor" / "pcmonitor.py",
    title="PC 모니터",
    icon="🖥️"
)

stock_page = st.Page(
    BASE_DIR / "stock" / "stock.py",
    title="주식 관심종목 대시보드",
    icon="📈"
)

lotto_page = st.Page(
    BASE_DIR / "lotto" / "lotto.py",
    title="lotto 대시보드",
    icon="🎱"
)

search_page = st.Page(
    BASE_DIR / "rag" / "frontend" / "main.py",
    title="문서검색 대시보드",
    icon=":material/search:"
)

auto_page = st.Page(
    BASE_DIR / "auto" / "auto.py",
    title="자동화 대시보드"
)

# 페이지 네비게이션
pg = st.navigation(
    {
        "메인": [dashboard_page], 
        "모니터링": [pcmonitor_page, stock_page], 
        "AI": [lotto_page, search_page],
        "자동화": [auto_page]
    },
    position="sidebar"
)

# 선택된 페이지 실행
pg.run()