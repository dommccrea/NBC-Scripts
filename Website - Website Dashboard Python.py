import os
import pandas as pd
import pyodbc
from html import unescape
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import Rule
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

# Paths to CSV files
BASE_DIR = r'C:\Users\dmccrea\Documents\Python Scripts\New folder'
PRICING_CSV = os.path.join(BASE_DIR, 'AU_product_offer_price_en_AU.csv')
PRODUCTS_CSV = os.path.join(BASE_DIR, 'AU_products_en_AU.csv')
IMAGES_CSV = os.path.join(BASE_DIR, 'AU_product_image_en_AU.csv')

# SQL Server connection parameters
SERVER = '5909z0ndbsrvt02'
DATABASE = 'BIRD_IDS_DDS'
CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER={SERVER};'
    f'DATABASE={DATABASE};'
    'Trusted_Connection=yes;'
    'Encrypt=yes;'
    'TrustServerCertificate=yes;'
)

EXPECTED_REGIONS = ['BRE', 'DAN', 'DER', 'JKT', 'MIN', 'PRE', 'RGY', 'STP']


def load_region_lookup(conn):
    query = """
    SELECT [AHEAD_Plant_ID] AS StoreID, [Legacy_Region_Name_Short] AS Region
    FROM dds.INT_OBJ_MD_Store
    """
    df = pd.read_sql(query, conn)
    return dict(zip(df['StoreID'].astype(str), df['Region']))


def load_pricing_data():
    df = pd.read_csv(
        PRICING_CSV,
        usecols=['concrete_sku', 'merchant_reference', 'value_gross', 'is_active'],
        dtype={'merchant_reference': 'string', 'is_active': 'string'}
    )
    df['concrete_sku'] = pd.to_numeric(df['concrete_sku'], errors='coerce').astype('Int64')
    df['value_gross'] = pd.to_numeric(df['value_gross'], errors='coerce').astype('Int64')
    df = df[df['is_active'] == '1'].copy()
    df = df.rename(columns={
        'concrete_sku': 'SellableID',
        'merchant_reference': 'StoreID',
        'value_gross': 'RetailCents'
    })
    return df[['SellableID', 'StoreID', 'RetailCents']]


def compute_product_pricing(pricing_df, region_map):
    df = pricing_df.copy()
    df['Retail'] = df['RetailCents'] / 100.0
    df['Region'] = df['StoreID'].astype(str).map(region_map)
    df = df.dropna(subset=['Region'])
    df = df.drop_duplicates(subset=['SellableID', 'Retail', 'Region'])

    grouped = (
        df.sort_values('Region')
          .groupby(['SellableID', 'Retail'])['Region']
          .apply(lambda r: ', '.join(r))
          .reset_index(name='RegionList')
    )

    def flag_all(regions):
        regions_sorted = sorted(regions.split(', '))
        return 'ALL' if regions_sorted == EXPECTED_REGIONS else regions

    grouped['Regions'] = grouped['RegionList'].apply(flag_all)
    return grouped[['SellableID', 'Retail', 'Regions']]


def compute_product_location(pricing_df, region_map):
    df = pricing_df[['SellableID', 'StoreID']].drop_duplicates()
    df['Region'] = df['StoreID'].astype(str).map(region_map)
    df = df.dropna(subset=['Region'])

    grouped = df.groupby('SellableID').agg(
        Regions=('Region', lambda x: ', '.join(sorted(set(x)))),
        StoreCount=('StoreID', 'nunique')
    ).reset_index()

    def flag_all(regions):
        return 'ALL' if sorted(regions.split(', ')) == EXPECTED_REGIONS else regions

    grouped['Regions'] = grouped['Regions'].apply(flag_all)
    return grouped


