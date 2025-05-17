import sqlite3

DB_PATH = "data/review.db"
TABLE = "review_queue"

def clear_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"DELETE FROM {TABLE};")
    conn.commit()
    conn.close()
    print(f"✅ All records cleared from {TABLE} in {DB_PATH}.")

if __name__ == "__main__":
    clear_table()
