import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import numpy as np

conn = sqlite3.connect("/Users/pranavpenmetsa/PycharmProjects/Worldcup/nhl.db")
df = pd.read_sql_query("SELECT * FROM features", conn)

df = df.dropna(subset=[
    "shots_rolling_5",
    "shots_rolling_10",
    "shots_rolling_5_std",
    "opponent_shots_allowed_10",
    "prev_shots_per_game",
    "prev_high_danger_per_game",
    "is_forward"
])


features = [
    "shots_rolling_5",
    "shots_rolling_10",
    "shots_rolling_5_std",
    "is_home",
    "opponent_shots_allowed_10",
    "prev_shots_per_game",
    "prev_high_danger_per_game",
    "is_forward"
]

target = "shots"

X = df[features]
y = df[target]

train = df[df["season_x"] != "20252026"]
test = df[df["season_x"] == "20252026"]

X_train = train[features]
y_train = train[target]
X_test = test[features]
y_test = test[target]


print(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}")

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"Linear Regression RMSE: {rmse:.3f}")

for feature, weight in zip(features, model.coef_):
    print(f"{feature}: {weight:.3f}")


naive_pred = [y_train.mean()] * len(y_test)
naive_rmse = np.sqrt(mean_squared_error(y_test, naive_pred))
print(f"Naive baseline RMSE: {naive_rmse:.3f}")

from xgboost import XGBRegressor

xgb_model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=5,
    objective="count:poisson",
    random_state=42
)

xgb_model.fit(X_train, y_train)

y_pred_xgb = xgb_model.predict(X_test)

rmse_xgb = np.sqrt(mean_squared_error(y_test, y_pred_xgb))
print(f"XGBoost RMSE: {rmse_xgb:.3f}")

import joblib

joblib.dump(xgb_model, "model.pkl")
print("Model saved to model.pkl")