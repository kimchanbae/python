from fastapi import FastAPI
import yfinance as yf

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Stock API Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    data = yf.download(
        symbol,
        period="1mo",
        progress=False
    )

    return {
        "symbol": symbol,
        "data": data.reset_index().to_dict(
            orient="records"
        )
    }