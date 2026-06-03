import joblib
import sqlite3
import pandas as pd
import numpy as np
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. create app first
app = FastAPI()

# 2. add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. load model
model = joblib.load("model.pkl")

# 4. define request model
class PredictionRequest(BaseModel):
    player_id: int
    opponent_abbrev: str
    home_road_flag: str

# 5. routes
@app.get("/")
def root():
    return {"message": "NHL Shot Predictor API"}

@app.get("/search/{query}")
async def search(query: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://api-web.nhle.com/v1/skater-stats-leaders/20242025/2?categories=goals&limit=100",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if res.status_code != 200:
            return []
        data = res.json()
        players = []
        for p in data.get("goals", []):
            full_name = f"{p['firstName']['default']} {p['lastName']['default']}"
            if query.lower() in full_name.lower():
                players.append({
                    "id": p["id"],
                    "name": full_name,
                    "team": p["teamAbbrev"],
                    "position": p["position"],
                    "headshot": p["headshot"]
                })
        return players[:5]

@app.get("/history/{player_id}")
def history(player_id: int):
    conn = sqlite3.connect("nhl.db")
    df = pd.read_sql_query("""
        SELECT game_date as date, shots
        FROM game_logs
        WHERE player_id = ?
        ORDER BY game_date DESC
        LIMIT 10
    """, conn, params=(player_id,))
    conn.close()
    return {"games": df.to_dict(orient="records")}

@app.post("/predict")
def predict(request: PredictionRequest):
    conn = sqlite3.connect("nhl.db")
    df = pd.read_sql_query("""
        SELECT * FROM game_logs
        WHERE player_id = ?
        ORDER BY game_date DESC
        LIMIT 10
    """, conn, params=(request.player_id,))
    conn.close()

    if len(df) == 0:
        return {"error": "Player not found"}

    shots_rolling_5 = df["shots"].head(5).mean()
    shots_rolling_10 = df["shots"].head(10).mean()
    shots_rolling_5_std = df["shots"].head(5).std()
    is_home = 1 if request.home_road_flag == "H" else 0

    conn = sqlite3.connect("nhl.db")
    opp = pd.read_sql_query("""
        SELECT AVG(shots) as avg_shots
        FROM game_logs
        WHERE opponent_abbrev = ?
        LIMIT 10
    """, conn, params=(request.opponent_abbrev,))
    conn.close()

    opponent_shots_allowed_10 = opp["avg_shots"].iloc[0] or 0

    features = pd.DataFrame([{
        "shots_rolling_5": shots_rolling_5,
        "shots_rolling_10": shots_rolling_10,
        "shots_rolling_5_std": shots_rolling_5_std,
        "is_home": is_home,
        "opponent_shots_allowed_10": opponent_shots_allowed_10,
        "prev_shots_per_game": shots_rolling_10,
        "prev_high_danger_per_game": 0,
        "is_forward": 1
    }])

    prediction = model.predict(features)[0]

    return {
        "player_id": request.player_id,
        "predicted_shots": round(float(prediction), 2),
        "opponent": request.opponent_abbrev
    }