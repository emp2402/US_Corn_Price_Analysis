import logging
from datetime import datetime
import pandas as pd

# Import your custom BigQuery Client
# Assuming this class handles authentication and table insertion
from data_ingestion.src.bigquery_api_client import BigQueryClient

# Import your scraper modules
# Make sure your scraper files have a main execution function (e.g., 'run_scrape()')
from data_ingestion.src.scrape_functions import (
    scrape_corn_supply_and_demand,
    scrape_corn_condition,
    scrape_corn_plantings,
    scrape_climate_data,
    scrape_corn_price
)

# Configure logging to see what's happening in the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_ingestion_pipeline(jobs=None):
    """
    Triggers all scraping jobs, uploads data to BigQuery, and returns a summary report.
    """
    
    # Initialize the BigQuery Client
    bq_client = BigQueryClient()
    
    # Define the execution plan: (Module, Function within module, Target BigQuery Table)
    # Adjust 'run_scrape' to whatever the main function is named inside your scraper files.
    jobs_config = [
        {
            "id": "supply",
            "name": "Corn Supply & Demand",
            "module": scrape_corn_supply_and_demand,
            "target_table": "us_corn_supply_demand"
        },
        {
            "id": "conditions",
            "name": "Corn Conditions",
            "module": scrape_corn_condition,
            "target_table": "us_corn_conditions"
        },
        {
            "id": "plantings",
            "name": "Corn Plantings",
            "module": scrape_corn_plantings,
            "target_table": "us_corn_plantings"
        },
        {
            "id": "climate",
            "name": "Climate Data",
            "module": scrape_climate_data,
            "target_table": "us_climate_data"
        },
        {
            "id": "prices",
            "name": "Corn Prices",
            "module": scrape_corn_price,
            "target_table": "us_corn_prices"
        }
    ]

    if jobs:
        # Normalize to lowercase for easy matching
        jobs = [j.lower() for j in jobs]
        
        # Only keep jobs where the 'id' is in the user's list
        jobs_to_run = [
            job for job in jobs_config 
            if job["id"] in jobs
        ]
        
        # Validation: Did the user type something that doesn't exist?
        if not jobs_to_run:
            logger.error(f"No matching jobs found for inputs: {jobs}")
            logger.info(f"Available jobs: {[j['id'] for j in jobs_config]}")
            return
    else:
        # If no arguments provided, run everything
        jobs_to_run = jobs_config

    # Initialize the final report
    pipeline_report = {
        "pipeline_start_time": datetime.now().isoformat(),
        "total_jobs": len(jobs_config),
        "successful_jobs": 0,
        "failed_jobs": 0,
        "details": []
    }

    logger.info("Starting Data Ingestion Pipeline...")

    for job in jobs_to_run:
        job_report = {
            "job_name": job["name"],
            "status": "PENDING",
            "records_collected": 0,
            "upload_status": "N/A",
            "error_message": None
        }

        try:
            logger.info(f"Starting job: {job['name']}")
            
            # --- STEP 1: SCRAPE ---
            # We assume the module has a function called 'run_scrape' or similar
            # that returns a Pandas DataFrame or a list of dictionaries.
            scraped_data = job["module"].run_scrape() 
            
            # Basic validation
            if scraped_data is None or (isinstance(scraped_data, pd.DataFrame) and scraped_data.empty):
                raise ValueError("Scraper returned no data.")

            record_count = len(scraped_data)
            job_report["records_collected"] = record_count
            logger.info(f"Collected {record_count} records for {job['name']}")

            # --- STEP 2: UPLOAD TO BIGQUERY ---
            # We assume push_data returns True on success or raises an error
            upload_success = bq_client.push_data(
                table_id=job["target_table"], 
                data=scraped_data
            )
            
            job_report["upload_status"] = "SUCCESS"
            job_report["status"] = "COMPLETED"
            pipeline_report["successful_jobs"] += 1

        except Exception as e:
            # Catch ANY error so the pipeline continues to the next job
            error_msg = str(e)
            logger.error(f"Job {job['name']} failed: {error_msg}")
            
            job_report["status"] = "FAILED"
            job_report["upload_status"] = "FAILED"
            job_report["error_message"] = error_msg
            pipeline_report["failed_jobs"] += 1

        # Append individual job stats to the main report
        pipeline_report["details"].append(job_report)

    pipeline_report["pipeline_end_time"] = datetime.now().isoformat()
    logger.info("Pipeline Execution Finished.")
    
    return pipeline_report