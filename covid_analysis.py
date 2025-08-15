# covid_sample_streamlit.py
# -------------------------------------------
# Simple Streamlit app: upload CSV/TSV/XLS/XLSX or use built-in sample,
# take only a percentage sample, show simple charts, and download CSV/TSV/XLSX.
# Beginner-friendly, easy comments.
# Run: streamlit run covid_sample_streamlit.py
# -------------------------------------------

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import StringIO, BytesIO

# -------------------------
# Built-in tiny sample (if user does not upload)
# -------------------------
SAMPLE_CSV = """Date_reported,Country_code,Country,WHO_region,New_cases,Cumulative_cases,New_deaths,Cumulative_deaths
2020-01-04,NE,Niger,AFR,,0,,0
2020-01-04,NO,Norway,EUR,,0,,0
2020-01-04,PW,Palau,WPR,0,0,0,0
2020-01-04,PY,Paraguay,AMR,,0,,0
2020-01-04,PN,Pitcairn,WPR,0,0,0,0
2020-01-04,SH,Saint Helena,AFR,,0,,0
2020-01-04,SM,San Marino,EUR,,0,,0
2020-01-04,RS,Serbia,EUR,,0,,0
2020-01-04,ZA,South Africa,AFR,0,0,0,0
2020-01-04,ES,Spain,EUR,0,0,0,0
2020-01-04,TH,Thailand,SEAR,0,0,0,0
2020-01-04,VU,Vanuatu,WPR,0,0,0,0
2020-01-04,VE,Venezuela (Bolivarian Republic of),AMR,,0,,0
2020-01-04,AI,Anguilla,AMR,,0,,0
2020-01-04,AZ,Azerbaijan,EUR,,0,,0
2020-01-04,BT,Bhutan,SEAR,0,0,0,0
"""

# -------------------------
# Page title
# -------------------------
st.set_page_config(page_title="COVID Sample App", layout="wide")
st.title("COVID Data — Sample Only")
st.write("Upload CSV / TSV / XLS / XLSX or use a small built-in sample. Choose sample % and download CSV / TSV / Excel.")

# -------------------------
# Upload file or use sample text
# -------------------------
st.sidebar.header("Data source")
uploaded = st.sidebar.file_uploader("Upload Data (CSV, TSV, XLS, XLSX)", type=["csv", "tsv", "txt", "xls", "xlsx"])

use_builtin = False
if uploaded is None:
    st.sidebar.write("No file uploaded — using tiny built-in sample (fast).")
    use_builtin = True
else:
    st.sidebar.write(f"Uploaded: {uploaded.name}")

# -------------------------
# Choose sample percentage
# -------------------------
st.sidebar.header("Sampling options")
pct = st.sidebar.slider("Sample percentage (%)", min_value=1, max_value=50, value=5, step=1)
st.sidebar.caption("We will take this % of rows (random sample).")

# -------------------------
# Helper: read uploaded file correctly by type
# -------------------------
def read_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    # read needed columns to save memory
    use_cols = ["Date_reported", "Country", "WHO_region", "New_cases", "Cumulative_cases", "New_deaths", "Cumulative_deaths"]
    if name.endswith((".xls", ".xlsx")):
        # Excel file
        df_full = pd.read_excel(uploaded_file, usecols=use_cols, parse_dates=["Date_reported"])
    elif name.endswith((".tsv", ".txt")):
        # TSV or text with tabs
        df_full = pd.read_csv(uploaded_file, sep="\t", usecols=use_cols, parse_dates=["Date_reported"])
    else:
        # default: CSV (commas)
        df_full = pd.read_csv(uploaded_file, usecols=use_cols, parse_dates=["Date_reported"])
    return df_full

# -------------------------
# Load data (only sample)
# -------------------------
@st.cache_data
def load_small_sample(uploaded_file, fraction, use_builtin_sample):
    if use_builtin_sample:
        # Read from the small inline CSV (already tiny)
        df = pd.read_csv(StringIO(SAMPLE_CSV), parse_dates=["Date_reported"])
        return df
    else:
        # Read uploaded file (only needed columns) then sample
        df_full = read_uploaded_file(uploaded_file)
        # Make fraction between 1% and 50%
        frac = max(0.01, min(0.5, fraction / 100.0))
        df_sample = df_full.sample(frac=frac, random_state=42).reset_index(drop=True)
        return df_sample