def load_product_catalog():
    df = pd.read_csv(
        PRODUCTS_CSV,
        usecols=[
            'concrete_sku', 'is_active', 'name', 'description', 'brand_name',
            'price_unit', 'comparison_price_unit', 'net_content', 'content_unit',
            'product_class', 'legal_disclaimer'
        ],
        dtype=str
    )

    df['concrete_sku'] = df['concrete_sku'].str.lstrip('0')
    df['Sellable ID'] = pd.to_numeric(df['concrete_sku'], errors='coerce').astype('Int64')
    df['Net Content'] = df['net_content'].fillna('').astype(str) + ' ' + df['content_unit'].fillna('').astype(str)

    df = df.rename(columns={
        'is_active': 'Online Active',
        'name': 'Product Name',
        'description': 'Product Description',
        'brand_name': 'Brand',
        'price_unit': 'Unit',
        'comparison_price_unit': 'Comparison Unit Price',
        'product_class': 'Hierarchy',
        'legal_disclaimer': 'Legal Disclaimer'
    })

    df = df[[
        'Sellable ID', 'Online Active', 'Product Name', 'Product Description',
        'Brand', 'Unit', 'Comparison Unit Price', 'Net Content', 'Hierarchy',
        'Legal Disclaimer'
    ]]

    # Clean HTML from descriptions and decode entities
    df['Product Description'] = (
        df['Product Description']
        .astype(str)
        .str.replace(r'<[^>]+>', '', regex=True)
        .apply(unescape)
    )
    return df


def load_general_product_info(conn):
    query = """
        SELECT p.[Article] as SellableID,
               p.[Medium_Description] as Description,
               pg.short_description as BD,
               ph.Long_Description as Hierarchy,
               cg.Medium_Description as CG,
               scg.Medium_Description as SCG
        FROM [BIRD_IDS_DDS].[dds].[INT_OBJ_MD_Product] as P
        left join [BIRD_IDS_DDS].[dds].[INT_OBJ_MD_PurchasingGroup] as PG
               on pg.purchasing_group = p.purch_grp_buyer
        left join [BIRD_IDS_DDS].[dds].[INT_OBJ_MD_ProductHierarchy] as PH
               on ph.Product_Hierarchy = p.Product_Hierarchy
        left join [BIRD_IDS_DDS].[dds].[INT_OBJ_MD_SubCommodityGroup] as SCG
               on scg.Sub_Commodity_Group = p.Sub_Commodity_Group
        left join [BIRD_IDS_DDS].[dds].[INT_OBJ_MD_CommodityGroup] as CG
               on cg.Commodity_Group = p.Commodity_Group
    """
    df = pd.read_sql(query, conn)
    df['SellableID'] = pd.to_numeric(df['SellableID'], errors='coerce').astype('Int64')
    return df


def load_product_images():
    """Return dataframe of sellable IDs that have images online."""
    try:
        df = pd.read_csv(IMAGES_CSV, usecols=[0], dtype=str)
    except FileNotFoundError:
        return pd.DataFrame(columns=['SellableID'])

    df = df.rename(columns={df.columns[0]: 'concrete_sku'})
    df['concrete_sku'] = df['concrete_sku'].str.lstrip('0')
    df['SellableID'] = pd.to_numeric(df['concrete_sku'], errors='coerce').astype('Int64')
    return df[['SellableID']].dropna()


