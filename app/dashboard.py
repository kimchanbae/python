import streamlit as st

st.title("🏠 통합 대시보드")

st.caption(
    "통합 시스템 모니터링 및 관리"
)

st.divider()

col_count = 3

st.subheader("모니터링 서비스")

mot_pages = [
    {
        "title": "🖥️ PC Monitor",
        "description": "CPU, RAM, 디스크, 네트워크 상태를 "
                        "실시간으로 모니터링합니다.",
        "path": "pcmonitor/pcmonitor.py",
        "label": "PC 모니터 실행",
        "icon": "🖥️"
    },
    {
        "title": "📈 Stock Monitor",
        "description": "주식 관심종목 및 시세 모니터링",
        "path": "stock/stock.py",
        "label": "주식 관심종목 대시보드",
        "icon": "📈"
    }
]

for i in range(0, len(mot_pages), col_count):
    cols = st.columns(col_count)
    for col, page in zip(cols, mot_pages[i:i + col_count]):
        with col:
            st.markdown(f"### {page['title']}")
            st.write(page['description'])
            st.page_link(
                page["path"],
                label=page["label"],
                icon=page["icon"],
                use_container_width=True
            )

st.divider()

st.subheader("AI 서비스")

ai_pages = [
    {
        "title": "🎱 Lotto Monitor",
        "description": "AI 로또 번호 생성 서비스입니다.",
        "path": "lotto/lotto.py",
        "label": "Lotto 번호생성 서비스 실행",
        "icon": "🎱"
    },
    {
        "title": "🔍 검색 Monitor",
        "description": "AI 문서검색 서비스입니다.",
        "path": "rag/frontend/main.py",
        "label": "문서검색 서비스 실행",
        "icon": ":material/search:"
    }
]

for i in range(0, len(ai_pages), col_count):
    cols = st.columns(col_count)
    for col, page in zip(cols, ai_pages[i:i + col_count]):
        with col:
            st.markdown(f"### {page['title']}")
            st.write(page['description'])
            st.page_link(
                page["path"],
                label=page["label"],
                icon=page["icon"],
                use_container_width=True
            )

st.divider()

st.subheader("자동화 서비스")

auto_pages = [
    {
        "title": "자동화 monitor",
        "description": "자동화 모니터링 서비스입니다.",
        "path": "auto/auto.py",
        "label": "준비중",
        "icon": ""
    }
]

for i in range(0, len(auto_pages), col_count):
    cols = st.columns(col_count)
    for col, page in zip(cols, auto_pages[i:i + col_count]):
        with col:
            st.markdown(f"### {page['title']}")
            st.write(page['description'])
            st.page_link(
                page["path"],
                label=page["label"],
                icon=page["icon"],
                use_container_width=True
            )

st.divider()

st.caption(
    "Python Integrated Monitoring System"
)