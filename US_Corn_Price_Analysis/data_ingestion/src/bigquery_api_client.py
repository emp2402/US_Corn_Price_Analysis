import logging
import os
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BigQueryClient:
    def __init__(self, project_id="us-corn-data", dataset_id="us_corn_data"):
        """
        Initialize the BigQuery Client.
        
        Args:
            project_id (str): GCP Project ID. If None, infers from the environment.
            dataset_id (str): The default dataset to hold the tables.
        """
        # Define the path where the key IS EXPECTED to be for the professor
        local_key_path = os.path.join(os.getcwd(), 'keys', 'service_account.json')

        if os.path.exists(local_key_path):
            # This tells Google's library to use this specific file
            logger.info(f"Loading credentials from: {local_key_path}")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_key_path
        else:
            logger.warning("No local key found in 'keys/service_account.json'. Assuming environment variables are set.")

        # Client automatically uses Application Default Credentials (ADC)
        # Initialize Client
        try:
            self.client = bigquery.Client(project=project_id)
            self.dataset_id = dataset_id
            self._create_dataset_if_not_exists()
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery Client. Authentication Error? {e}")
            raise e
        
        # Ensure the dataset exists upon initialization
        self._create_dataset_if_not_exists()

    def _create_dataset_if_not_exists(self):
        """
        Checks if the dataset exists; creates it if it doesn't.
        """
        dataset_ref = f"{self.client.project}.{self.dataset_id}"
        
        try:
            self.client.get_dataset(dataset_ref)
            logger.info(f"Dataset '{self.dataset_id}' already exists.")
        except NotFound:
            logger.info(f"Dataset '{self.dataset_id}' not found. Creating it...")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"  # Modify region if needed (e.g., "EU")
            self.client.create_dataset(dataset)
            logger.info(f"Dataset '{self.dataset_id}' created successfully.")

    def push_data(self, table_id, data, write_disposition="WRITE_TRUNCATE"):
        """
        Uploads a Pandas DataFrame to a BigQuery table.

        Args:
            table_id (str): Name of the table (e.g., 'us_corn_prices').
            data (pd.DataFrame): The data to upload.
            write_disposition (str): Action if table exists. 
                                     'WRITE_APPEND' (default) or 'WRITE_TRUNCATE' (overwrite).
        
        Returns:
            bool: True if successful.
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a Pandas DataFrame.")

        # --- FIX: COLUMN SANITIZATION ---
        # 1. Replace special chars (like %, (, ), space) with underscores
        # 2. Remove consecutive underscores
        # 3. Strip leading/trailing underscores
        data.columns = (data.columns
            .str.replace(r'[^a-zA-Z0-9_]', '_', regex=True)  # Replace invalid chars with _
            .str.replace(r'_+', '_', regex=True)             # Collapse multiple _
            .str.strip('_')                                  # Trim edges
        )
        # Example: "CV (%)" becomes "CV" or "CV_"
        # Example: "Data Item" becomes "Data_Item"
        # --------------------------------

        full_table_id = f"{self.client.project}.{self.dataset_id}.{table_id}"

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            # Automatically infer schema from the DataFrame
            autodetect=True,
            
            # Options: WRITE_TRUNCATE (overwrite), WRITE_APPEND (add to end), WRITE_EMPTY (fail if exists)
            write_disposition=write_disposition,
        )

        try:
            logger.info(f"Uploading {len(data)} rows to {full_table_id}...")
            
            job = self.client.load_table_from_dataframe(
                data, full_table_id, job_config=job_config
            )
            
            # Wait for the job to complete
            job.result()
            
            table = self.client.get_table(full_table_id)
            logger.info(f"Upload complete. Table {full_table_id} now has {table.num_rows} rows.")
            return True

        except Exception as e:
            logger.error(f"Failed to upload data to {table_id}: {e}")
            raise e