import streamlit as st
import psutil
import pandas as pd
import sqlite3
import plotly.express as px
import os
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="PC Monitor",
    page_icon="🖥️",
    layout="wide"
)

DB_FILE = "monitor_history.db"
REFRESH_INTERVAL = 10000

# 자동 새로고침: 10초
st_autorefresh(
    interval=REFRESH_INTERVAL,
    key="pc_monitor_refresh"
)

# =========================
# 데이터베이스 생성
# =========================
def init_db():
    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS monitoring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu REAL,
            memory REAL,
            disk REAL,
            network_sent REAL,
            network_recv REAL
        )
    """)

    conn.commit()
    conn.close()  

# =========================
# PC 상태 측정
# =========================
def get_pc_status():

    cpu = psutil.cpu_percent(interval=None)

    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    disk = psutil.disk_usage(
        os.path.abspath(os.sep)
    )
    disk_percent = disk.percent

    net = psutil.net_io_counters()

    now = datetime.now()

    # 이전 네트워크 측정값
    previous = st.session_state.get("previous_net")

    if previous is None:
        sent_speed = 0
        recv_speed = 0
    else:
        elapsed = (
            now - previous["time"]
        ).total_seconds()

        if elapsed > 0:
            sent_speed = (
                net.bytes_sent - previous["sent"]
            ) / elapsed / 1024 / 1024

            recv_speed = (
                net.bytes_recv - previous["recv"]
            ) / elapsed / 1024 / 1024
        else:
            sent_speed = 0
            recv_speed = 0

    st.session_state.previous_net = {
        "time": now,
        "sent": net.bytes_sent,
        "recv": net.bytes_recv
    }

    return {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "cpu": cpu,
        "memory": memory_percent,
        "disk": disk_percent,
        "network_sent": sent_speed,
        "network_recv": recv_speed,
        "memory_used": memory.used / 1024**3,
        "memory_total": memory.total / 1024**3,
        "disk_used": disk.used / 1024**3,
        "disk_total": disk.total / 1024**3
    }

# =========================
# 측정 데이터 저장
# =========================
def save_data(data):
  
    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        INSERT INTO monitoring (
            timestamp,
            cpu,
            memory,
            disk,
            network_sent,
            network_recv
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["cpu"],
        data["memory"],
        data["disk"],
        data["network_sent"],
        data["network_recv"]
    ))

    conn.commit()
    conn.close()

# =========================
# 이력 조회
# =========================
def get_history(period):

    conn = sqlite3.connect(DB_FILE)

    if period == "최근 1시간":
        cutoff = datetime.now() - timedelta(hours=1)
        query = """
            SELECT * FROM monitoring
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(
            query, conn,
            params=(cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
        )

    elif period == "최근 24시간":
        cutoff = datetime.now() - timedelta(hours=24)
        query = """
            SELECT * FROM monitoring
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(
            query, conn,
            params=(cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
        )

    elif period == "최근 7일":
        cutoff = datetime.now() - timedelta(days=7)
        query = """
            SELECT * FROM monitoring
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(
            query, conn,
            params=(cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
        )

    else:
        df = pd.read_sql_query(
            "SELECT * FROM monitoring ORDER BY timestamp ASC",
            conn
        )

    conn.close()

    return df

# =========================
# 오래된 기록 자동 삭제
# =========================
RETENTION_DAYS = 30

def cleanup_old_data(days=RETENTION_DAYS):

    conn = sqlite3.connect(DB_FILE)

    try:
        cutoff = (
            datetime.now() - timedelta(days=days)
        ).strftime("%Y-%m-%d %H:%M:%S")

        cursor = conn.execute("""
            DELETE FROM monitoring
            WHERE timestamp < ?
        """, (cutoff,))

        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()

        return deleted_count
    finally:
        conn.close()  


# =========================
# 그래프 생성
# =========================
def draw_chart(df, column, title, color):

    if df.empty:
        st.info("아직 저장된 데이터가 없습니다.")
        return

    fig = px.line(
        df,
        x="timestamp",
        y=column,
        title=title,
        markers=False
    )

    fig.update_traces(
        line=dict(color=color, width=2)
    )

    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_title="시간",
        yaxis_title="사용률 (%)",
        yaxis=dict(range=[0, 100]),
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )    


# =========================
# 메인 화면
# =========================
init_db()

cleanup_old_data()

st.title("🖥️ PC Monitor Dashboard")

st.caption(
    "실시간 컴퓨터 상태 모니터링 및 이력 관리 시스템"
)

# PC 상태 측정
data = get_pc_status()

# 측정 데이터 저장
save_data(data)

# =========================
# 상단 상태 표시
# =========================
st.subheader("📊 현재 PC 상태")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "CPU 사용률",
    f'{data["cpu"]:.1f}%'
)

