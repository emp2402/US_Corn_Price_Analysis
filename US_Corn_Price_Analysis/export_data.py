import os
from google.cloud import bigquery
import pandas as pd

# CONFIGURATION
KEY_PATH = os.path.join("keys", "service_account.json")
PROJECT_ID = "us-corn-data" 
DATASET_ID = "us_corn_data_transformed"        
OUTPUT_DIR = "final_data_submission"

def export_tables():
    # Setup
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
    client = bigquery.Client()
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Get all tables in dataset
    tables = client.list_tables(f"{PROJECT_ID}.{DATASET_ID}")
    
    print(f"--- Exporting tables from {DATASET_ID} ---")
    
    for table in tables:
        table_id = table.table_id
        full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
        
        print(f"Downloading {table_id}...", end=" ")
        
        # Download to DataFrame
        sql = f"SELECT * FROM `{full_table_id}`"
        df = client.query(sql).to_dataframe()
        
        # Save to CSV
        csv_path = os.path.join(OUTPUT_DIR, f"{table_id}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Done! ({len(df)} rows)")

    print(f"\nAll data exported to folder: {OUTPUT_DIR}/")

if __name__ == "__main__":
    export_tables()