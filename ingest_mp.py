import sqlite3
import pandas as pd

conn = sqlite3.connect("/Users/pranavpenmetsa/PycharmProjects/Worldcup/nhl.db")

df_2023 = pd.read_csv("skaters_2022-2023.csv")
df_2024 = pd.read_csv("skaters_2023-2024.csv")
df_2025 = pd.read_csv("skaters_2024-2025.csv")

df = pd.concat([df_2023, df_2024, df_2025])

df = df[df["situation"] == "5on5"]

df.to_sql("skaters_season", conn, if_exists="replace", index=False)
print(f"Saved {df.shape[0]} rows")
conn.close()