col2.metric(
    "RAM 사용률",
    f'{data["memory"]:.1f}%',
    f'{data["memory_used"]:.2f} / {data["memory_total"]:.2f} GB'
)

col3.metric(
    "디스크 사용률",
    f'{data["disk"]:.1f}%',
    f'{data["disk_used"]:.1f} / {data["disk_total"]:.1f} GB'
)

col4.metric(
    "네트워크 다운로드",
    f'{data["network_recv"]:.3f} MB/s'
)

st.caption(
    f'마지막 측정: {data["timestamp"]} | '
    f'업로드: {data["network_sent"]:.3f} MB/s'
)

st.divider()

# =========================
# 실시간 그래프
# =========================
st.subheader("📈 실시간 모니터링 그래프")

history = get_history("최근 1시간")

col1, col2 = st.columns(2)

with col1:
    draw_chart(
        history,
        "cpu",
        "CPU 사용률",
        "#3B82F6"
    )

with col2:
    draw_chart(
        history,
        "memory",
        "RAM 사용률",
        "#16A34A"
    )

col3, col4 = st.columns(2)

with col3:
    draw_chart(
        history,
        "disk",
        "디스크 사용률",
        "#F59E0B"
    )

with col4:
    if not history.empty:
        fig = px.line(
            history,
            x="timestamp",
            y=["network_sent", "network_recv"],
            title="네트워크 송수신 속도",
            labels={
                "value": "MB/s",
                "timestamp": "시간",
                "variable": "구분",
                "network_sent": "업로드",
                "network_recv": "다운로드"
            },
            color_discrete_map={
                "network_sent": "#9333EA",
                "network_recv": "#06B6D4"
            }
        )

        fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=45, b=10),
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

st.divider()

# =========================
# 모니터링 이력 조회
# =========================
st.subheader("🗂️ 모니터링 이력 조회")

period = st.selectbox(
    "조회 기간",
    [
        "최근 1시간",
        "최근 24시간",
        "최근 7일",
        "전체 기록"
    ]
)

df = get_history(period)

if not df.empty:

    st.write(
        f"총 {len(df):,}개의 측정 기록"
    )

    # 평균 사용률
    a, b, c = st.columns(3)

    a.metric(
        "평균 CPU",
        f'{df["cpu"].mean():.1f}%'
    )

    b.metric(
        "평균 RAM",
        f'{df["memory"].mean():.1f}%'
    )

    c.metric(
        "평균 디스크",
        f'{df["disk"].mean():.1f}%'
    )

    st.dataframe(
        df.sort_values(
            "timestamp",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    # CSV 다운로드
    csv = df.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 이력 CSV 다운로드",
        data=csv,
        file_name="pc_monitor_history.csv",
        mime="text/csv"
    )

else:
    st.info("선택한 기간에 저장된 기록이 없습니다.")

st.divider()

st.caption(
    "PC Monitor | Python + Streamlit + SQLite"
)

# =========================
# 기록 관리
# =========================
st.divider()

st.subheader("🧹 모니터링 기록 관리")

st.write(
    "오래된 모니터링 데이터를 정리하여 "
    "데이터베이스 용량을 관리합니다."
)

days_to_keep = st.selectbox(
    "보관 기간",
    [7, 15, 30, 60, 90, 180],
    index=2,
    format_func=lambda x: f"최근 {x}일 보관"
)

if st.button("🗑️ 오래된 기록 정리"):

    deleted = cleanup_old_data(days_to_keep)

    st.success(
        f"정리 완료! {deleted:,}개의 기록을 삭제했습니다."
    )

    st.rerun()


