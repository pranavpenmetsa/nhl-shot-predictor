import requests
import sqlite3



def get(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Setup database - do this once at the top
conn = sqlite3.connect("nhl.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_logs (
        player_id       INTEGER,
        season          TEXT,
        game_id         INTEGER,
        game_date       TEXT,
        team_abbrev     TEXT,
        opponent_abbrev TEXT,
        home_road_flag  TEXT,
        goals           INTEGER,
        assists         INTEGER,
        shots           INTEGER,
        toi             TEXT,
        pim             INTEGER,
        UNIQUE(player_id, game_id)
    )
""")
conn.commit()

# Get teams
data1 = get("https://api-web.nhle.com/v1/standings/now")
teams = []
for team in data1["standings"]:
    teams.append(team["teamAbbrev"]["default"])

seasons = ["20232024", "20242025", "20252026"]


for season in seasons:
    seen_players = set()
    for team in teams:
        try:
            roster_data = get(f"https://api-web.nhle.com/v1/roster/{team}/{season}")

        except Exception as e:
            print(f"Skipping {team} {season}: {e}")
            continue


        player_ids = []
        for group in ["forwards", "defensemen"]:
            for player in roster_data[group]:
                player_ids.append(player["id"])

        for player_id in player_ids:
            if player_id not in seen_players:
                seen_players.add(player_id)
                game_log = get(f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season}/2")

                # Insert each game into the database
                for game in game_log["gameLog"]:
                    cursor.execute("""
                        INSERT OR IGNORE INTO game_logs
                            (player_id, season, game_id, game_date, team_abbrev,
                             opponent_abbrev, home_road_flag, goals, assists, shots, toi, pim)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        player_id,
                        season,
                        game["gameId"],
                        game["gameDate"],
                        game["teamAbbrev"],
                        game["opponentAbbrev"],
                        game["homeRoadFlag"],
                        game["goals"],
                        game["assists"],
                        game["shots"],
                        game["toi"],
                        game["pim"]
                    ))

        conn.commit()  # commit after each team

conn.close()