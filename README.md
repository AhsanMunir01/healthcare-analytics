# Healthcare Analytics

This project loads a synthetic healthcare CSV into SQLite, cleans admission records, and presents the results in a Streamlit dashboard.

## Run locally

From the project folder, set up the Python environment (verified with Python 3.12):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the pipeline and start the dashboard:

```bash
python pipeline/ingest.py
python pipeline/transform.py
python pipeline/analytics.py
python -m streamlit run dashboard/app.py
```

Open [the local dashboard](http://localhost:8501). Use the sidebar to filter the four metrics, charts, and records by medical condition. The database is included, so you can also launch the dashboard directly after installing the packages.

## Data and metrics

The [Kaggle dataset](https://www.kaggle.com/datasets/prasad22/healthcare-dataset) is synthetic. The CSV included here came from a [public copy on Hugging Face](https://huggingface.co/datasets/Kilos1/healthcare_dataset/blob/main/healthcare_dataset.csv). Ingestion writes the source records to `raw_healthcare`. Transformation removes exact duplicates, saves invalid records to `rejected_healthcare`, and adds analysis fields to `clean_healthcare`.

The included CSV has 55,500 rows. Transformation removes 534 duplicates and produces 54,966 valid admissions. Admissions count records. Average stay uses the difference between discharge and admission dates in days. The billing metric sums nonnegative amounts. The 106 negative amounts remain in the cleaned records with a flag.
