import sqlite3
import pandas as pd

conn = sqlite3.connect("/Users/pranavpenmetsa/PycharmProjects/Worldcup/nhl.db")

df = pd.read_sql_query("SELECT * FROM game_logs ORDER BY player_id, game_date", conn)

min_periods=1

df=df.sort_values(["player_id", "game_date"])

#Last 5 games shooting average for each row

df["shots_rolling_5"] = (
    df.groupby("player_id")["shots"]
    .transform(lambda x: x.shift(1).rolling(5, min_periods).mean())
)

#Last 10 games shooting average for each row

df["shots_rolling_10"] = (
    df.groupby("player_id")["shots"]
    .transform(lambda x: x.shift(1).rolling(10, min_periods).mean())
)

df["shots_rolling_5_std"] = (
    df.groupby("player_id")["shots"]
    .transform(lambda x: x.shift(1).rolling(5, min_periods=1).std())
)

#Time on Ice rolling average per row

df["toi_seconds"] = df["toi"].apply(
    lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1])
)

df["toi_minutes"] = df["toi_seconds"] / 60

df["toi_rolling_5"] = (
    df.groupby("player_id")["toi_minutes"]
    .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
)

#converting flag to int

df["is_home"] = (df["home_road_flag"] == "H").astype(int)


# sort by opponent and date
df = df.sort_values(["opponent_abbrev", "game_date"])

# rolling average shots allowed by opponent over last 10 games
df["opponent_shots_allowed_10"] = (
    df.groupby("opponent_abbrev")["shots"]
    .transform(lambda x: x.shift(1).rolling(10, min_periods).mean())
)

# re-sort back to player/date order
df = df.sort_values(["player_id", "game_date"])



print(df[["player_id", "game_date", "opponent_abbrev", "shots", "opponent_shots_allowed_10"]].head(20))

# map current season to previous season for join
season_map = {
    "20232024": 2022,
    "20242025": 2023,
    "20252026": 2024
}

df["prev_season"] = df["season"].map(season_map)

# load moneypuck season stats
df_mp = pd.read_sql_query("""
    SELECT playerId, season,
           position,
           games_played,
           I_F_shotsOnGoal,
           I_F_highDangerShots,
           I_F_xGoals,
           icetime
    FROM skaters_season
""", conn)
# join previous season stats onto each game row
df = df.merge(
    df_mp,
    left_on=["player_id", "prev_season"],
    right_on=["playerId", "season"],
    how="left"
)
print(df.columns.tolist())
print(df[["player_id", "prev_season", "I_F_shotsOnGoal", "position"]].head(5))

# per game rates from previous season
df["prev_shots_per_game"] = df["I_F_shotsOnGoal"] / df["games_played"]
df["prev_high_danger_per_game"] = df["I_F_highDangerShots"] / df["games_played"]
df["prev_xgoals_per_game"] = df["I_F_xGoals"] / df["games_played"]

# encode position as binary — 1 for forward, 0 for defenseman
df["is_forward"] = (df["position"].isin(["C", "L", "R"])).astype(int)

print(df[["player_id", "game_date", "shots", "I_F_shotsOnGoal", "I_F_highDangerShots", "position"]].head(10))

df.to_sql("features", conn, if_exists="replace", index=False)
print("saved to features table")

conn.close()

