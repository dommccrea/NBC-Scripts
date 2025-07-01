# NBC Scripts

This repository contains various SQL scripts used across Merchandising, Listing, and Supply Chain Management (SCM).

## Overview

These scripts were created for data analysis and reporting purposes. They query the business database to retrieve information about product listings, merchandising parameters, store statuses, and more. The scripts are plain SQL text files that can be executed against the relevant database once a connection is established.

### Running the Scripts

1. Connect to the business database using your preferred SQL client (e.g. DBeaver or SQL Server Management Studio).
2. Ensure you have the required permissions to read from the underlying tables. Most scripts expect access to product, store, and contract tables.
3. Open the desired script file from this repository and execute it within your SQL client.
4. For Python-based queries you can run `Website - Python SQL Script Test`,
   which connects to server `5909z0ndbsrvt02` and the `BIRD_IDS_D` database using
   ODBC. This script exports query results to Excel and can be adapted for other
   SQL statements.

Some scripts reference multiple schemas or require the connection to be set to the correct database. Adjust any schema references if needed before running.

## Script Summary

| File | Purpose |
| ---- | ------- |
| Listing - Alcohol Brokerage Check DC and Listing | Checks brokerage articles for active DC listings |
| Listing - CT098 - Contract Item Validation for Displays with DC Listings AU | Validates contract items for display articles with DC listings |
| Listing - Core Articles Status 21 | Lists core articles currently at status 21 |
| Listing - DC Listed, DC Active, Contract not active | Finds items listed and active at DC without an active contract |
| Listing - FT002 Bulletin Greater Than Store Listing | Compares FT002 bulletin quantity against store listings |
| Listing - Manual Listing and Delisting per Month Excluding Produce | Counts manual listings and delistings per month excluding produce |
| Listing - NDO Listing Lead Time Report | Calculates lead time between NDO listing events |
| Listing - NDO Listing error report | Reports any listing errors found for NDO |
| Listing - SCM Autodelisting Check.txt | Checks whether automatic delisting is functioning |
| Listing - Specials IDC Delisting Check | Validates delisting status for specials in IDC |
| Merch - Critical Error - Duplicate PAR no infil or liq st | Detects duplicate PAR records without infiltration or liquidation |
| Merch - Critical Error - Store Parameter Check Overview | Summarizes store parameter configuration issues |
| Merch - Critical Error - Stores Missing Listing | Identifies stores missing required listings |
| Merch - Critical error - ASSORTMENT VALIDITY CHECK | Checks for assortment validity problems |
| Produce - Delisting Report | Report showing produce delistings |
| Produce - Listing Check | Verifies produce listings across stores |
| Q3 Seasonal Product List | Seasonal product list used in Q3 |
| SCM - Alcohol Stores Status 31 | Returns alcohol stores currently at status 31 |
| SCM - Blocked Stores with Articles Listed | Finds blocked stores that still have articles listed |
| SCM - CDPOS No Longer DC Status 10.txt | Shows stores removed from DC status 10 |
| SCM - DiscontinuedProductStoreStatus10.txt | Discontinued products with store status 10 |
| SCM - One store 30 but not all stores 30 | Checks for inconsistent store status 30 across locations |
| WIP - Listing - DC Status 30 with Valid Listing | WIP query for DC status 30 with valid listings |
| WIP - Listing - DC Stock with status 30 or delisted | WIP query for DC stock that is status 30 or delisted |
| WIP - Listing - DC and Store listing mismatch | WIP check for mismatched DC and store listings |
| WIP - Listing - DNU Articles Listed | WIP query for DNU articles that are listed |
| WIP - Listing - FT002 Compliance | WIP query checking FT002 compliance |
| WIP - Listing - FT002 not actioned | WIP list of FT002 records not actioned |
| WIP - Listing - Stores Missing Listing | WIP identification of stores missing listings |
| WIP - MERCH - Retail Price Change | WIP query reviewing pending retail price changes |
| WIP - SCM - FT002 not sent | WIP list of FT002 records not sent |
| Website Dashboard BD SQL Info.txt | Extracts data used on the BD website dashboard |
| Website - Python SQL Script Test | Example Python script using ODBC to query BIRD_IDS_D on server 5909z0ndbsrvt02 and export results to Excel |
| Website - Website Dashboard HTML.py | Generates an interactive offline dashboard as an HTML file |

