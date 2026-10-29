import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 絶対パスを使ってデータベースファイルを指定する
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
DATABASE_URI = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URI, echo=False)

# 学習用データの教科・カテゴリの候補（model/model.pkl はこのデータで学習した）
SUBJECTS = ["キャリア教育基礎", "選択独語第一", "微分積分学第一", "Academic Spoken English"]
CATEGORIES = ["小テスト", "レポート", "復習", "予習", "課題", "グループワーク"]
DIFFICULTY_RANGE = [1, 2, 3, 4, 5]

# デモ用の曜日ごとの使える時間（時間）: 月〜日
DEMO_AVAILABLE_HOURS = [6, 8, 5, 7, 4, 3, 3]

# デモ用の時間割（weekday: 0=月 … 4=金, period: 1〜5限）
DEMO_TIMETABLE = [
    (0, 1, "線形代数"), (0, 2, "物理学基礎"), (0, 3, "プログラミング基礎"),
    (1, 1, "統計学"), (1, 2, "英語コミュニケーション"), (1, 3, "化学実験"),
    (2, 1, "経済学概論"), (2, 2, "体育"), (2, 3, "データ構造"),
    (3, 1, "微分積分"), (3, 2, "歴史学概論"), (3, 3, "情報理論"),
    (4, 1, "哲学入門"), (4, 2, "プログラミング応用"),
]


def generate_task_data(subject, n=60, rng=random):
    """学習用の課題データを自動生成する（所要時間 time_spent は分単位）"""
    now = datetime.now()
    rows = []
    for _ in range(n):
        created_at = now - timedelta(days=rng.randint(5, 20))
        due_date = created_at + timedelta(days=rng.randint(1, 14))
        rows.append({
            "subject": subject,
            "category": rng.choice(CATEGORIES),
            "difficulty": rng.choice(DIFFICULTY_RANGE),
            "due_date": due_date.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "time_spent": round(rng.uniform(30, 180), 1),
        })
    return rows


def insert_training_tasks(conn, rng=random):
    """4教科分の学習用データを入れる（is_deleted=1 で画面には出さない）"""
    for subject in SUBJECTS:
        for row in generate_task_data(subject, rng=rng):
            conn.execute(text("""
                INSERT INTO task (subject, category, difficulty, due_date, created_at, time_spent, is_deleted)
                VALUES (:subject, :category, :difficulty, :due_date, :created_at, :time_spent, 1)
            """), row)


def init_db():
    """表が無ければ作り、空ならデモ用の初期データを入れる"""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                due_date DATE NOT NULL,
                created_at DATETIME NOT NULL,
                predicted_time REAL,
                time_spent REAL,
                assigned_for_today INTEGER DEFAULT 0,
                assigned_date DATE,
                is_completed BOOLEAN DEFAULT 0,
                is_deleted INTEGER DEFAULT 0
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS available_time (
                weekday INTEGER PRIMARY KEY,
                available_hours REAL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS timetable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                weekday INTEGER NOT NULL,
                period INTEGER NOT NULL,
                subject TEXT NOT NULL
            )
        """))

        if conn.execute(text("SELECT COUNT(*) FROM available_time")).scalar() == 0:
            for weekday, hours in enumerate(DEMO_AVAILABLE_HOURS):
                conn.execute(text("""
                    INSERT INTO available_time (weekday, available_hours) VALUES (:weekday, :hours)
                """), {"weekday": weekday, "hours": hours})

        if conn.execute(text("SELECT COUNT(*) FROM timetable")).scalar() == 0:
            for weekday, period, subject in DEMO_TIMETABLE:
                conn.execute(text("""
                    INSERT INTO timetable (weekday, period, subject) VALUES (:weekday, :period, :subject)
                """), {"weekday": weekday, "period": period, "subject": subject})

        if conn.execute(text("SELECT COUNT(*) FROM task")).scalar() == 0:
            insert_training_tasks(conn, rng=random.Random(0))
