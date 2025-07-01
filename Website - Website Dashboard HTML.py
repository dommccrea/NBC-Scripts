import os
import pandas as pd
from html import escape

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
JQUERY_PATH = os.path.join(ASSETS_DIR, 'jquery.min.js')
DT_JS_PATH = os.path.join(ASSETS_DIR, 'jquery.dataTables.min.js')
DT_CSS_PATH = os.path.join(ASSETS_DIR, 'jquery.dataTables.min.css')

EXPECTED_REGIONS = ['BRE', 'DAN', 'DER', 'JKT', 'MIN', 'PRE', 'RGY', 'STP']

# -------------------------------
# Helper functions reused from the Excel script
# -------------------------------

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
            'SAP BD': first_row.get('SAP BD'),
            'Sellable ID': sid,
            'Website Product Name': first_row['Product Name'],
            'SAP Product Name': first_row.get('SAP Description'),
            'Regions On Website': region_label,
            'Available in Stores (Count)': first_row['Available in Stores (Count)'],
            'Retail by Region (updated weekly)': retail_by_region,
            'Product Description': first_row['Product Description'],
            'Legal Disclaimer': first_row.get('Legal Disclaimer'),
            'Image Status': first_row.get('ImageStatus', 'No Image Online'),
            'Hierarchy': first_row.get('SAP Hierarchy') or first_row.get('Hierarchy'),
            'SAP Commodity Group': first_row.get('SAP Commodity Group'),
            'SAP Sub Commodity Group': first_row.get('SAP Sub Commodity Group'),
            'Brand': first_row['Brand'],
            'Net Content': first_row['Net Content'],
            'Product Link': first_row['Product Link'],
            'Multiple Prices': multiple_prices,
        })

    out = pd.DataFrame(grouped)
    out['Image Status'] = out['Image Status'].fillna('No Image Online')
    return out


def export_to_html(df, output_path):
    with open(JQUERY_PATH, 'r', encoding='utf-8') as f:
        jquery_js = f.read()
    with open(DT_JS_PATH, 'r', encoding='utf-8') as f:
        dt_js = f.read()
    with open(DT_CSS_PATH, 'r', encoding='utf-8') as f:
        dt_css = f.read()

    # Build BD filter options
    bd_values = sorted([bd for bd in df['SAP BD'].dropna().unique()])
    options = '\n'.join(f'<option value="{escape(str(bd))}">{escape(str(bd))}</option>' for bd in bd_values)

    # Convert Product Link to clickable anchor
    if 'Product Link' in df.columns:
        df['Product Link'] = df['Product Link'].apply(lambda u: f'<a href="{u}">View Online</a>' if pd.notnull(u) else '')

    table_html = df.to_html(index=False, escape=False, table_id='dashboard', classes='display nowrap')

    html = """<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>Website Dashboard</title>
<style>
{dt_css}
body {{ font-family: Arial, sans-serif; margin: 20px; }}
#column-toggle label {{ margin-right: 10px; }}
</style>
</head>
<body>
<h1>Website Dashboard</h1>
<label for=\"bd-filter\">Filter by BD:</label>
<select id=\"bd-filter\">
<option value=\"\">All</option>
{options}
</select>
<div id=\"column-toggle\" style=\"margin-top:10px; margin-bottom:10px;\"></div>
{table_html}
<script>
{jquery_js}
</script>
<script>
{dt_js}
</script>
<script>
var table;
$(document).ready(function() {{
    table = $('#dashboard').DataTable({{pageLength:25}});
    $('#bd-filter').on('change', function() {{
        var val = $(this).val();
        table.column(0).search(val ? '^' + val + '$' : '', true, false).draw();
    }});
    var container = $('#column-toggle');
    table.columns().every(function(index) {{
        var column = this;
        var name = $(column.header()).text();
        var checkbox = $('<input type=\"checkbox\" checked>').on('change', function() {{
            column.visible(this.checked);
        }});
        var label = $('<label/>').append(checkbox).append(' ' + name);
        container.append(label);
    }});
}});
</script>
</body>
</html>""".format(
        dt_css=dt_css,
        jquery_js=jquery_js,
        dt_js=dt_js,
        options=options,
        table_html=table_html,
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML dashboard saved to {output_path}")


if __name__ == '__main__':
    # Example usage assuming you already have the final dataframe
    # Replace the following with actual data loading if needed
    sample = pd.DataFrame({
        'SAP BD': ['BD1', 'BD1', 'BD2'],
        'Sellable ID': [111, 112, 120],
        'Website Product Name': ['Item A', 'Item B', 'Item C'],
        'SAP Product Name': ['Prod A', 'Prod B', 'Prod C'],
        'Regions On Website': ['ALL', 'ALL', 'BRE, DAN'],
        'Available in Stores (Count)': [10, 15, 5],
        'Retail by Region (updated weekly)': ['10 - ALL', '12 - ALL', '11 - BRE'],
        'Product Description': ['Desc A', 'Desc B', 'Desc C'],
        'Legal Disclaimer': ['', '', ''],
        'Image Status': ['Image Online', 'No Image Online', 'Image Online'],
        'Hierarchy': ['H1', 'H1', 'H2'],
        'SAP Commodity Group': ['CG1', 'CG1', 'CG2'],
        'SAP Sub Commodity Group': ['SCG1', 'SCG1', 'SCG2'],
        'Brand': ['BrandA', 'BrandB', 'BrandC'],
        'Net Content': ['1L', '2L', '1L'],
        'Product Link': [
            'https://www.aldi.com.au/product/0000000000000111',
            'https://www.aldi.com.au/product/0000000000000112',
            'https://www.aldi.com.au/product/0000000000000120'
        ],
        'Multiple Prices': [False, False, True],
    })
    export_to_html(sample, os.path.join(os.path.dirname(__file__), 'Website_Dashboard_Output.html'))