# Try to load sample
try:
    df = load_small_sample(uploaded, pct, use_builtin)
except Exception as e:
    st.error("Could not load data. If you uploaded a file, make sure it is a valid CSV/TSV/XLS/XLSX with expected columns.")
    st.stop()

# -------------------------
# Quick info and show sample
# -------------------------
st.subheader("Sample preview (only the sampled rows)")
st.write(f"Rows: {len(df)} — Columns: {len(df.columns)}")
st.dataframe(df.head(10))

# Convert numeric columns (some may be strings or empty)
for col in ["New_cases", "Cumulative_cases", "New_deaths", "Cumulative_deaths"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# -------------------------
# Simple stats (top countries by cumulative cases in sample)
# -------------------------
st.subheader("Top countries in this sample (by cumulative cases)")
if "Cumulative_cases" in df.columns:
    total_cases = df.groupby("Country", dropna=True)["Cumulative_cases"].max().fillna(0).astype(int).reset_index()
    top = total_cases.sort_values("Cumulative_cases", ascending=False).head(10)
    st.table(top)
else:
    st.write("Cumulative_cases column not found in sample.")

# -------------------------
# Plot 1: Bar chart of top countries (sample)
# -------------------------
st.subheader("Bar chart — cumulative cases (sample)")
if "top" in locals() and not top.empty:
    fig1, ax1 = plt.subplots(figsize=(8,5))
    sns.barplot(data=top, x="Cumulative_cases", y="Country", palette="Reds_r", ax=ax1)
    ax1.set_xlabel("Cumulative cases")
    ax1.set_ylabel("Country")
    st.pyplot(fig1)
else:
    st.write("Not enough data to plot top countries.")

# -------------------------
# Plot 2: Trend for chosen country
# -------------------------
st.subheader("Time series for one country (sample)")
countries = sorted(df["Country"].dropna().unique().tolist())
sel_country = st.selectbox("Choose a country (from sample)", countries, index=0 if countries else None)

if sel_country:
    country_df = df[df["Country"] == sel_country].sort_values("Date_reported")
    if country_df.empty:
        st.write("No data for this country in the sample.")
    else:
        fig2, ax2 = plt.subplots(figsize=(10,4))
        if "Cumulative_cases" in country_df.columns:
            sns.lineplot(data=country_df, x="Date_reported", y="Cumulative_cases", marker="o", ax=ax2, label="Cumulative cases")
        if "New_cases" in country_df.columns:
            sns.lineplot(data=country_df, x="Date_reported", y="New_cases", marker="o", ax=ax2, label="New cases")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Cases")
        ax2.legend()
        plt.xticks(rotation=25)
        st.pyplot(fig2)

# -------------------------
# Download sampled data: CSV, TSV, Excel
# -------------------------
st.subheader("Download the sampled data")

# Convert Date to string to avoid Excel datetime issues
to_download = df.copy()
if "Date_reported" in to_download.columns:
    to_download["Date_reported"] = to_download["Date_reported"].dt.strftime("%Y-%m-%d")

# CSV bytes
csv_bytes = to_download.to_csv(index=False).encode("utf-8")
st.download_button("Download as CSV", data=csv_bytes, file_name=f"covid_sample_{pct}percent.csv", mime="text/csv")

# TSV bytes (tab separated)
tsv_bytes = to_download.to_csv(index=False, sep="\t").encode("utf-8")
st.download_button("Download as TSV", data=tsv_bytes, file_name=f"covid_sample_{pct}percent.tsv", mime="text/tab-separated-values")

# Excel bytes
def make_excel_bytes(df_in):
    output = BytesIO()
    df_in.to_excel(output, index=False, engine="openpyxl")
    return output.getvalue()

excel_bytes = make_excel_bytes(to_download)
st.download_button("Download as Excel (.xlsx)", data=excel_bytes, file_name=f"covid_sample_{pct}percent.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# -------------------------
# Small help text
# -------------------------
st.markdown("---")
st.write("""
**How this app works (very simple):**
- Upload CSV / TSV / XLS / XLSX, or use the built-in tiny sample.
- The app reads only needed columns then takes a random sample of the percent you choose.
- You can download the sampled rows as CSV, TSV, or Excel (.xlsx).
- The app never analyzes the full dataset — only the sampled rows — so it is fast and safe for small computers.
""")