def build_dashboard(df_catalog, df_location, df_gp, df_price, df_images):
    df = df_catalog.merge(
        df_location,
        left_on='Sellable ID',
        right_on='SellableID',
        how='left'
    ).drop(columns=['SellableID'])

    df = df.rename(columns={
        'Regions': 'Available Online by Region',
        'StoreCount': 'Available in Stores (Count)'
    })
    df['Available Online by Region'] = df['Available Online by Region'].fillna('Not Online')
    df['Available in Stores (Count)'] = df['Available in Stores (Count)'].fillna(0).astype(int)

    df['Product Link'] = df['Sellable ID'].apply(
        lambda x: f"https://www.aldi.com.au/product/{int(x):018d}" if pd.notnull(x) else None
    )

    df = df.merge(
        df_gp,
        left_on='Sellable ID',
        right_on='SellableID',
        how='left'
    ).drop(columns=['SellableID'])

    df = df.rename(columns={
        'Description': 'SAP Description',
        'BD': 'SAP BD',
        'Hierarchy_y': 'SAP Hierarchy',
        'CG': 'SAP Commodity Group',
        'SCG': 'SAP Sub Commodity Group'
    })

    # If both Hierarchy columns exist after merge, prefer SAP Hierarchy but keep first
    if 'Hierarchy_x' in df.columns:
        df = df.drop(columns=['Hierarchy_x'])

    df = df.merge(
        df_price,
        left_on='Sellable ID',
        right_on='SellableID',
        how='left'
    ).drop(columns=['SellableID'])

    df = df.merge(
        df_images.assign(ImageStatus='Image Online'),
        left_on='Sellable ID',
        right_on='SellableID',
        how='left'
    ).drop(columns=['SellableID'])
    df = df.rename(columns={
        'Retail': 'Product Pricing.Retail',
        'Regions': 'Product Pricing.Regions'
    })

    grouped = []
    for sid, grp in df.groupby('Sellable ID'):
        first_row = grp.iloc[0]
        regions_list = ', '.join(sorted(set(grp['Product Pricing.Regions'].dropna())))
        if regions_list:
            region_label = 'ALL' if sorted(regions_list.split(', ')) == EXPECTED_REGIONS else regions_list
        else:
            region_label = ''
        price_pairs = grp[['Product Pricing.Regions', 'Product Pricing.Retail']].dropna()
        price_pairs = price_pairs.drop_duplicates().sort_values([
            'Product Pricing.Regions', 'Product Pricing.Retail'
        ])
        retail_by_region = ', '.join(
            f"{r}: {p}" for r, p in zip(
                price_pairs['Product Pricing.Regions'],
                price_pairs['Product Pricing.Retail']
            )
        )
        multiple_prices = price_pairs['Product Pricing.Retail'].nunique() > 1
        grouped.append({
            'Sellable ID': sid,
            'Product Name': first_row['Product Name'],
            'Product Description': first_row['Product Description'],
            'Brand': first_row['Brand'],
            'SAP Description': first_row.get('SAP Description'),
            'Net Content': first_row['Net Content'],
            'SAP BD': first_row.get('SAP BD'),
            'Hierarchy': first_row.get('SAP Hierarchy') or first_row.get('Hierarchy'),
            'SAP Commodity Group': first_row.get('SAP Commodity Group'),
            'SAP Sub Commodity Group': first_row.get('SAP Sub Commodity Group'),
            'Legal Disclaimer': first_row.get('Legal Disclaimer'),
            'Image Status': first_row.get('ImageStatus', 'No Image Online'),
            'Product Link': first_row['Product Link'],
            'Available in Stores (Count)': first_row['Available in Stores (Count)'],
            'Regions On Website': region_label,
            'Retail by Region': retail_by_region,
            'Multiple Prices': multiple_prices
        })

    out = pd.DataFrame(grouped)
    out = out.rename(columns={
        'Product Name': 'Website Product Name',
        'SAP Description': 'SAP Product Name',
        'Retail by Region': 'Retail by Region (updated weekly)'
    })
    out = out[[
        'SAP BD', 'Sellable ID', 'Website Product Name', 'SAP Product Name',
        'Regions On Website', 'Available in Stores (Count)',
        'Retail by Region (updated weekly)', 'Product Description',
        'Legal Disclaimer', 'Image Status', 'Hierarchy',
        'SAP Commodity Group', 'SAP Sub Commodity Group',
        'Brand', 'Net Content', 'Product Link', 'Multiple Prices'
    ]]
    out['Image Status'] = out['Image Status'].fillna('No Image Online')
    return out


