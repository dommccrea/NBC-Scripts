import os
import pandas as pd
import re

# ◾ adjust these paths
file_a = r"C:\Users\dmccrea\OneDrive - ALDI-HOFER\A Python Scripts\csvListing250423.csv"
file_b = r"C:\Users\dmccrea\OneDrive - ALDI-HOFER\A Python Scripts\publishedOffers20250423.csv"
output_xlsx = r"C:\Users\dmccrea\OneDrive - ALDI-HOFER\A Python Scripts\mismatch_report_buckets2.xlsx"

file_a_name = os.path.basename(file_a)  # csvListing250423.csv
file_b_name = os.path.basename(file_b)  # publishedOffers20250423.csv

# 1) Load each (single-column) file
df_a = pd.read_csv(file_a, header=0, dtype=str, names=['SellableID_StoreNumber'])
df_b = pd.read_csv(file_b, header=0, dtype=str, names=['SellableID_StoreNumber'])

# 2) Merge with publishedOffers (df_b) as the "left" table, csvListing as "right"
df = df_b.merge(
    df_a,
    on="SellableID_StoreNumber",
    how="outer",
    indicator=True
)

# 3) Friendly source labels
df['Source'] = df['_merge'].map({
    'left_only':  f'Only in {file_b_name}',  # publishedOffers-only
    'right_only': f'Only in {file_a_name}',  # csvListing-only
    'both':       'In both files'
})

# 4) Remove any exact duplicates so each key appears once
df = df.drop_duplicates(subset=['SellableID_StoreNumber'])

# 5) Split SellableID vs StoreNumber
df[['SellableID','StoreNumber']] = (
    df['SellableID_StoreNumber'].str.rsplit('_', n=1, expand=True)
)

# 6) Zero-pad & bucket into G001–G050, G051–G100, etc.
def bucket_label(n):
    start = ((n-1)//50)*50 + 1
    end   = start + 49
    return f"G{start:03d}-G{end:03d}"

df['StoreNumInt'] = df['StoreNumber'].str.extract(r'(\d+)', expand=False).astype(int)
df['StoreBucket'] = df['StoreNumInt'].apply(bucket_label)

# 7) Build ProductURL **only** for bucket "G001-G050" AND merge=left_only
first_bucket = bucket_label(1)  # "G001-G050"
base_url     = "https://www.aldi.com.au/product/"

df['ProductURL'] = ''
mask = (df['StoreBucket'] == first_bucket) & (df['_merge'] == 'left_only')
df.loc[mask, 'ProductURL'] = base_url + df.loc[mask, 'SellableID']

# 8) Build the summary (counts per bucket & source, plus Matched/NotMatched)
counts = df.groupby('StoreBucket')['Source'] \
           .value_counts() \
           .unstack(fill_value=0)

for col in (f'Only in {file_b_name}',
            f'Only in {file_a_name}',
            'In both files'):
    counts[col] = counts.get(col, 0)

counts['Matched']    = counts['In both files']
counts['NotMatched'] = counts[f'Only in {file_b_name}'] + counts[f'Only in {file_a_name}']
counts['Total']      = counts['Matched'] + counts['NotMatched']

summary = counts.reset_index().sort_values('StoreBucket')

# 9) Write one workbook with all buckets
with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
    # Summary sheet
    summary.to_excel(writer, sheet_name='Summary', index=False)

    # Detail sheets by bucket
    for bucket, chunk in df.groupby('StoreBucket'):
        sheet = bucket if len(bucket) <= 31 else bucket[:31]
        chunk[
            ['SellableID_StoreNumber','SellableID','StoreNumber','ProductURL','Source']
        ].to_excel(writer, sheet_name=sheet, index=False)

print(f"Wrote report with URLs only for {first_bucket} → {output_xlsx}")
