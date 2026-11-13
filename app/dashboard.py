import streamlit as st

st.title("🏠 Python 통합 대시보드")

st.caption(
    "통합 시스템 모니터링 및 관리"
)

st.divider()

st.subheader("모니터링 서비스")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🖥️ PC Monitor")
    st.write(
        "CPU, RAM, 디스크, 네트워크 상태를 "
        "실시간으로 모니터링합니다."
    )
    st.page_link(
        "app/pcmonitor/pcmonitor.py",
        label="PC 모니터 실행",
        icon="🖥️",
        use_container_width=True
    )

with col2:
    st.markdown("### 📈 Stock Monitor")
    st.write("주식 관심종목 및 시세 모니터링")
    st.page_link(
        "app/stock/stock.py",
        label="주식 관심종목 대시보드",
        icon="📈",
        use_container_width=True
    )

with col3:
    st.markdown("### 자동화 monitor")
    st.write("자동화 모니터링")
    st.page_link(
        "app/auto/auto.py",
        label="준비중",
        use_container_width=True
    )

st.divider()

st.caption(
    "Python Integrated Monitoring System"
)