def main():
    output_path = os.path.join(BASE_DIR, 'Website_Dashboard_Output.xlsx')
    os.makedirs(BASE_DIR, exist_ok=True)
    try:
        conn = pyodbc.connect(CONN_STR)
        region_map = load_region_lookup(conn)
        pricing_base = load_pricing_data()
        pricing_data = compute_product_pricing(pricing_base, region_map)
        location_data = compute_product_location(pricing_base, region_map)
        catalog = load_product_catalog()
        gp_info = load_general_product_info(conn)
        images_df = load_product_images()
        final_df = build_dashboard(catalog, location_data, gp_info, pricing_data, images_df)

        # Determine most common store count per region combination
        mode_map = (final_df.groupby('Regions On Website')['Available in Stores (Count)']
                    .agg(lambda x: x.mode().iat[0] if not x.mode().empty else None))
        final_df['Deviation'] = final_df.apply(
            lambda r: r['Available in Stores (Count)'] != mode_map.get(r['Regions On Website']),
            axis=1
        )

         # Append helper column for formatting
        column_order = [
            'SAP BD', 'Sellable ID', 'Website Product Name', 'SAP Product Name',
            'Regions On Website', 'Available in Stores (Count)',
            'Retail by Region (updated weekly)', 'Product Description',
            'Legal Disclaimer', 'Image Status', 'Hierarchy',
            'SAP Commodity Group', 'SAP Sub Commodity Group',
            'Brand', 'Net Content', 'Product Link',
            'Multiple Prices', 'Deviation'
        ]
        final_df = final_df[column_order]

        final_df.to_excel(output_path, index=False)

        wb = load_workbook(output_path)
        ws = wb.active

        # Auto filter
        ws.auto_filter.ref = ws.dimensions

        # Column widths and wrap text
        width_map = {
            'A': 16,  # SAP BD
            'B': 14,
            'C': 35,  # Website Product Name
            'D': 35,
            'E': 19,
            'F': 20,
            'g': 27,
            'H': 86,  # Product Description
            'I': 71,  # Legal Disclaimer
            'J': 15,
            'K': 15,
            'L': 15,
            'M': 15,
            'N': 15,
            'O': 15,
            'P': 15,
        }
        for col, width in width_map.items():
            ws.column_dimensions[col].width = width
        for cell in ws['H']:
            cell.alignment = Alignment(wrap_text=True)

        # Grey out rows with no stores
        grey_fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
        rule = Rule(type='expression', dxf=DifferentialStyle(fill=grey_fill))
        avail_col = get_column_letter([c.value for c in ws[1]].index('Available in Stores (Count)') + 1)
        rule.formula = [f"${avail_col}2=0"]
        ws.conditional_formatting.add(f"A2:{get_column_letter(ws.max_column)}{ws.max_row}", rule)

        # Highlight counts deviating from mode
        yellow_fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
        dev_col = get_column_letter([c.value for c in ws[1]].index('Deviation') + 1)
        rule = Rule(type='expression', dxf=DifferentialStyle(fill=yellow_fill))
        rule.formula = [f"${dev_col}2"]
        count_col = get_column_letter([c.value for c in ws[1]].index('Available in Stores (Count)') + 1)
        ws.conditional_formatting.add(f"{count_col}2:{count_col}{ws.max_row}", rule)

        # Highlight multiple prices
        multi_col = get_column_letter([c.value for c in ws[1]].index('Multiple Prices') + 1)
        rule = Rule(type='expression', dxf=DifferentialStyle(fill=yellow_fill))
        rule.formula = [f"${multi_col}2"]
        price_col = get_column_letter([c.value for c in ws[1]].index('Retail by Region (updated weekly)') + 1)
        ws.conditional_formatting.add(f"{price_col}2:{price_col}{ws.max_row}", rule)

        # Red warnings
        red_fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
        img_col = get_column_letter([c.value for c in ws[1]].index('Image Status') + 1)
        brand_col = get_column_letter([c.value for c in ws[1]].index('Brand') + 1)
        net_col = get_column_letter([c.value for c in ws[1]].index('Net Content') + 1)
        rule = Rule(type='expression', dxf=DifferentialStyle(fill=red_fill))
        rule.formula = [f"${img_col}2=\"No Image Online\""]
        ws.conditional_formatting.add(f"{img_col}2:{img_col}{ws.max_row}", rule)
        rule = Rule(type='expression', dxf=DifferentialStyle(fill=red_fill))
        rule.formula = [f"LEN(${brand_col}2)=0"]
        ws.conditional_formatting.add(f"{brand_col}2:{brand_col}{ws.max_row}", rule)
        rule = Rule(type='expression', dxf=DifferentialStyle(fill=red_fill))
        rule.formula = [f"LEN(${net_col}2)=0"]
        ws.conditional_formatting.add(f"{net_col}2:{net_col}{ws.max_row}", rule)

        # Hyperlinks
        link_col = get_column_letter([c.value for c in ws[1]].index('Product Link') + 1)
        col_num = [c.value for c in ws[1]].index('Product Link') + 1
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row,
                                min_col=col_num, max_col=col_num):
            for cell in row:
                if cell.value:
                    cell.hyperlink = cell.value
                    cell.value = 'View Online'
                    cell.font = Font(color='0000FF', underline='single')

        # Hide helper columns
        ws.column_dimensions[dev_col].hidden = True
        ws.column_dimensions[multi_col].hidden = True

        # Create pivot summary sheet
        pivot_df = final_df[final_df['Available in Stores (Count)'] > 0].groupby('SAP BD').agg(
            Product_Count=('Sellable ID', 'nunique'),
            No_Image_Count=('Image Status', lambda x: (x == 'No Image Online').sum())
        ).reset_index()

        piv_ws = wb.create_sheet('BD Pivot')
        for r in dataframe_to_rows(pivot_df, index=False, header=True):
            piv_ws.append(r)
        piv_ws.auto_filter.ref = piv_ws.dimensions

        wb.save(output_path)
        print(f"Export successful! File saved to: {output_path}")
        os.startfile(output_path)
    except Exception as e:
        print('Error:', e)
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    main()
