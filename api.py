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

@app.get("/teams")
def teams():
    return [
        {"abbrev": "ANA", "name": "Anaheim Ducks", "logo": "https://assets.nhle.com/logos/nhl/svg/ANA_light.svg"},
        {"abbrev": "BOS", "name": "Boston Bruins", "logo": "https://assets.nhle.com/logos/nhl/svg/BOS_light.svg"},
        {"abbrev": "BUF", "name": "Buffalo Sabres", "logo": "https://assets.nhle.com/logos/nhl/svg/BUF_light.svg"},
        {"abbrev": "CGY", "name": "Calgary Flames", "logo": "https://assets.nhle.com/logos/nhl/svg/CGY_light.svg"},
        {"abbrev": "CAR", "name": "Carolina Hurricanes", "logo": "https://assets.nhle.com/logos/nhl/svg/CAR_light.svg"},
        {"abbrev": "CHI", "name": "Chicago Blackhawks", "logo": "https://assets.nhle.com/logos/nhl/svg/CHI_light.svg"},
        {"abbrev": "COL", "name": "Colorado Avalanche", "logo": "https://assets.nhle.com/logos/nhl/svg/COL_light.svg"},
        {"abbrev": "CBJ", "name": "Columbus Blue Jackets", "logo": "https://assets.nhle.com/logos/nhl/svg/CBJ_light.svg"},
        {"abbrev": "DAL", "name": "Dallas Stars", "logo": "https://assets.nhle.com/logos/nhl/svg/DAL_light.svg"},
        {"abbrev": "DET", "name": "Detroit Red Wings", "logo": "https://assets.nhle.com/logos/nhl/svg/DET_light.svg"},
        {"abbrev": "EDM", "name": "Edmonton Oilers", "logo": "https://assets.nhle.com/logos/nhl/svg/EDM_light.svg"},
        {"abbrev": "FLA", "name": "Florida Panthers", "logo": "https://assets.nhle.com/logos/nhl/svg/FLA_light.svg"},
        {"abbrev": "LAK", "name": "Los Angeles Kings", "logo": "https://assets.nhle.com/logos/nhl/svg/LAK_light.svg"},
        {"abbrev": "MIN", "name": "Minnesota Wild", "logo": "https://assets.nhle.com/logos/nhl/svg/MIN_light.svg"},
        {"abbrev": "MTL", "name": "Montreal Canadiens", "logo": "https://assets.nhle.com/logos/nhl/svg/MTL_light.svg"},
        {"abbrev": "NSH", "name": "Nashville Predators", "logo": "https://assets.nhle.com/logos/nhl/svg/NSH_light.svg"},
        {"abbrev": "NJD", "name": "New Jersey Devils", "logo": "https://assets.nhle.com/logos/nhl/svg/NJD_light.svg"},
        {"abbrev": "NYI", "name": "New York Islanders", "logo": "https://assets.nhle.com/logos/nhl/svg/NYI_light.svg"},
        {"abbrev": "NYR", "name": "New York Rangers", "logo": "https://assets.nhle.com/logos/nhl/svg/NYR_light.svg"},
        {"abbrev": "OTT", "name": "Ottawa Senators", "logo": "https://assets.nhle.com/logos/nhl/svg/OTT_light.svg"},
        {"abbrev": "PHI", "name": "Philadelphia Flyers", "logo": "https://assets.nhle.com/logos/nhl/svg/PHI_light.svg"},
        {"abbrev": "PIT", "name": "Pittsburgh Penguins", "logo": "https://assets.nhle.com/logos/nhl/svg/PIT_light.svg"},
        {"abbrev": "STL", "name": "St. Louis Blues", "logo": "https://assets.nhle.com/logos/nhl/svg/STL_light.svg"},
        {"abbrev": "SJS", "name": "San Jose Sharks", "logo": "https://assets.nhle.com/logos/nhl/svg/SJS_light.svg"},
        {"abbrev": "SEA", "name": "Seattle Kraken", "logo": "https://assets.nhle.com/logos/nhl/svg/SEA_light.svg"},
        {"abbrev": "TBL", "name": "Tampa Bay Lightning", "logo": "https://assets.nhle.com/logos/nhl/svg/TBL_light.svg"},
        {"abbrev": "TOR", "name": "Toronto Maple Leafs", "logo": "https://assets.nhle.com/logos/nhl/svg/TOR_light.svg"},
        {"abbrev": "UTA", "name": "Utah Hockey Club", "logo": "https://assets.nhle.com/logos/nhl/svg/UTA_light.svg"},
        {"abbrev": "VAN", "name": "Vancouver Canucks", "logo": "https://assets.nhle.com/logos/nhl/svg/VAN_light.svg"},
        {"abbrev": "VGK", "name": "Vegas Golden Knights", "logo": "https://assets.nhle.com/logos/nhl/svg/VGK_light.svg"},
        {"abbrev": "WSH", "name": "Washington Capitals", "logo": "https://assets.nhle.com/logos/nhl/svg/WSH_light.svg"},
        {"abbrev": "WPG", "name": "Winnipeg Jets", "logo": "https://assets.nhle.com/logos/nhl/svg/WPG_light.svg"}
    ]


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