import os
import pandas as pd
import pickle
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from db import BASE_DIR, engine

MODEL_DIR = os.path.join(BASE_DIR, "model")

def preprocess_dates(df):
    df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    df = df.dropna(subset=['due_date', 'created_at'])
    df = df.copy()  # スライス警告回避

    df['days_until_due'] = (df['due_date'] - df['created_at']).dt.days
    df['weekday'] = df['created_at'].dt.weekday
    return df

def retrain_model():
    df = pd.read_sql(
        """
        SELECT subject, category, difficulty, due_date, created_at, time_spent
        FROM task
        WHERE time_spent IS NOT NULL
        """,
        engine
    )

    if df.empty:
        print("❌ 学習に使えるデータがありません。")
        return

    df = preprocess_dates(df)
    if df.empty:
        print("❌ 有効な日付データがありません。")
        return

    # 説明変数と目的変数に分割
    X_raw = df[['subject', 'category', 'difficulty', 'days_until_due', 'weekday']]
    y = df['time_spent']

    # カテゴリ変数エンコード
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    X_cat = encoder.fit_transform(X_raw[['subject', 'category']])
    X_cat_df = pd.DataFrame(X_cat, columns=encoder.get_feature_names_out(['subject', 'category']))

    # 数値データと連結
    X_final = pd.concat([X_raw.drop(columns=['subject', 'category']).reset_index(drop=True), X_cat_df], axis=1)

    # 学習・テストデータ分割
    X_train, X_test, y_train, y_test = train_test_split(X_final, y, test_size=0.2, random_state=42)

    # モデル学習
    model = RandomForestRegressor()
    model.fit(X_train, y_train)

    # 保存用ディレクトリ作成
    os.makedirs(MODEL_DIR, exist_ok=True)

    # モデル保存
    with open(os.path.join(MODEL_DIR, "model.pkl"), "wb") as f:
        pickle.dump(model, f)

    # エンコーダ保存
    with open(os.path.join(MODEL_DIR, "encoder.pkl"), "wb") as f:
        pickle.dump(encoder, f)

    print("✅ モデル再学習完了")

# モジュール単体実行時の動作
if __name__ == "__main__":
    retrain_model()
