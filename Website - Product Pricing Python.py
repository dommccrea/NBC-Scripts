import os
import pyodbc
import pandas as pd

# CSV file path (downloaded manually to local folder)
csv_path = r'C:\Users\dmccrea\Documents\Python Scripts\New folder\AU_product_offer_price_en_AU.csv'

# SQL Server connection parameters
server = '5909z0ndbsrvt02'
database = 'BIRD_IDS_DDS'

conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER={server};'
    f'DATABASE={database};'
    'Trusted_Connection=yes;'
    'Encrypt=yes;'
    'TrustServerCertificate=yes;'
)

# Output file path
output_dir = r'C:\Users\dmccrea\Documents\Python Scripts\New folder'
output_file = 'Website_Product_Pricing_Output.xlsx'
output_path = os.path.join(output_dir, output_file)

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

try:
    # --------------------------------------------------------------
    # 1. Load CSV and select required columns in manageable chunks
    CHUNK_SIZE = 100000  # adjust based on available memory
    chunks = []
    for chunk in pd.read_csv(
            csv_path,
            usecols=['concrete_sku', 'merchant_reference', 'value_gross', 'is_active'],
            dtype={'merchant_reference': 'string', 'is_active': 'string'},
            chunksize=CHUNK_SIZE
    ):
        chunk['concrete_sku'] = pd.to_numeric(chunk['concrete_sku'], errors='coerce').astype('Int64')
        chunk['value_gross'] = pd.to_numeric(chunk['value_gross'], errors='coerce').astype('Int64')
        chunk = chunk[chunk['is_active'] == '1'][['concrete_sku', 'merchant_reference', 'value_gross']]
        chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)

    # --------------------------------------------------------------
    # 2. Rename columns (records already filtered as active)
    df = df.rename(columns={
        'concrete_sku': 'Sellable ID',
        'merchant_reference': 'Store ID',
        'value_gross': 'Retail (cents)'
    })

    # Convert cents to dollars
    df['Retail'] = df['Retail (cents)'] / 100.0

    # --------------------------------------------------------------
    # 3. Load region lookup from SQL once
    conn = pyodbc.connect(conn_str)
    region_query = """
    SELECT
        [AHEAD_Plant_ID] AS StoreID,
        [Legacy_Region_Name_Short] AS Region
    FROM dds.INT_OBJ_MD_Store
    """
    region_df = pd.read_sql(region_query, conn)
    region_map = dict(zip(region_df['StoreID'].astype(str), region_df['Region']))

    # --------------------------------------------------------------
    # 4. Add Region using fast dictionary lookup
    df['Region'] = df['Store ID'].astype(str).map(region_map)
    df = df.dropna(subset=['Region'])

    # --------------------------------------------------------------
    # 5. Deduplicate by Sellable ID, Retail, Region
    df = df.drop_duplicates(subset=['Sellable ID', 'Retail', 'Region'])

    # --------------------------------------------------------------
    # 6. Group and flag "ALL" when region list matches expected
    expected_regions = ['BRE', 'DAN', 'DER', 'JKT', 'MIN', 'PRE', 'RGY', 'STP']

    grouped = (
        df
        .sort_values('Region')
        .groupby(['Sellable ID', 'Retail'])['Region']
        .apply(lambda regions: ', '.join(regions))
        .reset_index(name='Regions')
    )

    def flag_all(regions_str):
        regions_sorted = sorted(regions_str.split(', '))
        return 'ALL' if regions_sorted == expected_regions else regions_str

    grouped['Regions'] = grouped['Regions'].apply(flag_all)

    # --------------------------------------------------------------
    # 7. Combine Retail and Region pairs per Sellable ID
    grouped['Retail_Regions'] = grouped.apply(
        lambda row: f"{row['Retail']:.2f} - {row['Regions']}", axis=1
    )
    final_df = (
        grouped
        .groupby('Sellable ID')['Retail_Regions']
        .apply('; '.join)
        .reset_index(name='Retail - Regions')
    )

    # --------------------------------------------------------------
    # Export results to Excel
    final_df.to_excel(output_path, index=False)
    print(f"Export successful! File saved to: {output_path}")

    # Automatically open the file (Windows)
    os.startfile(output_path)

except Exception as e:
    print("Error:", e)

finally:
    if 'conn' in locals():
        conn.close()
