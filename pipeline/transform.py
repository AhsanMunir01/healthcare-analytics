import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from ingest import DATABASE


def transform_data():
    engine = create_engine(URL.create("sqlite", database=str(DATABASE)))
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            raw = pd.read_sql_table("raw_healthcare", connection)
            records = raw.drop_duplicates().copy()
            records.columns = records.columns.str.strip().str.lower().str.replace(" ", "_")

            admission = pd.to_datetime(records["date_of_admission"], format="%Y-%m-%d", errors="coerce")
            discharge = pd.to_datetime(records["discharge_date"], format="%Y-%m-%d", errors="coerce")
            age = pd.to_numeric(records["age"], errors="coerce")
            billing = pd.to_numeric(records["billing_amount"], errors="coerce")

            valid = age.between(0, 120) & discharge.ge(admission) & np.isfinite(billing)
            rejected = records.loc[~valid]
            clean = records.loc[valid].copy()
            clean["date_of_admission"] = admission.loc[valid]
            clean["discharge_date"] = discharge.loc[valid]
            clean["age"] = age.loc[valid]
            clean["billing_amount"] = billing.loc[valid]
            clean["length_of_stay"] = (clean["discharge_date"] - clean["date_of_admission"]).dt.days
            clean["age_group"] = pd.cut(
                clean["age"],
                bins=[-1, 18, 35, 50, 65, 120],
                labels=["0-18", "19-35", "36-50", "51-65", "66+"],
            )
            clean["admission_month"] = clean["date_of_admission"].dt.strftime("%Y-%m")
            clean["negative_billing"] = clean["billing_amount"] < 0

            clean.to_sql("clean_healthcare", connection, if_exists="replace", index=False)
            rejected.to_sql("rejected_healthcare", connection, if_exists="replace", index=False)
    finally:
        engine.dispose()

    print(f"Duplicates removed: {len(raw) - len(records):,}")
    print(f"Clean records: {len(clean):,}")
    print(f"Rejected records: {len(rejected):,}")
    print(f"Negative billing records flagged: {clean['negative_billing'].sum():,}")


if __name__ == "__main__":
    transform_data()
