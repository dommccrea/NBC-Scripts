import os, glob, re, datetime, math
import pandas as pd

# ───────── Adjust this to your folder ─────────
BASE_DIR = r"C:\Users\dmccrea\OneDrive - ALDI-HOFER\A Python Scripts"
OUT_XLSX = os.path.join(BASE_DIR, "FullComparison_Report.xlsx")

# 1) Find latest ListingYYYYMMDD.txt
listing_pat = re.compile(r"Listing(\d{8})\.txt$")
latest_txt, txt_date = None, None
for f in glob.glob(os.path.join(BASE_DIR, "Listing*.txt")):
    m = listing_pat.search(os.path.basename(f))
    if m:
        d = datetime.datetime.strptime(m.group(1), "%Y%m%d")
        if txt_date is None or d > txt_date:
            txt_date, latest_txt = d, f
if not latest_txt:
    raise FileNotFoundError("No ListingYYYYMMDD.txt found")

# 2) Clean-export parse of that listing file
rows = []
with open(latest_txt, encoding="utf-8") as rf:
    for line in rf:
        if not line.startswith("|"): continue
        if set(line.strip()) <= {"|","-"}: continue
        cells = [c for c in line.strip().strip("|").split("|") if c]
        rows.append(cells[0])
df_a = pd.DataFrame({"SellableID_StoreNumber": rows})

# 3) Find latest publishedOffersYYYYMMDD.csv
pub_pat = re.compile(r"publishedOffers(\d{8})\.csv$")
latest_csv, csv_date = None, None
for f in glob.glob(os.path.join(BASE_DIR, "publishedOffers*.csv")):
    m = pub_pat.search(os.path.basename(f))
    if m:
        d = datetime.datetime.strptime(m.group(1), "%Y%m%d")
        if csv_date is None or d > csv_date:
            csv_date, latest_csv = d, f
if not latest_csv:
    raise FileNotFoundError("No publishedOffersYYYYMMDD.csv found")

# 4) Load publishedOffers and merge
df_b = pd.read_csv(latest_csv, header=0, dtype=str,
                   names=["SellableID_StoreNumber"])
df = df_b.merge(df_a, on="SellableID_StoreNumber", how="outer",
                indicator="_merge")

# 5) Split SellableID vs StoreNumber safely
parts = df["SellableID_StoreNumber"].str.split("_", n=1, expand=True)
df["SellableID"], df["StoreNumber"] = parts[0], parts[1]

# Drop any rows where StoreNumber is missing
df = df.dropna(subset=["StoreNumber"])

# 6) Safe numeric extraction (once only)
df["StoreNumInt"] = (
    pd.to_numeric(
        df["StoreNumber"].str.lstrip("G"),  # strip the 'G'
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
)

# 7) Bucket into G001-G050, etc.
def bucket_label(n):
    start = ((n-1)//50)*50 + 1
    return f"G{start:03d}-G{start+49:03d}"

df["StoreBucket"] = df["StoreNumInt"].apply(bucket_label)


# 8) Build bucket summary
counts = df.groupby("StoreBucket")["Source"] \
           .value_counts().unstack(fill_value=0)
for col in (f"Only in {file_pub}", f"Only in {file_lst}", "In both files"):
    counts[col] = counts.get(col, 0)
counts["Matched"]    = counts["In both files"]
counts["NotMatched"] = counts[f"Only in {file_pub}"] \
                      + counts[f"Only in {file_lst}"]
counts["Total"]      = counts["Matched"] + counts["NotMatched"]
bucket_summary = counts.reset_index().sort_values("StoreBucket")

# 9) Write Excel with sheet‐chunking per bucket
MAX_ROWS = 1048576
with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as writer:
    # Metrics & summaries
    pd.DataFrame([{"AverageMissingPerStore": avg_miss}]) \
      .to_excel(writer, sheet_name="Metrics", index=False)
    bucket_summary.to_excel(writer, sheet_name="Summary", index=False)
    store_summary.to_excel(writer, sheet_name="StoreSummary", index=False)

    # Raw detail, chunked if any bucket >1,048,576 rows
    for bucket, grp in df.groupby("StoreBucket"):
        parts = math.ceil(len(grp) / MAX_ROWS)
        for part in range(parts):
            sub = grp.iloc[part*MAX_ROWS:(part+1)*MAX_ROWS]
            name = f"{bucket}" + (f"_part{part+1}" if parts>1 else "")
            name = name[:31]  # Excel sheet limit
            sub[["SellableID_StoreNumber","SellableID",
                 "StoreNumber","Source"]] \
              .to_excel(writer, sheet_name=name, index=False)

print("Done! Report saved to:", OUT_XLSX)
