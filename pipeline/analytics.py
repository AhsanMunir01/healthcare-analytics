from contextlib import closing
import sqlite3

import pandas as pd

from ingest import DATABASE


def condition_filter(conditions):
    if conditions is None:
        return "", ()
    if not conditions:
        return "WHERE 0", ()
    placeholders = ", ".join("?" for _ in conditions)
    return f"WHERE medical_condition IN ({placeholders})", tuple(conditions)


def calculate_metrics(connection, conditions=None):
    where, params = condition_filter(conditions)
    summary = pd.read_sql_query(
        f"""
        SELECT COUNT(*) AS total_admissions,
               AVG(age) AS average_age,
               AVG(length_of_stay) AS average_length_of_stay,
               COALESCE(SUM(CASE WHEN billing_amount >= 0 THEN billing_amount END), 0)
                   AS total_positive_billing
        FROM clean_healthcare
        {where}
        """,
        connection,
        params=params,
    ).iloc[0].to_dict()
    summary["total_admissions"] = int(summary["total_admissions"])

    breakdowns = {}
    for dimension in ("medical_condition", "admission_month", "admission_type", "insurance_provider"):
        ordering = dimension if dimension == "admission_month" else f"admissions DESC, {dimension}"
        breakdowns[dimension] = pd.read_sql_query(
            f"""
            SELECT {dimension}, COUNT(*) AS admissions
            FROM clean_healthcare
            {where}
            GROUP BY {dimension}
            ORDER BY {ordering}
            """,
            connection,
            params=params,
        )
    return summary, breakdowns


def main():
    with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as connection:
        with connection:
            connection.execute("BEGIN")
            summary, breakdowns = calculate_metrics(connection)

    print("Healthcare analytics")
    print(f"Total admissions: {summary['total_admissions']:,}")
    if summary["total_admissions"]:
        print(f"Average patient age: {summary['average_age']:.2f} years")
        print(f"Average length of stay: {summary['average_length_of_stay']:.2f} days")
    else:
        print("Average patient age: N/A")
        print("Average length of stay: N/A")
    print(f"Total positive billing: {summary['total_positive_billing']:,.2f}")

    for dimension, counts in breakdowns.items():
        print(f"\nAdmissions by {dimension.replace('_', ' ')}")
        print(counts.to_string(index=False))


if __name__ == "__main__":
    main()
