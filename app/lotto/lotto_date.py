import os
import time
import requests
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier

BASE_URL = "https://www.dhlottery.co.kr/lt645"

# project/app/lotto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# project/app/lotto/lotto_data
DATA_DIR = os.path.join(BASE_DIR, "lotto_data")

CSV_PATH = os.path.join(DATA_DIR, "draws.csv")

# 데이터 폴더 자동 생성(app->lotto->lotto_data)
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.dhlottery.co.kr/lt645/result"
}

NUMBER_COLS = [f"n{i}" for i in range(1, 7)]


def api_get(url, params=None):
    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    if "application/json" not in response.headers.get(
        "Content-Type", ""
    ):
        raise RuntimeError("동행복권 API가 JSON을 반환하지 않았습니다.")

    return response.json()


def get_last_round():
    data = api_get(
        f"{BASE_URL}/selectPstLt645Info.do"
    )

    rows = data["data"]["list"]

    if not rows:
        raise RuntimeError("최신 회차를 확인할 수 없습니다.")

    return int(rows[0]["ltEpsd"])


def fetch_rounds(center):
    data = api_get(
        f"{BASE_URL}/selectPstLt645InfoNew.do",
        params={
            "srchDir": "center",
            "srchLtEpsd": center
        }
    )

    return data["data"]["list"]


def convert_row(item):

    numbers = [
        int(item[f"tm{i}WnNo"])
        for i in range(1, 7)
    ]

    date = str(item["ltRflYmd"])

    return {
        "draw_no": int(item["ltEpsd"]),
        "date": (
            f"{date[:4]}-{date[4:6]}-{date[6:]}"
        ),
        **{
            f"n{i+1}": numbers[i]
            for i in range(6)
        },
        "bonus": int(item["bnsWnNo"])
    }


def collect_all(progress=None):

    os.makedirs(DATA_DIR, exist_ok=True)

    latest = get_last_round()

    # 기존 데이터 읽기
    if os.path.exists(CSV_PATH):
        old = pd.read_csv(CSV_PATH)
    else:
        old = pd.DataFrame()

    existing = {}

    if not old.empty:
        existing = {
            int(row["draw_no"]): row.to_dict()
            for _, row in old.iterrows()
        }

    # 최초 수집은 전체 회차
    if not existing:
        center = 1
    else:
        center = max(existing.keys()) + 1

    # 신규 회차만 수집
    while center <= latest:

        items = fetch_rounds(center)

        if not items:
            raise RuntimeError(
                f"{center}회차 주변 데이터가 없습니다."
            )

        for item in items:
            row = convert_row(item)
            existing[row["draw_no"]] = row

        if progress:
            progress(
                min(center + 5, latest),
                latest
            )

        center += 10

        if center <= latest:
            time.sleep(0.7)

    df = pd.DataFrame(
        list(existing.values())
    )

    df = df.sort_values("draw_no")
    df = df[
        df["draw_no"] <= latest
    ].reset_index(drop=True)

    # CSV 저장
    df.to_csv(
        CSV_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    return df


def load_data():

    if not os.path.exists(CSV_PATH):
        return collect_all()

    df = pd.read_csv(CSV_PATH)

    latest = get_last_round()

    cached_latest = int(df["draw_no"].max())

    # 신규 회차가 있을 때만 갱신
    if latest > cached_latest:
        df = collect_all()

    return df.sort_values("draw_no").reset_index(drop=True)


# ---------------------------------
# 번호별 머신러닝 데이터 생성
# ---------------------------------
def make_ml_dataset(df):

    draws = df[NUMBER_COLS].values
    X = []
    y = []

    # 과거 100회 데이터가 쌓인 이후 학습
    for t in range(100, len(draws)):

        past = draws[:t]

        for number in range(1, 46):

            features = []

            # 최근 출현 빈도
            for window in [20, 50, 100]:

                recent = past[-window:]

                count = np.sum(recent == number)

                features.append(count / window)

            # 마지막 출현 후 경과 회차
            appeared = np.where(
                np.any(past == number, axis=1)
            )[0]

            gap = (
                t - 1 - appeared[-1]
                if len(appeared)
                else t
            )

            features.append(min(gap, 200) / 200)

            # 번호 자체의 특성
            features.append(number / 45)

            # 홀수 여부
            features.append(number % 2)

            X.append(features)

            y.append(
                int(number in draws[t])
            )

    return np.array(X), np.array(y)


# ---------------------------------
# Random Forest 학습
# ---------------------------------
def train_model(df):

    X, y = make_ml_dataset(df)

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    return model


# ---------------------------------
# 최신 번호별 점수
# ---------------------------------
def get_number_scores(df, model):

    draws = df[NUMBER_COLS].values
    t = len(draws)

    scores = []

    for number in range(1, 46):

        features = []

        for window in [20, 50, 100]:

            recent = draws[-window:]

            count = np.sum(recent == number)

            features.append(count / window)

        appeared = np.where(
            np.any(draws == number, axis=1)
        )[0]

        gap = (
            t - 1 - appeared[-1]
            if len(appeared)
            else t
        )

        features.append(min(gap, 200) / 200)
        features.append(number / 45)
        features.append(number % 2)

        probability = model.predict_proba(
            [features]
        )[0, 1]

        scores.append({
            "번호": number,
            "ML 점수": round(
                float(probability) * 100, 2
            ),
            "최근20회": round(features[0] * 100, 1),
            "최근50회": round(features[1] * 100, 1),
            "최근100회": round(features[2] * 100, 1),
            "미출현": gap
        })

    return pd.DataFrame(scores)