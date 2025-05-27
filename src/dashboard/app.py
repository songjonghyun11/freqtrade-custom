# src/dashboard/app.py
from fastapi import FastAPI
from .models import Trade, Reflection

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/trades")
def get_trades():
    # TODO: DB에서 trade 리스트 조회
    return []

@app.get("/reflections")
def get_reflections():
    # TODO: DB에서 reflection 리스트 조회
    return []

@app.post("/reflections")
def create_reflection(ref: Reflection):
    # TODO: DB에 reflection 저장
    return ref
