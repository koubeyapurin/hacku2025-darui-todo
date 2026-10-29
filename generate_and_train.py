# 学習用の課題データを自動生成して task テーブルに追加し、モデルを学習し直す
# 使い方: python generate_and_train.py
from db import engine, init_db, insert_training_tasks
from train_model import retrain_model

init_db()

with engine.begin() as conn:
    insert_training_tasks(conn)

print("✅ 学習用データを task テーブルに追加しました")

# モデルを再学習
retrain_model()
