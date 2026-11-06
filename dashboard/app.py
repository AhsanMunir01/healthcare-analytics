from contextlib import closing
from pathlib import Path
import sqlite3
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from analytics import calculate_metrics, condition_filter
from ingest import DATABASE


st.set_page_config(page_title="Healthcare Analytics", layout="wide")
st.title("Healthcare Analytics")
st.caption("Explore admissions, length of stay, and billing in a synthetic healthcare dataset.")

try:
    with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.execute("BEGIN")
        conditions = [
            row[0] for row in connection.execute(
                "SELECT DISTINCT medical_condition FROM clean_healthcare "
                "WHERE medical_condition IS NOT NULL ORDER BY medical_condition"
            )
        ]
        st.sidebar.header("Filters")
        selected = st.sidebar.multiselect("Medical condition", conditions, default=conditions)
        # The unfiltered view also includes records with a missing condition.
        scope = None if conditions and selected == conditions else selected
        summary, breakdowns = calculate_metrics(connection, scope)
        where, params = condition_filter(scope)
        records = pd.read_sql_query(f"SELECT * FROM clean_healthcare {where}", connection, params=params)
except (sqlite3.Error, pd.errors.DatabaseError):
    st.error("Could not read the cleaned admissions. Run ingestion and transformation, then reload the dashboard.")
    st.stop()

count = summary["total_admissions"]
admissions, age, stay, billing = st.columns(4)
admissions.metric("Total admissions", f"{count:,}")
age.metric("Average age", f"{summary['average_age']:.2f} years" if count else "N/A")
stay.metric("Average length of stay", f"{summary['average_length_of_stay']:.2f} days" if count else "N/A")
billing.metric("Total nonnegative billing", f"{summary['total_positive_billing']:,.2f}")

if not count:
    st.info("No admissions match this selection. Select a medical condition to explore its records.")
    st.stop()

monthly = breakdowns["admission_month"].copy()
monthly["admission_month"] = pd.to_datetime(monthly["admission_month"], format="%Y-%m")
st.plotly_chart(px.line(
    monthly, x="admission_month", y="admissions", markers=True,
    title="Monthly admissions",
    labels={"admission_month": "Admission month", "admissions": "Admissions"},
), width="stretch")

condition_chart, type_chart = st.columns(2)
condition_chart.plotly_chart(px.bar(
    breakdowns["medical_condition"], x="medical_condition", y="admissions",
    title="Admissions by medical condition",
    labels={"medical_condition": "Medical condition", "admissions": "Admissions"},
), width="stretch")
type_chart.plotly_chart(px.pie(
    breakdowns["admission_type"], names="admission_type", values="admissions",
    title="Admissions by type",
), width="stretch")

st.plotly_chart(px.bar(
    breakdowns["insurance_provider"], x="insurance_provider", y="admissions",
    title="Admissions by insurance provider",
    labels={"insurance_provider": "Insurance provider", "admissions": "Admissions"},
), width="stretch")

st.subheader("Admission records")
st.dataframe(records, hide_index=True, width="stretch")
