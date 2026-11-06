from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw" / "healthcare.csv"
DATABASE = ROOT / "database" / "healthcare.db"


def ingest_data():
    records = pd.read_csv(SOURCE)
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(URL.create("sqlite", database=str(DATABASE)))
    try:
        with engine.begin() as connection:
            # Include the table replacement and inserts in the same SQLite transaction.
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            records.to_sql("raw_healthcare", connection, if_exists="replace", index=False)
    finally:
        engine.dispose()

    print(f"Loaded {len(records):,} records and {len(records.columns)} columns into raw_healthcare.")


if __name__ == "__main__":
    ingest_data()
