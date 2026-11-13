FROM python:3.14

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8501

CMD ["streamlit", "run", "app/app.py", "--server.address=127.0.0.1", "--server.port=8501", "--server.headless=true"]