from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

# 나중에 /trades, /reflections 등 추가 예정
