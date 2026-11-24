import streamlit as st
import requests
import time
import os

# FastAPI 주소
API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
)

st.set_page_config(
    page_title="통합 지식검색 AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 통합 지식검색 AI")
st.caption(
    "Qwen2.5 1.5B + LangChain + ChromaDB"
)

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# API 연결 확인
def api_get(endpoint):

    try:
        st.info(f"API 요청: {API_URL}{endpoint}")

        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=(5, 120)
        )

        response.raise_for_status()

        st.success("Backend 응답 성공")

        return response.json()

    except requests.exceptions.ConnectTimeout:
        st.error("Backend 연결 시간 초과")

    except requests.exceptions.ReadTimeout:
        st.error("Backend 응답 대기 시간 초과")

    except requests.exceptions.ConnectionError as e:
        st.error(f"Backend 연결 실패: {e}")

    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP 오류: {e}")

    except Exception as e:
        st.error(f"기타 오류: {repr(e)}")

    return None


# 문서 업로드
st.sidebar.header("📂 문서 관리")

uploaded_files = st.sidebar.file_uploader(
    "문서 선택",
    type=[
        "pdf", "docx", "txt", "md",
        "csv", "xlsx", "pptx", "html", "htm"
    ],
    accept_multiple_files=True
)


if st.sidebar.button(
    "문서 업로드",
    use_container_width=True
):

    if not uploaded_files:

        st.sidebar.warning(
            "업로드할 문서를 선택하세요."
        )

    else:

        files = []

        for file in uploaded_files:

            files.append((
                "files",
                (
                    file.name,
                    file.getvalue(),
                    "application/octet-stream"
                )
            ))

        try:

            response = requests.post(
                f"{API_URL}/api/upload",
                files=files,
                timeout=300
            )

            response.raise_for_status()

            result = response.json()

            st.sidebar.success(
                f"{result['total']}개 파일 업로드 완료"
            )

            if result["errors"]:
                st.sidebar.warning(result["errors"])

        except requests.RequestException as e:

            st.sidebar.error(str(e))


# 문서 색인
if st.sidebar.button(
    "문서 색인 실행",
    use_container_width=True
):

    try:
        # 색인 시작 요청
        response = requests.post(
            f"{API_URL}/api/index",
            timeout=60
        )

        response.raise_for_status()

        st.sidebar.info("문서 색인 작업이 시작되었습니다.")
        # 진행 상태 표시
        status_box = st.sidebar.empty()

        while True:
            try:
                response = requests.get(
                    f"{API_URL}/api/index/status",
                    timeout=60
                )

                response.raise_for_status()
            except requests.Timeout:
                status_box.warning(
                    "Backend 응답 대기 중입니다. 다시 확인합니다..."
                )

                time.sleep(3)
                continue
            
            result = response.json()

            status = result["status"]

            print("[FRONTEND STATUS]", result)

            status_box.info(
                f"현재 상태: {status}\n\n"
                f"메시지: {result['message']}"
            )
            
            if status in ("queued", "running"):
                time.sleep(3)

            elif status == "completed":

                status_box.success(
                    f"색인 완료! "
                    f"전체 청크: "
                    f"{result['document_chunks']}"
                )

                break

            elif status == "failed":

                status_box.error(
                    result["error"]
                )

                break

            else:

                status_box.warning(
                    f"예상하지 못한 상태: {status}"
                )

                break
    except requests.RequestException as e:
        st.sidebar.error(str(e))


# 문서 현황
st.sidebar.divider()
st.sidebar.subheader("📊 문서 현황")

if st.sidebar.button(
    "현황 새로고침",
    use_container_width=True
):

    status = api_get("/api/documents")

    if status:

        st.sidebar.metric(
            "색인된 문서",
            status["total_files"]
        )

        st.sidebar.metric(
            "전체 청크",
            status["total_chunks"]
        )

        with st.sidebar.expander("문서 목록"):

            for doc in status["documents"]:

                st.write(
                    f"📄 {doc['filename']} "
                    f"({doc['chunks']} chunks)"
                )

# 대화 이력 출력
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message.get("sources"):

            with st.expander("참고 문서"):

                for source in message["sources"]:

                    st.write(
                        source["source"]
                    )

                    if source.get("location"):
                        st.caption(
                            ", ".join(source["location"])
                        )


# 질문 입력
question = st.chat_input(
    "지식 저장소에 질문하세요."
)

if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner("AI가 답변을 생성하고 있습니다..."):

            try:

                response = requests.post(
                    f"{API_URL}/api/query",
                    json={
                        "question": question,
                        "top_k": 5
                    },
                    timeout=300
                )

                response.raise_for_status()

                result = response.json()

                answer = result["answer"]
                sources = result["sources"]

                st.markdown(answer)

                if sources:

                    with st.expander("📚 참고 문서"):

                        for i, source in enumerate(
                            sources, 1
                        ):

                            st.write(
                                f"{i}. {source['source']}"
                            )

                            if source.get("location"):
                                st.caption(
                                    ", ".join(
                                        source["location"]
                                    )
                                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except requests.RequestException as e:

                st.error(
                    f"답변 생성 오류: {e}"
                )